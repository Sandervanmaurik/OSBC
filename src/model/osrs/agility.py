"""
A bot that completes agility courses in OSRS.
"""

import random
import time
from model.bot import BotStatus
import utilities.color as clr
import utilities.random_util as rd
from utilities.geometry import Point, Rectangle
from model.osrs.osrs_bot import OSRSBot
from utilities.options_builder import OptionsBuilder
from utilities.behavior import BotBehaviorConfig
import cv2


class AgilityBot(OSRSBot):
    def __init__(self):
        bot_title = "Agility Bot"
        description = "Completes agility courses automatically."
        # Pass behavior config to parent for proper initialization
        super().__init__(
            bot_title=bot_title,
            description=description,
            behavior_config=BotBehaviorConfig.skilling(),
        )
        self.primary_skill = "agility"

        self.obstacle_color = clr.GREEN
        self.mark_color = clr.RED
        self.stuck_counter = 0
        self.no_obstacle_count = 0
        self.obstacle_count = 0
        self.runtime_minutes = 60  # Default runtime in minutes
        self.continue_color = clr.GREEN  # Color([170, 0, 255])
        self.continue2_color = clr.OFF_GREEN  # Color([255, 0, 231])
        self.last_continue = None  # Track which continue was last used
        self.last_was_continue = False  # Track if last action was a continue

        # Default options
        self.course = "Gnome"  # Default agility course

        # Enable default options - can be customized via Options button
        self.options_set = True

        # Define number of obstacles per course
        self.course_obstacles = {
            "Seers": 6,
            "Gnome": 6,
            "Draynor": 6,
            "Al Kharid": 6,
            "Varrock": 6,
            "Canifis": 7,  # Canifis has 7 obstacles
        }

    def create_options(self):
        """
        Use the OptionsBuilder to define the options for the bot.
        """
        self.options_builder.add_dropdown_option(
            "course",
            "Agility Course",
            ["Seers", "Gnome", "Draynor", "Al Kharid", "Varrock", "Canifis"],
        )
        self.options_builder.add_text_edit_option(
            "runtime", "Runtime (minutes, 1-3600)", "60"
        )

    def save_options(self, options: dict):
        """
        Save the options from the GUI and validate runtime
        """
        self.options = options
        self.course = options["course"]

        # Validate and convert runtime
        try:
            runtime = int(options["runtime"])
            if runtime < 1 or runtime > 3600:
                self.log_msg(
                    "Runtime must be between 1 and 3600 minutes. Setting to 60 minutes."
                )
                runtime = 60
        except ValueError:
            self.log_msg("Invalid runtime value. Setting to 60 minutes.")
            runtime = 60

        self.runtime_minutes = runtime
        self.log_msg(f"Bot will run for {self.runtime_minutes} minutes")
        self.options_set = True

    def is_character_moving(self):
        """
        Checks if the character is currently moving by comparing screenshots
        Returns: True if character is moving, False otherwise
        """
        # Take first screenshot
        screenshot1 = self.win.game_view.screenshot()
        self.behavior.timing.sleep((0.2, 0.4))
        # Take second screenshot
        screenshot2 = self.win.game_view.screenshot()

        # Compare the two screenshots
        diff = cv2.absdiff(screenshot1, screenshot2)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Calculate total area of changes
        total_change = sum(cv2.contourArea(c) for c in contours)
        self.log_msg(f"Movement detection - change area: {total_change}")

        return total_change > 1000  # Adjust threshold as needed

    def wait_for_movement_to_stop(self, timeout=10):
        """
        Waits for character movement to stop
        Args:
            timeout: Maximum time to wait in seconds
        """
        start_time = time.time()
        consecutive_still = 0

        while time.time() - start_time < timeout:
            if not self.is_character_moving():
                consecutive_still += 1
                if consecutive_still >= 2:  # Need 2 consecutive still checks
                    self.log_msg("Character stopped moving")
                    return True
            else:
                consecutive_still = 0
            self.behavior.timing.sleep((0.4, 0.6))

        self.log_msg("Movement wait timed out")
        return False

    def is_at_course_end(self):
        """
        Checks if we're at the end of the course by looking for blue tiles
        Returns: True if at course end, False otherwise
        """
        self.log_msg("Checking for course end...")

        # Take screenshot of game view
        game_view = self.win.game_view.screenshot()

        # Look for blue tiles
        blue_mask = clr.isolate_colors(game_view, [clr.BLUE])
        contours, _ = cv2.findContours(
            blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if contours:
            # Calculate total blue area
            total_blue_area = sum(cv2.contourArea(c) for c in contours)
            self.log_msg(f"Found blue area: {total_blue_area}")

            # Save debug image if significant blue area found
            if total_blue_area > 1000:
                debug_img = game_view.copy()
                cv2.drawContours(debug_img, contours, -1, (255, 0, 0), 2)
                cv2.imwrite("debug_end_blue.png", debug_img)

                self.log_msg("Course end detected (blue tiles found)")
                self.obstacle_count = 0  # Reset counter
                return True

        return False

    def find_mark_of_grace(self):
        """
        Finds a mark of grace on screen
        Returns: Rectangle containing the mark, or None if not found
        """
        self.log_msg("Searching for mark of grace...")
        game_view = self.win.game_view.screenshot()

        red_mask = clr.isolate_colors(game_view, [self.mark_color])
        contours, _ = cv2.findContours(
            red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if contours:
            self.log_msg(f"Found {len(contours)} red objects")

            # Filter and sort contours by area
            valid_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w) / h
                self.log_msg(
                    f"Red object - Area: {area}, Size: {w}x{h}, Aspect ratio: {aspect_ratio:.2f}"
                )

                # More lenient size range for marks (adjusted based on logs)
                if (
                    10 < area < 10000 and 0.5 < aspect_ratio < 1.5
                ):  # Increased upper limit, added aspect ratio check
                    valid_contours.append((area, contour))
                    self.log_msg(
                        f"Valid mark of grace candidate found with area: {area}"
                    )

            if valid_contours:
                # Sort by area and get the most likely mark
                valid_contours.sort(key=lambda x: x[0])  # Sort by area
                area, mark_contour = valid_contours[0]  # Get smallest valid contour

                x, y, w, h = cv2.boundingRect(mark_contour)

                # Translate coordinates relative to game window
                game_view_rect = self.win.game_view
                abs_x = game_view_rect.left + x
                abs_y = game_view_rect.top + y

                self.log_msg(
                    f"Found mark of grace at: ({abs_x}, {abs_y}) with size: {w}x{h}"
                )
                return Rectangle(abs_x, abs_y, w, h)
            else:
                self.log_msg("No contours passed the size/shape filters")

        self.log_msg("No valid marks of grace found")
        return None

    def main_loop(self):
        """
        Main bot loop with proper runtime handling
        """
        self.log_msg("Starting Agility Bot...")
        self.setup_camera()
        last_obstacle_pos = None
        fails = 0
        self.obstacle_count = 0

        # Use timed_session for runtime management (already in minutes)
        self.log_msg(f"Bot will run for {self.runtime_minutes} minutes")

        with self.timed_session(self.runtime_minutes) as session:
            while session.running:
                # Check for breaks
                if self.behavior.breaks.should_take_break():
                    self.log_msg("Taking a break...")
                    self.behavior.breaks.take_break()
                    continue

                try:
                    # First check if we're at course end
                    if self.is_at_course_end():
                        self.log_msg("Reached end of course, continuing...")
                        self.behavior.timing.sleep((0.8, 1.2))
                        continue

                    # Find next obstacle first
                    obstacle = self.find_next_obstacle()

                    if obstacle:
                        self.log_msg("Found obstacle...")
                        self.no_obstacle_count = 0
                        self.last_was_continue = False
                        self.last_continue = None

                        # Check if we're stuck on same obstacle
                        current_pos = (obstacle.left, obstacle.top)
                        if last_obstacle_pos == current_pos:
                            self.stuck_counter += 1
                            self.log_msg(
                                f"Same obstacle detected {self.stuck_counter} times"
                            )
                        else:
                            self.stuck_counter = 0
                            self.log_msg("New obstacle found")
                        last_obstacle_pos = current_pos

                        # If stuck for too long, stop the bot
                        if self.stuck_counter > 5:
                            self.log_msg(
                                "Stuck on same obstacle for too long! Stopping bot..."
                            )
                            # Take debug screenshot
                            debug_img = self.win.game_view.screenshot()
                            cv2.imwrite("debug_stuck_obstacle.png", debug_img)
                            self.status = BotStatus.STOPPED
                            break

                        # Click the obstacle with some randomization
                        click_point = obstacle.random_point()
                        self.log_msg(f"Clicking obstacle at: {click_point}")
                        self.interaction_pre_click_delay()
                        self.behavior.mouse.move_to(click_point, mouseSpeed="fast")
                        self.behavior.mouse.click()

                        self.obstacle_count += 1
                        self.log_msg(
                            f"Completed obstacle {self.obstacle_count} of {self.course_obstacles.get(self.course, '?')}"
                        )

                        # Add delay based on course type
                        if self.course == "Canifis":
                            self.behavior.timing.sleep((1.3, 1.7))
                        else:
                            self.behavior.timing.sleep((0.4, 0.6))

                        # Wait for movement to complete with randomized timeout
                        if self.course == "Canifis":
                            timeout = rd.truncated_normal_sample(
                                13, 17, mean=15, std=1.2
                            )  # 13-17 seconds
                        else:
                            timeout = rd.truncated_normal_sample(
                                8, 12, mean=10, std=1.2
                            )  # 8-12 seconds
                        self.wait_for_movement_to_stop(timeout)

                        # Occasionally perform random behaviors
                        if rd.random_chance(0.15):
                            self.behavior.attention.perform_random_behaviors()

                        continue

                    # Then check for mark of grace if no obstacle found
                    mark = self.find_mark_of_grace()
                    if mark:
                        self.log_msg("Found mark of grace - collecting...")
                        self.interaction_pre_click_delay()
                        self.behavior.mouse.move_to(
                            mark.random_point(), mouseSpeed="fast"
                        )
                        self.behavior.mouse.click()
                        self.behavior.timing.sleep((0.4, 0.6))
                        self.wait_for_movement_to_stop()
                        self.last_was_continue = False
                        # Trigger profile cycling on mark collection
                        self.behavior.on_inventory_complete()

                        # Occasionally perform random behaviors
                        if rd.random_chance(0.15):
                            self.behavior.attention.perform_random_behaviors()
                        continue

                    # Try to find continue squares if no obstacle or mark found
                    continue_square = None
                    if not self.last_was_continue:
                        # Try first continue square
                        continue_square = self.find_continue_square(1)
                    elif self.last_continue == 1:
                        # If we just used continue1, try continue2
                        continue_square = self.find_continue_square(2)

                    if continue_square:
                        self.log_msg("Found continue square...")
                        self.interaction_pre_click_delay()
                        self.behavior.mouse.move_to(
                            continue_square.random_point(), mouseSpeed="fast"
                        )
                        self.behavior.mouse.click()
                        self.behavior.timing.sleep((0.4, 0.6))
                        self.wait_for_movement_to_stop()
                        self.last_was_continue = True
                        self.last_continue = 2 if self.last_continue == 1 else 1
                        self.no_obstacle_count = 0

                        # Occasionally perform random behaviors
                        if rd.random_chance(0.15):
                            self.behavior.attention.perform_random_behaviors()
                    else:
                        self.log_msg(
                            f"No obstacle or continue square found (count: {self.no_obstacle_count})"
                        )
                        self.no_obstacle_count += 1

                        # Use progressive recovery actions (similar to mining bot)
                        if self.no_obstacle_count <= 8:
                            self.log_msg(
                                f"Performing recovery action {self.no_obstacle_count}..."
                            )
                            self.perform_search_recovery(self.no_obstacle_count - 1)
                            self.behavior.timing.sleep((0.6, 1.2))
                        else:
                            self.log_msg(
                                "No obstacles found after recovery attempts! Stopping bot..."
                            )
                            # Take final debug screenshot
                            debug_img = self.win.game_view.screenshot()
                            cv2.imwrite("debug_no_obstacles_final.png", debug_img)
                            self.status = BotStatus.STOPPED
                            break

                    self.update_progress(0.5)

                except Exception as e:
                    self.log_msg(f"Error in main loop: {str(e)}")
                    fails += 1
                    if fails > 5:
                        self.log_msg("Too many errors, stopping bot...")
                        # Take final debug screenshot
                        debug_img = self.win.game_view.screenshot()
                        cv2.imwrite("debug_error_final.png", debug_img)
                        self.status = BotStatus.STOPPED
                        break
                    self.behavior.timing.sleep((1.3, 1.7))

        self.log_msg(
            f"Runtime of {self.runtime_minutes} minutes completed. Stopping bot..."
        )

    def find_next_obstacle(self):
        """
        Finds the next green highlighted obstacle on screen
        Returns: Rectangle containing the obstacle, or None if not found
        """
        self.log_msg("Searching for next obstacle...")
        game_view = self.win.game_view.screenshot()

        # Isolate green color
        green_mask = clr.isolate_colors(game_view, [self.obstacle_color])
        cv2.imwrite("debug_obstacle_mask.png", green_mask)

        # Find contours in the mask
        contours, _ = cv2.findContours(
            green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if contours:
            self.log_msg(f"Found {len(contours)} green objects")

            # Filter contours by area
            valid_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)
                self.log_msg(f"Found green object with area: {area}")
                # Adjusted area range to include larger obstacles
                if 100 < area < 100000:  # Increased upper limit
                    valid_contours.append(contour)
                    self.log_msg(f"Valid green object found with area: {area}")

            if not valid_contours:
                self.log_msg("No valid obstacles found (all objects were wrong size)")
                return None

            # Get the largest valid contour
            largest_contour = max(valid_contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            x, y, w, h = cv2.boundingRect(largest_contour)

            # Additional shape filtering (more lenient)
            aspect_ratio = float(w) / h
            self.log_msg(
                f"Selected obstacle - Area: {area}, Size: {w}x{h}, Aspect ratio: {aspect_ratio:.2f}"
            )

            # More lenient aspect ratio filtering
            if aspect_ratio < 0.1 or aspect_ratio > 10:
                self.log_msg("Obstacle rejected - bad aspect ratio")
                return None

            # Add some padding
            padding = 3
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = w + padding * 2
            h = h + padding * 2

            # Translate coordinates relative to game window
            game_view_rect = self.win.game_view
            abs_x = game_view_rect.left + x
            abs_y = game_view_rect.top + y

            self.log_msg(
                f"Found valid obstacle at: ({abs_x}, {abs_y}) with size: {w}x{h}"
            )
            return Rectangle(abs_x, abs_y, w, h)

        self.log_msg("No green objects found")
        return None

    def is_lap_complete(self):
        """
        Checks if a lap was completed by looking for XP drop
        Returns: True if lap complete, False otherwise
        """
        # Look for agility XP drop in the chat
        return bool(self.mouseover_text(contains="You completed a lap", color=clr.BLUE))

    def setup_camera(self):
        """
        Sets up the camera angle for optimal obstacle detection
        """
        self.log_msg("Setting up camera...")
        # Set compass North
        self.set_compass_north()
        # Set camera to highest angle
        self.move_camera(vertical=90)

    def perform_search_recovery(self, attempt: int):
        """
        Progressive recovery actions when obstacles aren't found.

        Similar to mining bot's _run_recovery, cycles through different
        camera adjustments to find green tiles that are off-screen.

        Args:
            attempt: The attempt number (0-7), cycles through 6 recovery actions
        """
        import pyautogui as pag

        stage = attempt % 6  # Cycle through 6 different recovery actions

        if stage == 0:
            # Light camera rotation left/right
            self.log_msg("Recovery: Light camera rotation")
            key = "left" if rd.random_chance(0.5) else "right"
            if self._safe_key_down(key):
                try:
                    duration = rd.truncated_normal_sample(0.4, 0.9, mean=0.65, std=0.15)
                    self.behavior.timing.sleep((duration, duration))
                finally:
                    self._safe_key_up(key)

        elif stage == 1:
            # Zoom out for wider view
            self.log_msg("Recovery: Zoom out for wider view")
            try:
                if self._ensure_focus():
                    center = self.win.game_view.get_center()
                    self.behavior.mouse.move_to(center, mouseSpeed="fast")
                    self.behavior.timing.sleep((0.1, 0.2))
                    scroll_clicks = int(
                        rd.truncated_normal_sample(3, 5, mean=4, std=0.6)
                    )
                    for _ in range(scroll_clicks):
                        pag.scroll(-240)
                        self.behavior.timing.sleep((0.05, 0.12))
            except Exception as exc:
                self.log_msg(f"Zoom out error: {exc}")

        elif stage == 2:
            # Larger rotation
            self.log_msg("Recovery: Large camera rotation")
            key = "left" if rd.random_chance(0.5) else "right"
            if self._safe_key_down(key):
                try:
                    duration = rd.truncated_normal_sample(1.0, 1.8, mean=1.4, std=0.25)
                    self.behavior.timing.sleep((duration, duration))
                finally:
                    self._safe_key_up(key)

        elif stage == 3:
            # Zoom in for closer view
            self.log_msg("Recovery: Zoom in for closer view")
            try:
                if self._ensure_focus():
                    center = self.win.game_view.get_center()
                    self.behavior.mouse.move_to(center, mouseSpeed="fast")
                    self.behavior.timing.sleep((0.1, 0.2))
                    scroll_clicks = int(
                        rd.truncated_normal_sample(2, 4, mean=3, std=0.6)
                    )
                    for _ in range(scroll_clicks):
                        pag.scroll(240)
                        self.behavior.timing.sleep((0.05, 0.12))
            except Exception as exc:
                self.log_msg(f"Zoom in error: {exc}")

        elif stage == 4:
            # Mini camera adjustment (vertical + small horizontal)
            self.log_msg("Recovery: Mini camera adjustment")
            try:
                # Vertical adjustment
                if rd.random_chance(0.7):
                    v_key = "up" if rd.random_chance(0.5) else "down"
                    if self._safe_key_down(v_key):
                        try:
                            duration = rd.truncated_normal_sample(
                                0.2, 0.5, mean=0.35, std=0.1
                            )
                            self.behavior.timing.sleep((duration, duration))
                        finally:
                            self._safe_key_up(v_key)
                        self.behavior.timing.sleep((0.1, 0.2))

                # Small horizontal adjustment
                if rd.random_chance(0.6):
                    h_key = "left" if rd.random_chance(0.5) else "right"
                    if self._safe_key_down(h_key):
                        try:
                            duration = rd.truncated_normal_sample(
                                0.3, 0.6, mean=0.45, std=0.1
                            )
                            self.behavior.timing.sleep((duration, duration))
                        finally:
                            self._safe_key_up(h_key)
            except Exception as exc:
                self.log_msg(f"Mini camera adjust error: {exc}")

        elif stage == 5:
            # Full rotation to opposite direction
            self.log_msg("Recovery: Full opposite rotation")
            key = random.choice(["left", "right"])
            if self._safe_key_down(key):
                try:
                    # Very long duration for near-180° turn
                    duration = rd.truncated_normal_sample(1.8, 2.8, mean=2.3, std=0.3)
                    self.behavior.timing.sleep((duration, duration))
                finally:
                    self._safe_key_up(key)

    def find_continue_square(self, continue_num=1):
        """
        Finds a continue square (purple or pink) on screen
        Args:
            continue_num: 1 for first continue (purple), 2 for second continue (pink)
        Returns: Rectangle containing the square, or None if not found
        """
        self.log_msg(f"Searching for continue square {continue_num}...")
        game_view = self.win.game_view.screenshot()

        # Select color based on continue number
        color = self.continue2_color if continue_num == 2 else self.continue_color
        color_name = "PINK" if continue_num == 2 else "GREEN"
        self.log_msg(f"Using color: {color_name}")
        self.log_msg(f"Color values - Lower: {color.lower}, Upper: {color.upper}")

        # Create and save color mask
        continue_mask = clr.isolate_colors(game_view, [color])
        cv2.imwrite(f"debug_continue{continue_num}_mask.png", continue_mask)

        contours, _ = cv2.findContours(
            continue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if contours:
            self.log_msg(f"Found {len(contours)} continue squares")

            # Draw all contours on debug image
            debug_img = game_view.copy()
            cv2.drawContours(debug_img, contours, -1, (0, 255, 0), 2)
            cv2.imwrite(f"debug_continue{continue_num}_contours.png", debug_img)

            # Filter and sort contours by area
            valid_contours = []
            for i, contour in enumerate(contours):
                area = cv2.contourArea(contour)
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w) / h if h != 0 else 0
                self.log_msg(
                    f"Contour {i}: Area={area}, Size={w}x{h}, Aspect ratio={aspect_ratio:.2f}"
                )

                if 1000 < area < 100000:  # Adjust these values based on testing
                    valid_contours.append((area, contour))
                    self.log_msg(f"Valid continue square found with area: {area}")

            if valid_contours:
                # Get the largest valid contour
                valid_contours.sort(key=lambda x: x[0], reverse=True)
                area, continue_contour = valid_contours[0]

                x, y, w, h = cv2.boundingRect(continue_contour)
                self.log_msg(f"Selected contour: Area={area}, Size={w}x{h}")

                # Draw selected contour in different color
                cv2.drawContours(debug_img, [continue_contour], -1, (0, 0, 255), 3)
                cv2.imwrite(f"debug_continue{continue_num}_selected.png", debug_img)

                # Translate coordinates relative to game window
                game_view_rect = self.win.game_view
                abs_x = game_view_rect.left + x
                abs_y = game_view_rect.top + y

                return Rectangle(abs_x, abs_y, w, h)
            else:
                self.log_msg("No valid contours found within size constraints")
        else:
            self.log_msg("No contours found at all")

        return None
