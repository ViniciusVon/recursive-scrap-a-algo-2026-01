"""
Tests for the ActionLogger module.
"""

import pytest
import os
from src.logger import ActionLogger


class TestActionLogger:
    """Test suite for ActionLogger."""

    def setup_method(self):
        """Set up test fixtures."""
        self.logger = ActionLogger(log_file="test_actions.log")

    def teardown_method(self):
        """Clean up after tests."""
        if os.path.exists("test_actions.log"):
            os.remove("test_actions.log")

    # Username validation tests

    def test_validate_username_valid_simple(self):
        """Test valid simple username."""
        is_valid, error = self.logger.validate_username("Gabriel")
        assert is_valid is True
        assert error == ""

    def test_validate_username_valid_compound(self):
        """Test valid compound username."""
        is_valid, error = self.logger.validate_username("Gabriel Heni")
        assert is_valid is True
        assert error == ""

    def test_validate_username_valid_accented(self):
        """Test valid username with accents."""
        is_valid, error = self.logger.validate_username("José María")
        assert is_valid is True
        assert error == ""

    def test_validate_username_too_short(self):
        """Test username that is too short."""
        is_valid, error = self.logger.validate_username("Jo")
        assert is_valid is False
        assert "at least 3 characters" in error

    def test_validate_username_with_numbers(self):
        """Test username with numbers (invalid)."""
        is_valid, error = self.logger.validate_username("Gabriel123")
        assert is_valid is False
        assert "only letters" in error

    def test_validate_username_with_special_chars(self):
        """Test username with special characters (invalid)."""
        is_valid, error = self.logger.validate_username("Gabriel@Heni")
        assert is_valid is False
        assert "only letters" in error

    def test_validate_username_short_parts(self):
        """Test compound name with all parts < 3 chars."""
        is_valid, error = self.logger.validate_username("Jo Li")
        assert is_valid is False
        assert "3 or more characters" in error

    # Set username tests

    def test_set_username_valid(self):
        """Test setting a valid username."""
        result = self.logger.set_username("Gabriel")
        assert result is True
        assert self.logger.username == "Gabriel"

    def test_set_username_invalid(self):
        """Test setting an invalid username."""
        result = self.logger.set_username("Jo")
        assert result is False
        assert self.logger.username is None

    # Logging tests

    def test_log_action_basic(self):
        """Test basic action logging."""
        self.logger.set_username("TestUser")
        self.logger.log_action("TEST_ACTION", "This is a test")

        logs = self.logger.get_logs()
        # Should have 2 logs: USER_LOGIN and TEST_ACTION
        assert len(logs) == 2
        assert logs[1]["action_type"] == "TEST_ACTION"
        assert logs[1]["description"] == "This is a test"
        assert logs[1]["username"] == "TestUser"

    def test_log_action_anonymous(self):
        """Test logging without username."""
        self.logger.log_action("TEST_ACTION", "Anonymous action")

        logs = self.logger.get_logs()
        assert len(logs) == 1
        assert logs[0]["username"] == "ANONYMOUS"

    def test_get_logs_filtered(self):
        """Test getting filtered logs."""
        self.logger.log_action("TYPE_A", "First")
        self.logger.log_action("TYPE_B", "Second")
        self.logger.log_action("TYPE_A", "Third")

        type_a_logs = self.logger.get_logs("TYPE_A")
        assert len(type_a_logs) == 2

        type_b_logs = self.logger.get_logs("TYPE_B")
        assert len(type_b_logs) == 1

    def test_clear_logs(self):
        """Test clearing logs."""
        self.logger.log_action("TEST", "Test log")
        assert len(self.logger.logs) == 1

        self.logger.clear_logs()
        assert len(self.logger.logs) == 0

    def test_logs_written_to_file(self):
        """Test that logs are written to file."""
        self.logger.log_action("FILE_TEST", "Testing file write")

        assert os.path.exists("test_actions.log")
        with open("test_actions.log", 'r') as f:
            content = f.read()
            assert "FILE_TEST" in content
            assert "Testing file write" in content

    def test_get_logs_summary(self):
        """Test logs summary generation."""
        self.logger.set_username("TestUser")
        self.logger.log_action("ACTION1", "First action")

        summary = self.logger.get_logs_summary()
        assert "TestUser" in summary
        assert "ACTION1" in summary
        assert "First action" in summary
