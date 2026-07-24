from auth_utils import (
    generate_otp,
    is_allowed_email,
    normalize_auth_config,
    normalize_email,
)


def test_normalize_email_lowercases_and_strips_whitespace():
    assert normalize_email("  User@SAMA.com ") == "user@sama.com"


def test_allowed_domains_only():
    assert is_allowed_email("user@sama.com") is True
    assert is_allowed_email("user@saama.com") is True
    assert is_allowed_email("user@triad.com") is True
    assert is_allowed_email("user@example.com") is False
    assert is_allowed_email("not-an-email") is False


def test_generate_otp_is_numeric_and_expected_length():
    otp = generate_otp()
    assert len(otp) == 6
    assert otp.isdigit()


def test_normalize_auth_config_removes_spaces_from_password():
    config = normalize_auth_config(
        {
            "gmail_address": "  user@gmail.com  ",
            "gmail_password": "ab cd ef gh ij kl mn op",
            "smtp_server": " smtp.gmail.com ",
            "smtp_port": " 587 ",
        }
    )
    assert config["gmail_address"] == "user@gmail.com"
    assert config["gmail_password"] == "abcdefghijklmnop"
    assert config["smtp_server"] == "smtp.gmail.com"
    assert config["smtp_port"] == "587"
