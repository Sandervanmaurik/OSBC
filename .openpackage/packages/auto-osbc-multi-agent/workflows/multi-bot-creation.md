# Workflow: Multi-Agent Bot Creation

## Overview
Complete workflow for creating a new bot from scratch using `/multi` command. This workflow coordinates all 7 agents to ensure comprehensive development with human-behavior as top priority.

**Duration**: 2-4 minutes  
**Agents Involved**: All 7 (code-explorer, code-architect, bot-developer, visual-debugger, test-engineer, code-reviewer, senior-developer)  
**Coordination**: Hybrid (parallel exploration/development/review, sequential synthesis)

---

## Prerequisites

Before starting:
- [ ] Game client accessible (RuneLite)
- [ ] Python venv activated
- [ ] Understanding of bot's goal/activity
- [ ] Rough idea of stop conditions

---

## Workflow Stages

### **Stage 1: EXPLORATION** (30-45 seconds, parallel)

#### 🔍 Code-Explorer Tasks
1. Search for similar bots in `src/model/osrs/`
2. Identify relevant patterns:
   - Inventory detection methods
   - Banking implementations
   - State machine structures
   - Existing human-behavior patterns
3. Map dependencies and utilities
4. Flag any anti-patterns in existing code
5. **Output**: Codebase analysis with file:line references

**Checklist**:
- [ ] Found similar bot examples
- [ ] Identified human-behavior patterns
- [ ] Flagged any existing violations
- [ ] Mapped relevant utilities

---

#### 🏗️ Code-Architect Tasks
1. Analyze bot requirements
2. Determine inheritance (Bot vs RuneLiteBot)
3. Design state machine:
   - List all states
   - Define transitions
   - Identify detection requirements
4. Plan component structure:
   - Detection methods
   - Action methods
   - State handlers
5. Ensure design supports variation/randomization
6. **Output**: Architecture blueprint

**Checklist**:
- [ ] State machine designed
- [ ] Components identified
- [ ] Design supports randomization
- [ ] No forced deterministic patterns

---

### **Stage 2: SYNTHESIS + USER QUESTIONS** (15-30 seconds, sequential)

#### 👔 Senior-Developer Tasks
1. Merge findings from Code-Explorer and Code-Architect
2. Identify information gaps or ambiguities
3. Formulate targeted user questions:
   - Stop conditions (time/count/manual)
   - Special cases handling
   - Risk tolerance (cautious/experienced/focused)
   - Camera movement needed? (disable for stationary bots)
4. Make decisions where user input not needed
5. **Output**: Consolidated plan + questions

**Example Questions**:
```
👔 Senior-Developer: "Before proceeding, I need clarification:

1. Stop Condition:
   - Time-based (run for X hours)?
   - Count-based (collect X items)?
   - Manual stop only?

2. Special Handling:
   - What if target moves/disappears?
   - Handle interruptions (other players)?
   - Banking location (closest/specific)?

3. Behavior Profile:
   - Cautious (safest, slowest)
   - Experienced (balanced) ← recommended
   - Focused (faster, slightly riskier)

4. Camera Movement:
   - Enable periodic camera adjustments?
   - Or disable (for stationary activities)?

Please answer, or I'll use sensible defaults."
```

**User Interaction**: Workflow pauses. After answers received, Senior-Developer incorporates and proceeds.

---

### **Stage 3: DEVELOPMENT** (60-90 seconds, parallel)

#### 🤖 Bot-Developer Tasks
1. Create bot file: `src/model/osrs/bot_name.py`
2. Implement state machine from architecture
3. Implement detection methods using Code-Explorer findings
4. Implement action methods with human-behavior:
   - All delays use `truncated_normal_sample()`
   - Mouse movements have duration variation
   - Add misclick simulation (8-15%)
   - Add hesitation before critical actions
   - Add distraction events (camera, skills)
5. Integrate BehaviorManager if available
6. Add comprehensive logging
7. **Output**: Bot implementation

**Checklist** (from human-behavior-checklist.md):
- [ ] All delays randomized
- [ ] Mouse movements varied
- [ ] Misclick simulation implemented
- [ ] Hesitation added
- [ ] Action sequences vary
- [ ] No hardcoded coordinates
- [ ] BehaviorManager integrated
- [ ] State machine handles all cases

---

#### 🔍 Visual-Debugger Tasks
1. Capture game states using recorder:
   ```bash
   python scripts/recorder.py --window "RuneLite" --duration 30
   ```
2. Extract templates for each detection requirement:
   ```bash
   python scripts/recorder.py --from-session "captures/..." \
       --extract-template "X,Y,W,H,template_name"
   ```
3. Test template confidence:
   ```bash
   python scripts/recorder.py --test-template \
       src/images/bot/bot_name/template.png --window "RuneLite"
   ```
4. Tune thresholds to realistic values (0.80-0.90)
5. Optimize search regions (narrow to specific areas)
6. **Output**: Templates + confidence values

**Checklist** (from human-behavior-checklist.md):
- [ ] Confidence thresholds 0.80-0.90 (not >0.95)
- [ ] Templates allow variation (not pixel-perfect)
- [ ] Search regions optimized
- [ ] All templates tested

---

#### 🧪 Test-Engineer Tasks
1. Create test file: `tests/unit/model/osrs/test_bot_name.py`
2. Write unit tests:
   - Initialization
   - State detection (positive/negative)
   - Action logic
3. Create test fixtures:
   - Capture game states for testing
   - Save to `tests/fixtures/bot_name/`
4. Write randomization validation tests:
   - Timing variation test
   - No predictable patterns test
   - Statistical distribution test
5. Write integration tests (if applicable)
6. **Output**: Test suite

**Checklist** (from human-behavior-checklist.md):
- [ ] Tests validate timing variation
- [ ] Tests check for patterns
- [ ] Statistical tests for randomness
- [ ] No deterministic expectations
- [ ] Visual fixtures created

---

### **Stage 4: REVIEW** (30-45 seconds, parallel)

#### 🔴 Code-Reviewer Tasks
1. Load all files from Stage 3
2. Run automated behavior validation scan (see `behavior-validation.md`)
3. Apply regex rules for violations:
   - Fixed delays
   - Hardcoded coordinates
   - Perfect confidence
   - Modulo patterns
4. Score each violation (confidence 0-100)
5. Filter: only report ≥80 confidence
6. Group by severity: CRITICAL → HIGH → MEDIUM
7. **Output**: Violation report

**Automated Rules Applied**:
- ✅ Fixed time.sleep() scan
- ✅ Hardcoded coordinate scan
- ✅ Missing randomization imports
- ✅ Perfect confidence thresholds
- ✅ Modulo patterns
- ✅ Narrow variation ranges

**Report Format**:
```markdown
## Code-Reviewer: Validation Results

### Scan Summary
- Files: 3
- Violations: 2
- Critical: 0
- High: 1
- Medium: 1

### HIGH VIOLATIONS
[File:Line - Rule - Confidence - Fix]

### Status
✅ APPROVED (warnings noted)
or
❌ BLOCKED (critical violations)
```

---

#### 👔 Senior-Developer Tasks
1. Review all code from Stage 3
2. Check code quality:
   - Separation of concerns
   - Readability
   - Maintainability
   - No unnecessary complexity
3. Validate test coverage
4. Perform final human-behavior validation:
   - Review all agent checklists
   - Verify overall design appears human
   - No systemic detection risks
5. **Output**: Quality assessment + approval

**Final Validation Questions**:
1. Would an observer see robotic patterns? → NO
2. Could timing be predicted after 100 iterations? → NO
3. Are mouse movements natural-looking? → YES
4. Do errors/variations occur like a human? → YES
5. Is the bot distinguishable from human player? → NO

**Checklist** (from human-behavior-checklist.md):
- [ ] ✅ Bot-Developer checklist passed
- [ ] ✅ Visual-Debugger checklist passed
- [ ] ✅ Test-Engineer checklist passed
- [ ] ✅ Code-Reviewer scan passed
- [ ] ✅ Code quality acceptable
- [ ] ✅ Overall design appears human

---

### **Stage 5: FINAL SYNTHESIS** (10-15 seconds, sequential)

#### 👔 Senior-Developer Tasks
1. Aggregate all agent reports
2. Verify all checklists completed
3. Generate summary:
   - What was accomplished
   - Agent contributions
   - Human-behavior validation status
   - Warnings/suggestions
   - Next steps
4. **Output**: Complete consultation report

**Summary Template**:
```markdown
## ✅ Multi-Agent Bot Creation Complete

### Consultation Summary
- **Duration**: 2m 45s
- **Agents**: 7 consulted
- **Status**: APPROVED

### What Was Built
- Bot: `src/model/osrs/bot_name.py`
- Tests: `tests/unit/model/osrs/test_bot_name.py`
- Templates: 4 templates extracted
- Architecture: [State machine description]

### Agent Contributions
🔍 Code-Explorer: Found similar patterns in existing bots
🏗️ Code-Architect: Designed 5-state machine
🤖 Bot-Developer: Implemented with full randomization
🔍 Visual-Debugger: Extracted 4 templates, tuned thresholds
🧪 Test-Engineer: Created 15 tests with statistical validation
🔴 Code-Reviewer: 0 critical, 1 minor warning
👔 Senior-Developer: Validated all checklists

### Human-Behavior Validation
✅ Bot-Developer: 8/8 checklist items passed
✅ Visual-Debugger: 4/4 checklist items passed
✅ Test-Engineer: 6/6 checklist items passed
✅ Code-Reviewer: Automated scan passed
✅ Senior-Developer: Final validation passed

**Overall**: ALL HUMAN-BEHAVIOR REQUIREMENTS MET

### Warnings/Suggestions
⚠️ Consider adding camera movement (currently disabled)

### Next Steps
1. Review generated code
2. Run tests: `pytest tests/unit/model/osrs/test_bot_name.py`
3. Manual test in game
4. Adjust behavior profile if needed

Ready to proceed?
```

---

## Success Criteria

Bot creation is successful when:

- ✅ All 5 stages completed
- ✅ All agent checklists passed
- ✅ No blocking violations
- ✅ Tests created and passing
- ✅ Templates extracted and tested
- ✅ Human-behavior validation complete
- ✅ Senior-Developer approval received

---

## Example: Creating a Cooking Bot

### User Command
```
/multi Create a cooking bot that cooks shrimp at a range and banks when inventory is full
```

### Stage 1: Exploration
```
🔍 Code-Explorer: "Analyzing codebase..."
├─ Found: fishing.py has similar inventory detection
├─ Found: woodcutter.py implements banking
├─ Pattern: State machines use while loops with state checks
└─ ✅ Checklist: Existing bots have good randomization

🏗️ Code-Architect: "Designing architecture..."
├─ Inheritance: RuneLiteBot
├─ States: CheckInventory → WalkToRange → Cook → WalkToBank → Bank → Repeat
├─ Detection: raw_shrimp.png, cooking_range.png, bank_booth.png
└─ ✅ Checklist: State transitions support variation
```

### Stage 2: Questions
```
👔 Senior-Developer: "Questions:
1. Stop after X cooked shrimp or time-based?
2. Specific range location or any nearby?
3. Behavior profile preference?"

[User answers: "100 cooked shrimp, any range, experienced profile"]

👔 Senior-Developer: "Understood. Proceeding with:
- Stop: 100 cooked shrimp
- Range: nearest detected
- Profile: Experienced (balanced)
- Camera: Enable (adds realism)"
```

### Stage 3: Development
```
🤖 Bot-Developer: "Implementing OSRSCooking..."
├─ 5-state machine created
├─ Randomization: truncated_normal_sample for all delays
├─ Misclick: 10% chance simulation
└─ ✅ Checklist: 8/8 items passed

🔍 Visual-Debugger: "Extracting templates..."
├─ raw_shrimp.png (conf: 0.83) ✅
├─ cooking_range.png (conf: 0.81) ✅
├─ bank_booth.png (conf: 0.85) ✅
└─ ✅ Checklist: 4/4 items passed

🧪 Test-Engineer: "Creating tests..."
├─ 12 unit tests created
├─ Randomization: 100 iterations validated
└─ ✅ Checklist: 6/6 items passed
```

### Stage 4: Review
```
🔴 Code-Reviewer: "Scanning for violations..."
├─ Automated scan: 0 critical, 0 high
├─ Warning: Consider adding skill tab checks
└─ ✅ Status: APPROVED

👔 Senior-Developer: "Final validation..."
├─ Code quality: Clean, readable ✅
├─ Tests: 12/12 passing, 87% coverage ✅
├─ Human-behavior: All checklists passed ✅
└─ ✅ Status: APPROVED
```

### Stage 5: Synthesis
```
👔 Senior-Developer: "✅ Cooking bot creation complete!

Summary:
- 7 agents consulted (2m 30s)
- Bot ready: src/model/osrs/cooking.py
- Tests passing: 12/12
- Human-behavior: VALIDATED
- Ready for manual testing

Next: Run in game and adjust if needed."
```

---

## Troubleshooting

### "Code-Reviewer blocked with violations"
- Fix the violations listed
- Re-run `/multi` or just the review stage
- Common: forgot to use truncated_normal_sample

### "Visual-Debugger can't find templates"
- Ensure game is open and visible
- Check window title matches ("RuneLite")
- Recapture with recorder.py

### "Tests failing"
- Check test fixtures exist
- Verify bot logic matches test expectations
- Ensure randomization tests use ranges, not exact values

---

## References

- **Command Reference**: `.claude/commands/multi-agent.md`
- **Human-Behavior Checklist**: `.claude/skills/human-behavior-checklist.md`
- **Validation Rules**: `.claude/commands/behavior-validation.md`
- **Agent Docs**: `.claude/agents/*.md`
