# Example: Multi-Agent Bot Creation (Fishing Bot)

## User Command
```
/multi Create a fishing bot that fishes shrimp at a fishing spot and banks when inventory is full
```

---

## Stage 1: EXPLORATION (35 seconds)

```
🔍 Code-Explorer: "Analyzing codebase for fishing-related patterns..."
├─ Found: src/model/osrs/fishing.py (existing but incomplete)
├─ Found: src/model/osrs/woodcutter.py (good banking example)
├─ Pattern: Inventory detection using search_img_in_rect
├─ Pattern: Banking state machine in woodcutter
├─ Behavior: Both use truncated_normal_sample ✅
└─ ✅ Checklist: 4/4 items - Existing patterns validated

🏗️ Code-Architect: "Designing fishing bot architecture..."
├─ Inheritance: RuneLiteBot (uses game window detection)
├─ State Machine:
│   1. CheckInventory (is full?)
│   2. FindFishingSpot (template detection)
│   3. Fish (click spot, wait for animation)
│   4. WalkToBank (path to nearest bank)
│   5. Bank (deposit fish, return)
├─ Detection Requirements:
│   - fishing_spot_shrimp.png (Net icon)
│   - inventory_shrimp.png (Raw shrimp)
│   - bank_booth.png (Bank)
│   - fishing_animation.png (Character fishing)
├─ Data Flow: State → Detection → Action → Delay → State
└─ ✅ Checklist: 4/4 items - Architecture supports variation
```

---

## Stage 2: SYNTHESIS + QUESTIONS (18 seconds)

```
👔 Senior-Developer: "Consolidating findings from exploration phase...

Based on Code-Explorer and Code-Architect analysis:
- Similar pattern to woodcutter (proven approach)
- Need 4 templates for detection
- 5-state machine with clear transitions

Questions before I proceed:

1. **Stop Condition**:
   a) Time-based (e.g., run for 2 hours)
   b) Count-based (e.g., catch 500 shrimp)
   c) Manual stop only

2. **Fishing Location**:
   a) Assume player is already at fishing spot
   b) Bot should walk to specific location first

3. **Behavior Profile**:
   a) Cautious (safest, 30% slower, 12% misclick)
   b) Experienced (balanced) ← recommended
   c) Focused (15% faster, 5% misclick)

4. **Camera Movement**:
   a) Enable periodic camera adjustments (more human-like)
   b) Disable (if player maintains view)

Please answer 1-4, or I'll use: b, a, b, a (sensible defaults)."
```

**User Response**:
```
"Count-based: 1000 shrimp. Assume at spot. Experienced profile. Enable camera."
```

```
👔 Senior-Developer: "Understood! Proceeding with:
├─ Stop: 1000 shrimp collected
├─ Location: Player at fishing spot
├─ Profile: Experienced (balanced)
├─ Camera: Enabled (5% chance per iteration)
└─ Estimated implementation time: 60-90 seconds"
```

---

## Stage 3: DEVELOPMENT (75 seconds, parallel)

```
🤖 Bot-Developer: "Implementing OSRSFishing class..."
├─ File: src/model/osrs/fishing.py
├─ Inherits: RuneLiteBot
├─ State machine: 5 states implemented
│   
├─ Randomization applied:
│   ├─ Fishing delay: truncated_normal_sample(15.0, 3.0, 10.0, 25.0)
│   ├─ Mouse duration: truncated_normal_sample(0.3, 0.1, 0.2, 0.6)
│   ├─ Misclick chance: 10% (experienced profile)
│   └─ Camera check: random.random() < 0.05
│   
├─ Human behavior patterns:
│   ├─ Occasional hesitation before banking
│   ├─ Random skill tab checks (3% chance)
│   ├─ Click variation within fishing spot bounds
│   └─ Variable banking paths
│   
└─ ✅ Checklist: 8/8 items passed
    ✅ All delays use truncated_normal_sample
    ✅ Mouse movements varied
    ✅ Misclick simulation (10%)
    ✅ Hesitation implemented
    ✅ Action sequences vary
    ✅ No hardcoded coordinates
    ✅ BehaviorManager integrated
    ✅ State machine handles all cases

🔍 Visual-Debugger: "Extracting templates and testing confidence..."
├─ Capturing game state...
│   python scripts/recorder.py --window "RuneLite" --duration 10
│   
├─ Template 1: fishing_spot_shrimp.png
│   ├─ Extracted from frame 003 (coords: 450,320,80,80)
│   ├─ Testing confidence...
│   │   python scripts/recorder.py --test-template \
│   │       src/images/bot/fishing/fishing_spot_shrimp.png \
│   │       --window "RuneLite"
│   ├─ Result: confidence 0.84 ✅
│   └─ Threshold set: 0.80
│   
├─ Template 2: inventory_shrimp.png
│   ├─ Confidence: 0.89 ✅
│   └─ Threshold: 0.85
│   
├─ Template 3: bank_booth.png
│   ├─ Confidence: 0.82 ✅
│   └─ Threshold: 0.78
│   
├─ Template 4: fishing_animation.png
│   ├─ Confidence: 0.76 (acceptable)
│   └─ Threshold: 0.70
│   
└─ ✅ Checklist: 4/4 items passed
    ✅ All thresholds 0.70-0.89 (not >0.95)
    ✅ Templates allow variation
    ✅ Search regions optimized (inventory area only for shrimp)
    ✅ All templates tested in-game

🧪 Test-Engineer: "Creating comprehensive test suite..."
├─ File: tests/unit/model/osrs/test_fishing.py
│   
├─ Test fixtures created:
│   ├─ tests/fixtures/fishing/spot_visible.png
│   ├─ tests/fixtures/fishing/inventory_empty.png
│   ├─ tests/fixtures/fishing/inventory_full.png
│   └─ tests/fixtures/fishing/bank_open.png
│   
├─ Unit tests (12 tests):
│   ├─ test_initialization() ✅
│   ├─ test_detect_fishing_spot_positive() ✅
│   ├─ test_detect_fishing_spot_negative() ✅
│   ├─ test_inventory_full_detection() ✅
│   ├─ test_state_transitions() ✅
│   └─ ... (7 more)
│   
├─ Randomization validation tests:
│   ├─ test_fishing_delays_are_randomized()
│   │   └─ Validated: 100 delays, 62 unique values ✅
│   ├─ test_no_predictable_patterns()
│   │   └─ No repeating sequences detected ✅
│   ├─ test_statistical_distribution()
│   │   └─ Mean: 14.8s (expected 15s) ✅
│   └─ test_mouse_duration_varies()
│       └─ Range: 0.21-0.58s (expected 0.2-0.6s) ✅
│   
├─ Test results: 12/12 passed
│   
└─ ✅ Checklist: 6/6 items passed
    ✅ Tests validate timing variation
    ✅ Tests check for patterns (none found)
    ✅ Statistical tests for randomness ✅
    ✅ No deterministic expectations
    ✅ Visual fixtures created
    ✅ Coverage: 87%
```

---

## Stage 4: REVIEW (38 seconds, parallel)

```
🔴 Code-Reviewer: "Running automated behavior validation scan..."
├─ Files scanned: 3
│   ├─ src/model/osrs/fishing.py
│   ├─ tests/unit/model/osrs/test_fishing.py
│   └─ src/images/bot/fishing/*.png (templates)
│   
├─ Automated rules applied:
│   ├─ Rule 1: Fixed time.sleep() → 0 violations ✅
│   ├─ Rule 2: Hardcoded coordinates → 0 violations ✅
│   ├─ Rule 3: Fixed mouse duration → 0 violations ✅
│   ├─ Rule 4: Missing imports → 0 violations ✅
│   ├─ Rule 5: Perfect confidence → 0 violations ✅
│   ├─ Rule 6: Modulo patterns → 0 violations ✅
│   ├─ Rule 7: Narrow ranges → 0 violations ✅
│   └─ Rule 8: Missing error sim → 0 violations ✅
│   
├─ Scan results:
│   ├─ Critical violations: 0 ✅
│   ├─ High violations: 0 ✅
│   └─ Medium violations: 1 ⚠️
│   
├─ MEDIUM VIOLATION (Confidence: 70):
│   File: src/model/osrs/fishing.py
│   Line: 87
│   Rule: Consider adding more camera variation
│   Message: "Camera check at 5% - consider 8-12% for longer sessions"
│   Severity: MEDIUM (suggestion, not blocking)
│   
└─ ✅ Status: APPROVED (1 minor suggestion noted)

👔 Senior-Developer: "Performing final quality validation..."
├─ Code quality review:
│   ├─ Separation of concerns: ✅
│   │   └─ Detection, logic, behavior well separated
│   ├─ Readability: ✅
│   │   └─ Clear method names, good comments
│   ├─ Maintainability: ✅
│   │   └─ State machine easy to extend
│   └─ No unnecessary complexity: ✅
│   
├─ Test coverage: 87% ✅
│   └─ All critical paths covered
│   
├─ Human-behavior validation:
│   ├─ ✅ Bot-Developer checklist: 8/8 passed
│   ├─ ✅ Visual-Debugger checklist: 4/4 passed
│   ├─ ✅ Test-Engineer checklist: 6/6 passed
│   ├─ ✅ Code-Reviewer scan: 0 critical violations
│   └─ Final validation questions:
│       1. Would observer see robotic patterns? → NO ✅
│       2. Could timing be predicted? → NO ✅
│       3. Mouse movements natural? → YES ✅
│       4. Errors/variations like human? → YES ✅
│       5. Distinguishable from human? → NO ✅
│   
└─ ✅ Status: APPROVED
    └─ Note: Consider Code-Reviewer's camera suggestion (optional)
```

---

## Stage 5: FINAL SYNTHESIS (12 seconds)

```
👔 Senior-Developer: "✅ Multi-Agent Fishing Bot Creation Complete!

═══════════════════════════════════════════════════════════
CONSULTATION SUMMARY
═══════════════════════════════════════════════════════════

Duration: 2 minutes 38 seconds
Agents Consulted: 7/7
Overall Status: ✅ APPROVED

───────────────────────────────────────────────────────────
WHAT WAS BUILT
───────────────────────────────────────────────────────────

📁 Implementation:
   ├─ src/model/osrs/fishing.py (245 lines)
   ├─ tests/unit/model/osrs/test_fishing.py (180 lines)
   ├─ src/images/bot/fishing/fishing_spot_shrimp.png
   ├─ src/images/bot/fishing/inventory_shrimp.png
   ├─ src/images/bot/fishing/bank_booth.png
   └─ src/images/bot/fishing/fishing_animation.png

🎯 Architecture:
   5-state machine: CheckInventory → FindSpot → Fish → WalkToBank → Bank
   
📊 Tests: 12 tests created, all passing
   Coverage: 87% (excellent)

───────────────────────────────────────────────────────────
AGENT CONTRIBUTIONS
───────────────────────────────────────────────────────────

🔍 Code-Explorer:
   └─ Identified woodcutter.py banking pattern as template
   └─ Found existing randomization utilities
   
🏗️ Code-Architect:
   └─ Designed 5-state machine with clear transitions
   └─ Planned 4 template detections
   
🤖 Bot-Developer:
   └─ Implemented full bot with BehaviorManager integration
   └─ Applied truncated_normal_sample to all delays
   └─ Added misclick (10%) and hesitation patterns
   
🔍 Visual-Debugger:
   └─ Extracted 4 templates with confidence 0.76-0.89
   └─ Tuned thresholds for realistic detection
   
🧪 Test-Engineer:
   └─ Created 12 unit tests + 4 randomization tests
   └─ Statistical validation: distribution confirmed
   
🔴 Code-Reviewer:
   └─ Automated scan: 0 critical violations
   └─ 1 minor suggestion (camera frequency)
   
👔 Senior-Developer:
   └─ Validated all checklists and code quality
   └─ Final human-behavior approval

───────────────────────────────────────────────────────────
HUMAN-BEHAVIOR VALIDATION
───────────────────────────────────────────────────────────

✅ Bot-Developer: 8/8 checklist items PASSED
✅ Visual-Debugger: 4/4 checklist items PASSED
✅ Test-Engineer: 6/6 checklist items PASSED
✅ Code-Reviewer: Automated scan PASSED
✅ Senior-Developer: Final validation PASSED

🎯 Overall: ALL HUMAN-BEHAVIOR REQUIREMENTS MET

───────────────────────────────────────────────────────────
WARNINGS & SUGGESTIONS
───────────────────────────────────────────────────────────

⚠️  Medium (Optional):
    Consider increasing camera check frequency from 5% to 8-12%
    for sessions longer than 1 hour. Current frequency is fine
    for shorter sessions.

───────────────────────────────────────────────────────────
NEXT STEPS
───────────────────────────────────────────────────────────

1. Review the generated code:
   - src/model/osrs/fishing.py
   - Check state machine logic
   - Verify behavior profile settings

2. Run the test suite:
   pytest tests/unit/model/osrs/test_fishing.py -v

3. Manual testing in game:
   - Stand at Draynor fishing spot
   - Run bot with Experienced profile
   - Observe 5-10 iterations for natural behavior
   - Check logs for any errors

4. Optional adjustments:
   - Tweak camera frequency if desired
   - Adjust misclick rate via behavior profile
   - Fine-tune delay ranges if needed

5. Production testing:
   - Test with full 1000 shrimp goal
   - Monitor for detection patterns
   - Verify banking works smoothly

───────────────────────────────────────────────────────────

Ready to proceed with testing? Let me know if you need any
adjustments or have questions about the implementation!
"
```

---

## Summary

**Total Duration**: 2 minutes 38 seconds  
**Agents**: 7 consulted in hybrid coordination  
**Result**: Fully functional fishing bot with comprehensive tests  
**Human-Behavior**: ✅ Validated at every stage  
**Status**: Ready for manual testing  

**Key Achievements**:
- Zero critical violations
- 87% test coverage
- All delays randomized
- Realistic confidence thresholds
- Human-like behavior patterns throughout
