"""
Tests for the validators module.
"""

import pytest
from src.utils.validators import validate_url


class TestValidateUrl:
    """Test suite for URL validation."""

    def test_valid_http_url(self):
        """Test valid HTTP URL."""
        is_valid, error = validate_url("http://example.com")
        assert is_valid is True
        assert error == ""

    def test_valid_https_url(self):
        """Test valid HTTPS URL."""
        is_valid, error = validate_url("https://example.com")
        assert is_valid is True
        assert error == ""

    def test_valid_url_with_path(self):
        """Test valid URL with path."""
        is_valid, error = validate_url("https://example.com/path/to/page")
        assert is_valid is True
        assert error == ""

    def test_valid_url_with_params(self):
        """Test valid URL with query parameters."""
        is_valid, error = validate_url("https://example.com/search?q=test&page=1")
        assert is_valid is True
        assert error == ""

    def test_empty_url(self):
        """Test empty URL."""
        is_valid, error = validate_url("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_url_without_scheme(self):
        """Test URL without scheme."""
        is_valid, error = validate_url("example.com")
        assert is_valid is False
        assert "scheme" in error.lower()

    def test_url_with_invalid_scheme(self):
        """Test URL with invalid scheme."""
        is_valid, error = validate_url("ftp://example.com")
        assert is_valid is False
        assert "http" in error.lower()

    def test_url_only_scheme(self):
        """Test URL with only scheme."""
        is_valid, error = validate_url("https://")
        assert is_valid is False
