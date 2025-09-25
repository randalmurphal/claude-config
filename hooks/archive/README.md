# Archived Hooks

This directory contains hooks that have been temporarily disabled while we restructure the PRISM MCP integration and orchestration systems.

## Archive Structure

### `/prism/` - PRISM MCP Integration Hooks
Contains all hooks related to the PRISM memory and pattern detection system:
- **Core PRISM infrastructure**: Connection clients, HTTP startup scripts
- **Memory management**: Semantic analysis, pattern detection, context providers
- **Response monitoring**: Real-time capture and analysis of Claude responses
- **User preference tracking**: Preference management and enforcement
- **Knowledge validation**: Universal learner and validation systems

**Why archived**: The PRISM MCP system is being restructured. These hooks were causing unintended triggering and need to be reconfigured before reactivation.

### `/orchestration/` - Orchestration System Hooks
Contains hooks for the multi-agent orchestration system:
- **Chamber management**: Git worktree chamber creation and cleanup
- **Orchestration control**: Dashboard, progress tracking, auto-detection
- **Task coordination**: Learner systems and bash guardians
- **Coverage enforcement**: Test coverage requirements

**Why archived**: The orchestration system is being redesigned to work with the new MCP server architecture.

## Currently Active Hooks

Only the following utility hook remains active:
- `auto_formatter.py` - Provides automatic code formatting for Python, JavaScript, and Go files

## Reactivation Plan

To reactivate specific hooks:
1. Move the desired hook file back to the parent `hooks/` directory
2. Ensure any dependencies are satisfied
3. Test the hook in isolation before full deployment
4. Update this README to reflect the change

## Note on Hook Caching

If you see hooks still triggering after archiving:
1. Restart your Claude Code session
2. Check for any running Python processes: `ps aux | grep python.*hook`
3. Clear any cache directories if they exist

## Archive Date
**Archived**: September 23, 2025
**Reason**: System restructuring and PRISM MCP integration issues
**Archived by**: User request to clean up and restart hook configuration