---
name: large_task_complete
description: Complete and exit Large Task Mode
---

You are completing Large Task Mode for the current project.

## Completion Steps

1. **Check Current State**
   - Read `.claude/LARGE_TASK_MODE.json` for current status
   - If not active, inform user mode is not currently active

2. **Run Final Validation**
   - Use validator-master agent to run comprehensive validation
   - Check test coverage, security, implementation completeness
   - Run retrospective validator to calculate success metrics

3. **Handle Validation Results**

   ### If Validation Passes:
   - Update `.claude/LARGE_TASK_MODE.json`:
     - Set status to "completed"
     - Add completion timestamp
     - Record final metrics
   - Generate completion report in `.claude/FINAL_REPORT.md` with:
     - Task summary
     - Files created/modified
     - Test coverage achieved
     - Validation results
   - Run completion-auditor agent for detailed retrospective analysis
   - Review `.claude/RETROSPECTIVE_SUMMARY.md` for improvement recommendations
   - Archive validators to `.claude/archive/` directory
   - Clear active work files

   ### If Validation Fails:
   - Show user the specific failures
   - Ask: "Validation failed. Options:
     1. Continue working (keeps mode active)
     2. Force complete (deactivates despite failures)
     3. Run recovery (automatic fix attempt)"
   - Handle based on user choice

4. **Cleanup**
   - Remove `.claude/ACTIVE_WORK.json`
   - Clear session-specific files
   - Keep PROJECT_CONTEXT.md and FINAL_REPORT.md for reference

5. **Inform User**
   - Provide summary of what was accomplished
   - Note that infrastructure remains for future use
   - Mention automatic activation will still work for complex tasks