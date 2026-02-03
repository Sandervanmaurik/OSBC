# Behavior System

A modular, configurable system for adding realistic human-like behaviors to bots.

## Quick Start

### Basic Usage

```python
from utilities.behavior import BehaviorManager

class MyBot(OSRSBot):
    def __init__(self):
        super().__init__(...)
        
        # Initialize with a profile
        self.behavior = BehaviorManager(
            bot=self,
            profile="experienced"  # or "cautious", "focused"
        )
    
    def main_loop(self):
        while running:
            # Random attention behaviors
            self.behavior.attention.perform_random_behaviors()
            
            # Sleep with human-like timing
            self.behavior.timing.sleep("short")
            
            # Mouse movement
            self.behavior.mouse.move_to(target)
            
            # Click with misclick chance
            if self.behavior.action.should_misclick():
                self.behavior.action.execute_misclick(target)
            else:
                self.behavior.mouse.click()
            
            # Take breaks
            if self.behavior.breaks.should_take_break():
                self.behavior.breaks.take_break()
```

### Per-Bot Customization

```python
# Fletching bot - disable camera (standing at bank)
self.behavior = BehaviorManager(
    bot=self,
    profile="focused",
    custom_config={
        "attention": {
            "camera_enabled": False,
            "skill_check_enabled": False,
        }
    }
)

# Woodcutting bot - enable all behaviors
self.behavior = BehaviorManager(
    bot=self,
    profile="experienced",
    custom_config={
        "attention": {
            "camera_enabled": True,
            "skill_check_enabled": True,
        },
        "breaks": {
            "enabled": True,
        }
    }
)
```

## Behavior Modules

### 1. TimingBehavior

Controls sleep patterns, delays, and reaction times.

```python
# Use presets
self.behavior.timing.sleep("instant")    # 0.01-0.03s
self.behavior.timing.sleep("very_fast")  # 0.02-0.08s
self.behavior.timing.sleep("fast")       # 0.05-0.15s
self.behavior.timing.sleep("short")      # 0.1-0.4s
self.behavior.timing.sleep("medium")     # 0.3-0.8s
self.behavior.timing.sleep("long")       # 0.6-1.5s
self.behavior.timing.sleep("very_long")  # 1.5-3.5s

# Use custom range
self.behavior.timing.sleep((0.2, 0.6))

# Use fixed duration
self.behavior.timing.sleep(0.5)

# Special timing methods
self.behavior.timing.reaction_delay()    # Human reaction time
self.behavior.timing.micro_delay()       # Very short delay
self.behavior.timing.thinking_pause()    # Brief hesitation
```

### 2. MouseBehavior

Handles mouse movement patterns.

```python
# Move with profile default speed
self.behavior.mouse.move_to(target)

# Override speed for this move
self.behavior.mouse.move_to(target, mouseSpeed="slow")

# Relative movement
self.behavior.mouse.move_rel(10, 20, x_var=3, y_var=3)

# Click at current position
self.behavior.mouse.click()
self.behavior.mouse.right_click()

# Move with possible overshoot
self.behavior.mouse.move_with_overshoot(target)
```

### 3. ActionBehavior

Execution patterns like misclicks and hesitation.

```python
# Check if should misclick
if self.behavior.action.should_misclick():
    self.behavior.action.execute_misclick(target)
else:
    self.normal_click(target)

# Hesitation before action
if self.behavior.action.should_hesitate():
    self.behavior.action.hesitate()

# Pre-click delay (hover time)
self.behavior.action.pre_click_delay()

# Complete click sequence with all behaviors
self.behavior.action.execute_click_sequence(
    target,
    check_mouseover=True,
    mouseover_check_fn=lambda: self.bot.mouseover_text(contains="Chop")
)
```

### 4. AttentionBehavior

Random attention patterns like camera movement.

```python
# Perform all random behaviors (call in main loop)
self.behavior.attention.perform_random_behaviors()

# Individual attention behaviors
self.behavior.attention.random_camera_movement()
self.behavior.attention.mini_camera_adjust()
self.behavior.attention.random_mouse_movement()
self.behavior.attention.check_inventory_random()
self.behavior.attention.random_skill_check()

# Disable specific attention behaviors
self.behavior.attention.update_config(
    camera_enabled=False,
    skill_check_enabled=False
)
```

### 5. BreakBehavior

Break timing and patterns.

```python
# Check if should take break (call periodically)
if self.behavior.breaks.should_take_break():
    self.behavior.breaks.take_break()

# Take custom break
self.behavior.breaks.take_custom_break(60, 180, "Taking lunch break")

# Enable/configure breaks
self.behavior.breaks.enable()
self.behavior.breaks.update_config(chance_per_check=0.03)
```

## Behavior Profiles

### Cautious
- **Description**: Slower, more deliberate. Maximum human-like behavior.
- **Speed**: 30% slower than base
- **Misclick**: 12% chance
- **Best for**: High-risk activities, ban-averse users

### Experienced (Recommended)
- **Description**: Balanced, efficient gameplay.
- **Speed**: Normal
- **Misclick**: 8% chance
- **Best for**: Most bots, general use

### Focused
- **Description**: Fast, minimal distractions.
- **Speed**: 15% faster than base
- **Misclick**: 5% chance
- **Best for**: Short sessions, efficiency-focused tasks

## Migration Guide

### Before (Old Way)

```python
# Old timing
self._sleep(0.2, 0.6)
time.sleep(rd.truncated_normal_sample(0.1, 0.4))

# Old mouse movement
self.mouse.move_to(target.random_point(), mouseSpeed="fast")

# Old misclick
if random.random() < 0.08:
    miss_point = Point(click_point.x + random.randint(-12, 12), ...)
    self.mouse.move_to(miss_point)
    self.mouse.click()
    self._sleep(0.2, 0.6)

# Old random behaviors
self._perform_random_behaviors()
```

### After (New Way)

```python
# New timing
self.behavior.timing.sleep("short")
self.behavior.timing.sleep((0.1, 0.4))

# New mouse movement
self.behavior.mouse.move_to(target.random_point())

# New misclick
if self.behavior.action.should_misclick():
    self.behavior.action.execute_misclick(target)

# New random behaviors
self.behavior.attention.perform_random_behaviors()
```

## Configuration

### Runtime Configuration

```python
# Disable camera for specific bot
self.behavior.configure(camera_enabled=False)

# Disable all attention behaviors
self.behavior.configure(attention_enabled=False)

# Enable breaks
self.behavior.configure(breaks_enabled=True)

# Update speed multiplier
self.behavior.update_speed_multiplier(1.2)  # 20% slower
```

### Full Custom Configuration

```python
self.behavior = BehaviorManager(
    bot=self,
    profile="experienced",
    custom_config={
        "timing": {
            "speed_multiplier": 1.1,
            "reaction_min": 0.2,
            "reaction_max": 0.5,
        },
        "mouse": {
            "default_speed": "medium",
            "overshoot_chance": 0.1,
        },
        "action": {
            "misclick_chance": 0.15,
            "hesitation_chance": 0.2,
        },
        "attention": {
            "camera_enabled": True,
            "camera_interval": (20.0, 60.0),
            "skill_check_enabled": False,
        },
        "breaks": {
            "enabled": True,
            "chance_per_check": 0.05,
            "duration_min": 15.0,
            "duration_max": 45.0,
        },
    }
)
```

## Advanced Usage

### Print Configuration Summary

```python
print(self.behavior.summary())
```

### Temporarily Disable Behaviors

```python
# Disable all
self.behavior.disable_all()

# Do precise actions...

# Re-enable
self.behavior.enable_all()
```

### Module-Specific Methods

```python
# Check if module is enabled
if self.behavior.timing.is_enabled():
    # ...

# Disable specific module
self.behavior.timing.disable()

# Update module config
self.behavior.timing.update_config(speed_multiplier=1.5)
```

## Best Practices

1. **Use behavior system consistently**: Don't mix old `time.sleep()` with new `behavior.timing.sleep()`
2. **Configure once in __init__**: Set up profile and customizations in bot initialization
3. **Use presets when possible**: `sleep("short")` is clearer than `sleep((0.1, 0.4))`
4. **Disable unused behaviors**: If bot doesn't need camera movement, disable it
5. **Profile selection**:
   - Use "cautious" for high-risk activities
   - Use "experienced" for most bots
   - Use "focused" for short, efficient sessions

## Examples

See the migration example in `src/model/osrs/woodcutter.py` (updated with behavior system).

## API Reference

See individual module files for complete API documentation:
- `utilities/behavior/modules/timing.py`
- `utilities/behavior/modules/mouse.py`
- `utilities/behavior/modules/action.py`
- `utilities/behavior/modules/attention.py`
- `utilities/behavior/modules/breaks.py`
