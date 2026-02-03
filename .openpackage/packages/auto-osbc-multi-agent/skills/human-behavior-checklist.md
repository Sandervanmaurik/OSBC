# Human-Behavior Validation Checklist

## Purpose
Mandatory validation checklist for all agents to ensure undetectable, human-like bot behavior. Every agent must validate their work against relevant checklist items before completing their task.

---

## 🔴 UNIVERSAL REQUIREMENTS (ALL AGENTS MUST VERIFY)

### Timing & Delays
- [ ] **No fixed time.sleep() values** - All delays use `truncated_normal_sample()` or similar randomization
- [ ] **Variable delay ranges** - Min/max spread is realistic (not too tight)
- [ ] **Context-appropriate timing** - Delays match human reaction times for the action

### Coordinates & Positioning
- [ ] **No hardcoded coordinates** - All positions use template detection or relative positioning
- [ ] **Click variation** - Clicks within target area vary (not same pixel)
- [ ] **Movement paths vary** - Mouse doesn't take identical paths

### Patterns & Predictability
- [ ] **Action sequences vary** - Order of operations changes between iterations
- [ ] **No deterministic loops** - Loop counts, timing, patterns have randomization
- [ ] **Variation in success rate** - Occasional misses/errors simulate human imperfection

---

## 🤖 BOT DEVELOPER CHECKLIST

### Randomization Implementation
- [ ] All `time.sleep()` calls use `truncated_normal_sample(mean, std, min, max)`
- [ ] Mouse movements have duration variation: `duration=truncated_normal_sample(0.3, 0.1, 0.2, 0.6)`
- [ ] Click positions vary within target bounds (use region, not point)
- [ ] Action sequences shuffled or varied using random.random() checks

### Human Behavior Patterns
- [ ] **Misclick simulation**: 8-15% chance to miss click and retry
- [ ] **Hesitation**: Random pauses before critical actions
- [ ] **Distraction**: Occasional random camera movements or skill checks
- [ ] **Fatigue simulation**: Slight increase in reaction time over long sessions

### State Machine Design
- [ ] State transitions include variable delays
- [ ] State checking intervals are randomized
- [ ] Error recovery paths exist and vary in approach
- [ ] No infinite loops without exit conditions

### Integration with Behavior System
- [ ] Uses `BehaviorManager` if available (see `src/behavior/`)
- [ ] Profile-aware: respects cautious/experienced/focused settings
- [ ] Misclick behavior configured appropriately
- [ ] Break patterns integrated

### Code Examples Review
```python
# ✅ GOOD - Randomized timing
delay = truncated_normal_sample(2.5, 0.5, 1.5, 4.0)
time.sleep(delay)

# ❌ BAD - Fixed timing
time.sleep(2.5)

# ✅ GOOD - Varied mouse movement
mouse.move_to(point, duration=truncated_normal_sample(0.3, 0.1, 0.2, 0.6))

# ❌ BAD - Fixed duration
mouse.move_to(point, duration=0.3)

# ✅ GOOD - Occasional variation
if random.random() < 0.15:  # 15% chance
    self.check_skill_tab()
    
# ❌ BAD - Predictable every N iterations
if iteration % 10 == 0:
    self.check_skill_tab()
```

---

## 🏗️ CODE ARCHITECT CHECKLIST

### Architecture Design
- [ ] **State machine supports variation** - Transitions allow multiple paths
- [ ] **No forced deterministic patterns** - Design doesn't require fixed sequences
- [ ] **Randomization hooks** - Architecture provides places to inject variation
- [ ] **Behavior profiles supported** - Design works with cautious/experienced/focused modes

### Component Boundaries
- [ ] Detection logic separated from timing logic
- [ ] Behavior/timing configurable per component
- [ ] No tight coupling that forces fixed patterns
- [ ] Mouse/keyboard actions abstracted (allows variation injection)

### Data Flow
- [ ] Configuration supports randomization parameters (min/max ranges)
- [ ] State transitions include timing metadata
- [ ] Error paths designed for variation (not always same recovery)

### Design Patterns
- [ ] Strategy pattern for action variation
- [ ] Observer pattern for distraction events
- [ ] Factory pattern for randomized object creation
- [ ] No singleton patterns that store fixed timing values

---

## 🔍 CODE EXPLORER CHECKLIST

### Pattern Detection
- [ ] **Identify existing human-behavior patterns** in similar bots
- [ ] **Flag anti-patterns**: Fixed delays, hardcoded coords, deterministic loops
- [ ] **Map randomization utilities** used in codebase
- [ ] **Document behavior system integration** if present

### Risk Assessment
- [ ] Identify code that uses fixed `time.sleep()` values
- [ ] Find hardcoded coordinate usage
- [ ] Detect perfect pattern matching (confidence=1.0)
- [ ] Flag deterministic loop structures

### Reporting
- [ ] List files with good human-behavior examples
- [ ] List files with detection risks
- [ ] Provide file:line references for violations
- [ ] Suggest remediation based on existing patterns

---

## 🔴 CODE REVIEWER CHECKLIST

### Automated Detection Rules
- [ ] **Scan for `time.sleep(<number>)`** - Flag all fixed delays
- [ ] **Scan for hardcoded coordinates** - Detect `x=<number>, y=<number>` patterns
- [ ] **Detect missing randomization imports** - No `random_util` or `random` imports
- [ ] **Check confidence thresholds** - Flag confidence > 0.95 (too perfect)

### Regex Patterns to Apply
```python
# Anti-patterns to detect:
time\.sleep\(\d+\.?\d*\)                    # Fixed delays
time\.sleep\([0-9.]+\)                       # Literal sleep values
mouse\.move_to\(.*duration=\d+\.?\d*\)      # Fixed mouse duration
if.*%.*==.*0:                                # Modulo patterns (predictable)
\.click\(\s*\(\s*\d+\s*,\s*\d+\s*\)\s*\)   # Hardcoded click coords
```

### Confidence Scoring
```
100: time.sleep(2.5) found → CRITICAL violation
95:  Hardcoded coordinates found → CRITICAL violation  
90:  Pattern uses % for predictability → HIGH violation
85:  No randomization imports found → HIGH violation
80:  Confidence threshold = 0.99 → MEDIUM violation
```

### Review Output Format
- [ ] Group violations by severity (Critical/High/Medium)
- [ ] Provide file:line references
- [ ] Suggest fix using existing utilities
- [ ] Reference human-behavior skill doc

---

## 👔 SENIOR DEVELOPER CHECKLIST

### Overall Design Review
- [ ] **System appears human** - No obvious patterns when observing execution
- [ ] **Variation at multiple levels** - Timing, paths, sequences all vary
- [ ] **No systemic detection risks** - Design doesn't create predictable signatures
- [ ] **Behavior configurable** - User can adjust risk tolerance

### Code Quality + Behavior
- [ ] Randomization doesn't sacrifice code readability
- [ ] Timing logic separated from business logic
- [ ] Human-behavior patterns well-documented
- [ ] Tests validate variation (not just functionality)

### Cross-Agent Validation
- [ ] ✅ Bot-Developer checklist reviewed and passed
- [ ] ✅ Code-Architect checklist reviewed and passed
- [ ] ✅ Code-Explorer findings addressed
- [ ] ✅ Code-Reviewer violations resolved
- [ ] ✅ Visual-Debugger detection allows variation
- [ ] ✅ Test-Engineer validated randomness

### Final Approval Questions
1. Would an observer see robotic patterns?
2. Could timing be predicted after 100 iterations?
3. Are mouse movements natural-looking?
4. Do errors/variations occur like a human?
5. Is the bot distinguishable from human player?

**If ANY answer is "yes" or "maybe" to questions 1-2 or "no" to 3-5, DO NOT APPROVE.**

---

## 🔍 VISUAL DEBUGGER CHECKLIST

### Template Matching
- [ ] **Confidence thresholds realistic** - Not 0.99 (allows for variation)
- [ ] **Templates not pixel-perfect** - Some tolerance built in
- [ ] **Detection regions allow movement** - Not single-pixel precision
- [ ] **Multiple templates for states** - Accounts for UI variations

### Threshold Configuration
```python
# ✅ GOOD - Allows variation
result = search_img_in_rect(template, rect, conf=0.82)

# ⚠️ CAUTION - Too perfect
result = search_img_in_rect(template, rect, conf=0.99)

# ✅ GOOD - Confidence range
conf = random.uniform(0.80, 0.85)  # Vary threshold
```

### Performance vs Behavior
- [ ] Optimization doesn't force deterministic patterns
- [ ] Cache strategies don't eliminate variation
- [ ] Region-of-interest allows for positional variance

---

## 🧪 TEST ENGINEER CHECKLIST

### Randomization Testing
- [ ] **Timing variation tests** - Verify delays are not fixed
- [ ] **Statistical distribution tests** - Confirm truncated normal distribution
- [ ] **Path variation tests** - Mouse paths differ between runs
- [ ] **Sequence variation tests** - Action order varies

### Test Examples
```python
def test_timing_randomization(bot):
    """Verify delays are randomized, not fixed"""
    delays = [bot.get_action_delay() for _ in range(100)]
    
    # Should have substantial variation
    assert len(set(delays)) > 50, "Too little variation in delays"
    assert max(delays) - min(delays) > 0.5, "Range too narrow"
    
    # Should follow expected distribution
    mean = sum(delays) / len(delays)
    assert 2.0 < mean < 3.0, "Mean outside expected range"

def test_no_predictable_patterns(bot):
    """Ensure actions don't follow predictable patterns"""
    actions = [bot.next_action() for _ in range(50)]
    
    # No repeating sequences
    for i in range(len(actions) - 3):
        sequence = tuple(actions[i:i+3])
        count = actions.count(sequence)
        assert count < 3, f"Pattern {sequence} repeats too often"
```

### Anti-Determinism Tests
- [ ] No test expects exact timing
- [ ] No test expects exact sequences
- [ ] Tests use ranges, not exact values
- [ ] Statistical tests for randomness quality

---

## 📊 VALIDATION SUMMARY TEMPLATE

Each agent should report their validation status:

```markdown
## [Agent Name] Human-Behavior Validation

### Checklist Results
✅ Item 1: Description - PASSED
✅ Item 2: Description - PASSED  
⚠️ Item 3: Description - WARNING (details)
❌ Item 4: Description - FAILED (details + fix)

### Overall Status
- Total Items: X
- Passed: Y
- Warnings: Z
- Failed: W

### Recommendation
[APPROVED / NEEDS REVISION / BLOCKED]

### Notes
[Any additional context or concerns]
```

---

## 🚨 ENFORCEMENT RULES

### Blocking Violations (Must Fix Before Proceeding)
1. Any `time.sleep()` with literal numeric value
2. Hardcoded click coordinates (x=123, y=456)
3. Deterministic loops without variation
4. Confidence thresholds > 0.95
5. No randomization imports in bot file

### Warning Violations (Should Fix, Can Defer)
1. Limited variation range (max-min < 0.3)
2. Predictable patterns using modulo
3. No misclick/error simulation
4. Insufficient action sequence variation

### Process
1. Code-Reviewer detects violations automatically
2. Senior-Developer reviews all checklists
3. If blocking violations exist → HALT, request fixes
4. If only warnings → Proceed with notation
5. All violations logged for user review

---

## 📚 REFERENCES

- **Human Behavior Skill**: `.claude/skills/human-behavior.md`
- **Behavior System**: `BEHAVIOR_SYSTEM_COMPLETE.md`
- **Random Utilities**: `src/utilities/random_util.py`
- **Behavior Manager**: `src/behavior/manager.py`
- **Existing Examples**: `src/model/osrs/thieving.py`, `src/model/osrs/woodcutter.py`

---

## ✅ QUICK REFERENCE

**Before completing ANY task, ask yourself:**
1. Does this code have randomization?
2. Could someone predict the next action?
3. Does it look human when running?

**If uncertain about any answer → CONSULT CHECKLIST**
