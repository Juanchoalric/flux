# tests/conftest.py
import pytest
import os
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def mock_env():
    """Mock environment variables."""
    with patch.dict(
        os.environ,
        {
            "TELEGRAM_BOT_TOKEN": "test_token",
            "GOOGLE_API_KEY": "test_key",
            "ADMIN_CHAT_ID": "123456",
            "GEMINI_MODEL": "gemini-2.0-flash",
        },
    ):
        yield


@pytest.fixture
def mock_call_llm():
    """Mock del LLM."""
    with patch("nodes.call_llm") as mock:
        yield mock


@pytest.fixture
def sample_expense():
    """Sample expense data."""
    return {
        "date": "2024-01-01",
        "amount": 5000,
        "category": "comida",
        "description": "almuerzo",
        "who": "Juan",
        "type": "Gasto",
    }


@pytest.fixture
def today_str():
    """Today's date string."""
    from datetime import date

    return date.today().strftime("%Y-%m-%d")
