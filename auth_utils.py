"""Authentication utilities for Clinical NER login."""

import random
import re
from typing import Final

ALLOWED_DOMAINS: Final[tuple[str, ...]] = ("@saama.com", "@triad.com")


def normalize_email(email: str) -> str:
    """Normalize email by stripping whitespace and converting to lowercase."""
    return (email or "").strip().lower()


def normalize_auth_config(config: dict[str, str]) -> dict[str, str]:
    """Normalize Gmail authentication configuration."""
    return {
        "gmail_address": str(config.get("gmail_address", "") or "").strip(),
        "gmail_password": str(config.get("gmail_password", "") or "").strip().replace(" ", ""),
        "smtp_server": str(config.get("smtp_server", "smtp.gmail.com") or "smtp.gmail.com").strip(),
        "smtp_port": str(config.get("smtp_port", "587") or "587").strip(),
    }


def is_allowed_email(email: str) -> bool:
    """Check if email is from an allowed domain."""
    normalized = normalize_email(email)
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
        return False
    return normalized.endswith(ALLOWED_DOMAINS)


def generate_otp(length: int = 6) -> str:
    """Generate a random OTP code."""
    return "".join(str(random.randint(0, 9)) for _ in range(length))
