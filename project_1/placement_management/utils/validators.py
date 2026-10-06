"""
Input validation utilities.
"""

import re
from typing import Optional


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))


def validate_phone(phone: str) -> bool:
    """Validate 10-digit Indian phone number."""
    cleaned = re.sub(r"[\s\-\+]", "", phone)
    return bool(re.match(r"^[6-9]\d{9}$", cleaned))


def validate_cgpa(cgpa: float) -> bool:
    """Validate CGPA is between 0 and 10."""
    return 0.0 <= cgpa <= 10.0


def validate_register_number(reg_no: str) -> bool:
    """Validate register number format (alphanumeric, 8-15 chars)."""
    return bool(re.match(r"^[A-Z0-9]{6,20}$", reg_no.strip().upper()))


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength.
    Returns (is_valid, message).
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    return True, "Password is strong."


def sanitize_string(value: str, max_length: int = 255) -> str:
    """Strip whitespace and truncate string."""
    if value is None:
        return ""
    return str(value).strip()[:max_length]


def validate_package(package: float) -> bool:
    """Validate package value (LPA) is reasonable."""
    return 0.0 <= package <= 500.0


def validate_year(year: int) -> bool:
    """Validate academic year (1-4 for UG)."""
    return year in [1, 2, 3, 4]


def validate_file_extension(filename: str,
                             allowed: list = None) -> bool:
    """Validate uploaded file extension."""
    if allowed is None:
        allowed = [".pdf", ".doc", ".docx"]
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in allowed


def validate_arrears(arrears: int) -> bool:
    """Validate arrears count is non-negative."""
    return isinstance(arrears, int) and arrears >= 0
