# Skill: Human-Like Behavior Implementation

## Core Principle
Every bot action must appear human. No fixed patterns, no robotic precision, no predictable timing.

## Required Implementation Patterns

### 1. Timing Randomization
```python
# ALWAYS use random_util for delays
from utilities.random_util import truncated_normal_sample

# Natural task duration (mean, std_dev, min, max)
delay = truncated_normal_sample(2.5, 0.5, 1.5, 4.0)
time.sleep(delay)

# NEVER use fixed delays
time.sleep(2.5)  # ❌ FORBIDDEN - Detectable pattern
```

### 2. Mouse Movement
```python
# Use mouse utility with randomization
from utilities.mouse import Mouse

# Natural click with variation
mouse = Mouse()
mouse.move_to(point, duration=random_util.truncated_normal_sample(0.3, 0.1, 0.2, 0.6))
mouse.click()

# Add occasional misclicks/adjustments
if random.random() < 0.15:  # 15% chance
    mouse.move_rel(random.randint(-5, 5), random.randint(-5, 5))
    time.sleep(random.uniform(0.1, 0.3))
```

### 3. Action Variation
```python
# Vary the sequence of actions
actions = ["check_inventory", "look_around", "continue_task"]
if random.random() < 0.2:  # 20% chance to change order
    random.shuffle(actions)

# Add "thinking" pauses
if random.random() < 0.25:  # 25% chance
    time.sleep(truncated_normal_sample(1.0, 0.3, 0.5, 2.0))
```

### 4. Camera/View Changes
```python
# Periodically adjust camera (humans don't stare at one spot)
if self.iterations % random.randint(8, 15) == 0:
    self.adjust_camera()  # Implement slight camera movements
```

### 5. Failure/Mistake Simulation
```python
# Occasionally "miss" a click or hesitate
if random.random() < 0.08:  # 8% error rate
    self.log_msg("Missed click, retrying...")
    time.sleep(random.uniform(0.2, 0.5))
    # Then retry the action
```

## Anti-Detection Checklist

Before submitting any bot code, verify:
- [ ] No fixed `time.sleep()` values
- [ ] Mouse movements use duration randomization
- [ ] Action sequences vary between iterations
- [ ] Camera/view adjustments included
- [ ] "Distraction" events implemented
- [ ] No perfect pattern matching (use thresholds)
- [ ] Input timing varies (clicks, keys)

## When to Apply

**EVERY** bot action that:
- Moves the mouse
- Clicks/interacts
- Waits/delays
- Performs repeated actions
- Makes decisions

## Examples in Codebase

See existing implementations:
- `src/model/osrs/thieving.py` - Random timing patterns
- `utilities/mouse.py` - Movement variation
- `utilities/random_util.py` - Distribution functions
