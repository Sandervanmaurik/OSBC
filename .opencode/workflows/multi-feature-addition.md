# Workflow: Multi-Agent Feature Addition

## Overview
Workflow for adding features to existing bots using `/multi`. Faster than full bot creation as foundation already exists.

**Duration**: 1-2 minutes  
**Agents Involved**: Subset of 7 (typically 5-6)  
**Coordination**: Hybrid

---

## When to Use

- Adding banking to existing bot
- Implementing special detection (player detection, danger awareness)
- Adding new states to state machine
- Integrating behavior system into legacy bot

---

## Abbreviated Workflow

### Stage 1: EXPLORATION (20-30s, parallel)

**🔍 Code-Explorer**:
- Analyze existing bot file
- Find similar feature implementations
- Identify integration points
- **Output**: Integration analysis

**🏗️ Code-Architect**:
- Design feature architecture
- Plan integration with existing code
- Ensure minimal changes principle
- **Output**: Feature design

---

### Stage 2: SYNTHESIS (10-15s)

**👔 Senior-Developer**:
- Questions about feature behavior
- Confirm integration approach
- **Output**: Plan + questions

---

### Stage 3: DEVELOPMENT (40-60s, parallel)

**🤖 Bot-Developer**:
- Implement feature
- Maintain existing human-behavior
- **Checklist**: Bot-Developer items

**🔍 Visual-Debugger** (if needed):
- Extract new templates
- Test detection
- **Checklist**: Visual items

**🧪 Test-Engineer**:
- Add tests for new feature
- Ensure existing tests still pass
- **Checklist**: Test items

---

### Stage 4: REVIEW (20-30s, parallel)

**🔴 Code-Reviewer**:
- Scan new/modified code
- **Output**: Violation report

**👔 Senior-Developer**:
- Validate integration
- Check for regressions
- **Checklist**: All items

---

### Stage 5: SYNTHESIS (5-10s)

**👔 Senior-Developer**:
- Summary of changes
- Validation status
- **Output**: Report

---

## Example: Adding Banking

```
/multi Add banking support to the mining bot - walk to nearest bank when inventory full
```

**Flow**:
1. Explorer finds banking in woodcutter.py
2. Architect designs BankWalk + BankDeposit states
3. Senior-Dev asks: "Deposit all or keep pickaxe?"
4. Bot-Dev adds states with randomization
5. Visual-Debug extracts bank_booth.png
6. Test-Engineer adds banking tests
7. Reviewer: 0 violations
8. Senior-Dev: Approved ✅

**Duration**: ~1m 30s

---

## Success Criteria

- ✅ Feature integrated cleanly
- ✅ Existing functionality preserved
- ✅ Human-behavior maintained
- ✅ Tests updated

---

## References

- **Full Workflow**: `.claude/workflows/multi-bot-creation.md`
- **Checklist**: `.claude/skills/human-behavior-checklist.md`
