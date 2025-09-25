#!/usr/bin/env python3
"""
Vibe Tracking Hook for Claude Code
Maintains communication personality modes across sessions using parent terminal PID
"""

import json
import sys
import os
import psutil
import random
from pathlib import Path
from typing import Dict, Optional

class VibeTracker:
    def __init__(self):
        self.vibe_file = Path.home() / ".claude" / "vibe_state.json"
        self.vibe_file.parent.mkdir(exist_ok=True)

        # Vibe mode configurations
        self.vibe_configs = {
            "solo": {
                "description": "Casual, slightly sarcastic, to the point",
                "reminder_frequency": 10,
                "reminder_texts": [
                    "[VIBE: Solo] 🎸 Keep it casual and direct - no corporate speak, just get shit done",
                    "[VIBE: Solo] 🎸 Stay sarcastic and real - if it's overengineered, say so",
                    "[VIBE: Solo] 🎸 Cut through the BS - 'That won't work' beats 'That might be suboptimal'",
                    "[VIBE: Solo] 🎸 Be the helpful asshole - brutally honest but actually useful",
                    "[VIBE: Solo] 🎸 Skip the pleasantries - dive straight into the problem",
                    "[VIBE: Solo] 🎸 Channel your inner developer - if there's a built-in solution, use it"
                ]
            },
            "concert": {
                "description": "Professional precision, brutally honest",
                "reminder_frequency": 0,  # Disabled - no interruptions during focused work
                "reminder_texts": []  # No reminders for focus mode
            },
            "duo": {
                "description": "Collaborative problem-solving, building together",
                "reminder_frequency": 10,
                "reminder_texts": [
                    "[VIBE: Duo] 🎼 Build on their ideas - 'Your instinct is right, but what about...'",
                    "[VIBE: Duo] 🎼 Think together - question assumptions collaboratively",
                    "[VIBE: Duo] 🎼 Collaborative exploration - we're in this together",
                    "[VIBE: Duo] 🎼 'Building on that idea...' - always be building up, not tearing down"
                ]
            },
            "mentor": {
                "description": "Socratic method - guides with questions, never gives direct answers",
                "reminder_frequency": 5,  # More frequent since it's hardest to maintain
                "reminder_texts": [
                    "[VIBE: Mentor] 📚 Guide with questions - 'What do you think happens when...?'",
                    "[VIBE: Mentor] 📚 Never give direct answers - make them discover the solution",
                    "[VIBE: Mentor] 📚 Socratic method - 'Try running it. What error did you get? Why?'",
                    "[VIBE: Mentor] 📚 Review their code, don't write it - they need to find their own bugs"
                ]
            },
            "improv": {
                "description": "Creative exploration with dad jokes and dry humor",
                "reminder_frequency": 8,  # Conversational but not overwhelming
                "reminder_texts": [
                    "[VIBE: Improv] 🎭 Dad joke energy - 'That function is doing more jobs than a single parent'",
                    "[VIBE: Improv] 🎭 Dry humor + honest assessment - be self-aware about being a nerd",
                    "[VIBE: Improv] 🎭 'Your code is cleaner than my browser history' - relatable analogies",
                    "[VIBE: Improv] 🎭 Still brutally honest but with humor - 'That's optimistic. I like optimistic.'",
                    "[VIBE: Improv] 🎭 Creative exploration - build on wild ideas while keeping it real",
                    "[VIBE: Improv] 🎭 'That bug is more elusive than my motivation on Monday' - dad joke vibes"
                ]
            }
        }

    def get_parent_terminal_pid(self) -> Optional[int]:
        """Get the PID of the parent terminal process"""
        try:
            current_pid = os.getpid()
            current_process = psutil.Process(current_pid)

            # Walk up the process tree to find the actual terminal
            parent = current_process
            terminal_pid = None

            while parent:
                parent_name = parent.name().lower()

                # Look for actual terminal emulators first
                terminal_emulators = ['gnome-terminal', 'xterm', 'konsole', 'alacritty',
                                    'kitty', 'terminator', 'tilix', 'wezterm', 'st']

                if any(term in parent_name for term in terminal_emulators):
                    return parent.pid

                # Keep track of shell processes as fallback
                if parent_name in ['bash', 'zsh', 'fish', 'sh']:
                    if terminal_pid is None:  # Use the first shell we find
                        terminal_pid = parent.pid

                parent = parent.parent()

            # Return shell PID if no terminal emulator found
            return terminal_pid

        except Exception:
            # Ultimate fallback - use session leader
            try:
                return os.getsid(os.getpid())
            except:
                return None

    def load_vibe_state(self) -> Dict:
        """Load vibe state from file"""
        if not self.vibe_file.exists():
            return {}

        try:
            with open(self.vibe_file) as f:
                return json.load(f)
        except Exception:
            return {}

    def save_vibe_state(self, state: Dict):
        """Save vibe state to file"""
        try:
            with open(self.vibe_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception:
            pass

    def set_vibe(self, mode: str) -> bool:
        """Set vibe mode for current terminal session"""
        if mode not in self.vibe_configs:
            return False

        terminal_pid = self.get_parent_terminal_pid()
        if not terminal_pid:
            return False

        state = self.load_vibe_state()

        if 'sessions' not in state:
            state['sessions'] = {}

        state['sessions'][str(terminal_pid)] = {
            'mode': mode,
            'message_count': 0,
            'last_reminder': 0
        }

        self.save_vibe_state(state)
        return True

    def get_current_vibe(self) -> Optional[Dict]:
        """Get current vibe mode for this terminal session"""
        terminal_pid = self.get_parent_terminal_pid()
        if not terminal_pid:
            return None

        state = self.load_vibe_state()
        session_data = state.get('sessions', {}).get(str(terminal_pid))

        if not session_data:
            return None

        mode = session_data['mode']
        if mode not in self.vibe_configs:
            return None

        return {
            'mode': mode,
            'config': self.vibe_configs[mode],
            'session_data': session_data
        }

    def should_inject_reminder(self) -> tuple[bool, str]:
        """Check if we should inject a vibe reminder"""
        vibe_info = self.get_current_vibe()
        if not vibe_info:
            return False, ""

        config = vibe_info['config']
        session_data = vibe_info['session_data']

        # Concert mode disabled - no reminders
        if config['reminder_frequency'] == 0 or not config.get('reminder_texts'):
            return False, ""

        # Check if it's time for a reminder
        messages_since_reminder = session_data['message_count'] - session_data['last_reminder']

        if messages_since_reminder >= config['reminder_frequency']:
            # Pick a random reminder text for variety
            reminder_text = random.choice(config['reminder_texts'])
            return True, reminder_text

        return False, ""

    def increment_message_count(self):
        """Increment message count for current session"""
        terminal_pid = self.get_parent_terminal_pid()
        if not terminal_pid:
            return

        state = self.load_vibe_state()
        session_key = str(terminal_pid)

        if 'sessions' not in state or session_key not in state['sessions']:
            return

        state['sessions'][session_key]['message_count'] += 1

        # Check if we should update last_reminder
        should_remind, _ = self.should_inject_reminder()
        if should_remind:
            state['sessions'][session_key]['last_reminder'] = state['sessions'][session_key]['message_count']

        self.save_vibe_state(state)

    def cleanup_stale_sessions(self):
        """Remove sessions for PIDs that no longer exist"""
        state = self.load_vibe_state()
        if 'sessions' not in state:
            return

        active_pids = {str(p.pid) for p in psutil.process_iter(['pid'])}
        stale_pids = []

        for pid in state['sessions'].keys():
            if pid not in active_pids:
                stale_pids.append(pid)

        for pid in stale_pids:
            del state['sessions'][pid]

        if stale_pids:
            self.save_vibe_state(state)

def main():
    """Hook entry point"""
    if len(sys.argv) < 2:
        return

    hook_type = sys.argv[1]
    tracker = VibeTracker()

    if hook_type == "preToolUse":
        # Clean up stale sessions periodically
        tracker.cleanup_stale_sessions()

        # Check if we should inject a vibe reminder
        should_remind, reminder_text = tracker.should_inject_reminder()

        if should_remind:
            # Inject reminder into the user's message
            print(f"\n{reminder_text}\n", file=sys.stderr)

        # Increment message count
        tracker.increment_message_count()

    elif hook_type == "setVibe":
        # Handle vibe setting command
        if len(sys.argv) >= 3:
            mode = sys.argv[2]
            if tracker.set_vibe(mode):
                print(f"Vibe set to: {mode}", file=sys.stderr)
            else:
                print(f"Invalid vibe mode: {mode}", file=sys.stderr)
                print("Available modes: solo, concert, duo, mentor, improv", file=sys.stderr)

    elif hook_type == "getVibe":
        # Show current vibe
        vibe_info = tracker.get_current_vibe()
        if vibe_info:
            mode = vibe_info['mode']
            description = vibe_info['config']['description']
            print(f"Current vibe: {mode} - {description}", file=sys.stderr)
        else:
            print("No vibe set for this session", file=sys.stderr)

if __name__ == "__main__":
    main()