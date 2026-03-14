# tests/test_nodes.py
"""
Tests para los nodes de PocketFlow.
"""

import pytest
import json
from unittest.mock import MagicMock, patch
from datetime import date, timedelta


class TestParseExpenseListNode:
    """Tests para ParseExpenseListNode."""

    @patch("nodes.call_llm")
    def test_parse_expense_with_date_yesterday(self, mock_call_llm, today_str):
        """Test que parsea un gasto con 'ayer' correctamente."""
        from nodes import ParseExpenseListNode

        yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

        # Mock del LLM retornando gasto con yesterday
        mock_call_llm.return_value = json.dumps(
            [
                {
                    "amount": 1000,
                    "category": "auto",
                    "description": "nafta",
                    "date": "yesterday",
                }
            ]
        )

        node = ParseExpenseListNode()
        shared = {
            "telegram_input": {
                "message_text": "ayer gaste 1000 en nafta",
                "user_name": "Juan",
                "chat_id": 123456,
            },
            "valid_categories": ["alimentos", "auto", "otros"],
        }

        result = node.run(shared)

        assert result == "default"
        assert len(shared["parsed_transactions"]) == 1
        assert shared["parsed_transactions"][0]["date"] == yesterday
        assert shared["parsed_transactions"][0]["amount"] == 1000
        assert shared["parsed_transactions"][0]["category"] == "auto"

    @patch("nodes.call_llm")
    def test_parse_expense_with_date_today(self, mock_call_llm, today_str):
        """Test que parsea un gasto sin fecha (today) correctamente."""
        from nodes import ParseExpenseListNode

        mock_call_llm.return_value = json.dumps(
            [
                {
                    "amount": 500,
                    "category": "alimentos",
                    "description": "supermercado",
                    "date": "today",
                }
            ]
        )

        node = ParseExpenseListNode()
        shared = {
            "telegram_input": {
                "message_text": "gaste 500 en super",
                "user_name": "Juan",
                "chat_id": 123456,
            },
            "valid_categories": ["alimentos", "auto", "otros"],
        }

        result = node.run(shared)

        assert result == "default"
        assert shared["parsed_transactions"][0]["date"] == today_str

    @patch("nodes.call_llm")
    def test_parse_expense_with_date_2daysago(self, mock_call_llm, today_str):
        """Test que parsea un gasto con 'anteayer' correctamente."""
        from nodes import ParseExpenseListNode

        two_days_ago = (date.today() - timedelta(days=2)).strftime("%Y-%m-%d")

        mock_call_llm.return_value = json.dumps(
            [
                {
                    "amount": 15000,
                    "category": "auto",
                    "description": "nafta",
                    "date": "2daysago",
                }
            ]
        )

        node = ParseExpenseListNode()
        shared = {
            "telegram_input": {
                "message_text": "anteayer cargue nafta por 15000",
                "user_name": "Juan",
                "chat_id": 123456,
            },
            "valid_categories": ["alimentos", "auto", "otros"],
        }

        result = node.run(shared)

        assert result == "default"
        assert shared["parsed_transactions"][0]["date"] == two_days_ago

    @patch("nodes.call_llm")
    def test_parse_expense_with_exact_date(self, mock_call_llm):
        """Test que parsea un gasto con fecha exacta."""
        from nodes import ParseExpenseListNode

        mock_call_llm.return_value = json.dumps(
            [
                {
                    "amount": 2000,
                    "category": "alimentos",
                    "description": "farmacia",
                    "date": "2024-01-10",
                }
            ]
        )

        node = ParseExpenseListNode()
        shared = {
            "telegram_input": {
                "message_text": "gaste 2000 en farmacia el 10 de enero",
                "user_name": "Juan",
                "chat_id": 123456,
            },
            "valid_categories": ["alimentos", "auto", "otros"],
        }

        result = node.run(shared)

        assert result == "default"
        assert shared["parsed_transactions"][0]["date"] == "2024-01-10"

    @patch("nodes.call_llm")
    def test_parse_multiple_expenses_with_different_dates(
        self, mock_call_llm, today_str
    ):
        """Test que parsea múltiples gastos con diferentes fechas."""
        from nodes import ParseExpenseListNode

        yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

        mock_call_llm.return_value = json.dumps(
            [
                {
                    "amount": 1000,
                    "category": "alimentos",
                    "description": "supermercado",
                    "date": "today",
                },
                {
                    "amount": 500,
                    "category": "auto",
                    "description": "nafta",
                    "date": "yesterday",
                },
            ]
        )

        node = ParseExpenseListNode()
        shared = {
            "telegram_input": {
                "message_text": "gaste 1000 en super y 500 en nafta ayer",
                "user_name": "Juan",
                "chat_id": 123456,
            },
            "valid_categories": ["alimentos", "auto", "otros"],
        }

        result = node.run(shared)

        assert result == "default"
        assert len(shared["parsed_transactions"]) == 2
        assert shared["parsed_transactions"][0]["date"] == today_str
        assert shared["parsed_transactions"][1]["date"] == yesterday

    @patch("nodes.call_llm")
    def test_invalid_json_returns_empty(self, mock_call_llm):
        """Test que retorna lista vacía cuando el LLM retorna JSON inválido."""
        from nodes import ParseExpenseListNode

        mock_call_llm.return_value = "invalid json response"

        node = ParseExpenseListNode()
        shared = {
            "telegram_input": {
                "message_text": "gaste 1000",
                "user_name": "Juan",
                "chat_id": 123456,
            },
            "valid_categories": ["alimentos", "auto", "otros"],
        }

        result = node.run(shared)

        assert shared["parsed_transactions"] == []


# Nota: Los tests de ProcessTransactionBatchNode requieren mocks más complejos
# porque usa asyncio internamente. La funcionalidad de fechas ya está probada
# en los tests de ParseExpenseListNode que son los que parsean la fecha.
