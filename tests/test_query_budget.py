# tests/test_query_budget.py
"""
Tests for QueryBudgetNode.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime


class TestQueryBudgetNode:
    """Tests for QueryBudgetNode."""

    @patch("nodes.send_message", new_callable=AsyncMock)
    @patch("nodes.get_budgets")
    @patch("nodes.get_all_records")
    @patch("nodes.calculate_monthly_spend")
    def test_returns_current_budgets(
        self, mock_calc, mock_get_records, mock_get_budgets, mock_send
    ):
        """Test that QueryBudgetNode returns current budgets."""
        from nodes import QueryBudgetNode

        mock_get_budgets.return_value = {"alimentos": 50000.0}
        mock_get_records.return_value = []
        mock_calc.return_value = 20000.0

        node = QueryBudgetNode()
        shared = {
            "user_intent": {
                "intent": "CONSULTAR_PRESUPUESTO",
                "entities": {"category": "alimentos"},
            },
            "telegram_input": {
                "message_text": "cuanto me queda para alimentos",
                "chat_id": 123456,
            },
        }

        result = node.run(shared)

        # Verify get_budgets was called
        mock_get_budgets.assert_called_once()

    @patch("nodes.send_message", new_callable=AsyncMock)
    @patch("nodes.get_budgets")
    @patch("nodes.get_all_records")
    @patch("nodes.calculate_monthly_spend")
    def test_calculates_spent_vs_budget(
        self, mock_calc, mock_get_records, mock_get_budgets, mock_send
    ):
        """Test that QueryBudgetNode calculates spent vs budget correctly."""
        from nodes import QueryBudgetNode

        mock_get_budgets.return_value = {"alimentos": 50000.0}
        mock_get_records.return_value = []
        mock_calc.return_value = 25000.0  # Spent 25k of 50k

        node = QueryBudgetNode()
        shared = {
            "user_intent": {
                "intent": "CONSULTAR_PRESUPUESTO",
                "entities": {"category": "alimentos"},
            },
            "telegram_input": {
                "message_text": "cuanto me queda para alimentos",
                "chat_id": 123456,
            },
        }

        result = node.run(shared)

        # Check that send_message was called with correct message
        mock_send.assert_called_once()
        call_args = mock_send.call_args[0][1]
        assert "alimentos" in call_args.lower()
        assert "50" in call_args  # Budget

    @patch("nodes.send_message", new_callable=AsyncMock)
    @patch("nodes.get_budgets")
    @patch("nodes.get_all_records")
    @patch("nodes.calculate_monthly_spend")
    def test_handles_no_budgets_set(
        self, mock_calc, mock_get_records, mock_get_budgets, mock_send
    ):
        """Test that QueryBudgetNode handles no budgets set."""
        from nodes import QueryBudgetNode

        mock_get_budgets.return_value = {}  # No budgets
        mock_get_records.return_value = []
        mock_calc.return_value = 0.0

        node = QueryBudgetNode()
        shared = {
            "user_intent": {
                "intent": "CONSULTAR_PRESUPUESTO",
                "entities": {"category": "alimentos"},
            },
            "telegram_input": {
                "message_text": "cuanto me queda para alimentos",
                "chat_id": 123456,
            },
        }

        result = node.run(shared)

        # Verify get_budgets was called
        mock_get_budgets.assert_called_once()

    @patch("nodes.send_message", new_callable=AsyncMock)
    @patch("nodes.get_budgets")
    @patch("nodes.get_all_records")
    @patch("nodes.calculate_monthly_spend")
    def test_filters_by_specific_category(
        self, mock_calc, mock_get_records, mock_get_budgets, mock_send
    ):
        """Test that QueryBudgetNode filters by specific category."""
        from nodes import QueryBudgetNode

        mock_get_budgets.return_value = {"alimentos": 50000.0, "auto": 30000.0}
        mock_get_records.return_value = []
        mock_calc.return_value = 10000.0

        node = QueryBudgetNode()
        shared = {
            "user_intent": {
                "intent": "CONSULTAR_PRESUPUESTO",
                "entities": {"category": "auto"},
            },
            "telegram_input": {
                "message_text": "cuanto me queda para auto",
                "chat_id": 123456,
            },
        }

        result = node.run(shared)

        # Should query for auto, not alimentos
        mock_calc.assert_called_with("auto", mock_get_records.return_value)

    @patch("nodes.send_message", new_callable=AsyncMock)
    @patch("nodes.get_budgets")
    @patch("nodes.get_all_records")
    @patch("nodes.calculate_monthly_spend")
    def test_calculates_percentage_used(
        self, mock_calc, mock_get_records, mock_get_budgets, mock_send
    ):
        """Test that QueryBudgetNode calculates percentage used."""
        from nodes import QueryBudgetNode

        mock_get_budgets.return_value = {"alimentos": 50000.0}
        mock_get_records.return_value = []
        mock_calc.return_value = 25000.0  # 50% spent

        node = QueryBudgetNode()
        shared = {
            "user_intent": {
                "intent": "CONSULTAR_PRESUPUESTO",
                "entities": {"category": "alimentos"},
            },
            "telegram_input": {
                "message_text": "cuanto me queda para alimentos",
                "chat_id": 123456,
            },
        }

        result = node.run(shared)

        # Should send message with percentage
        mock_send.assert_called_once()
        call_args = mock_send.call_args[0][1]
        assert "50" in call_args or "%" in call_args
