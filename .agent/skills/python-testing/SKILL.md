---
name: python-testing
description: >
  Guía para testing en Python. pytest, mocks, fixtures, coverage.
  Trigger: Cuando se agregan tests o se modifica código que necesita tests.
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## When to Use

- Proyecto no tiene tests
- Se agregan nuevos nodes o funcionalidades
- Se hace refactoring
- Se quiere coverage alto

## Setup

```bash
pip install pytest pytest-asyncio pytest-mock
```

## Estructura de Tests

```
tests/
├── __init__.py
├── test_nodes.py       # Tests de nodes
├── test_flow.py        # Tests de flow
├── test_utils.py       # Tests de utilities
└── conftest.py         # Fixtures compartidas
```

## Test de Node (PocketFlow)

```python
# tests/test_nodes.py
import pytest
from unittest.mock import MagicMock, patch
from nodes import DetectIntentNode, ParseExpenseListNode

@pytest.fixture
def mock_shared():
    """Shared store fixture."""
    return {
        "telegram_input": {
            "message_text": "gaste 5000 en cafe",
            "user_name": "Juan",
            "chat_id": 123456
        },
        "valid_categories": ["comida", "transporte", "otros"]
    }

@pytest.fixture
def mock_call_llm():
    """Mock del LLM."""
    with patch('nodes.call_llm') as mock:
        mock.return_value = '{"intent": "REGISTRAR_GASTO", "entities": {}}'
        yield mock

def test_detect_intent_gasto(mock_shared, mock_call_llm):
    """Test que detecta intent de registrar gasto."""
    node = DetectIntentNode()
    
    # Run node
    result = node.run(mock_shared)
    
    # Assertions
    assert result == "log_expense"
    assert mock_shared["user_intent"]["intent"] == "REGISTRAR_GASTO"

def test_detect_intent_fallback():
    """Test fallback cuando no se entiende."""
    node = DetectIntentNode()
    
    with patch('nodes.call_llm') as mock:
        mock.return_value = "invalid response"
        
        result = node.run(mock_shared)
        
        assert result == "fallback"
```

## Test de Utility

```python
# tests/test_utils.py
from utils.gsheets_api import append_row, get_all_records

@patch('utils.gsheets_api.gc')
def test_append_row(mock_gc):
    """Test append row."""
    # Setup mock
    mock_sheet = MagicMock()
    mock_gc.open.return_value.sheet1 = mock_sheet
    
    # Call
    result = append_row(["2024-01-01", 5000, "comida", "almuerzo", "Juan", "Gasto"])
    
    # Assert
    assert result is True
    mock_sheet.append_row.assert_called_once()

def test_get_all_records_empty():
    """Test cuando no hay records."""
    with patch('utils.gsheets_api.gc') as mock_gc:
        mock_sheet = MagicMock()
        mock_sheet.get_all_records.return_value = []
        mock_gc.open.return_value.sheet1 = mock_sheet
        
        result = get_all_records()
        
        assert result == []
```

## Pytest Fixtures (conftest.py)

```python
# tests/conftest.py
import pytest
from unittest.mock import MagicMock, patch
import os

@pytest.fixture(autouse=True)
def mock_env():
    """Mock environment variables."""
    with patch.dict(os.environ, {
        'TELEGRAM_BOT_TOKEN': 'test_token',
        'GOOGLE_API_KEY': 'test_key',
        'ADMIN_CHAT_ID': '123456'
    }):
        yield

@pytest.fixture
def sample_expense():
    """Sample expense data."""
    return {
        "date": "2024-01-01",
        "amount": 5000,
        "category": "comida",
        "description": "almuerzo",
        "who": "Juan",
        "type": "Gasto"
    }

@pytest.fixture
def mock_gsheets():
    """Mock Google Sheets."""
    with patch('utils.gsheets_api.gc') as mock:
        yield mock
```

## Async Tests

```python
# tests/test_async.py
import pytest
import asyncio
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_send_message_async():
    """Test mensaje async."""
    with patch('utils.telegram_api.application') as mock_app:
        mock_app.bot.send_message = AsyncMock()
        
        from utils.telegram_api import send_message
        await send_message(123456, "Test message")
        
        mock_app.bot.send_message.assert_called_once()
```

## Mocks Comunes

```python
from unittest.mock import Mock, patch, MagicMock, AsyncMock

# Mock function
@patch('module.function_name')

# Mock class
@patch('module.ClassName')

# Mock async
@patch('module.async_function', new_callable=AsyncMock)

# Mock file
from unittest.mock import mock_open
@m.patch("builtins.open", mock_open(read_data="data"))
```

## Run Tests

```bash
# Run all tests
pytest

# Run specific file
pytest tests/test_nodes.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific marker
pytest -m "not integration"

# Verbose
pytest -v

# Stop on first failure
pytest -x
```

## Coverage

```ini
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --tb=short"

[tool.coverage.run]
source = ["."]
omit = ["venv/*", "tests/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if __name__ == .__main__.:",
    "raise NotImplementedError"
]
```

## Test-Driven Development (TDD)

1. **Red**: Escribir test que falla
2. **Green**: Escribir mínimo código para pasar
3. **Refactor**: Mejorar código manteniendo tests passing

## Tips

- Testear un behavior por test
- Nombres descriptivos: `test_node_crea_transaccion_cuando_intent_es_gasto`
- AAA: Arrange, Act, Assert
- Tests independientes (no dependen de orden)
- Mockear external services (API, LLM, Sheets)

## Resources

- **pytest docs**: https://docs.pytest.org/
- **unittest.mock**: https://docs.python.org/3/library/unittest.mock.html
- **pytest-cov**: https://pytest-cov.readthedocs.io/
