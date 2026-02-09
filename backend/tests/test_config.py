"""Tests for app config (settings)."""
import pytest
from backend.app.core.config import settings


def test_settings_load():
    assert settings.PROJECT_NAME
    assert settings.API_V1_STR == "/api/v1"


def test_freemium_limits():
    assert settings.FREE_TIER_CONVERSIONS_LIMIT >= 1
    assert settings.ANONYMOUS_CONVERSIONS_LIMIT >= 1
    assert settings.MAX_FILE_SIZE_MB >= 1


def test_security_settings():
    assert settings.SECRET_KEY
    assert settings.ALGORITHM == "HS256"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0


def test_log_level():
    assert settings.LOG_LEVEL.upper() in ("DEBUG", "INFO", "WARNING", "ERROR")
