import random
import time
from typing import Union

import cv2
import numpy as np

import utilities.color as clr
import utilities.game_launcher as launcher
import utilities.imagesearch as imsearch
import utilities.random_util as rd
from model.osrs.osrs_bot import OSRSBot
from utilities.geometry import Point


class OSRSWoodcutter(OSRSBot, launcher.Launchable):
    def __init__(self):
        bot_title = "Woodcutter"
        description = "Chops trees and banks logs using Banker's Note (for now). Position near trees and tag them."
        super().__init__(bot_title=bot_title, description=description)

        # Initialize default values
        self.running_time = 360  # Default of 60 minutes
        self.take_breaks = False
        self.tree_type = "Oak"  # Default tree type
        self.tag_color = clr.PINK  # Default tag color
        self.logs_chopped = 0
        self.failed_searches = 0

        # Define tree types and their properties
        self.tree_types = {
            "Normal": {"level": 1, "xp": 25},
            "Oak": {"level": 15, "xp": 37.5},
            "Willow": {"level": 30, "xp": 67.5},
            "Maple": {"level": 45, "xp": 100},
            "Yew": {"level": 60, "xp": 175},
            "Magic": {"level": 75, "xp": 250},
            "Mahogany": {"level": 50, "xp": 125},
        }

    def create_options(self):
        """
        Use the OptionsBuilder to define the options for the bot.
        """
        self.options_builder.add_slider_option("running_time", "How long to run (minutes)?", 1, 500)
        self.options_builder.add_checkbox_option("take_breaks", "Take breaks?", [" "])
        self.options_builder.add_dropdown_option("tree_type", "Tree type", ["Normal", "Oak", "Willow", "Maple", "Yew", "Magic", "Mahogany"])

    def save_options(self, options: dict):
        """
        Save the options from the GUI.
        """
        for option in options:
            if option == "running_time":
                self.running_time = options[option]
            elif option == "take_breaks":
                self.take_breaks = options[option] != []
            elif option == "tree_type":
                self.tree_type = options[option]
            else:
                self.log_msg(f"Unknown option: {option}")
                self.options_set = False
                return

        self.log_msg(f"Running time: {self.running_time} minutes")
        self.log_msg(f"Bot will{' ' if self.take_breaks else ' not '}take breaks")
        self.log_msg(f"Tree type: {self.tree_type}")
        self.options_set = True

    def main_loop(self):
        """
        Main bot loop with time and tree-count based inventory management
        """
        self.log_msg("Starting woodcutting bot...")
        
        # DEBUG: Print control panel and tab positions
        self.log_msg(f"Control Panel: left={self.win.control_panel.left}, top={self.win.control_panel.top}, width={self.win.control_panel.width}, height={self.win.control_panel.height}")
        self.log_msg(f"Game View: left={self.win.game_view.left}, top={self.win.game_view.top}, width={self.win.game_view.width}, height={self.win.game_view.height}")
        self.log_msg(f"Number of cp_tabs: {len(self.win.cp_tabs)}")
        if len(self.win.cp_tabs) > 3:
            tab3 = self.win.cp_tabs[3]
            self.log_msg(f"Tab 3 (Inventory) position: left={tab3.left}, top={tab3.top}, width={tab3.width}, height={tab3.height}")
            self.mouse.move_to(self.win.cp_tabs[3].random_point())
        self.mouse.click()
        time.sleep(1)

        # Main timing
        start_time = time.time()
        end_time = self.running_time * 60

        # Inventory management tracking
        successful_chops = 0
        last_camera_move = time.time()
        last_random_action = time.time()
        tree_search_failures = 0  # Track consecutive failures to find trees
        
        while time.time() - start_time < end_time:
            try:
                # Random human-like behaviors
                self.perform_random_behaviors(last_camera_move, last_random_action)
                
                # Update timers if behaviors were performed
                if random.random() < 0.15:  # 15% chance each loop
                    last_camera_move = time.time()
                if random.random() < 0.08:  # 8% chance each loop
                    last_random_action = time.time()

                # Check if inventory is full - go to bank
                if self.is_inventory_full():
                    self.log_msg("Inventory is full! Going to bank...")
                    if self.bank_items():
                        self.log_msg("Successfully banked items, resuming woodcutting...")
                        successful_chops = 0
                        time.sleep(2)
                    else:
                        self.log_msg("Failed to bank items, waiting...")
                        time.sleep(5)
                    continue

                # Find and click tree
                tree = self.find_tagged_tree()
                if not tree:
                    tree_search_failures += 1
                    self.log_msg(f"No tree found (attempt {tree_search_failures})...")
                    
                    # After 2 failed attempts, try zooming out and rotating camera
                    if tree_search_failures >= 2:
                        self.log_msg("Zooming out to search for trees...")
                        self.zoom_out()
                        time.sleep(0.5)
                        
                        self.log_msg("Rotating camera to search for trees...")
                        self.rotate_camera_to_search()
                        time.sleep(1)
                        
                        # Reset counter after searching
                        if tree_search_failures >= 4:
                            tree_search_failures = 0
                    else:
                        time.sleep(2)
                    
                    continue
                
                # Reset failure counter when tree is found
                tree_search_failures = 0
                
                # Click tree and verify chop option
                self.mouse.move_to(tree)
                time.sleep(0.5)
                
                # Debug: check what mouseover text is showing
                mouseover = self.mouseover_text()
                self.log_msg(f"Mouseover text: '{mouseover}'")
                
                if not self.mouseover_text(contains="Chop" or not self.mouseover_text(contains="Tree") or not self.mouseover_text(contains="opTr")):
                    self.log_msg("No chop option, waiting...")
                    time.sleep(1.5)
                    continue
                    
                self.mouse.click()
                time.sleep(3)

                # Wait for chopping to finish using not_woodcutting counter
                not_woodcutting_count = 0
                last_action_check = time.time()

                while True:
                    if time.time() - last_action_check >= 1.5:
                        if self.is_player_doing_action("Woodcutting"):
                            not_woodcutting_count = 0
                            self.log_msg("Still chopping...")
                            self.perform_random_behaviors(last_camera_move, last_random_action)
                        else:
                            not_woodcutting_count += 1
                            self.log_msg(f"Not chopping check #{not_woodcutting_count}")
                            if not_woodcutting_count >= 2:
                                self.log_msg("No longer chopping, looking for new tree...")
                                break
                        last_action_check = time.time()
                    time.sleep(0.1)

                # If we got here, we successfully chopped a tree
                successful_chops += 1
                self.log_msg(f"Successful chops this cycle: {successful_chops}")
                time.sleep(1)

            except Exception as e:
                self.log_msg(f"Error in main loop: {e}")
                time.sleep(2)

        self.log_msg(f"Bot finished. Total runtime: {int((time.time() - start_time) / 60)} minutes")

    def should_stop(self) -> bool:
        """Check if the bot should stop running"""
        try:
            if not self.thread:
                self.log_msg("Stop detected: Thread is None")
                return True
            if not self.thread.is_alive():
                self.log_msg("Stop detected: Thread is not alive")
                return True
            return False
        except Exception as e:
            self.log_msg(f"Error checking thread status: {str(e)}")
            return True

    def perform_random_behaviors(self, last_camera_move: float, last_random_action: float):
        """
        Perform random human-like behaviors to avoid detection.
        Includes camera movements, random mouse movements, and skill checks.
        """
        current_time = time.time()
        
        # Random camera movement every 30-90 seconds
        if current_time - last_camera_move >= random.randint(30, 90):
            if random.random() < 0.7:  # 70% chance to actually move camera
                self.random_camera_movement()
        
        # Other random actions every 45-120 seconds
        if current_time - last_random_action >= random.randint(45, 120):
            action = random.choice([
                'check_skills',
                'random_mouse',
                'check_inventory',
                'mini_camera'
            ])
            
            if action == 'check_skills':
                self.random_skill_check()
            elif action == 'random_mouse':
                self.random_mouse_movement()
            elif action == 'check_inventory':
                self.check_inventory_random()
            elif action == 'mini_camera':
                self.mini_camera_adjust()

    def random_camera_movement(self):
        """Move camera in a random direction"""
        try:
            # Randomly choose horizontal or vertical movement (or both)
            move_horizontal = random.random() < 0.6
            move_vertical = random.random() < 0.3
            
            horizontal = 0
            vertical = 0
            
            if move_horizontal:
                # Random rotation between -180 and 180 degrees
                horizontal = random.randint(-180, 180)
            
            if move_vertical:
                # Smaller vertical movements (-30 to 30 degrees)
                vertical = random.randint(-30, 30)
            
            if horizontal != 0 or vertical != 0:
                self.log_msg(f"Moving camera: H={horizontal}°, V={vertical}°")
                self.move_camera(horizontal=horizontal, vertical=vertical)
                time.sleep(random.uniform(0.3, 0.8))
        except Exception as e:
            self.log_msg(f"Error moving camera: {e}")

    def mini_camera_adjust(self):
        """Small camera adjustment - looks more natural"""
        try:
            horizontal = random.randint(-45, 45)
            self.log_msg(f"Minor camera adjustment: {horizontal}°")
            self.move_camera(horizontal=horizontal)
            time.sleep(random.uniform(0.2, 0.5))
        except Exception as e:
            self.log_msg(f"Error in mini camera adjust: {e}")

    def random_skill_check(self):
        """Randomly open skills tab to check woodcutting level"""
        try:
            if random.random() < 0.5:  # 50% chance
                self.log_msg("Checking skills tab...")
                # Click skills tab (usually tab 1)
                self.mouse.move_to(self.win.cp_tabs[1].random_point())
                self.mouse.click()
                time.sleep(random.uniform(1.0, 2.5))
                # Go back to inventory
                self.mouse.move_to(self.win.cp_tabs[3].random_point())
                self.mouse.click()
                time.sleep(random.uniform(0.3, 0.7))
        except Exception as e:
            self.log_msg(f"Error checking skills: {e}")

    def random_mouse_movement(self):
        """Move mouse to a random location on screen briefly"""
        try:
            if random.random() < 0.4:  # 40% chance
                # Move to random spot in game view
                random_point = self.win.game_view.random_point()
                self.log_msg(f"Random mouse movement to ({random_point.x}, {random_point.y})")
                self.mouse.move_to(random_point, mouseSpeed="medium")
                time.sleep(random.uniform(0.3, 1.0))
        except Exception as e:
            self.log_msg(f"Error in random mouse movement: {e}")

    def check_inventory_random(self):
        """Briefly hover over inventory items"""
        try:
            if random.random() < 0.5:  # 50% chance
                self.log_msg("Checking inventory...")
                # Make sure inventory is open
                self.mouse.move_to(self.win.cp_tabs[3].random_point())
                self.mouse.click()
                time.sleep(0.3)
                # Hover over a random inventory slot
                if hasattr(self.win, 'inventory') and self.win.inventory:
                    random_slot = random.randint(0, 27)
                    slot_rect = self.win.inventory_slots[random_slot]
                    self.mouse.move_to(slot_rect.random_point(), mouseSpeed="medium")
                    time.sleep(random.uniform(0.5, 1.5))
        except Exception as e:
            self.log_msg(f"Error checking inventory: {e}")

    def find_green_bank(self) -> Point | None:
        """
        Find the bank marked with green color.
        Returns: Point if found, None otherwise
        """
        try:
            game_view = self.win.game_view.screenshot()
            if game_view is None:
                self.log_msg("Failed to get game view screenshot")
                return None

            # Convert to HSV for better green detection
            hsv = cv2.cvtColor(game_view, cv2.COLOR_BGR2HSV)

            # Define green color range (for bright green markers)
            lower_green = np.array([40, 100, 100])
            upper_green = np.array([80, 255, 255])

            # Create mask for green color
            green_mask = cv2.inRange(hsv, lower_green, upper_green)

            # Count green pixels
            green_pixels = cv2.countNonZero(green_mask)
            self.log_msg(f"Total green pixels detected: {green_pixels}")

            # Find contours
            contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            self.log_msg(f"Number of green contours found: {len(contours)}")

            if not contours:
                self.log_msg("No green bank marker found")
                return None

            # Find largest green contour (should be the bank marker)
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            
            if area < 100:  # Minimum size threshold
                self.log_msg(f"Green marker too small (area: {area})")
                return None

            # Get bounding box
            x, y, w, h = cv2.boundingRect(largest_contour)
            
            # Calculate center point
            cx = x + w // 2
            cy = y + h // 2

            # Convert from image coordinates to screen coordinates
            screen_point = Point(
                self.win.game_view.left + cx,
                self.win.game_view.top + cy
            )

            self.log_msg(f"Found bank at (screen): ({screen_point.x}, {screen_point.y})")
            return screen_point

        except Exception as e:
            self.log_msg(f"Error finding bank: {e}")
            import traceback
            self.log_msg(f"Traceback: {traceback.format_exc()}")
            return None

    def bank_items(self) -> bool:
        """
        Navigate to bank and deposit all items.
        Returns: True if successful, False otherwise
        """
        try:
            # Try to find bank with camera rotation if needed
            max_attempts = 4
            for attempt in range(max_attempts):
                # Find the bank
                bank_location = self.find_green_bank()
                
                if bank_location:
                    break  # Found it!
                
                if attempt < max_attempts - 1:
                    # Rotate camera to look for bank
                    self.log_msg(f"Bank not found (attempt {attempt + 1}/{max_attempts}), rotating camera...")
                    self.rotate_camera_to_search()
                    time.sleep(1)
            
            if not bank_location:
                self.log_msg("Could not find bank marker after rotating camera!")
                return False

            # Click on the bank
            self.log_msg("Moving to bank...")
            self.mouse.move_to(bank_location, mouseSpeed="medium")
            time.sleep(0.5)

            # Check if we see "Bank" option
            if not self.mouseover_text(contains="Bank"):
                self.log_msg("No 'Bank' option found, trying again...")
                # Try clicking to walk there
                self.mouse.click()
                time.sleep(3)
                
                # Try finding bank again after walking
                bank_location = self.find_green_bank()
                if bank_location:
                    self.mouse.move_to(bank_location, mouseSpeed="medium")
                    time.sleep(0.5)
                    
                    if not self.mouseover_text(contains="Bank"):
                        self.log_msg("Still no 'Bank' option")
                        return False
                else:
                    return False

            # Click the bank
            self.log_msg("Clicking bank...")
            self.mouse.click()
            time.sleep(2)

            # Wait for bank interface to open
            time.sleep(1.5)

            # Deposit all items
            self.log_msg("Depositing all items...")
            return self.deposit_all()

        except Exception as e:
            self.log_msg(f"Error banking items: {e}")
            import traceback
            self.log_msg(f"Traceback: {traceback.format_exc()}")
            return False

    def rotate_camera_to_search(self):
        """
        Rotate camera using middle mouse button drag to search for objects.
        Uses realistic human-like mouse movement with Bezier curves.
        """
        try:
            import pyautogui as pag
            
            # Get a point in the middle of the game view
            center = self.win.game_view.get_center()
            start_point = Point(center.x, center.y)
            
            # Move to center with human-like movement
            self.mouse.move_to(start_point, mouseSpeed="fast")
            time.sleep(random.uniform(0.05, 0.15))
            
            # Hold middle mouse button
            pag.mouseDown(button='middle')
            time.sleep(random.uniform(0.05, 0.1))
            
            # Calculate end point for camera rotation
            # Rotate 90-180 degrees in a random direction
            rotation_distance = random.randint(150, 300)
            direction = random.choice([-1, 1])  # Left or right
            
            # Add slight vertical component (pitch adjustment)
            vertical_offset = random.randint(-40, 40)
            
            end_point = Point(
                start_point.x + (rotation_distance * direction),
                start_point.y + vertical_offset
            )
            
            # Use human-like Bezier curve movement while holding middle mouse
            self.mouse.move_to(end_point, mouseSpeed="medium")
            time.sleep(random.uniform(0.05, 0.1))
            
            # Release middle mouse button
            pag.mouseUp(button='middle')
            time.sleep(random.uniform(0.2, 0.4))
            
            self.log_msg(f"Rotated camera {'right' if direction > 0 else 'left'} (~{rotation_distance}px)")
            
        except Exception as e:
            self.log_msg(f"Error rotating camera: {e}")
            import traceback
            self.log_msg(f"Traceback: {traceback.format_exc()}")

    def zoom_out(self):
        """
        Zoom out the camera by scrolling down (negative scroll).
        This helps see more of the game area when searching for objects.
        """
        try:
            import pyautogui as pag
            
            # Move mouse to center of game view
            center = self.win.game_view.get_center()
            pag.moveTo(center.x, center.y)
            time.sleep(random.uniform(0.15, 0.25))
            
            # Scroll down to zoom out (larger amount for visibility)
            # Negative values zoom out in OSRS
            scroll_clicks = random.randint(4, 7)
            pag.scroll(-scroll_clicks * 120)  # Multiply by 120 for full scroll units
            
            time.sleep(random.uniform(0.2, 0.3))
            self.log_msg(f"Zoomed out camera ({scroll_clicks} clicks)")
            
        except Exception as e:
            self.log_msg(f"Error zooming out: {e}")

    def deposit_all(self) -> bool:
        """
        Deposit all logs in inventory by shift-clicking them.
        Returns: True if successful, False otherwise
        """
        try:
            import pyautogui as pag
            
            # Wait for bank interface to be fully loaded
            time.sleep(0.8)
            
            # Shift-click the first few inventory slots to deposit all
            self.log_msg("Depositing items with shift-click...")
            
            # Select a random inventory slot to shift-click
            random_slot_index = random.randint(0, min(19, len(self.win.inventory_slots) - 1))
            slot = self.win.inventory_slots[random_slot_index]
            
            pag.keyDown('shift')
            time.sleep(0.1)
            self.mouse.move_to(slot.random_point(), mouseSpeed="fastest")
            time.sleep(0.1)
            self.mouse.click()
            time.sleep(0.1)
            pag.keyUp('shift')
            time.sleep(0.5)
            
            # Close bank interface
            self.log_msg("Closing bank...")
            pag.press('escape')
            time.sleep(0.8)
            
            self.log_msg("Banking complete!")
            return True

        except Exception as e:
            self.log_msg(f"Error depositing items: {e}")
            import traceback
            self.log_msg(f"Traceback: {traceback.format_exc()}")
            return False

    def find_tagged_tree(self) -> Point | None:
        """
        Find nearest tagged tree using color detection.
        Returns: Point if found, None otherwise
        """
        try:
            # Take screenshot of game view
            game_view = self.win.game_view.screenshot()

            if game_view is None:
                self.log_msg("Failed to get game view screenshot")
                return None

            # Log image dimensions
            h, w = game_view.shape[:2]
            self.log_msg(f"Game view dimensions: {w}x{h}")

            # Convert to HSV for better pink detection
            hsv = cv2.cvtColor(game_view, cv2.COLOR_BGR2HSV)

            # Define pink color range
            lower_pink = np.array([145, 30, 180])
            upper_pink = np.array([175, 255, 255])

            # Create mask for pink color
            pink_mask = cv2.inRange(hsv, lower_pink, upper_pink)

            # Count pink pixels
            pink_pixels = cv2.countNonZero(pink_mask)
            self.log_msg(f"Total pink pixels detected: {pink_pixels}")

            # Find contours
            contours, _ = cv2.findContours(pink_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            self.log_msg(f"Number of contours found: {len(contours)}")

            if not contours:
                self.log_msg("No pink contours found")
                return None

            # Get center point of game view for distance calculation
            center = self.win.game_view.get_center()
            self.log_msg(f"Game view center: ({center.x}, {center.y})")

            # Find closest valid tree contour
            closest_tree = None
            min_distance = float("inf")

            # Log details for each contour
            for i, contour in enumerate(contours):
                area = cv2.contourArea(contour)
                perimeter = cv2.arcLength(contour, True)
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h != 0 else 0

                self.log_msg(f"Contour {i}:")
                self.log_msg(f"  Area: {area}")
                self.log_msg(f"  Perimeter: {perimeter}")
                self.log_msg(f"  Bounding box: x={x}, y={y}, w={w}, h={h}")
                self.log_msg(f"  Aspect ratio: {aspect_ratio}")

                # Check if contour matches tree criteria
                if 1000 < area < 30000 and 0.8 < aspect_ratio < 1.2 and abs(w - h) < 50:
                    # Calculate center point - move slightly towards the trunk
                    cx = x + w // 2
                    cy = y + int(h * 0.6)  # Aim 60% down from the top
                    distance = ((cx - center.x) ** 2 + (cy - center.y) ** 2) ** 0.6

                    self.log_msg(f"  Distance from center: {distance}")
                    self.log_msg(f"  Valid contour: Yes")

                    if distance < min_distance:
                        min_distance = distance
                        # Store more info about the tree
                        closest_tree = {"center": Point(cx, cy), "width": w, "height": h, "area": area}
                else:
                    self.log_msg(f"  Valid contour: No (failed validation checks)")

            if closest_tree:
                import random

                # Calculate random point inside the tree (avoiding edges)
                w_offset = closest_tree["width"] // 4
                h_offset = closest_tree["height"] // 4
                offset_x = random.randint(-w_offset, w_offset)
                offset_y = random.randint(-h_offset, h_offset)

                # Calculate point relative to the screenshot
                image_point = Point(closest_tree["center"].x + offset_x, closest_tree["center"].y + offset_y)

                # Convert from image coordinates to screen coordinates
                # Add the game_view's screen offset
                screen_point = Point(
                    self.win.game_view.left + image_point.x,
                    self.win.game_view.top + image_point.y
                )

                self.log_msg(f"Selected tree center at (image): ({closest_tree['center'].x}, {closest_tree['center'].y})")
                self.log_msg(f"Click target (image): ({image_point.x}, {image_point.y})")
                self.log_msg(f"Click target (screen): ({screen_point.x}, {screen_point.y})")
                return screen_point

            return None

        except Exception as e:
            self.log_msg(f"Error finding tree: {e}")
            import traceback

            self.log_msg(f"Traceback: {traceback.format_exc()}")
            return None

    def is_inventory_full(self) -> bool:
        """
        Check if inventory is full by counting filled slots
        """
        try:
            # Check for the inventory full message in game text
            if self.get_game_message("Your inventory is too full"):
                self.log_msg("Inventory full message found!")
                return True

            # Count non-empty inventory slots
            filled_slots = 0
            for slot in self.win.inventory_slots:
                slot_img = slot.screenshot()
                if slot_img is None:
                    continue
                
                # Check if slot has content by looking at brightness and color variance
                # Empty slots are uniform dark brown, items are brighter with more variation
                mean_color = cv2.mean(slot_img)[:3]
                avg_brightness = sum(mean_color) / 3
                
                # Calculate standard deviation to detect texture/variation
                std_dev = np.std(slot_img)
                
                # Item detected if: bright enough OR has significant variation (texture)
                if avg_brightness > 70 or std_dev > 15:
                    filled_slots += 1
            
            self.log_msg(f"Inventory slots filled: {filled_slots}/28")
            if filled_slots >= 28:
                self.log_msg("All inventory slots are filled!")
                return True

            return False

        except Exception as e:
            self.log_msg(f"Error checking inventory: {e}")
            return False

    def get_chat_text(self) -> str | None:
        """
        Get text from the chat area using OCR
        """
        try:
            # Take screenshot of chat area
            chat_area = self.win.chat_area.screenshot()

            if chat_area is None:
                return None

            # Convert to grayscale
            gray = cv2.cvtColor(chat_area, cv2.COLOR_BGR2GRAY)

            # Threshold to get black text
            _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)

            # Use OCR to get text
            text = pytesseract.image_to_string(thresh)

            return text

        except Exception as e:
            self.log_msg(f"Error getting chat text: {e}")
            return None

    def get_empty_inventory_slots(self) -> list:
        """
        Get list of empty inventory slots by checking slot colors.
        Returns: List of empty slot indices
        """
        empty_slots = []

        for i, slot in enumerate(self.win.inventory_slots):
            # Take small screenshot of slot
            slot_img = slot.screenshot()

            # Check if slot has the inventory background color
            if self.is_slot_empty(slot_img):
                empty_slots.append(i)

        return empty_slots

    def is_slot_empty(self, slot_img) -> bool:
        """
        Check if an inventory slot is empty by looking for the background color.
        Args:
            slot_img: Screenshot of the inventory slot
        Returns: True if slot is empty, False otherwise
        """
        if slot_img is None:
            return False

        try:
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(slot_img, cv2.COLOR_BGR2HSV)

            # Define inventory background color range in HSV
            lower = np.array([0, 0, 20])  # Dark grey
            upper = np.array([180, 30, 80])

            # Create mask for background color
            mask = cv2.inRange(hsv, lower, upper)

            # Calculate percentage of background color
            total_pixels = slot_img.shape[0] * slot_img.shape[1]
            if total_pixels == 0:
                return False

            background_pixels = cv2.countNonZero(mask)
            background_percentage = (background_pixels / total_pixels) * 100

            return background_percentage > 90  # Slot is empty if >90% matches background

        except Exception as e:
            self.log_msg(f"Error checking slot: {e}")
            return False

    def is_chopping(self) -> bool:
        """
        Check if the player is currently chopping by looking for the woodcutting animation.
        Returns: True if chopping, False otherwise
        """
        return self.is_player_doing_action("Woodcutting")

    def wait_for_chopping_to_start(self, timeout: int = 10) -> bool:
        """
        Wait for the chopping animation to start.
        Args:
            timeout: Maximum time to wait in seconds
        Returns: True if chopping started, False if timeout
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_chopping():
                return True
            time.sleep(0.1)
        return False

    def take_break(self):
        """
        Takes a short break between actions.
        """
        if not self.take_breaks:
            return

        if rd.random_chance(0.1):  # 10% chance to take break
            break_time = rd.random_int(1, 5)
            self.log_msg(f"Taking a short break ({break_time}s)")
            time.sleep(break_time)

    def take_debug_screenshot(self, reason: str):
        """
        Takes a screenshot and saves it with timestamp and reason
        """
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"debug_{reason}_{timestamp}.png"

            # Save screenshot of game view
            screenshot = self.win.game_view.screenshot()
            if screenshot is not None:
                import cv2

                cv2.imwrite(filename, screenshot)
                self.log_msg(f"Debug screenshot saved: {filename}")
        except Exception as e:
            self.log_msg(f"Error taking debug screenshot: {str(e)}")

    def chatbox_text(self, contains: str = None) -> Union[bool, str]:
        """
        Examines the chatbox for text. Currently only captures player chat text.
        Args:
            contains: The text to search for (single word or phrase). Case sensitive. If left blank,
                      returns all text in the chatbox.
        Returns:
            True if exact string is found, False otherwise.
            If args are left blank, returns the text in the chatbox.
        """
        if contains is None:
            return ocr.extract_text(self.win.chat, ocr.PLAIN_12, clr.BLUE)
        if ocr.find_text(contains, self.win.chat, ocr.PLAIN_12, clr.BLUE):
            return True
