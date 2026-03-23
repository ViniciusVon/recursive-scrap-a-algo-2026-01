"""
Action Logger Module

Logs all user actions with timestamps and username.
Validates username input according to requirements.

Big O Analysis:
- validate_username(): O(n) where n is the length of the username
- log_action(): O(1) for adding to list, O(n) for file write where n is log size
- get_logs(): O(n) where n is the number of logs
"""

import re
from datetime import datetime
from typing import Optional


class ActionLogger:
    """
    Logs all user actions in the system.

    Attributes:
        username (str): The current user's name
        logs (list): List of all logged actions
        log_file (str): Path to the log file
    """

    def __init__(self, log_file: str = "user_actions.log"):
        """
        Initialize the ActionLogger.

        Args:
            log_file: Path to save the log file

        Time Complexity: O(1)
        """
        self.username: Optional[str] = None
        self.logs: list[dict] = []
        self.log_file = log_file

    def validate_username(self, name: str) -> tuple[bool, str]:
        """
        Validate the username according to requirements.

        Requirements:
        - Must be at least 3 characters
        - Must contain only letters (can be compound names with spaces)
        - Duplicate names are allowed

        Args:
            name: The username to validate

        Returns:
            Tuple of (is_valid, error_message)

        Time Complexity: O(n) where n is the length of the name
        """
        # Check minimum length - O(1)
        if len(name) < 3:
            return False, "Username must be at least 3 characters"

        # Check if contains only letters and spaces (compound names allowed) - O(n)
        # Allow accented characters for Portuguese names
        if not re.match(r'^[a-zA-ZÀ-ÿ\s]+$', name):
            return False, "Username must contain only letters (compound names allowed)"

        # Check if at least one part has 3+ characters - O(n)
        parts = name.split()
        has_valid_part = any(len(part) >= 3 for part in parts)
        if not has_valid_part:
            return False, "At least one name part must have 3 or more characters"

        return True, ""

    def set_username(self, name: str) -> bool:
        """
        Set the username after validation.

        Args:
            name: The username to set

        Returns:
            True if username was set successfully

        Time Complexity: O(n) where n is the length of the name
        """
        is_valid, error = self.validate_username(name)

        if is_valid:
            self.username = name
            self.log_action("USER_LOGIN", f"User '{name}' logged in")
            print(f"[LOGGER] Username set: {name}")
            return True
        else:
            print(f"[LOGGER] Invalid username: {error}")
            return False

    def request_username(self) -> bool:
        """
        Interactively request and validate username.

        Returns:
            True if username was set successfully

        Time Complexity: O(n * k) where n is name length, k is number of attempts
        """
        print("\n[LOGGER] Please enter your username")
        print("[LOGGER] (Must be at least 3 characters, letters only, compound names allowed)")

        while True:
            name = input("Username: ").strip()

            if not name:
                print("[LOGGER] Username cannot be empty")
                continue

            if self.set_username(name):
                return True

            retry = input("Try again? (y/n): ").strip().lower()
            if retry != 'y':
                return False

    def log_action(self, action_type: str, description: str) -> None:
        """
        Log a user action.

        Args:
            action_type: Type of action (e.g., 'MONITOR_START', 'PRICE_CHANGE')
            description: Description of the action

        Time Complexity: O(1) for memory, O(n) for file write
        """
        timestamp = datetime.now().isoformat()

        log_entry = {
            "timestamp": timestamp,
            "username": self.username or "ANONYMOUS",
            "action_type": action_type,
            "description": description
        }

        # Add to memory - O(1)
        self.logs.append(log_entry)

        # Format log line
        log_line = f"[{timestamp}] [{log_entry['username']}] [{action_type}] {description}"

        # Print to console
        print(f"[LOG] {log_line}")

        # Write to file - O(1) for append
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_line + '\n')
        except Exception as e:
            print(f"[LOGGER] Warning: Could not write to log file: {e}")

    def get_logs(self, action_type: Optional[str] = None) -> list[dict]:
        """
        Get logged actions, optionally filtered by type.

        Args:
            action_type: Filter by action type (optional)

        Returns:
            List of log entries

        Time Complexity: O(n) where n is the number of logs
        """
        if action_type:
            return [log for log in self.logs if log['action_type'] == action_type]
        return self.logs.copy()

    def get_logs_summary(self) -> str:
        """
        Get a summary of all logged actions.

        Returns:
            Formatted string summary

        Time Complexity: O(n) where n is the number of logs
        """
        if not self.logs:
            return "No actions logged yet."

        summary = f"\n{'='*60}\n"
        summary += f"ACTION LOG SUMMARY - User: {self.username or 'ANONYMOUS'}\n"
        summary += f"Total actions: {len(self.logs)}\n"
        summary += f"{'='*60}\n\n"

        for log in self.logs:
            summary += f"[{log['timestamp']}] [{log['action_type']}]\n"
            summary += f"  {log['description']}\n\n"

        return summary

    def clear_logs(self) -> None:
        """
        Clear all logs from memory (file remains).

        Time Complexity: O(1)
        """
        self.logs.clear()
        print("[LOGGER] Logs cleared from memory")
