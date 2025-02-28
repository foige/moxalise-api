"""
Unit tests for security utilities.

This module contains unit tests for the security utilities.
"""
import pytest
from unittest.mock import patch, MagicMock

from moxalise.core.security import hash_ip_address, sanitize_input, sanitize_object


@pytest.mark.parametrize(
    "ip_address,expected_type",
    [
        ("192.168.1.1", str),
        (None, type(None)),
    ],
)
def test_hash_ip_address_return_types(ip_address, expected_type):
    """
    Test that hash_ip_address returns the expected types.
    
    Args:
        ip_address: The IP address to hash.
        expected_type: The expected return type.
    """
    with patch("moxalise.core.security.settings") as mock_settings:
        mock_settings.IP_HASH_SALT = "test-salt"
        result = hash_ip_address(ip_address)
        assert isinstance(result, expected_type)


def test_hash_ip_address_consistent():
    """
    Test that hash_ip_address returns consistent results for the same input.
    """
    with patch("moxalise.core.security.settings") as mock_settings:
        mock_settings.IP_HASH_SALT = "test-salt"
        
        # Same IP should produce the same hash
        ip = "192.168.1.1"
        hash1 = hash_ip_address(ip)
        hash2 = hash_ip_address(ip)
        assert hash1 == hash2
        
        # Different IPs should produce different hashes
        ip2 = "192.168.1.2"
        hash3 = hash_ip_address(ip2)
        assert hash1 != hash3


def test_hash_ip_address_length():
    """
    Test that hash_ip_address returns a hash of the expected length.
    """
    with patch("moxalise.core.security.settings") as mock_settings:
        mock_settings.IP_HASH_SALT = "test-salt"
        
        result = hash_ip_address("192.168.1.1")
        assert len(result) == 8  # We're using the first 8 characters of the hash


def test_hash_ip_address_salt_required():
    """
    Test that hash_ip_address raises an error if the salt is not set.
    """
    with patch("moxalise.core.security.settings") as mock_settings:
        mock_settings.IP_HASH_SALT = ""
        
        with pytest.raises(ValueError, match="IP_HASH_SALT environment variable is not set"):
            hash_ip_address("192.168.1.1")


@pytest.mark.parametrize(
    "input_value,expected_result",
    [
        # Non-string values should be returned as is
        (123, 123),
        (None, None),
        (True, True),
        (3.14, 3.14),
        # HTML should be stripped
        ("<script>alert('XSS')</script>", "alert('XSS')"),
    ],
)
@patch("moxalise.core.security.bleach")
def test_sanitize_input(mock_bleach, input_value, expected_result):
    """
    Test that sanitize_input properly sanitizes input values using bleach.
    
    Args:
        mock_bleach: Mock for the bleach library.
        input_value: The input value to sanitize.
        expected_result: The expected sanitized result.
    """
    # Configure the mock to return the expected result
    mock_bleach.clean.return_value = expected_result
    
    result = sanitize_input(input_value)
    
    # For non-string values, bleach should not be called
    if isinstance(input_value, str) and input_value is not None:
        mock_bleach.clean.assert_called_once_with(
            input_value,
            tags=[],
            attributes={},
            strip=True,
            strip_comments=True
        )
    else:
        mock_bleach.clean.assert_not_called()
    
    assert result == expected_result


def test_sanitize_input_additional_features():
    """
    Test the additional sanitization features:
    1. Removing leading equals sign
    2. Replacing newlines with spaces
    """
    # Test removing leading equals sign
    assert sanitize_input("=SUM(A1:B1)") == "SUM(A1:B1)"
    
    # Test replacing newlines with spaces
    assert sanitize_input("Line1\nLine2\r\nLine3") == "Line1 Line2 Line3"
    
    # Test both features together
    assert sanitize_input("=Formula\nWith\r\nNewlines") == "Formula With Newlines"
    
    # Test with HTML content - bleach removes tags but may leave spaces
    sanitized = sanitize_input("<script>\nalert('XSS')\n</script>")
    assert "alert('XSS')" in sanitized
    
    # Test with equals sign in the middle (should not be removed)
    assert sanitize_input("This = that") == "This = that"


@patch("moxalise.core.security.sanitize_input")
def test_sanitize_object_dict(mock_sanitize_input):
    """
    Test that sanitize_object properly sanitizes dictionary objects.
    """
    # Configure the mock to return a sanitized version of the input
    mock_sanitize_input.side_effect = lambda x: f"sanitized_{x}" if isinstance(x, str) else x
    
    test_dict = {
        "safe": "normal text",
        "unsafe": "<script>alert('XSS')</script>",
        "nested": {
            "safe": 123,
            "unsafe": "javascript:evil()"
        }
    }
    
    result = sanitize_object(test_dict)
    
    assert result["safe"] == "sanitized_normal text"
    assert result["unsafe"] == "sanitized_<script>alert('XSS')</script>"
    assert result["nested"]["safe"] == 123
    assert result["nested"]["unsafe"] == "sanitized_javascript:evil()"


@patch("moxalise.core.security.sanitize_input")
def test_sanitize_object_list(mock_sanitize_input):
    """
    Test that sanitize_object properly sanitizes list objects.
    """
    # Configure the mock to return a sanitized version of the input
    mock_sanitize_input.side_effect = lambda x: f"sanitized_{x}" if isinstance(x, str) else x
    
    test_list = [
        "normal text",
        "<script>alert('XSS')</script>",
        123,
        ["nested", "javascript:evil()"]
    ]
    
    result = sanitize_object(test_list)
    
    assert result[0] == "sanitized_normal text"
    assert result[1] == "sanitized_<script>alert('XSS')</script>"
    assert result[2] == 123
    assert result[3][0] == "sanitized_nested"
    assert result[3][1] == "sanitized_javascript:evil()"


@patch("moxalise.core.security.sanitize_input")
def test_sanitize_object_mixed(mock_sanitize_input):
    """
    Test that sanitize_object properly sanitizes mixed objects.
    """
    # Configure the mock to return a sanitized version of the input
    mock_sanitize_input.side_effect = lambda x: f"sanitized_{x}" if isinstance(x, str) else x
    
    test_obj = {
        "strings": ["normal", "<script>alert('XSS')</script>"],
        "numbers": [1, 2, 3],
        "mixed": [123, "<script>alert('XSS')</script>", {"key": "javascript:evil()"}]
    }
    
    result = sanitize_object(test_obj)
    
    assert result["strings"][0] == "sanitized_normal"
    assert result["strings"][1] == "sanitized_<script>alert('XSS')</script>"
    assert result["numbers"] == [1, 2, 3]
    assert result["mixed"][0] == 123
    assert result["mixed"][1] == "sanitized_<script>alert('XSS')</script>"
    assert result["mixed"][2]["key"] == "sanitized_javascript:evil()"