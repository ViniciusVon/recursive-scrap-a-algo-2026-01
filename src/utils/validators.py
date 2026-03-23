"""
Validators Module

Contains validation functions for user inputs.

Big O Analysis:
- validate_url(): O(n) where n is the length of the URL
"""

from urllib.parse import urlparse


def validate_url(url: str) -> tuple[bool, str]:
    """
    Validate a URL string.

    Args:
        url: The URL to validate

    Returns:
        Tuple of (is_valid, error_message)

    Time Complexity: O(n) where n is the length of the URL
    """
    if not url:
        return False, "URL cannot be empty"

    # Basic URL pattern check - O(n)
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return False, "Invalid URL format. Must include scheme (http/https)"

        if result.scheme not in ['http', 'https']:
            return False, "URL must use http or https"

        return True, ""
    except Exception as e:
        return False, f"Invalid URL: {str(e)}"
