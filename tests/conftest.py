# tests/conftest.py
"""
Pytest fixtures for flux_cost_bot tests.
"""

import pytest
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, date, timedelta


# =============================================================================
# Environment Mocks
# =============================================================================


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
            "GOOGLE_SHEET_ID": "test_sheet_id",
            "TELEGRAM_TOKEN": "test_token",
            "DEEPSEEK_API_KEY": "sk-test-deepseek-key",
        },
    ):
        yield


# =============================================================================
# LLM Mock
# =============================================================================


@pytest.fixture
def mock_call_llm():
    """Mock del LLM."""
    with patch("nodes.call_llm") as mock:
        yield mock


# =============================================================================
# Telegram API Mocks
# =============================================================================


@pytest.fixture
def mock_telegram_send_message():
    """Mock for telegram_api.send_message."""
    with patch("utils.telegram_api.send_message", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_telegram():
    """Combined mock for telegram API (send_message + bot)."""
    with patch("utils.telegram_api.telegram.Bot") as mock_bot:
        mock_instance = MagicMock()
        mock_bot.return_value = mock_instance
        mock_instance.send_message = AsyncMock()
        yield mock_instance


@pytest.fixture
def mock_get_latest_updates():
    """Mock for telegram_api.get_latest_updates."""
    with patch("utils.telegram_api.get_latest_updates", new_callable=AsyncMock) as mock:
        yield mock


# =============================================================================
# Google Sheets API Mocks
# =============================================================================


@pytest.fixture
def mock_gsheets():
    """Mock for Google Sheets API functions."""
    with (
        patch("utils.gsheets_api.get_gsheets_client") as mock_client,
        patch("utils.gsheets_api.append_row") as mock_append,
        patch("utils.gsheets_api.get_all_records") as mock_get_records,
        patch("utils.gsheets_api.get_budgets") as mock_get_budgets,
        patch("utils.gsheets_api.set_budget") as mock_set_budget,
        patch("utils.gsheets_api.find_last_row_by_user") as mock_find_last,
        patch("utils.gsheets_api.update_row") as mock_update,
        patch("utils.gsheets_api.delete_row") as mock_delete,
        patch("utils.gsheets_api.get_categories") as mock_get_categories,
        patch("utils.gsheets_api.add_category") as mock_add_category,
    ):
        # Default return values
        mock_get_records.return_value = []
        mock_get_budgets.return_value = {}
        mock_append.return_value = True
        mock_set_budget.return_value = True
        mock_find_last.return_value = None
        mock_update.return_value = True
        mock_delete.return_value = True
        mock_get_categories.return_value = ["alimentos", "auto", "otros"]
        mock_add_category.return_value = True

        yield {
            "client": mock_client,
            "append_row": mock_append,
            "get_all_records": mock_get_records,
            "get_budgets": mock_get_budgets,
            "set_budget": mock_set_budget,
            "find_last_row_by_user": mock_find_last,
            "update_row": mock_update,
            "delete_row": mock_delete,
            "get_categories": mock_get_categories,
            "add_category": mock_add_category,
        }


# =============================================================================
# Test Data Fixtures
# =============================================================================


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
def sample_income():
    """Sample income data."""
    return {
        "date": "2024-01-15",
        "amount": 150000,
        "category": "Ingreso",
        "description": "sueldo",
        "who": "Juan",
        "type": "Ingreso",
    }


@pytest.fixture
def sample_transactions():
    """Sample list of mixed transactions (expenses + income)."""
    return [
        {
            "date": "2024-01-05",
            "amount": 5000,
            "category": "alimentos",
            "description": "supermercado",
            "who": "Juan",
            "type": "Gasto",
        },
        {
            "date": "2024-01-10",
            "amount": 15000,
            "category": "auto",
            "description": "nafta",
            "who": "Juan",
            "type": "Gasto",
        },
        {
            "date": "2024-01-15",
            "amount": 150000,
            "category": "Ingreso",
            "description": "sueldo",
            "who": "Juan",
            "type": "Ingreso",
        },
        {
            "date": "2024-01-20",
            "amount": 8000,
            "category": "otros",
            "description": "cinema",
            "who": "Maria",
            "type": "Gasto",
        },
    ]


@pytest.fixture
def sample_sheet_records():
    """
    Sample records as they come from Google Sheets.
    Uses current year/month to test date filtering.
    """
    today = date.today()
    current_year = today.year
    current_month = today.month

    # Create dates in different months
    same_month = date(current_year, current_month, 5).strftime("%Y-%m-%d")
    last_month = date(
        current_year, current_month - 1 if current_month > 1 else 12, 15
    ).strftime("%Y-%m-%d")
    next_month = date(
        current_year, current_month + 1 if current_month < 12 else 1, 10
    ).strftime("%Y-%m-%d")

    return [
        {
            "Fecha": same_month,
            "Monto": "5000",
            "Categoria": "alimentos",
            "Descripcion": "super",
            "Quien": "Juan",
            "Tipo": "Gasto",
        },
        {
            "Fecha": same_month,
            "Monto": "15000",
            "Categoria": "auto",
            "Descripcion": "nafta",
            "Quien": "Juan",
            "Tipo": "Gasto",
        },
        {
            "Fecha": last_month,
            "Monto": "8000",
            "Categoria": "alimentos",
            "Descripcion": "kiosko",
            "Quien": "Juan",
            "Tipo": "Gasto",
        },
        {
            "Fecha": next_month,
            "Monto": "2000",
            "Categoria": "alimentos",
            "Descripcion": "pan",
            "Quien": "Maria",
            "Tipo": "Gasto",
        },
        {
            "Fecha": same_month,
            "Monto": "150000",
            "Categoria": "Ingreso",
            "Descripcion": "sueldo",
            "Quien": "Juan",
            "Tipo": "Ingreso",
        },
        {
            "Fecha": same_month,
            "Monto": "3000",
            "Categoria": "ALIMENTOS",
            "Descripcion": "fruta",
            "Quien": "Maria",
            "Tipo": "Gasto",
        },  # Uppercase category
    ]


# =============================================================================
# Shared State Fixtures
# =============================================================================


@pytest.fixture
def mock_shared_base():
    """Base shared state for node tests."""
    return {
        "telegram_input": {
            "message_text": "gaste 5000 en super",
            "user_name": "Juan",
            "chat_id": 123456,
        },
        "valid_categories": ["alimentos", "auto", "otros", "ropa", "ocio"],
    }


@pytest.fixture
def mock_parsed_transactions():
    """Mock parsed transactions ready for processing."""
    today = datetime.now().strftime("%Y-%m-%d")
    return [
        {
            "date": today,
            "amount": 5000,
            "category": "alimentos",
            "description": "supermercado",
            "who": "Juan",
            "type": "Gasto",
            "chat_id": 123456,
        },
        {
            "date": today,
            "amount": 15000,
            "category": "auto",
            "description": "nafta",
            "who": "Juan",
            "type": "Gasto",
            "chat_id": 123456,
        },
    ]


@pytest.fixture
def mock_budgets():
    """Mock budgets data."""
    return {
        "alimentos": 50000.0,
        "auto": 30000.0,
        "otros": 20000.0,
    }


# =============================================================================
# Async Helpers
# =============================================================================


@pytest.fixture(autouse=True)
def mock_event_loop():
    """Create an event loop for async node tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def today_str():
    """Today's date string."""
    from datetime import date

    return date.today().strftime("%Y-%m-%d")


@pytest.fixture
def today_date():
    """Today's date object."""
    return date.today()


@pytest.fixture
def current_month_year():
    """Current month and year."""
    now = datetime.now()
    return {"month": now.month, "year": now.year}



