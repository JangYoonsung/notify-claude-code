# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Claude Code Advanced Notification System - A Python-based notification system that monitors Claude Code sessions and delivers detailed notifications about cost, tokens, code changes, and session information.

## Project Structure

```
~/.claude-monitor/
├── scripts/                          # Python modules
│   ├── notification_system.py        # Main notification system
│   ├── session_monitor.py            # Session info extraction from .claude.json
│   ├── notification_templates.py     # Message template generation
│   └── security_validator.py         # Security validation
├── cache/                            # Session snapshots (JSON)
├── logs/                             # Notification and session logs
├── reports/                          # Generated reports
└── notification_config.json          # System configuration
```

## Core Architecture

### 1. SessionMonitor (`session_monitor.py`)
- Reads `~/.claude/projects/{project}/*.jsonl` to parse session data
- Aggregates token usage from each API call in the session
- Calculates cost based on Claude Sonnet 4.5 pricing
- Tracks: cost, tokens (input/output/cache creation/cache read), duration, tool calls
- Generates session snapshots and logs
- Key method: `get_session_info()` returns comprehensive session data

### 2. NotificationTemplates (`notification_templates.py`)
- Uses `NotificationBuilder` to create messages from session data
- Supports multiple notification types: session completion, cost warnings, milestones, code changes
- Formats messages for different verbosity levels (compact/detailed/all)

### 3. NotificationSystem (`notification_system.py`)
- Main orchestrator integrating monitor, templates, and delivery
- `NotificationFormatter`: formats for terminal-notifier or osascript
- `NotificationDelivery`: handles actual notification dispatch
- Supports quiet hours, config management, logging

### 4. Configuration (`notification_config.json`)
- Controls: enabled state, mode (compact/detailed/all), thresholds
- Cost threshold, change threshold, session duration threshold
- Quiet hours support

## Common Commands

### Running Notifications
```bash
# Basic session notification (compact mode)
~/.claude/scripts/notification_system.py

# Detailed session notification
~/.claude/scripts/notification_system.py --mode detailed

# All applicable notifications
~/.claude/scripts/notification_system.py --mode all

# Custom notification
~/.claude/scripts/notification_system.py --custom "Title" "Message"
```

### Configuration Management
```bash
# Check status
~/.claude/scripts/notification_system.py --status

# Enable/disable notifications
~/.claude/scripts/notification_system.py --enable
~/.claude/scripts/notification_system.py --disable

# Change notification mode
~/.claude/scripts/notification_system.py --mode [compact|detailed|all]
```

### Session Monitoring
```bash
# Display current session info
~/.claude/scripts/session_monitor.py

# View notification logs
tail -20 ~/.claude-monitor/logs/notifications.log

# View session logs (current month)
tail -20 ~/.claude-monitor/logs/sessions_$(date +%Y%m).log
```

## Integration Points

### Claude Code Hooks
The system integrates with Claude Code hooks in `~/.claude/settings.json`:

- **Stop Hook**: Triggers on session stop → compact notification
- **SessionEnd Hook**: Triggers on session end → detailed notification
- **Notification Hook**: Triggers on user input wait → custom message
- **SubagentStop Hook**: Triggers on subagent completion → custom message

### Data Sources
- **Primary**: `~/.claude/projects/{project}/*.jsonl` - Session conversation history with API usage data
- **Secondary**: `~/.claude.json` - Claude Code configuration for project detection
- **Output**: Session snapshots in `cache/`, logs in `logs/`

## Key Design Patterns

### Session Hash Calculation
Sessions are uniquely identified by hashing `session_id` + `timestamp`. Snapshots saved as `session_{hash}.json`.

### Notification Levels
- `success`: Completion notifications (Glass sound)
- `info`: Informational (Tink sound)
- `warning`: Cost/change warnings (Basso sound)
- `milestone`: Token milestones (Hero sound)

### Project Detection
`SessionMonitor.get_current_project()` matches current working directory against projects in `.claude.json`, selecting the longest matching path (most specific).

## Configuration Schema

```json
{
  "enabled": bool,                    // Master enable/disable
  "mode": "compact|detailed|all",     // Notification verbosity
  "cost_threshold": float,            // Dollar amount for warnings
  "large_change_threshold": int,      // Lines changed for warnings
  "long_session_minutes": int,        // Minutes for long session alerts
  "enable_milestones": bool,          // Token milestone notifications
  "enable_warnings": bool,            // Cost/change warnings
  "quiet_hours": {
    "enabled": bool,
    "start": "HH:MM",                // 24-hour format
    "end": "HH:MM"
  }
}
```

## Development Notes

- All scripts are executable Python 3 with shebang `#!/usr/bin/env python3`
- Module imports use `sys.path.insert(0, str(Path(__file__).parent))` for local imports
- Logs use monthly rotation: `sessions_YYYYMM.log`
- Terminal-notifier preferred over osascript when available (install: `brew install terminal-notifier`)
- Security validation in `security_validator.py` (check this module when making security-related changes)

## Common Modification Scenarios

### Adding New Notification Types
1. Add template method in `NotificationTemplates` class
2. Update `NotificationBuilder` to include new notification in appropriate mode
3. Add corresponding sound mapping in `NotificationFormatter`

### Changing Thresholds
Edit `notification_config.json` or use CLI:
```bash
~/.claude/scripts/notification_system.py --mode [mode]
```

### Custom Sounds
Modify `sound_map` in `NotificationFormatter.format_for_terminal_notifier()` and `format_for_osascript()`.

Available macOS sounds: Glass, Tink, Basso, Hero, Ping, Pop, Purr, Submarine, etc.

## File Locations

- Main scripts: `~/.claude/scripts/` (system-wide)
- Config/data: `~/.claude-monitor/` (repository root)
- Documentation: `.md` files in repository root (Japanese language)
- Claude config: `~/.claude.json` (source of session data)
