"""
Security utilities for the Moxalise API.
"""
import hashlib
import hmac
from typing import Optional, Any, Dict, List, Tuple, Union
import bleach

from moxalise.core.config import settings


def hash_ip_address(ip_address: Optional[str]) -> Optional[str]:
    """
    Hash an IP address using HMAC-SHA256 with a salt and truncate to first 8 characters.
    
    Similar to GitHub's approach, this preserves privacy while maintaining some uniqueness.
    
    Returns None if the input is None.
    """
    if ip_address is None:
        return None

    if not settings.IP_HASH_SALT:
        raise ValueError("IP_HASH_SALT environment variable is not set")

    # Use HMAC with SHA-256 and return only first 8 characters
    digest = hmac.new(
        settings.IP_HASH_SALT.encode(),
        ip_address.encode(),
        hashlib.sha256
    ).hexdigest()[:8]

    return digest


def sanitize_input(value: Any) -> Any:
    """
    Sanitize input to prevent XSS and other injection attacks using the bleach library.
    
    This function:
    1. Returns non-string values as is
    2. Uses bleach to clean HTML content, removing all tags and attributes
    3. Removes leading equals sign (=) to prevent formula injection in spreadsheets
    4. Replaces all newline characters with a single space
    
    Args:
        value: The input value to sanitize
        
    Returns:
        The sanitized value
    """
    # If not a string, return as is
    if not isinstance(value, str):
        return value
    
    if value is None:
        return None
    
    # Use bleach to clean the input, stripping all HTML tags
    # This prevents XSS by removing any script tags or event handlers
    sanitized = bleach.clean(
        value,
        tags=[],           # No HTML tags allowed
        attributes={},     # No attributes allowed
        strip=True,        # Strip disallowed tags
        strip_comments=True  # Strip HTML comments
    )
    
    # Remove leading equals sign to prevent formula injection in spreadsheets
    if sanitized.startswith('='):
        sanitized = sanitized[1:]
    
    # Replace all newline characters with a single space
    sanitized = ' '.join(sanitized.splitlines())
    
    return sanitized


def sanitize_object(obj: Any) -> Any:
    """
    Recursively sanitize all string values in an object.
    
    This function handles:
    - Dictionaries (recursively sanitize all values)
    - Lists/tuples (recursively sanitize all items)
    - Strings (sanitize using sanitize_input)
    - Other types (return as is)
    
    Args:
        obj: The object to sanitize
        
    Returns:
        The sanitized object
    """
    if isinstance(obj, dict):
        return {k: sanitize_object(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return type(obj)(sanitize_object(item) for item in obj)
    else:
        return sanitize_input(obj)