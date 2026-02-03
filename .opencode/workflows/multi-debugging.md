# Workflow: Multi-Agent Debugging

## Overview
Targeted multi-agent workflow for diagnosing and fixing bugs, especially detection/vision issues.

**Duration**: 1-2 minutes  
**Agents Involved**: 3-5 (focused subset)  
**Coordination**: Sequential with targeted parallel

---

## When to Use

- Template detection failing
- Intermittent detection issues
- Bot getting stuck in state
- Performance problems
- Logic errors

---

## Workflow (Targeted)

### Stage 1: DIAGNOSIS (30-45s, parallel)

**🔍 Code-Explorer**:
- Analyze problematic code
- Find related implementations
- **Output**: Code analysis

**🔍 Visual-Debugger**:
- Capture current game state
- Test existing templates
- Compare expected vs actual
- **Output**: Diagnostic report

---

### Stage 2: ROOT CAUSE (15-20s)

**👔 Senior-Developer**:
- Synthesize findings
- Identify root cause
- Plan fix
- **Output**: Fix plan

---

### Stage 3: FIX (30-45s, parallel)

**🤖 Bot-Developer** OR **🔍 Visual-Debugger**:
- Implement fix based on issue type
- **Checklist**: Relevant items

**🧪 Test-Engineer**:
- Create regression test
- Ensure fix doesn't break others
- **Checklist**: Test items

---

### Stage 4: VALIDATION (20-30s)

**🔴 Code-Reviewer**:
- Quick scan of changes
- **Output**: Violation check

**👔 Senior-Developer**:
- Verify fix resolves issue
- **Output**: Approval

---

## Example: Tree Detection Failing

```
/multi The tree detection in woodcutter is failing intermittently
```

**Flow**:
1. Explorer: Analyzes tree detection code
2. Visual-Debug: Captures game, tests template
   - Finding: Confidence drops to 0.65 with lighting changes
3. Senior-Dev: "Root cause: Template too specific for one lighting"
4. Visual-Debug: Extracts new template, lowers threshold to 0.75
5. Test-Engineer: Creates regression test with captured state
6. Reviewer: 0 violations
7. Senior-Dev: "Fix verified, confidence now stable 0.78-0.82" ✅

**Duration**: ~1m 15s

---

## Common Issue Patterns

| Issue | Lead Agent | Supporting |
|-------|-----------|------------|
| Detection failing | Visual-Debugger | Code-Explorer, Test-Engineer |
| Logic error | Bot-Developer | Code-Explorer, Test-Engineer |
| Performance slow | Code-Explorer | Bot-Developer, Visual-Debugger |
| State machine stuck | Bot-Developer | Code-Explorer |

---

## Success Criteria

- ✅ Root cause identified
- ✅ Fix implemented
- ✅ Regression test added
- ✅ Issue resolved

---

## References

- **Visual Debugging**: `.claude/agents/visual-debugger.md`
- **Checklist**: `.claude/skills/human-behavior-checklist.md`
