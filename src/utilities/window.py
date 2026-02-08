"""
This class contains functions for interacting with the game client window. All Bot classes have a
Window object as a property. This class allows you to locate important points/areas on screen no
matter where the game client is positioned. This class can be extended to add more functionality
(See RuneLiteWindow within runelite_bot.py for an example).

At the moment, it only works for 2007-style interfaces. In the future, to accomodate other interface
styles, this class should be abstracted, then extended for each interface style.
"""

import time
from typing import List, Optional
from contextlib import contextmanager

import pywinctl
from deprecated import deprecated

import utilities.color as clr
import utilities.debug as debug
import utilities.imagesearch as imsearch
import utilities.ocr as ocr
from utilities.geometry import Point, Rectangle
from utilities.machine_config import get_machine_config
from platform_utils.window import create_window, PlatformWindow


def get_character_from_title(title: str) -> str:
    """Extract character name from RuneLite window title.

    RuneLite titles are formatted as: 'RuneLite - characterName'

    Args:
        title: Window title to parse

    Returns:
        Character name if found, empty string otherwise
    """
    if " - " in title:
        return title.split(" - ", 1)[1].strip()
    return ""


def find_runelite_by_character(character_name: str) -> "pywinctl.Window":
    """Find a RuneLite window for a specific character.

    Args:
        character_name: The character name to search for

    Returns:
        The pywinctl Window if found, None otherwise
    """
    windows = pywinctl.getWindowsWithTitle("RuneLite", condition=2)
    for win in windows:
        if get_character_from_title(win.title) == character_name:
            return win
    return None


def get_all_runelite_windows():
    """Get all RuneLite windows with their character names.

    Returns:
        List of (character_name, window) tuples
    """
    windows = pywinctl.getWindowsWithTitle("RuneLite", condition=2)
    result = []
    for win in windows:
        char_name = get_character_from_title(win.title)
        result.append((char_name, win))
    return result


class WindowInitializationError(Exception):
    """
    Exception raised for errors in the Window class.
    """

    def __init__(self, message=None):
        if message is None:
            message = (
                "Failed to initialize window. Make sure the client is NOT in 'Resizable-Modern' "
                "mode. Make sure you're using the default client configuration (E.g., Opaque UI, status orbs ON)."
            )
        super().__init__(message)


class BankDetectionError(Exception):
    """
    Exception raised when bank interface cannot be detected.
    This typically occurs when:
    - Bank is not open
    - Bank title 'The Bank of Gielinor' is not visible
    - Window initialization has not completed (game_view or control_panel missing)
    """

    def __init__(
        self,
        message="Failed to detect bank interface. Ensure bank is open and 'The Bank of Gielinor' title is visible.",
    ):
        super().__init__(message)


class Window:
    client_fixed: bool = None

    # CP Area
    control_panel: Rectangle = None  # https://i.imgur.com/BeMFCIe.png
    cp_tabs: List[Rectangle] = []  # https://i.imgur.com/huwNOWa.png
    inventory_slots: List[Rectangle] = []  # https://i.imgur.com/gBwhAwE.png
    skill_slots: List[Rectangle] = []
    skill_total_level: Rectangle = None
    spellbook_normal: List[Rectangle] = []  # https://i.imgur.com/vkKAfV5.png
    prayers: List[Rectangle] = []  # https://i.imgur.com/KRmC3YB.png

    # Chat Area
    chat: Rectangle = None  # https://i.imgur.com/u544ouI.png
    chat_tabs: List[Rectangle] = []  # https://i.imgur.com/2DH2SiL.png

    # Minimap Area
    compass_orb: Rectangle = None
    hp_orb_text: Rectangle = None
    minimap_area: Rectangle = (
        None  # https://i.imgur.com/idfcIPU.png OR https://i.imgur.com/xQ9xg1Z.png
    )
    minimap: Rectangle = None
    prayer_orb_text: Rectangle = None
    prayer_orb: Rectangle = None
    run_orb_text: Rectangle = None
    run_orb: Rectangle = None
    spec_orb_text: Rectangle = None
    spec_orb: Rectangle = None

    # Game View Area
    game_view: Rectangle = None
    mouseover: Rectangle = None
    total_xp: Rectangle = None

    # Bank Interface (populated when bank is open)
    bank_slots: List[Rectangle] = []

    def __init__(self, window_title: str, padding_top: int, padding_left: int) -> None:
        """
        Creates a Window object with various methods for interacting with the client window.
        Args:
            window_title: The title of the client window.
            padding_top: The height of the client window's header.
            padding_left: The width of the client window's left border.
        """
        self.window_title = window_title
        self.padding_top = padding_top
        self.padding_left = padding_left
        
        # Focus caching for performance
        self._platform_window: Optional[PlatformWindow] = None
        self._last_focus_check: float = 0
        self._last_focus_result: bool = False
        self._focus_validity_window: float = 3.0  # Cache focus state for 3 seconds
        self._in_focus_sequence: bool = False

    def _get_window(self):
        """Get window using platform abstraction (cached)."""
        if self._platform_window is None:
            self._platform_window = create_window(self.window_title)
        return self._platform_window

    window = property(
        fget=_get_window,
        doc="A Win32Window reference to the game client and its properties.",
    )

    def focus(self) -> None:  # sourcery skip: raise-from-previous-error
        """
        Focuses the client window.
        """
        if client := self.window:
            try:
                client.activate()
                # Invalidate focus cache after focusing
                self._last_focus_check = 0
            except Exception:
                raise WindowInitializationError(
                    "Failed to focus client window. Try bringing it to the foreground."
                )

    def is_focused(self) -> bool:
        """
        Check if the game window is currently focused/active.
        Returns:
            True if focused, False otherwise.
        """
        try:
            if client := self.window:
                return client.isActive
        except Exception:
            pass
        return False
    
    def should_check_focus(self) -> bool:
        """
        Determine if focus should be checked based on timing and sequence state.
        
        This implements smart focus checking to avoid expensive focus checks
        on every mouse action. Focus is only checked if:
        - We're not in a focus sequence, OR
        - Enough time has passed since the last check
        
        Returns:
            True if focus should be checked, False if cached result can be used
        """
        if self._in_focus_sequence:
            # Inside a sequence, only check focus at sequence start
            return False
        
        # Check if cached result is still valid
        age = time.time() - self._last_focus_check
        return age >= self._focus_validity_window
    
    def check_focus_cached(self) -> bool:
        """
        Check focus with caching.
        
        Returns cached result if still valid, otherwise performs actual check.
        
        Returns:
            True if window is focused, False otherwise
        """
        if self.should_check_focus():
            # Cache expired or not in sequence, do actual check
            self._last_focus_result = self.is_focused()
            self._last_focus_check = time.time()
        
        return self._last_focus_result
    
    @contextmanager
    def focus_sequence(self):
        """
        Context manager for a sequence of actions that share focus state.
        
        Usage:
            with window.focus_sequence():
                # Focus checked once here
                mouse.move_to(x1, y1)
                mouse.click()
                mouse.move_to(x2, y2)
                # No additional focus checks
        """
        # Check focus once at sequence start
        was_focused = self.check_focus_cached()
        if not was_focused:
            self.focus()
        
        # Enter sequence mode
        self._in_focus_sequence = True
        try:
            yield
        finally:
            # Exit sequence mode
            self._in_focus_sequence = False
            # Invalidate cache after sequence (state may have changed)
            self._last_focus_check = 0

    def ensure_focus(self, max_retries: int = 3, retry_delay: float = 0.2) -> bool:
        """
        Ensure the game window is focused, with retry logic.
        Args:
            max_retries: Maximum number of focus attempts.
            retry_delay: Delay between retries in seconds.
        Returns:
            True if focus was achieved, False if all retries failed.
        """
        for attempt in range(max_retries):
            if self.is_focused():
                return True
            try:
                self.focus()
                time.sleep(retry_delay)
                if self.is_focused():
                    return True
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Failed to focus window after {max_retries} attempts: {e}")
        return False

    def position_in_zone(self, zone: dict) -> bool:
        """Position and maximize window within a specific zone.

        Args:
            zone: Dict with 'left' and 'width' keys defining the zone bounds

        Returns:
            True if successful, False otherwise
        """
        try:
            client = self.window
            if not client:
                return False

            # Get screen height from config
            config = get_machine_config()
            screen_height = config.get_screen_height()

            # Position window at zone left edge, top of screen
            client.moveTo(zone["left"], 0)
            # Resize to fill the zone
            client.resizeTo(zone["width"], screen_height)

            return True
        except Exception as e:
            print(f"Failed to position window in zone: {e}")
            return False

    def position(self) -> Point:
        """
        Returns the origin of the client window as a Point.
        """
        if client := self.window:
            rect = client.get_rect()
            return Point(rect.left, rect.top)

    def rectangle(self) -> Rectangle:
        """
        Returns a Rectangle outlining the entire client window.
        """
        if client := self.window:
            rect = client.get_rect()
            return Rectangle(rect.left, rect.top, rect.width, rect.height)

    def resize(self, width: int, height: int) -> None:
        """
        Resizes the client window..
        Args:
            width: The width to resize the window to.
            height: The height to resize the window to.
        """
        if client := self.window:
            client.size = (width, height)

    def initialize(self):
        """
        Initializes the client window by locating critical UI regions.
        This function should be called when the bot is started or resumed (done by default).
        Returns:
            True if successful, False otherwise along with an error message.
        """
        start_time = time.time()
        client_rect = self.rectangle()
        a = self.__locate_minimap(client_rect)
        b = self.__locate_chat(client_rect)
        c = self.__locate_control_panel(client_rect)
        d = self.__locate_game_view(client_rect)
        if all([a, b, c, d]):  # if all templates found
            print(f"Window.initialize() took {time.time() - start_time} seconds.")
            return True
        raise WindowInitializationError()

    def __locate_chat(self, client_rect: Rectangle) -> bool:
        """
        Locates the chat area on the client.
        Args:
            client_rect: The client area to search in.
        Returns:
            True if successful, False otherwise.
        """
        if chat := imsearch.search_img_in_rect(
            imsearch.get_template_path("ui_templates", "chat.png"), client_rect
        ):
            # Locate chat tabs
            self.chat_tabs = []
            x, y = 5, 143
            # Get chat tabs configuration from machine profile
            config = get_machine_config()
            chat_tabs_config = config.get_chat_tabs_config()

            if (
                self.client_fixed
                and "fixed_mode" in chat_tabs_config
                and "positions" in chat_tabs_config["fixed_mode"]
            ):
                # Use configured positions
                for pos in chat_tabs_config["fixed_mode"]["positions"]:
                    self.chat_tabs.append(
                        Rectangle(
                            left=pos["x"] + chat.left,
                            top=pos["y"] + chat.top,
                            width=pos["width"],
                            height=pos["height"],
                        )
                    )
            else:
                # Fallback to original logic
                for _ in range(7):
                    self.chat_tabs.append(
                        Rectangle(
                            left=x + chat.left, top=y + chat.top, width=52, height=19
                        )
                    )
                    x += 62  # btn width is 52px, gap between each is 10px
            self.chat = chat
            return True
        print("Window.__locate_chat(): Failed to find chatbox.")
        return False

    def __locate_control_panel(self, client_rect: Rectangle) -> bool:
        """
        Locates the control panel area on the client.
        Args:
            client_rect: The client area to search in.
        Returns:
            True if successful, False otherwise.
        """
        # Try both inv.png and bank_inv.png templates
        cp = imsearch.search_img_in_rect(
            imsearch.get_template_path("ui_templates", "inv.png"), client_rect
        )
        if not cp:
            cp = imsearch.search_img_in_rect(
                imsearch.get_template_path("ui_templates", "bank_inv.png"), client_rect
            )

        if cp:
            self.__locate_cp_tabs(cp)
            self.__locate_inv_slots(cp)
            self.__locate_skill_slots(cp)
            self.__locate_prayers(cp)
            self.__locate_spells(cp)
            self.control_panel = cp
            return True
        print("Window.__locate_control_panel(): Failed to find control panel.")
        return False

    def __locate_cp_tabs(self, cp: Rectangle) -> None:
        """
        Creates Rectangles for each interface tab (inventory, prayer, etc.) relative to the control panel, storing it in the class property.
        """
        self.cp_tabs = []
        config = get_machine_config()
        cp_tabs_config = config.get_control_panel_tabs_config()

        # Debug: print control panel position and config
        print(
            f"[DEBUG] Control Panel position: left={cp.left}, top={cp.top}, width={cp.width}, height={cp.height}"
        )
        print(f"[DEBUG] cp_tabs_config: {cp_tabs_config}")

        # Use configuration if available
        if "rows" in cp_tabs_config:
            # tab_width is at top level, not per-row
            tab_width = cp_tabs_config.get("tab_width", 30)
            for row_idx, row in enumerate(cp_tabs_config["rows"]):
                row_tab_width = row.get("tab_width", tab_width)
                for tab_idx, x_pos in enumerate(row["positions"]):
                    tab_rect = Rectangle(
                        left=x_pos + cp.left,
                        top=row["y"] + cp.top,
                        width=row_tab_width,
                        height=row["height"],
                    )
                    self.cp_tabs.append(tab_rect)
                    # Debug: print first few tabs
                    if len(self.cp_tabs) <= 5:
                        print(
                            f"[DEBUG] Tab {len(self.cp_tabs) - 1}: left={tab_rect.left}, top={tab_rect.top}, width={tab_rect.width}, height={tab_rect.height}"
                        )
        else:
            # Fallback to original logic
            slot_w, slot_h = 29, 26  # top row tab dimensions
            gap = 4  # 4px gap between tabs
            y = 4  # 4px from top for first row
            for _ in range(2):
                x = 8 + cp.left
                for _ in range(7):
                    self.cp_tabs.append(
                        Rectangle(left=x, top=y + cp.top, width=slot_w, height=slot_h)
                    )
                    x += slot_w + gap
                y = 303  # 303px from top for second row
                slot_h = 28  # slightly taller tab Rectangles for second row

    def __locate_inv_slots(self, cp: Rectangle) -> None:
        """
        Creates Rectangles for each inventory slot relative to the control panel, storing it in the class property.
        """
        self.inventory_slots = []

        # Get inventory configuration from machine profile
        config = get_machine_config()
        inv_config = config.get_inventory_config()

        slot_w = inv_config.get("slot_width", 36)
        slot_h = inv_config.get("slot_height", 32)
        gap_x = inv_config.get("gap_x", 6)
        gap_y = inv_config.get("gap_y", 4)
        start_x = inv_config.get("start_x", 40)
        start_y = inv_config.get("start_y", 44)

        click_w = max(1, slot_w - 5)
        click_h = max(1, slot_h - 1)
        offset_x = max(0, (slot_w - click_w) // 2)
        offset_y = max(0, (slot_h - click_h) // 2)

        y = start_y + cp.top
        for _ in range(7):
            x = start_x + cp.left
            for _ in range(4):
                self.inventory_slots.append(
                    Rectangle(
                        left=x + offset_x,
                        top=y + offset_y,
                        width=click_w,
                        height=click_h,
                    )
                )
                x += slot_w + gap_x
            y += slot_h + gap_y

    def locate_bank_slots(self, verbose: bool = False) -> None:
        """
        Creates Rectangles for each bank slot by detecting the bank title via OCR.

        This method uses OCR to find "The Bank of Gielinor" title, then calculates
        the bank interface position and generates a 8×8 grid of bank slots.

        The bank interface is centered between the game view left edge and the
        left edge of the inventory (inside the control panel). This method works
        in both fixed and resizable modes.

        Args:
            verbose: If True, prints detailed detection information for debugging

        Raises:
            BankDetectionError: If bank title cannot be found or prerequisites missing

        Example:
            >>> bot.win.locate_bank_slots(verbose=True)
            >>> first_slot = bot.win.bank_slots[0]  # Top-left slot
            >>> middle_slot = bot.win.bank_slots[40]  # Center slot (4,4)

        Bank layout:
        - Title: "The Bank of Gielinor" at top
        - Tab row: underneath the title
        - Item grid: 8×8 grid (64 slots total) starting below the tabs
        """
        
        
        # Constants based on OSRS bank interface layout
        TITLE_OFFSET_X = 5  # Title is ~5px from left edge of bank interface
        TITLE_OFFSET_Y = 8  # Title is ~8px from top edge of bank interface
        GRID_START_X = -44  # First slot is 0px from left edge of bank interface
        GRID_START_Y = 72  # First slot is 60px from top edge of bank interface
        SLOT_W = 37  # Full slot width
        SLOT_H = 35  # Full slot height
        GAP_X = 11  # Horizontal gap between slots
        GAP_Y = 1  # Vertical gap between rows
        CLICK_OFFSET_X = 2  # Reduce width by 4px total (2px each side) to avoid borders
        CLICK_OFFSET_Y = (
            2  # Reduce height by 4px total (2px each side) to avoid borders
        )

        # Step 1: Validate prerequisites
        if not self.game_view:
            raise BankDetectionError(
                "Cannot locate bank slots: game_view not initialized"
            )
        if not self.control_panel:
            raise BankDetectionError(
                "Cannot locate bank slots: control_panel not initialized"
            )
        if not self.inventory_slots:
            raise BankDetectionError(
                "Cannot locate bank slots: inventory_slots not initialized"
            )

        # Step 2: Calculate search area
        # Bank interface is centered between game_view.left and the LEFT EDGE of the inventory
        # The inventory is inside the control panel, starting at inventory_slots[0].left
        inventory_left_edge = self.inventory_slots[0].left
        search_width = inventory_left_edge - self.game_view.left
        search_area = Rectangle(
            left=self.game_view.left,
            top=self.game_view.top,
            width=search_width,
            height=self.game_view.height,
        )

        if verbose:
            print("[BANK DETECTION] Starting bank slot detection...")
            print(f"[BANK DETECTION] Game view left: {self.game_view.left}")
            print(f"[BANK DETECTION] Inventory left edge: {inventory_left_edge}")
            print(
                f"[BANK DETECTION] Search area: Rectangle(x={search_area.left}, y={search_area.top}, w={search_area.width}, h={search_area.height})"
            )

        # Step 3: OCR title detection
        title_rects = ocr.find_text(
            "The Bank of Gielinor",
            search_area,
            ocr.BOLD_12,
            [clr.ORANGE, clr.OFF_ORANGE],
        )

        if not title_rects:
            raise BankDetectionError(
                "Bank title 'The Bank of Gielinor' not found. Ensure bank is open."
            )

        title_rect = title_rects[0]  # Use first match

        if verbose:
            print(
                f"[BANK DETECTION] Found bank title at: Rectangle(x={title_rect.left}, y={title_rect.top}, w={title_rect.width}, h={title_rect.height})"
            )

        # Step 4: Calculate bank interface position
        bank_left = title_rect.left - TITLE_OFFSET_X
        bank_top = title_rect.top - TITLE_OFFSET_Y

        # Validate bounds
        if bank_left < self.game_view.left or bank_top < self.game_view.top:
            raise BankDetectionError(
                "Bank interface position invalid (outside game view)"
            )

        if verbose:
            print(
                f"[BANK DETECTION] Calculated bank interface position: ({bank_left}, {bank_top})"
            )

        # Step 5: Calculate grid start position
        grid_start_x = bank_left + GRID_START_X
        grid_start_y = bank_top + GRID_START_Y

        if verbose:
            print(
                f"[BANK DETECTION] Grid start position: ({grid_start_x}, {grid_start_y})"
            )
            print(
                f"[BANK DETECTION] Slot dimensions: {SLOT_W}x{SLOT_H}, gaps: {GAP_X}x{GAP_Y}, click area: {SLOT_W - 2 * CLICK_OFFSET_X}x{SLOT_H - 2 * CLICK_OFFSET_Y}"
            )

        # Step 6: Generate 8x8 slot grid
        self.bank_slots = []
        click_w = SLOT_W - 2 * CLICK_OFFSET_X
        click_h = SLOT_H - 2 * CLICK_OFFSET_Y

        for row in range(14):
            for col in range(8):
                slot_x = grid_start_x + col * (SLOT_W + GAP_X) + CLICK_OFFSET_X
                slot_y = grid_start_y + row * (SLOT_H + GAP_Y) + CLICK_OFFSET_Y

                self.bank_slots.append(
                    Rectangle(left=slot_x, top=slot_y, width=click_w, height=click_h)
                )

        # Step 7: Verbose logging
        if verbose:
            print(
                f"[BANK DETECTION] First slot: Rectangle(x={self.bank_slots[0].left}, y={self.bank_slots[0].top}, w={self.bank_slots[0].width}, h={self.bank_slots[0].height})"
            )
            print(
                f"[BANK DETECTION] Middle slot (4,4): Rectangle(x={self.bank_slots[40].left}, y={self.bank_slots[40].top}, w={self.bank_slots[40].width}, h={self.bank_slots[40].height})"
            )
            print(
                f"[BANK DETECTION] Last slot (8,8): Rectangle(x={self.bank_slots[63].left}, y={self.bank_slots[63].top}, w={self.bank_slots[63].width}, h={self.bank_slots[63].height})"
            )
            print(
                f"[BANK DETECTION] Successfully created {len(self.bank_slots)} bank slots"
            )

    def __locate_skill_slots(self, cp: Rectangle) -> None:
        """
        Creates Rectangles for each skill slot relative to the control panel, storing it in the class property.
        """
        self.skill_slots = []

        config = get_machine_config()
        skill_config = config.get_skills_config()

        slot_w = skill_config.get("slot_width", 36)
        slot_h = skill_config.get("slot_height", 36)
        gap_x = skill_config.get("gap_x", 6)
        gap_y = skill_config.get("gap_y", 4)
        start_x = skill_config.get("start_x", 40)
        start_y = skill_config.get("start_y", 44)
        rows = skill_config.get("grid_rows", 8)
        cols = skill_config.get("grid_cols", 3)
        total_level_height = skill_config.get("total_level_height", 30)
        total_level_gap = skill_config.get("total_level_gap", gap_y)

        y = start_y + cp.top
        for _ in range(rows):
            x = start_x + cp.left
            for _ in range(cols):
                self.skill_slots.append(
                    Rectangle(
                        left=x,
                        top=y,
                        width=slot_w,
                        height=slot_h,
                    )
                )
                x += slot_w + gap_x
            y += slot_h + gap_y

        grid_width = (cols * slot_w) + ((cols - 1) * gap_x)
        grid_height = (rows * slot_h) + ((rows - 1) * gap_y)
        total_top = start_y + grid_height + total_level_gap + cp.top
        self.skill_total_level = Rectangle(
            left=start_x + cp.left,
            top=total_top,
            width=grid_width,
            height=total_level_height,
        )

    def __locate_prayers(self, cp: Rectangle) -> None:
        """
        Creates Rectangles for each prayer in the prayer book menu relative to the control panel, storing it in the class property.
        """
        self.prayers = []

        # Get prayers configuration from machine profile
        config = get_machine_config()
        prayer_config = config.get_prayers_config()

        slot_w = (
            prayer_config.get("prayer_width", 33) + 1
        )  # Add 1 to match original behavior
        slot_h = (
            prayer_config.get("prayer_height", 33) + 1
        )  # Add 1 to match original behavior
        gap_x = prayer_config.get("gap_x", 3)
        gap_y = prayer_config.get("gap_y", 3)
        start_x = prayer_config.get("start_x", 30)
        start_y = prayer_config.get("start_y", 46)
        rows = prayer_config.get("grid_rows", 6)
        cols = prayer_config.get("grid_cols", 5)

        y = start_y + cp.top
        for _ in range(rows):
            x = start_x + cp.left
            for _ in range(cols):
                self.prayers.append(
                    Rectangle(left=x, top=y, width=slot_w, height=slot_h)
                )
                x += slot_w + gap_x
            y += slot_h + gap_y
        del self.prayers[29]  # remove the last prayer (unused)

    def __locate_spells(self, cp: Rectangle) -> None:
        """
        Creates Rectangles for each magic spell relative to the control panel, storing it in the class property.
        Currently only populates the normal spellbook spells.
        """
        self.spellbook_normal = []

        # Get spellbook configuration from machine profile
        config = get_machine_config()
        spell_config = config.get_spellbook_config()

        slot_w = (
            spell_config.get("spell_width", 23) - 1
        )  # Subtract 1 to match original behavior
        slot_h = (
            spell_config.get("spell_height", 23) - 1
        )  # Subtract 1 to match original behavior
        gap_x = spell_config.get("gap_x", 4)
        gap_y = spell_config.get("gap_y", 2)
        start_x = spell_config.get("start_x", 30)
        start_y = spell_config.get("start_y", 37)
        rows = spell_config.get("grid_rows", 10)
        cols = spell_config.get("grid_cols", 7)

        y = start_y + cp.top
        for _ in range(rows):
            x = start_x + cp.left
            for _ in range(cols):
                self.spellbook_normal.append(
                    Rectangle(left=x, top=y, width=slot_w, height=slot_h)
                )
                x += slot_w + gap_x
            y += slot_h + gap_y

    def __locate_game_view(self, client_rect: Rectangle) -> bool:
        """
        Locates the game view while considering the client mode (Fixed/Resizable). https://i.imgur.com/uuCQbxp.png
        Args:
            client_rect: The client area to search in.
        Returns:
            True if successful, False otherwise.
        """
        if self.minimap_area is None or self.chat is None or self.control_panel is None:
            print(
                "Window.__locate_game_view(): Failed to locate game view. Missing minimap, chat, or control panel."
            )
            return False
        if self.client_fixed:
            # Uses the chatbox and known fixed size of game_view to locate it in fixed mode
            config = get_machine_config()
            game_view_config = config.get_ui_coordinates("fixed_mode", "game_view") or {
                "width": 517,
                "height": 337,
            }
            self.game_view = Rectangle(
                left=self.chat.left,
                top=self.chat.top - game_view_config["height"],
                width=game_view_config["width"],
                height=game_view_config["height"],
            )
        else:
            # Uses control panel to find right-side bounds of game view in resizable mode
            self.game_view = Rectangle.from_points(
                Point(
                    client_rect.left + self.padding_left,
                    client_rect.top + self.padding_top,
                ),
                self.control_panel.get_bottom_right(),
            )
            # Locate the positions of the UI elements to be subtracted from the game_view, relative to the game_view
            minimap = self.minimap_area.to_dict()
            minimap["left"] -= self.game_view.left
            minimap["top"] -= self.game_view.top

            chat = self.chat.to_dict()
            chat["left"] -= self.game_view.left
            chat["top"] -= self.game_view.top

            control_panel = self.control_panel.to_dict()
            control_panel["left"] -= self.game_view.left
            control_panel["top"] -= self.game_view.top

            self.game_view.subtract_list = [minimap, chat, control_panel]
        config = get_machine_config()
        mouseover_config = config.get(
            "ui_coordinates", "mouseover", default={"width": 407, "height": 26}
        )
        self.mouseover = Rectangle(
            left=self.game_view.left,
            top=self.game_view.top,
            width=mouseover_config["width"],
            height=mouseover_config["height"],
        )
        return True

    def __locate_minimap(self, client_rect: Rectangle) -> bool:
        """
        Locates the minimap area on the clent window and all of its internal positions.
        Args:
            client_rect: The client area to search in.
        Returns:
            True if successful, False otherwise.
        """
        # 'm' refers to minimap area
        config = get_machine_config()

        if m := imsearch.search_img_in_rect(
            imsearch.get_template_path("ui_templates", "minimap.png"), client_rect
        ):
            self.client_fixed = False
            mode = "resizable_mode"
        elif m := imsearch.search_img_in_rect(
            imsearch.get_template_path("ui_templates", "minimap_fixed.png"), client_rect
        ):
            self.client_fixed = True
            mode = "fixed_mode"
        else:
            m = None

        if m:
            # Helper function to get coordinates with defaults
            def get_coords(element_name: str, defaults: dict):
                coords = config.get_ui_coordinates(mode, element_name)
                if coords:
                    return Rectangle(
                        left=coords.get("left", defaults["left"]) + m.left,
                        top=coords.get("top", defaults["top"]) + m.top,
                        width=coords.get("width", defaults["width"]),
                        height=coords.get("height", defaults["height"]),
                    )
                else:
                    return Rectangle(
                        left=defaults["left"] + m.left,
                        top=defaults["top"] + m.top,
                        width=defaults["width"],
                        height=defaults["height"],
                    )

            # Define defaults based on mode
            if self.client_fixed:
                defaults_map = {
                    "compass_orb": {"left": 31, "top": 7, "width": 24, "height": 25},
                    "hp_orb_text": {"left": 4, "top": 55, "width": 20, "height": 13},
                    "minimap": {"left": 52, "top": 4, "width": 147, "height": 160},
                    "prayer_orb": {"left": 30, "top": 80, "width": 19, "height": 20},
                    "prayer_orb_text": {
                        "left": 4,
                        "top": 89,
                        "width": 20,
                        "height": 13,
                    },
                    "run_orb": {"left": 40, "top": 112, "width": 19, "height": 20},
                    "run_orb_text": {"left": 14, "top": 121, "width": 20, "height": 13},
                    "spec_orb": {"left": 62, "top": 137, "width": 19, "height": 20},
                    "spec_orb_text": {
                        "left": 36,
                        "top": 146,
                        "width": 20,
                        "height": 13,
                    },
                    "total_xp": {"left": -104, "top": 6, "width": 104, "height": 21},
                }
            else:
                defaults_map = {
                    "compass_orb": {"left": 40, "top": 7, "width": 24, "height": 26},
                    "hp_orb_text": {"left": 4, "top": 60, "width": 20, "height": 13},
                    "minimap": {"left": 52, "top": 5, "width": 154, "height": 155},
                    "prayer_orb": {"left": 30, "top": 86, "width": 20, "height": 20},
                    "prayer_orb_text": {
                        "left": 4,
                        "top": 94,
                        "width": 20,
                        "height": 13,
                    },
                    "run_orb": {"left": 39, "top": 118, "width": 20, "height": 20},
                    "run_orb_text": {"left": 14, "top": 126, "width": 20, "height": 13},
                    "spec_orb": {"left": 62, "top": 144, "width": 18, "height": 20},
                    "spec_orb_text": {
                        "left": 36,
                        "top": 151,
                        "width": 20,
                        "height": 13,
                    },
                    "total_xp": {"left": -147, "top": 4, "width": 104, "height": 21},
                }

            # Create rectangles from configuration
            self.compass_orb = get_coords("compass_orb", defaults_map["compass_orb"])
            self.hp_orb_text = get_coords("hp_orb_text", defaults_map["hp_orb_text"])
            self.minimap = get_coords("minimap", defaults_map["minimap"])
            self.prayer_orb = get_coords("prayer_orb", defaults_map["prayer_orb"])
            self.prayer_orb_text = get_coords(
                "prayer_orb_text", defaults_map["prayer_orb_text"]
            )
            self.run_orb = get_coords("run_orb", defaults_map["run_orb"])
            self.run_orb_text = get_coords("run_orb_text", defaults_map["run_orb_text"])
            self.spec_orb = get_coords("spec_orb", defaults_map["spec_orb"])
            self.spec_orb_text = get_coords(
                "spec_orb_text", defaults_map["spec_orb_text"]
            )
            self.total_xp = get_coords("total_xp", defaults_map["total_xp"])
        if m:
            # Take a bite out of the bottom-left corner of the minimap to exclude orb's green numbers
            self.minimap.subtract_list = [
                {"left": 0, "top": self.minimap.height - 20, "width": 20, "height": 20}
            ]
            self.minimap_area = m
            return True
        print("Window.__locate_minimap(): Failed to find minimap.")
        return False


class MockWindow(Window):
    def __init__(self):
        super().__init__(window_title="None", padding_left=0, padding_top=0)

    def _get_window(self):
        print("MockWindow._get_window() called.")

    window = property(
        fget=_get_window,
        doc="A Win32Window reference to the game client and its properties.",
    )

    def initialize(self) -> None:
        print("MockWindow.initialize() called.")

    def focus(self) -> None:
        print("MockWindow.focus() called.")

    def is_focused(self) -> bool:
        print("MockWindow.is_focused() called.")
        return True

    def ensure_focus(self, max_retries: int = 3, retry_delay: float = 0.2) -> bool:
        print("MockWindow.ensure_focus() called.")
        return True

    def position(self) -> Point:
        print("MockWindow.position() called.")
