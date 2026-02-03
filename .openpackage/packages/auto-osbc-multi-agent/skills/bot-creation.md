# Skill: Bot Creation Workflow

## Step-by-Step Process for Creating New Bots

### 1. Research & Planning (MANDATORY)
```bash
# First, observe the game manually
python scripts/recorder.py --window "RuneLite" --duration 30 --interval 500

# This creates timestamped screenshots for analysis
```

**What to capture:**
- Starting state (where bot begins)
- Success state (what indicates task completion)
- All intermediate states
- Error/stuck conditions
- UI elements to detect

### 2. Create Bot File Structure
```python
# File: src/model/osrs/your_bot.py

from model.osrs.osrs_bot import OSRSBot
from utilities.api.status_socket import StatusSocket
from utilities.random_util import truncated_normal_sample
import time
import random

class OSRSYourBot(OSRSBot):
    def __init__(self):
        bot_title = "Your Bot Name"
        description = "What this bot does"
        super().__init__(bot_title=bot_title, description=description)
        self.running_time = 60  # minutes
        self.options_set = True  # or False if needs configuration UI
        
    def create_options(self):
        """Configuration UI - only if needed"""
        self.options_builder.add_dropdown("option_name", ["Choice1", "Choice2"])
        
    def save_options(self, options: dict):
        """Save user configuration"""
        self.log_msg(f"Options saved: {options}")
        self.options_set = True
        
    def main_loop(self):
        """Core bot logic - called repeatedly"""
        # API calls for status updates
        self.update_progress((self.iterations / 100) * 100)
        self.log_msg(f"Starting iteration {self.iterations}")
        
        # Your bot logic here
        if self.detect_state_a():
            self.handle_state_a()
        elif self.detect_state_b():
            self.handle_state_b()
        else:
            self.log_msg("Unknown state, waiting...")
            time.sleep(truncated_normal_sample(2, 0.5, 1, 3))
```

### 3. Implement Detection Methods

**Use recorder to extract templates:**
```bash
# Start a recording session
python scripts/recorder.py --window "RuneLite" --duration 10

# Extract a UI element as template
python scripts/recorder.py --from-session "captures/2025..." \
    --extract-template "100,200,50,50,button_name"
```

**In your bot:**
```python
def detect_state_a(self) -> bool:
    """Detect if we're in state A"""
    template = self.get_img_path("bot/your_bot/state_a_indicator.png")
    result = self.search_img_in_rect(template, self.win.game_view)
    return result is not None
```

### 4. Create Test File
```python
# File: tests/unit/model/osrs/test_your_bot.py

import pytest
from model.osrs.your_bot import OSRSYourBot

class TestYourBot:
    @pytest.fixture
    def bot(self):
        return OSRSYourBot()
        
    def test_initialization(self, bot):
        assert bot.bot_title == "Your Bot Name"
        assert bot.running_time == 60
        
    def test_state_detection(self, bot):
        # Test with mock images
        pass
```

### 5. Manual Testing Loop
```bash
# Run recorder in test mode
python scripts/recorder.py --test-template \
    src/images/bot/your_bot/template.png --window "RuneLite"

# Debug interactively
python scripts/debug_console.py
>>> from model.osrs.your_bot import OSRSYourBot
>>> bot = OSRSYourBot()
>>> bot.detect_state_a()
```

### 6. Integration & Refinement

**Add to UI:**
Edit `src/view/bot_view.py` to register your bot

**Test full lifecycle:**
```bash
osbc start  # Launch with GUI
# Select your bot, run for 5 minutes, observe
```

## Bot Architecture Patterns

### State Machine Pattern (Recommended)
```python
def main_loop(self):
    state = self.determine_state()
    
    if state == "IDLE":
        self.handle_idle()
    elif state == "WORKING":
        self.handle_working()
    elif state == "BANKING":
        self.handle_banking()
```

### Detection Priority Pattern
```python
def main_loop(self):
    # Check errors first
    if self.is_logged_out():
        self.handle_logout()
        return
        
    # Then check high-priority states
    if self.inventory_full():
        self.handle_full_inventory()
        return
        
    # Finally, normal operation
    self.continue_task()
```

## Common Pitfalls

❌ **Don't:**
- Hardcode pixel coordinates
- Use fixed delays
- Skip human-behavior randomization
- Forget error handling
- Test only in perfect conditions

✅ **Do:**
- Use template matching
- Randomize all timing
- Apply human-behavior skill
- Handle edge cases
- Test with variations

## Checklist Before Committing

- [ ] Recorder used to capture game states
- [ ] Templates extracted and tested
- [ ] Human-like behavior implemented
- [ ] Error states handled
- [ ] Tests written
- [ ] Manual testing completed
- [ ] Logging added for debugging
- [ ] API status updates included
