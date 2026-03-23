"""
Tests for the PriceMonitor module.

Note: Full integration tests require Selenium and a browser.
These are unit tests for the logic that doesn't require a browser.
"""

import pytest
from src.monitor import PriceMonitor


class TestPriceMonitor:
    """Test suite for PriceMonitor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = PriceMonitor("https://example.com", headless=True)

    # Price extraction tests

    def test_extract_price_usd_format(self):
        """Test extracting USD formatted price."""
        price = self.monitor.extract_price_value("$1,234.56")
        assert price == 1234.56

    def test_extract_price_eur_format(self):
        """Test extracting EUR formatted price (1.234,56)."""
        price = self.monitor.extract_price_value("€1.234,56")
        assert price == 1234.56

    def test_extract_price_brl_format(self):
        """Test extracting BRL formatted price."""
        price = self.monitor.extract_price_value("R$ 1.234,56")
        assert price == 1234.56

    def test_extract_price_simple(self):
        """Test extracting simple price."""
        price = self.monitor.extract_price_value("$99")
        assert price == 99.0

    def test_extract_price_with_text(self):
        """Test extracting price from text."""
        price = self.monitor.extract_price_value("Current price: $49.99 USD")
        assert price == 49.99

    def test_extract_price_no_currency(self):
        """Test extracting price without currency symbol."""
        price = self.monitor.extract_price_value("1234.56")
        assert price == 1234.56

    def test_extract_price_invalid(self):
        """Test extracting from text without price."""
        price = self.monitor.extract_price_value("No price here")
        assert price is None

    def test_extract_price_comma_decimal(self):
        """Test extracting price with comma as decimal (e.g., 99,99)."""
        price = self.monitor.extract_price_value("$99,99")
        assert price == 99.99

    def test_extract_price_large_number(self):
        """Test extracting large price."""
        price = self.monitor.extract_price_value("$1,000,000.00")
        assert price == 1000000.0

    # Pattern tests

    def test_custom_pattern(self):
        """Test with custom price pattern."""
        monitor = PriceMonitor("https://example.com", price_pattern=r'\d+\.\d{2}')
        price = monitor.extract_price_value("Price is 123.45 dollars")
        assert price == 123.45

    def test_default_pattern_matches_common_formats(self):
        """Test that default pattern matches common price formats."""
        test_cases = [
            ("$100", 100.0),
            ("$100.00", 100.0),
            ("R$ 50,00", 50.0),
            ("€ 75.50", 75.50),
            ("£99.99", 99.99),
        ]

        for text, expected in test_cases:
            price = self.monitor.extract_price_value(text)
            assert price == expected, f"Failed for: {text}"
