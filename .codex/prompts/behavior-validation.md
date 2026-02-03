# Behavior Validation Automation Rules

## Purpose
Automated detection rules for Code-Reviewer agent to scan code for human-behavior violations. These rules use regex patterns and heuristics to identify anti-patterns that make bots detectable.

---

## 🔴 CRITICAL VIOLATIONS (Confidence: 95-100)

### Rule 1: Fixed time.sleep() Values

**Pattern**:
```regex
time\.sleep\s*\(\s*\d+\.?\d*\s*\)
```

**Matches**:
```python
time.sleep(2.5)        # ❌ VIOLATION
time.sleep(1)          # ❌ VIOLATION
time.sleep(0.5)        # ❌ VIOLATION
```

**Doesn't Match** (OK):
```python
time.sleep(delay)                                    # ✅ Variable
time.sleep(truncated_normal_sample(2.5, 0.5, 1, 4)) # ✅ Randomized
time.sleep(random.uniform(1, 3))                     # ✅ Randomized
```

**Confidence**: 100  
**Severity**: CRITICAL  
**Message**: "Fixed delay detected. Use truncated_normal_sample() for randomization."  
**Fix Suggestion**:
```python
# Replace:
time.sleep(2.5)

# With:
from utilities.random_util import truncated_normal_sample
delay = truncated_normal_sample(2.5, 0.5, 1.5, 4.0)
time.sleep(delay)
```

---

### Rule 2: Hardcoded Click Coordinates

**Pattern**:
```regex
\.click\s*\(\s*\(\s*\d+\s*,\s*\d+\s*\)\s*\)
```

**Matches**:
```python
mouse.click((500, 300))     # ❌ VIOLATION
self.click((100, 200))      # ❌ VIOLATION
pyautogui.click(150, 250)   # ❌ VIOLATION
```

**Doesn't Match** (OK):
```python
mouse.click(point)                    # ✅ Variable
self.click_region(region)             # ✅ Region-based
self.mouse_click(detected_position)   # ✅ Detected
```

**Confidence**: 95  
**Severity**: CRITICAL  
**Message**: "Hardcoded coordinates detected. Use template detection or relative positioning."  
**Fix Suggestion**:
```python
# Replace:
mouse.click((500, 300))

# With:
template = self.get_img_path("bot/target.png")
result = self.search_img_in_rect(template, region)
if result:
    self.mouse_move_click(result.random_point())
```

---

### Rule 3: Hardcoded Mouse Move Coordinates

**Pattern**:
```regex
\.move_to\s*\(\s*\(\s*\d+\s*,\s*\d+\s*\)
```

**Matches**:
```python
mouse.move_to((640, 480))       # ❌ VIOLATION
pyautogui.moveTo(100, 200)      # ❌ VIOLATION
```

**Confidence**: 95  
**Severity**: CRITICAL  
**Message**: "Hardcoded mouse movement. Use template detection."

---

### Rule 4: Fixed Mouse Movement Duration

**Pattern**:
```regex
duration\s*=\s*\d+\.?\d*
```

**Matches**:
```python
mouse.move_to(point, duration=0.3)    # ❌ VIOLATION
self.mouse_move(p, duration=1.5)      # ❌ VIOLATION
```

**Doesn't Match** (OK):
```python
duration = truncated_normal_sample(0.3, 0.1, 0.2, 0.6)
mouse.move_to(point, duration=duration)              # ✅ Randomized
```

**Confidence**: 90  
**Severity**: CRITICAL  
**Message**: "Fixed mouse duration. Randomize for human-like movement."  
**Fix Suggestion**:
```python
# Replace:
mouse.move_to(point, duration=0.3)

# With:
from utilities.random_util import truncated_normal_sample
duration = truncated_normal_sample(0.3, 0.1, 0.2, 0.6)
mouse.move_to(point, duration=duration)
```

---

## 🟠 HIGH VIOLATIONS (Confidence: 85-94)

### Rule 5: Missing Randomization Imports

**Detection Logic**:
```python
# If file contains bot logic AND doesn't import random utilities
has_bot_class = re.search(r'class.*Bot\(', content)
has_random_import = re.search(r'from.*random', content) or \
                    re.search(r'import random', content)

if has_bot_class and not has_random_import:
    # VIOLATION
```

**Confidence**: 85  
**Severity**: HIGH  
**Message**: "Bot file missing randomization imports. Add random_util imports."  
**Fix Suggestion**:
```python
# Add to imports:
from utilities.random_util import truncated_normal_sample
import random
```

---

### Rule 6: Perfect Confidence Thresholds

**Pattern**:
```regex
conf(?:idence)?\s*=\s*(?:0\.9[5-9]|1\.0)
```

**Matches**:
```python
result = search(template, conf=0.99)    # ❌ VIOLATION
detection = find(img, confidence=1.0)   # ❌ VIOLATION
if match(template, conf=0.95):          # ⚠️ WARNING
```

**Confidence**: 85  
**Severity**: HIGH  
**Message**: "Confidence threshold too perfect (≥0.95). Lower to 0.80-0.90 for realistic detection."  
**Fix Suggestion**:
```python
# Replace:
result = search(template, conf=0.99)

# With:
result = search(template, conf=0.82)
```

---

### Rule 7: Modulo Pattern for Predictability

**Pattern**:
```regex
if.*%\s*\d+\s*==\s*0:
```

**Matches**:
```python
if iteration % 10 == 0:        # ❌ VIOLATION
if count % 5 == 0:             # ❌ VIOLATION
```

**Doesn't Match** (OK):
```python
if random.random() < 0.1:               # ✅ Probability-based
if iteration >= random.randint(8, 15):  # ✅ Randomized
```

**Confidence**: 85  
**Severity**: HIGH  
**Message**: "Modulo pattern creates predictable timing. Use probability or randomized intervals."  
**Fix Suggestion**:
```python
# Replace:
if iteration % 10 == 0:
    self.check_skill()

# With:
if random.random() < 0.1:  # ~10% chance each iteration
    self.check_skill()

# OR:
if iteration >= self.next_check_at:
    self.check_skill()
    self.next_check_at = iteration + random.randint(8, 15)
```

---

## 🟡 MEDIUM VIOLATIONS (Confidence: 75-84)

### Rule 8: Narrow Variation Range

**Detection Logic**:
```python
# Detect truncated_normal_sample with range < 0.3
pattern = r'truncated_normal_sample\s*\(\s*(\d+\.?\d*)\s*,\s*(\d+\.?\d*)\s*,\s*(\d+\.?\d*)\s*,\s*(\d+\.?\d*)\s*\)'

for match in matches:
    mean, std, min_val, max_val = map(float, match.groups())
    variation_range = max_val - min_val
    
    if variation_range < 0.3:
        # VIOLATION
```

**Example**:
```python
delay = truncated_normal_sample(2.0, 0.05, 1.9, 2.1)  # ❌ Range = 0.2 (too narrow)
```

**Confidence**: 75  
**Severity**: MEDIUM  
**Message**: "Variation range too narrow. Increase min/max spread for realistic variation."  
**Fix Suggestion**:
```python
# Replace:
delay = truncated_normal_sample(2.0, 0.05, 1.9, 2.1)

# With:
delay = truncated_normal_sample(2.0, 0.4, 1.2, 3.0)
```

---

### Rule 9: No Error Simulation

**Detection Logic**:
```python
# Check for misclick/error simulation in bot files
has_misclick = re.search(r'misclick|miss.*click|error.*sim', content, re.I)
has_hesitation = re.search(r'hesitat|pause.*before', content, re.I)
is_bot_file = 'class.*Bot' in content

if is_bot_file and not (has_misclick or has_hesitation):
    # VIOLATION
```

**Confidence**: 75  
**Severity**: MEDIUM  
**Message**: "No error/misclick simulation detected. Add human imperfection."  
**Fix Suggestion**:
```python
# Add to bot logic:
def perform_click(self, target):
    # 10% chance to miss and retry
    if random.random() < 0.10:
        self.log_msg("Missed click, retrying...")
        offset = (random.randint(-5, 5), random.randint(-5, 5))
        self.mouse_move(target.offset(*offset))
        time.sleep(random.uniform(0.1, 0.3))
    
    self.mouse_click(target)
```

---

### Rule 10: No Camera/View Variation

**Detection Logic**:
```python
# Check for camera adjustment in bot main loops
has_camera = re.search(r'camera|adjust.*view|rotate.*screen', content, re.I)
has_main_loop = re.search(r'def main_loop|while.*running', content)

if has_main_loop and not has_camera:
    # VIOLATION (unless explicitly disabled for fletching-type bots)
```

**Confidence**: 70  
**Severity**: MEDIUM  
**Message**: "No camera/view adjustments detected. Consider adding periodic camera movement."  
**Fix Suggestion**:
```python
# Add to main loop:
if random.random() < 0.05:  # 5% chance each iteration
    self.log_msg("Adjusting camera...")
    # Slight camera rotation
    pyautogui.keyDown('left' if random.random() < 0.5 else 'right')
    time.sleep(random.uniform(0.1, 0.3))
    pyautogui.keyUp('left')
    pyautogui.keyUp('right')
```

---

## 📊 AUTOMATED SCAN PROCESS

### Scan Sequence

1. **Load Code**: Read all modified/new files
2. **Apply Rules**: Run regex patterns and detection logic
3. **Score Violations**: Assign confidence to each match
4. **Filter Results**: Only report violations ≥80 confidence
5. **Group by Severity**: CRITICAL → HIGH → MEDIUM
6. **Generate Report**: File:line references + fix suggestions

### Output Format

```markdown
## Code-Reviewer: Automated Behavior Validation

### Scan Summary
- Files scanned: 3
- Total violations: 5
- Critical: 2
- High: 2
- Medium: 1

---

### CRITICAL VIOLATIONS (Must Fix)

**File**: `src/model/osrs/new_bot.py`  
**Line**: 45  
**Rule**: Fixed time.sleep() Values  
**Confidence**: 100  
**Code**:
```python
time.sleep(2.5)
```
**Fix**:
```python
delay = truncated_normal_sample(2.5, 0.5, 1.5, 4.0)
time.sleep(delay)
```

---

### HIGH VIOLATIONS (Recommended Fix)

**File**: `src/model/osrs/new_bot.py`  
**Line**: 78  
**Rule**: Modulo Pattern for Predictability  
**Confidence**: 85  
**Code**:
```python
if iteration % 10 == 0:
```
**Fix**:
```python
if random.random() < 0.1:
```

---

### Overall Status
❌ BLOCKED - Critical violations must be fixed before proceeding

### Recommendation
Fix 2 critical violations and re-run scan.
```

---

## 🔧 IMPLEMENTATION GUIDE (for Code-Reviewer Agent)

### Pseudo-Code

```python
def validate_human_behavior(files: list[str]) -> ValidationReport:
    violations = []
    
    for file_path in files:
        content = read_file(file_path)
        lines = content.split('\n')
        
        # Apply each rule
        for rule in RULES:
            matches = rule.pattern.finditer(content)
            for match in matches:
                line_num = get_line_number(content, match.start())
                
                violation = {
                    'file': file_path,
                    'line': line_num,
                    'rule': rule.name,
                    'confidence': rule.confidence,
                    'severity': rule.severity,
                    'code_snippet': lines[line_num-1],
                    'fix_suggestion': rule.fix_template,
                    'message': rule.message
                }
                
                violations.append(violation)
        
        # Apply heuristic rules (non-regex)
        violations.extend(check_missing_imports(content, file_path))
        violations.extend(check_narrow_ranges(content, file_path))
        violations.extend(check_error_simulation(content, file_path))
    
    # Filter: only confidence >= 80
    violations = [v for v in violations if v['confidence'] >= 80]
    
    # Sort: severity then confidence
    violations.sort(key=lambda v: (severity_order(v['severity']), -v['confidence']))
    
    return ValidationReport(violations)
```

---

## 🎯 INTEGRATION WITH /multi WORKFLOW

### Stage 4: Review

When Code-Reviewer is activated:

1. **Receive input**: List of files from Stage 3 (Development)
2. **Run automated scan**: Apply all rules from this document
3. **Generate report**: Violations with confidence ≥80
4. **Check blocking status**:
   - If CRITICAL violations exist → Status: BLOCKED
   - If only HIGH/MEDIUM → Status: APPROVED with warnings
5. **Output report**: To Senior-Developer for synthesis

---

## 📚 REFERENCES

- **Human-Behavior Checklist**: `.claude/skills/human-behavior-checklist.md`
- **Random Utilities**: `src/utilities/random_util.py`
- **Behavior System**: `src/behavior/`
- **Example Bots**: `src/model/osrs/thieving.py` (good patterns)

---

## ✅ TESTING THE RULES

### Test Cases

```python
# CRITICAL: Fixed delay
time.sleep(2.5)                           # Should detect ✓
delay = truncated_normal_sample(2.5, 0.5, 1, 4)
time.sleep(delay)                         # Should NOT detect ✓

# CRITICAL: Hardcoded coords
mouse.click((500, 300))                   # Should detect ✓
mouse.click(point)                        # Should NOT detect ✓

# HIGH: Perfect confidence
result = search(t, conf=0.99)             # Should detect ✓
result = search(t, conf=0.82)             # Should NOT detect ✓

# MEDIUM: Narrow range
delay = truncated_normal_sample(2, 0.05, 1.9, 2.1)  # Should detect ✓
delay = truncated_normal_sample(2, 0.5, 1, 3)       # Should NOT detect ✓
```

---

## 🔄 CONTINUOUS IMPROVEMENT

These rules should be updated as new anti-patterns are discovered:

1. **Monitor false positives**: If rule flags valid code, adjust confidence or pattern
2. **Add new rules**: As detection methods evolve, add new violation patterns
3. **Update fix suggestions**: Keep remediation examples current with best practices
4. **Calibrate confidence**: Adjust based on real-world violation accuracy

**Rule update process**: Document in this file, notify all agents via AGENTS.md update.
