# XP Watcher System

Automatic XP tracking for OSRS bots using real-time detection of XP popups.

## Overview

The XP Watcher monitors the XP popup area (left of minimap) to detect skill XP gains in real-time. When XP is detected, it automatically updates the SkillsManager and UI.

### Features

- ✅ **Automatic XP tracking** - No need to open skills tab
- ✅ **Real-time updates** - Detects XP as it appears in-game
- ✅ **Minimal overhead** - Checks every 2 seconds by default
- ✅ **Debug tools** - Visualize detection area and test setup
- ✅ **Template-based** - Match skill icons for accurate tracking
- ✅ **Non-intrusive** - Won't crash bot if detection fails

## Quick Start

### 1. Verify Detection Area

First, check that the XP detection area is correctly positioned:

```bash
python scripts/test_xp_watcher.py --screenshot
```

This saves a screenshot with the detection area highlighted in green. Check that it covers the XP popup location.

### 2. Setup (Automatic)

**Skill icons are now loaded automatically from `src/images/bot/skills/`!**

No manual extraction needed. The XP Watcher will:
- ✅ Automatically load all 24 skill icons at initialization
- ✅ Match icons using OpenCV template matching (0.75 confidence threshold)
- ✅ Log warnings if no skill matches (check detection area positioning)

The system uses the existing skill icons (22x22px) from your UI, so there's zero setup required.

### 3. Use in Your Bot

The XP Watcher is automatically initialized when your bot starts. In your bot's main loop, call:

```python
def main_loop(self):
    while self.status == BotStatus.RUNNING:
        # Your bot logic here
        ...
        
        # Check for XP gains (non-blocking)
        self.check_xp_watcher()
```

That's it! XP will be tracked automatically.

## Components

### 1. XPWatcher Class (`src/utilities/xp_watcher.py`)

Core XP detection service.

**Key Methods:**
- `should_check()` - Returns True if enough time has passed to check again
- `check_for_xp()` - Checks for XP popup and updates SkillsManager
- `save_debug_screenshot()` - Saves visualization of detection area
- `load_skill_templates()` - Loads skill icon templates

**Configuration:**
```python
watcher = XPWatcher(window)
watcher.CHECK_INTERVAL = 2.0  # Check every 2 seconds (default)
```

### 2. Debug Tools

#### Screenshot Tool (`scripts/test_xp_watcher.py`)

Visualize and test XP detection:

```bash
# Save debug screenshot
python scripts/test_xp_watcher.py --screenshot

# Monitor XP detection for 60 seconds
python scripts/test_xp_watcher.py --monitor --duration 60

# Show current configuration
python scripts/test_xp_watcher.py --adjust
```

#### Icon Testing Tool

Test skill icon matching on captured screenshots:

```bash
# Test icon matching on a screenshot
python scripts/test_xp_watcher.py --test-icon debug_screenshots/*/xp_area_closeup.png
```

This will show which skill was detected and the confidence score.

### 3. Integration with OSRSBot

XP Watcher is integrated into `OSRSBot`:

- **Initialization:** Automatic in `on_start()`
- **Usage:** Call `self.check_xp_watcher()` in main loop
- **No setup required** - Works out of the box

## How It Works

### Detection Flow

```
1. Bot main loop calls check_xp_watcher()
   │
2. XPWatcher checks if CHECK_INTERVAL has passed
   │
3. Captures screenshot of XP popup area
   │
4. Checks if popup is visible (dark background detection)
   │
5. If visible:
   ├─ Extract icon region (first 25x25 pixels from left edge)
   ├─ Match against all skill templates (confidence threshold: 0.75)
   ├─ OCR to extract XP amount (+123 XP)
   └─ Update SkillsManager with skill name and XP amount
   │
6. SkillsManager notifies observers
   │
7. UI updates automatically with new XP/level
```

### XP Popup Area

The XP popup appears **left of the minimap**:

- **Position:** `minimap.left - 160px, minimap.top + 5px`
- **Size:** `150px wide × 30px tall`
- **Format:** `[Skill Icon] +X XP`

You can adjust these values in `_calculate_xp_area()` if needed.

### Popup Visibility Detection

The watcher checks if the popup is visible by analyzing the screenshot:

- **Dark background:** Grayscale values 20-70
- **Threshold:** >30% of pixels in dark range
- **Result:** Popup is likely visible

This prevents false detections when no popup is present.

## Configuration

### Adjust Detection Area

If the green box in debug screenshots doesn't cover the XP popup:

1. Edit `src/utilities/xp_watcher.py`
2. Find `_calculate_xp_area()` method
3. Adjust these values:

```python
xp_popup_width = 150   # Popup width in pixels
xp_popup_height = 30   # Popup height in pixels
xp_left = minimap.left - xp_popup_width - 10  # Position
xp_top = minimap.top + 5
```

4. Test with `python scripts/test_xp_watcher.py --screenshot`

### Adjust Check Interval

Change how often XP is checked:

```python
# In your bot's on_start() or __init__
if self._xp_watcher:
    self._xp_watcher.CHECK_INTERVAL = 1.0  # Check every 1 second
```

**Note:** XP popups last ~4-5 seconds, so checking every 2 seconds is usually sufficient.

## Troubleshooting

### Problem: "XP Watcher initialized" but no XP detected

**Solutions:**
1. Check detection area with `--screenshot`
2. Verify popup is in the green box
3. Adjust coordinates in `_calculate_xp_area()`
4. Test with `--monitor` mode

### Problem: "No skill matched" warning

**Cause:** Icon confidence below threshold (0.75) or detection area misaligned

**Solutions:**
1. Check detection area with `--screenshot` - ensure XP popup icon is in the green box
2. Verify the icon is in the leftmost 25 pixels of the detection area
3. Test with `--test-icon` on a captured XP popup screenshot
4. Check console for confidence scores (e.g., "best: fishing @ 0.68")
5. If consistently below 0.75, the detection area may need adjustment

### Problem: Detection area is off-screen or wrong

**Cause:** Client mode changed (fixed vs resizable) or window position changed

**Solution:**
1. Re-initialize window: Restart bot
2. Check `test_xp_watcher.py --adjust` output
3. Verify minimap position is correct

## Performance Impact

- **Check frequency:** Every 2 seconds (configurable)
- **Screenshot size:** ~150×30 pixels
- **Processing time:** <10ms per check
- **CPU impact:** Negligible (<1% on modern systems)
- **Memory:** <1MB for loaded templates

## Example: Full Integration

```python
class MyBot(OSRSBot):
    def __init__(self):
        super().__init__("My Bot", "Does stuff")
        self.options_set = True
    
    def main_loop(self):
        while self.status == BotStatus.RUNNING:
            # Bot logic
            if self.detect_and_click_tree():
                self.log_msg("Clicked tree")
            
            # Check for XP (automatic tracking)
            if self.check_xp_watcher():
                # Optional: Log XP gain
                wc_skill = SkillsManager().get_skill("woodcutting")
                self.log_msg(f"XP gained! Total WC XP: {wc_skill.xp}")
            
            time.sleep(0.1)
```

## Advanced Usage

### Custom XP Detection Logic

```python
from utilities.xp_watcher import XPWatcher

# Create custom watcher
watcher = XPWatcher(self.win)

# Override check interval
watcher.CHECK_INTERVAL = 0.5  # Very frequent

# Manual check
if watcher.check_for_xp():
    print("XP detected!")
```

### Save Debug Screenshots Programmatically

```python
# In your bot
if self._xp_watcher:
    self._xp_watcher.save_debug_screenshot("my_bot_xp_debug")
```

### Access Raw XP Data

```python
from model.skills import SkillsManager

manager = SkillsManager()
fishing = manager.get_skill("fishing")

print(f"Level: {fishing.level}")
print(f"Total XP: {fishing.xp}")
print(f"XP gained this session: {fishing.xp_gained}")
print(f"Last updated: {fishing.timestamp}")
```

## Future Enhancements

Potential improvements (not yet implemented):

- [ ] **Multi-skill detection** - Detect XP from multiple skills simultaneously
- [ ] **XP rate tracking** - Calculate XP/hour
- [ ] **Level-up notifications** - Alert when leveling up
- [ ] **Session statistics** - Track XP gains per session
- [ ] **Template auto-extraction** - Automatically extract icons from popups

## Related Files

- `src/utilities/xp_watcher.py` - Core XP detection service
- `src/model/skills.py` - Skills state management
- `src/model/osrs/osrs_bot.py` - Bot integration
- `scripts/test_xp_watcher.py` - Debug and test tool
- `src/images/bot/skills/` - Skill icon templates (22x22px, automatically loaded)

## Questions?

- Check debug screenshots to verify detection area
- Run monitor mode to see if XP is being detected
- Review logs for XP Watcher messages
- Ensure templates are extracted and loaded
