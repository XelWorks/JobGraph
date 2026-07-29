import json
import logging

from app.infrastructure.logging.logger import JSONFormatter, redact_sensitive_data


def test_redact_sensitive_data_dict_and_list():
    """Verify recursive redaction on dictionaries and nested lists."""
    raw_payload = {
        "user": "gourav@example.com",
        "password": "SuperSecretPassword123!",
        "api_key": "AIzaSy_Secret_Key_12345",
        "nested": [
            {"refresh_token": "bearer_secret_token_val"},
            {"public_field": "public_val"}
        ]
    }

    cleaned = redact_sensitive_data(raw_payload)

    assert cleaned["user"] == "gourav@example.com"
    assert cleaned["password"] == "[REDACTED]"
    assert cleaned["api_key"] == "[REDACTED]"
    assert cleaned["nested"][0]["refresh_token"] == "[REDACTED]"
    assert cleaned["nested"][1]["public_field"] == "public_val"


def test_redact_sensitive_data_string_patterns():
    """Verify regex pattern matching redacts inline secrets inside plain string messages."""
    msg = "User authenticated with Bearer eyJhbGciOiJIUzI1NiI1c.secret_payload and Gemini key AIzaSyAUfNBp8-yT-mzI0nw5OaHeNV1f1Lg6hXg"
    cleaned = redact_sensitive_data(msg)

    assert "eyJhbGci" not in cleaned
    assert "AIzaSyAUfNBp8" not in cleaned
    assert "[REDACTED_GEMINI_KEY]" in cleaned
    assert "Bearer [REDACTED]" in cleaned


def test_json_formatter_outputs_valid_json():
    """Verify JSONFormatter generates valid JSON strings containing standard and extra attributes."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="logger.py",
        lineno=10,
        msg="User authorization attempt password=SecretPass",
        args=(),
        exc_info=None
    )
    # Add custom extra attribute
    record.__dict__["custom_extra"] = "my_extra_value"
    record.__dict__["api_key_param"] = "my_private_key"

    formatted_str = formatter.format(record)

    # Ensure it's valid JSON
    parsed = json.loads(formatted_str)
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test_logger"
    assert "SecretPass" not in parsed["message"]
    assert "[REDACTED]" in parsed["message"]
    assert parsed["custom_extra"] == "my_extra_value"
    assert parsed["api_key_param"] == "[REDACTED]"
