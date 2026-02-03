# /multi - Multi-Agent Collaboration Command

## Purpose
Activate comprehensive multi-agent consultation for complex bot development tasks. This command invokes the **Multi-Agent Orchestrator** to coordinate all 7 specialized agents, with **Bot-Developer as implementation lead**, ensuring human-like behavior is prioritized while maintaining code quality.

## Command Syntax
```
/multi <user request>
```

## Architecture

```
User → Multi-Agent Orchestrator (Workflow Manager)
           ↓
    Bot-Developer (Implementation Lead)
           ├─ Code-Explorer (Pattern Finder)
           ├─ Code-Architect (Design Specialist)
           ├─ Visual-Debugger (Template Specialist)
           ├─ Test-Engineer (Testing Specialist)
           ├─ Code-Reviewer (Violation Scanner)
           └─ Senior-Developer (Quality Gatekeeper)
```

**Orchestrator:** Manages 5-stage workflow, agent coordination  
**Bot-Developer:** Leads technical implementation, makes decisions  
**Other Agents:** Provide specialized expertise

## When to Use
Use `/multi` for:
- ✅ Creating new bots from scratch
- ✅ Adding major features to existing bots
- ✅ Complex refactoring requiring multiple perspectives
- ✅ Debugging issues that span multiple domains (detection + logic + behavior)
- ✅ When you want comprehensive validation across all quality dimensions

**Don't use** `/multi` for:
- ❌ Simple questions or clarifications
- ❌ Single-file edits
- ❌ Documentation-only changes
- ❌ Quick template tests

---

## Workflow Stages

The `/multi` command executes in 5 coordinated stages managed by **Multi-Agent Orchestrator**, with **Bot-Developer as implementation lead**:

### **Stage 1: EXPLORATION** (Parallel - ~30-45 seconds)

**Orchestrator** launches two agents simultaneously:

**🔍 Code-Explorer**
- Analyzes existing codebase for similar features
- Identifies patterns, abstractions, and conventions
- Maps relevant files and dependencies
- Flags existing human-behavior patterns or violations
- **Output**: Codebase analysis report with file:line references

**🏗️ Code-Architect**
- Reviews architecture requirements
- Designs component structure based on existing patterns
- Plans state machines and data flows
- Ensures design supports human-behavior variation
- **Output**: Architecture blueprint with component responsibilities

**Orchestrator** passes findings to **Bot-Developer** for review.

---

### **Stage 2: SYNTHESIS + USER QUESTIONS** (~15-30 seconds)

**🤖 Bot-Developer** (Implementation Lead)
- Receives Code-Explorer + Code-Architect findings
- Synthesizes into cohesive implementation plan
- Identifies gaps or ambiguities
- Formulates targeted questions for user
- Makes technical decisions
- **Output**: Implementation plan + user questions (if any)

**Orchestrator** presents questions to user, collects answers, passes back to Bot-Developer.

**User Interaction**: If questions raised, workflow pauses for user input. Bot-Developer incorporates answers and proceeds.

---

### **Stage 3: DEVELOPMENT** (Parallel - ~60-90 seconds)

**Bot-Developer** leads implementation while **Orchestrator** coordinates specialists:

**🤖 Bot-Developer** (Implementation Lead)
- Implements bot logic following architecture blueprint
- Integrates human-behavior patterns (timing, variation, errors)
- Uses existing utilities and patterns identified by Code-Explorer
- Coordinates with Visual-Debugger (provides template requirements)
- Coordinates with Test-Engineer (provides code for testing)
- **Output**: Bot implementation code
- **Checklist**: Bot-Developer human-behavior validation

**🔍 Visual-Debugger**
- Extracts/validates detection templates per Bot-Developer requirements
- Tests confidence thresholds for realistic values
- Ensures detection allows for variation (not pixel-perfect)
- **Output**: Templates, confidence thresholds, detection code
- **Checklist**: Visual-Debugger human-behavior validation

**🧪 Test-Engineer**
- Creates comprehensive test suite using Bot-Developer's code
- Writes randomization validation tests
- Ensures tests don't expect deterministic behavior
- **Output**: Test suite with statistical validation
- **Checklist**: Test-Engineer human-behavior validation
- **Output**: Test suite with statistical validation
- **Checklist**: Test-Engineer human-behavior validation

**Human-Behavior Checkpoint**: All three agents self-validate against their checklists before proceeding.

---

### **Stage 4: REVIEW** (Parallel - ~30-45 seconds)

**Orchestrator** launches reviewers while **Bot-Developer** stands by for fixes:

**🔴 Code-Reviewer**
- Automated scan for human-behavior violations
- Detects fixed delays, hardcoded coordinates, perfect patterns
- Scores violations by confidence (only report ≥80)
- Validates project guidelines compliance
- **Input**: Bot-Developer's code from Stage 3
- **Output**: Violation report with confidence scores

**👔 Senior-Developer**
- Reviews code quality and separation of concerns
- Validates readability and maintainability
- Checks test coverage and quality
- Performs human-behavior final validation
- **Input**: All code + test results
- **Output**: Quality assessment + approval/revision request

**If blocking violations found:**
- Orchestrator passes to Bot-Developer
- Bot-Developer fixes immediately
- Code-Reviewer re-scans
- Process repeats until clean

**Human-Behavior Checkpoint**: Both reviewers must approve before proceeding. Blocking violations halt the workflow.

---

### **Stage 5: FINAL SYNTHESIS** (~10-15 seconds)

**🎭 Multi-Agent Orchestrator**
- Aggregates all agent outputs
- Validates all checklists completed
- Creates comprehensive report:
  - What was accomplished
  - All agent contributions
  - Human-behavior validation status (all checklists)
  - Files created/modified
  - Any warnings or suggestions
  - Recommended next steps
- **Output**: Complete multi-agent consultation report

---

## Agent Responsibilities Matrix

| Agent | Stage | Mode | Responsibilities | Human-Behavior Checklist |
|-------|-------|------|------------------|-------------------------|
| **Multi-Agent Orchestrator** | ALL | Coordinator | Manage workflow, delegate tasks, aggregate outputs | Overall validation |
| **Code-Explorer** | 1 | Parallel | Find patterns, flag violations | Pattern detection items |
| **Code-Architect** | 1 | Parallel | Design architecture | Architecture design items |
| **Bot-Developer** | 2,3 | Lead | Synthesize, implement, coordinate | Bot implementation items |
| **Visual-Debugger** | 3 | Parallel | Extract templates, tune detection | Detection items |
| **Test-Engineer** | 3 | Parallel | Write tests, validate randomness | Testing items |
| **Code-Reviewer** | 4 | Parallel | Automated violation detection | Automated rules |
| **Senior-Developer** | 4 | Parallel | Quality review, final approval | All checklist review |
| **Code-Reviewer** | 4 | Parallel | Automated violation detection | Automated rules |
| **Senior-Developer** | 4 | Parallel | Quality review, final validation | All checklist review |
| **Senior-Developer** | 5 | Sequential | Final synthesis | Overall approval |

---

## Human-Behavior Validation Integration

### Mandatory Checkpoints

Every stage includes human-behavior validation:

1. **Stage 1**: Agents check that patterns/design support variation
2. **Stage 2**: Senior-Dev validates consolidated plan
3. **Stage 3**: Each agent self-validates against their checklist
4. **Stage 4**: Code-Reviewer runs automated detection + Senior-Dev final validation
5. **Stage 5**: All checklists reviewed and approved

### Enforcement Rules

**Blocking Violations** (HALT workflow):
- Fixed `time.sleep()` values detected
- Hardcoded coordinates found
- No randomization imports
- Confidence thresholds > 0.95
- Deterministic loops without variation

**Warning Violations** (Note but proceed):
- Limited variation ranges
- Predictable modulo patterns
- Missing misclick simulation
- Insufficient action sequence variation

### Validation Report Format

Each agent reports:
```markdown
## [Agent Name] Validation

✅ Checklist Item 1 - PASSED
✅ Checklist Item 2 - PASSED
⚠️ Checklist Item 3 - WARNING: Details
❌ Checklist Item 4 - FAILED: Details + Fix

**Status**: [APPROVED / NEEDS REVISION / BLOCKED]
```

---

## Dialogue Format (Interactive but Concise)

Agents communicate using emoji identifiers and concise messages:

```
🔍 Code-Explorer: "Analyzing fishing bots for patterns..."
├─ Found: src/model/osrs/fishing.py uses inventory detection
├─ Pattern: Banking in woodcutter.py
└─ ✅ Behavior: Good randomization in existing code

🏗️ Code-Architect: "Designing architecture..."
├─ Extends: RuneLiteBot
├─ States: Fish→Full→Bank→Repeat
└─ ✅ Behavior: State transitions support variation

---

👔 Senior-Developer: "Questions before proceeding:
1. Stop condition: time-based or fish count?
2. What if fishing spot moves?"

[User answers]

---

🤖 Bot-Developer: "Implementing OSRSFishing..."
├─ State machine: 4 states with transitions
├─ Using truncated_normal_sample for all delays
└─ ✅ Checklist: 8/8 items passed

🔍 Visual-Debugger: "Extracting templates..."
├─ fishing_spot.png confidence: 0.82 ✅
├─ inventory_fish.png confidence: 0.85 ✅
└─ ✅ Checklist: 4/4 items passed

🧪 Test-Engineer: "Creating tests..."
├─ Unit tests: 12 tests (detection, state logic)
├─ Randomization: Statistical validation ✅
└─ ✅ Checklist: 6/6 items passed

---

🔴 Code-Reviewer: "Reviewing implementation..."
├─ Automated scan: 0 blocking violations ✅
├─ Warnings: 1 (consider camera movement)
└─ ✅ Checklist: Automated rules passed

👔 Senior-Developer: "Final validation..."
├─ Code quality: Clean separation of concerns ✅
├─ Tests: Good coverage (83%) ✅
├─ Human-behavior: ALL CHECKLISTS PASSED ✅
└─ **Status: APPROVED**

---

👔 Senior-Developer: "✅ Multi-agent complete!

**Summary**:
- 7 agents consulted (2m 15s)
- Architecture designed & implemented
- 12 tests created, all passing
- Human-behavior: VALIDATED
- 1 minor suggestion noted

Ready to proceed with implementation?"
```

---

## Timing Expectations

| Stage | Duration | Parallelism |
|-------|----------|-------------|
| Stage 1: Exploration | 30-45s | 2 agents parallel |
| Stage 2: Synthesis | 15-30s | 1 agent sequential |
| Stage 3: Development | 60-90s | 3 agents parallel |
| Stage 4: Review | 30-45s | 2 agents parallel |
| Stage 5: Final | 10-15s | 1 agent sequential |
| **Total** | **2-4 minutes** | Hybrid coordination |

*Times are estimates. Complex tasks may take longer.*

---

## Example Usage

### Creating a New Bot
```
/multi Create a cooking bot that cooks shrimp at a range and banks when inventory is full
```

**Expected Flow**:
1. Code-Explorer finds similar bots (fishing, woodcutter)
2. Code-Architect designs state machine
3. Senior-Dev asks about stop conditions
4. Bot-Developer implements with human-behavior
5. Visual-Debugger extracts range/shrimp templates
6. Test-Engineer creates test suite
7. Code-Reviewer validates (no violations)
8. Senior-Dev approves

### Adding a Feature
```
/multi Add anti-PK detection to the mining bot - if player appears nearby, activate evasion behavior
```

**Expected Flow**:
1. Code-Explorer finds player detection in existing code
2. Code-Architect designs evasion state machine
3. Bot-Developer implements detection + evasion
4. Visual-Debugger creates player templates
5. Test-Engineer adds evasion tests
6. Code-Reviewer checks for detection risks
7. Senior-Dev validates behavior appears human

### Debugging
```
/multi The tree detection in woodcutter is failing intermittently
```

**Expected Flow**:
1. Code-Explorer analyzes woodcutter detection code
2. Visual-Debugger captures current game state
3. Visual-Debugger tests template matching
4. Visual-Debugger extracts new template if needed
5. Test-Engineer creates regression test
6. Code-Reviewer validates fix
7. Senior-Dev confirms resolution

---

## Customization Options

### Subset Activation

If you only need specific agents, specify in the request:

```
/multi [explorer, architect] How does the banking system work in existing bots?
```

Only Code-Explorer and Code-Architect will activate.

### Skip User Questions

If you want agents to make decisions without asking:

```
/multi --no-questions Create a firemaking bot
```

Agents will make reasonable assumptions and proceed.

### Verbose Output

For detailed agent reasoning:

```
/multi --verbose Add prayer flicking to combat bot
```

Agents provide extended explanations of their decisions.

---

## Success Criteria

A `/multi` consultation is successful when:

- ✅ All requested agents participated
- ✅ Each agent completed their checklist
- ✅ All blocking violations resolved
- ✅ Senior-Developer provided final approval
- ✅ User questions answered (if any)
- ✅ Implementation ready or clear next steps provided

---

## Troubleshooting

### "Too many violations detected"
- Code-Reviewer found blocking issues
- Fix violations before proceeding
- Re-run `/multi` after fixes

### "Agents asking too many questions"
- Use `--no-questions` flag
- Provide more context in initial request
- Answer questions to allow workflow to continue

### "Workflow taking too long"
- Complex tasks naturally take longer
- Consider breaking into smaller `/multi` requests
- Use subset activation for targeted consultation

---

## References

- **Human-Behavior Checklist**: `.claude/skills/human-behavior-checklist.md`
- **Individual Agent Docs**: `.claude/agents/*.md`
- **Workflow Examples**: `.claude/examples/multi-agent-*.md`
- **Behavior System**: `BEHAVIOR_SYSTEM_COMPLETE.md`

---

## Quick Reference

**Activate multi-agent**: `/multi <request>`  
**Subset only**: `/multi [agent1, agent2] <request>`  
**Skip questions**: `/multi --no-questions <request>`  
**Verbose**: `/multi --verbose <request>`  

**Total agents**: 7 (explorer, architect, bot-dev, visual-debug, test-eng, reviewer, senior-dev)  
**Typical duration**: 2-4 minutes  
**Coordination**: Hybrid (parallel + sequential)  
**Priority**: Human-like behavior (mandatory checklists)
