"""
Input validation and sanitization utilities.
"""
import re
from typing import Optional


def sanitize_phone(phone: str) -> str:
    """Remove non-numeric characters from phone number."""
    return re.sub(r'[^\d+]', '', phone)


def mask_phone(phone: str) -> str:
    """Mask phone number for logging (PII protection)."""
    if len(phone) < 4:
        return "***"
    return f"***{phone[-4:]}"


def mask_email(email: str) -> str:
    """Mask email for logging (PII protection)."""
    if '@' not in email:
        return "***"
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        return f"***@{domain}"
    return f"{local[:2]}***@{domain}"


def is_valid_phone(phone: str) -> bool:
    """Basic phone number validation."""
    cleaned = sanitize_phone(phone)
    return len(cleaned) >= 10


def is_valid_email(email: str) -> bool:
    """Basic email validation."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_input(text: str, max_length: int = 500) -> str:
    """Sanitize user input."""
    # Remove control characters except newlines and tabs
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    # Limit length
    return text[:max_length].strip()







