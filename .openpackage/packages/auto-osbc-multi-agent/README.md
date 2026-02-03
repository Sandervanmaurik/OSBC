# Auto-OSBC Multi-Agent System

Comprehensive multi-agent collaboration system for Auto-OSBC bot development with mandatory human-behavior validation to create undetectable game automation bots.

## Overview

This package provides a **7-agent collaborative system** that works together to ensure:
1. **Human-like behavior** is the top priority (validated at every stage)
2. **Code quality** remains high (separation of concerns, readability)
3. **Comprehensive validation** across all quality dimensions

## Quick Start

### Activate Multi-Agent Collaboration

```
/multi <your request>
```

**Examples**:
```
/multi Create a fishing bot that fishes shrimp and banks when full
/multi Add banking support to the mining bot  
/multi Debug the tree detection failing in woodcutter
```

### What Happens

1. **Stage 1: EXPLORATION** (30-45s, parallel)
   - 🔍 Code-Explorer finds existing patterns
   - 🏗️ Code-Architect designs architecture

2. **Stage 2: SYNTHESIS** (15-30s, sequential)
   - 👔 Senior-Developer asks targeted questions

3. **Stage 3: DEVELOPMENT** (60-90s, parallel)
   - 🤖 Bot-Developer implements with randomization
   - 🔍 Visual-Debugger extracts templates
   - 🧪 Test-Engineer creates test suite

4. **Stage 4: REVIEW** (30-45s, parallel)
   - 🔴 Code-Reviewer runs automated violation scan
   - 👔 Senior-Developer performs quality validation

5. **Stage 5: SYNTHESIS** (10-15s, sequential)
   - 👔 Senior-Developer provides complete report

**Total Duration**: 2-4 minutes  
**Human-Behavior**: Validated at EVERY stage

## The 7 Agents

| Agent | Role | When to Use |
|-------|------|-------------|
| 🤖 **Bot-Developer** | Creates bots with human-like behavior | New bots, features, logic |
| 🏗️ **Code-Architect** | Designs feature architectures | Architecture planning |
| 🔍 **Code-Explorer** | Analyzes existing codebase | Find patterns, understand code |
| 🔴 **Code-Reviewer** | Reviews for bugs & violations | Automated validation |
| 👔 **Senior-Developer** | Ensures quality & behavior | Final validation, synthesis |
| 🔍 **Visual-Debugger** | Fixes detection issues | Template problems, CV bugs |
| 🧪 **Test-Engineer** | Creates comprehensive tests | TDD, validation, coverage |

## Human-Behavior Validation

### Mandatory Requirements

ALL bot code must implement:
- ✅ Randomized delays (no fixed `time.sleep()`)
- ✅ Variable mouse movements
- ✅ Click position variation
- ✅ Action sequence shuffling
- ✅ Misclick simulation (8-15%)
- ✅ Hesitation patterns
- ✅ Distraction events

### Blocking Violations

These will HALT the workflow:
- ❌ `time.sleep(2.5)` → Use `truncated_normal_sample(2.5, 0.5, 1.5, 4.0)`
- ❌ `mouse.click((500, 300))` → Use template detection
- ❌ `if iteration % 10 == 0:` → Use `if random.random() < 0.1:`
- ❌ `conf=0.99` → Use 0.75-0.90 (realistic thresholds)

### Automated Validation

Code-Reviewer agent automatically scans for:
- Fixed delays (regex: `time\.sleep\(\d+\.?\d*\)`)
- Hardcoded coordinates
- Missing randomization imports
- Perfect confidence thresholds
- Modulo patterns
- Narrow variation ranges

**Confidence scoring**: Only reports violations ≥80 confidence

## Package Structure

```
auto-osbc-multi-agent/
├── openpackage.yml          # Package manifest
├── README.md                # This file
│
├── agents/                  # 7 specialized agents
│   ├── bot-developer.md
│   ├── code-architect.md
│   ├── code-explorer.md
│   ├── code-reviewer.md
│   ├── senior-developer.md
│   ├── visual-debugger.md
│   └── test-engineer.md
│
├── commands/                # Slash commands
│   ├── multi-agent.md       # /multi command
│   ├── behavior-validation.md
│   ├── quick-reference.md
│   └── senior-dev-checklist.md
│
├── skills/                  # Reusable knowledge
│   ├── human-behavior.md
│   ├── human-behavior-checklist.md
│   ├── bot-creation.md
│   └── senior-dev-principles.md
│
├── workflows/               # Process templates
│   ├── multi-bot-creation.md
│   ├── multi-feature-addition.md
│   └── multi-debugging.md
│
├── examples/                # Demonstrations
│   ├── multi-agent-bot-creation.md
│   └── multi-agent-debugging.md
│
└── root/                    # Project-specific docs
    ├── AGENTS.md
    └── CLAUDE.md
```

## Features

### Multi-Agent Coordination
7 specialized agents working in **hybrid mode** (parallel + sequential):
- **Parallel**: Stages 1, 3, 4 (exploration, development, review)
- **Sequential**: Stages 2, 5 (synthesis with user interaction)

### Human-Behavior Validation
Mandatory checklists for each agent:
- **Bot-Developer**: 8 items (randomization, patterns, behavior)
- **Code-Architect**: 4 items (design, variation support)
- **Code-Explorer**: 4 items (pattern detection, risk assessment)
- **Code-Reviewer**: 8 automated rules (violations, anti-patterns)
- **Visual-Debugger**: 4 items (thresholds, templates)
- **Test-Engineer**: 6 items (randomization tests, coverage)
- **Senior-Developer**: 6 items (cross-agent validation, final approval)

### Interactive Dialogue
Concise agent communication with emoji identifiers:
```
🔍 Code-Explorer: "Analyzing..."
├─ Found: pattern in file.py
└─ ✅ Checklist: 4/4 passed

🤖 Bot-Developer: "Implementing..."
└─ ✅ Checklist: 8/8 passed
```

### Automated Code Review
Regex-based violation detection with confidence scoring:
- **100 confidence**: Fixed delays → CRITICAL
- **95 confidence**: Hardcoded coords → CRITICAL
- **90 confidence**: Modulo patterns → HIGH
- **85 confidence**: Missing imports → HIGH
- **80 confidence**: Perfect thresholds → MEDIUM

## Workflows

### Bot Creation
Complete workflow for creating new bots from scratch with all 7 agents.

**See**: `workflows/multi-bot-creation.md`

### Feature Addition
Faster workflow for adding features to existing bots (typically 5-6 agents).

**See**: `workflows/multi-feature-addition.md`

### Debugging
Targeted workflow for diagnosing and fixing bugs (3-5 agents).

**See**: `workflows/multi-debugging.md`

## Examples

### Fishing Bot Creation
Complete example showing all 5 stages with agent dialogue and checklist validation.

**See**: `examples/multi-agent-bot-creation.md`

### Tree Detection Debugging
Debugging example showing root cause analysis and fix implementation.

**See**: `examples/multi-agent-debugging.md`

## When to Use `/multi`

### Use For:
- ✅ Creating new bots from scratch
- ✅ Adding major features (banking, combat, etc.)
- ✅ Complex refactoring requiring multiple perspectives
- ✅ Debugging issues spanning multiple domains

### Don't Use For:
- ❌ Simple questions or clarifications
- ❌ Single-file edits
- ❌ Documentation-only changes
- ❌ Quick template tests

## Integration

This package integrates with:
- **Auto-OSBC**: Game automation framework
- **Behavior System**: `src/behavior/` - Modular human-like behavior
- **Random Utilities**: `src/utilities/random_util.py` - Randomization functions
- **Testing Framework**: `pytest` - Comprehensive test suite

## Success Criteria

A `/multi` consultation is successful when:
- ✅ All requested agents participated
- ✅ Each agent completed their checklist
- ✅ All blocking violations resolved
- ✅ Senior-Developer provided final approval
- ✅ User questions answered (if any)
- ✅ Implementation ready or clear next steps provided

## Version

**Current Version**: 1.0.0  
**Release Date**: 2025-02-02

## License

MIT

## Contributing

Follow the human-behavior validation requirements and ensure all checklists pass before submitting code.

## Support

See project documentation:
- **Main**: `root/AGENTS.md`
- **Roadmap**: `root/CLAUDE.md`
- **Quick Start**: `commands/multi-agent.md`
