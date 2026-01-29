# Quick Command Reference

## Instant Actions

### 🎥 Capture Current Game State
```bash
python scripts/manual_capture.py "description_of_what_im_seeing"
```

### 🔍 Test if Template Matches
```bash
python scripts/recorder.py --test-template src/images/bot/your_bot/template.png --window "RuneLite"
```

### 📹 Record Game Session (30 seconds)
```bash
python scripts/recorder.py --window "RuneLite" --duration 30 --interval 500
```

### 🎯 Extract New Template from Recording
```bash
# First, find the session
python scripts/recorder.py --list-sessions

# Then extract (X, Y, Width, Height, name)
python scripts/recorder.py --from-session "captures/2025-..." --extract-template "100,200,50,50,button_name"
```

### 🐛 Open Interactive Debug Console
```bash
python scripts/debug_console.py
```

### ⚡ Profile Bot Performance
```bash
python scripts/performance_profiler.py
```

### 🧪 Run Tests
```bash
# All tests
pytest

# Specific bot
pytest tests/unit/model/osrs/test_woodcutter.py

# With output
pytest -v -s

# With coverage
pytest --cov=src
```

### 🚀 Launch Game
```bash
# Check status
osbc status

# Start RuneLite
osbc start --headless

# Auto-login
osbc login
```

## Common Workflows

### New Bot Development
```bash
# 1. Capture game states
python scripts/recorder.py --window "RuneLite" --duration 30

# 2. Create bot file
# src/model/osrs/your_bot.py

# 3. Extract templates from recording
python scripts/recorder.py --list-sessions
python scripts/recorder.py --from-session "..." --extract-template "..."

# 4. Test templates
python scripts/recorder.py --test-template src/images/bot/... --window "RuneLite"

# 5. Write tests
# tests/unit/model/osrs/test_your_bot.py

# 6. Run tests
pytest tests/unit/model/osrs/test_your_bot.py -v
```

### Debugging Detection Issues
```bash
# 1. Capture failing state
python scripts/manual_capture.py "detection_failing_here"

# 2. Test current template
python scripts/recorder.py --test-template src/images/bot/... --window "RuneLite"

# 3. If score low, extract new template
python scripts/recorder.py --window "RuneLite" --duration 5
python scripts/recorder.py --from-session "..." --extract-template "..."

# 4. Test new template
python scripts/recorder.py --test-template src/images/bot/.../NEW_template.png --window "RuneLite"
```

### Interactive Testing
```bash
python scripts/debug_console.py
```
```python
# In console:
from model.osrs.woodcutter import OSRSWoodcutter
bot = OSRSWoodcutter()
bot.setup()
bot.find_tree()  # Test individual methods
```

## Template Paths

Templates organized by purpose:
```
src/images/
  bot/              # Bot-specific templates
    woodcutter/
      tree_oak.png
      tree_willow.png
    thieving/
      npc_target.png
    login/          # Login screen elements
      existing_user_button.png
  ui/               # UI elements
    buttons/
    icons/
  temp/             # Temporary/test images
```

## Machine Profiles

Switch configurations:
```
machine_profiles/
  default.json      # Default settings
  desktop.json      # Desktop-specific
  laptop.json       # Laptop-specific
  desktop/
    images/         # Desktop-specific templates
```

## Environment

```bash
# Activate environment (Windows)
.\env\Scripts\activate

# Install dependencies
pip install -e .

# Update requirements
pip freeze > requirements.txt
```

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/new-bot-name

# Commit changes
git add .
git commit -m "Add new bot: description"

# Push
git push origin feature/new-bot-name
```

## Shortcuts for Common Tasks

| Task | Command |
|------|---------|
| Quick screenshot | `python scripts/manual_capture.py "desc"` |
| Test template | `python scripts/recorder.py --test-template PATH --window "RuneLite"` |
| Record 10 sec | `python scripts/recorder.py --window "RuneLite" --duration 10` |
| List templates | `python scripts/recorder.py --list-templates` |
| Run all tests | `pytest` |
| Debug console | `python scripts/debug_console.py` |
| Check game status | `osbc status` |
| Start game | `osbc start --headless` |
