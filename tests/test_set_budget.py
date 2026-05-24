# tests/test_set_budget.py
"""
Tests for SetBudgetNode.
"""

import pytest
from unittest.mock import patch, AsyncMock


class TestSetBudgetNode:
    """Tests for SetBudgetNode."""

    @patch("nodes.send_message", new_callable=AsyncMock)
    @patch("nodes.set_budget")
    def test_sets_new_budget(self, mock_set_budget, mock_send):
        """Test that SetBudgetNode sets a new budget."""
        from nodes import SetBudgetNode

        mock_set_budget.return_value = True

        node = SetBudgetNode()
        shared = {
            "budget_details": {
                "category": "alimentos",
                "amount": "50000",
            },
            "telegram_input": {
                "message_text": "fijar presupuesto de 50000 para alimentos",
                "chat_id": 123456,
            },
        }

        result = node.run(shared)

        # Verify set_budget was called
        mock_set_budget.assert_called_once_with("Alimentos", 50000.0)

    @patch("nodes.send_message", new_callable=AsyncMock)
    @patch("nodes.set_budget")
    def test_updates_existing_budget(self, mock_set_budget, mock_send):
        """Test that SetBudgetNode updates an existing budget."""
        from nodes import SetBudgetNode

        mock_set_budget.return_value = True

        node = SetBudgetNode()
        shared = {
            "budget_details": {
                "category": "alimentos",
                "amount": "75000",
            },
            "telegram_input": {
                "message_text": "cambiar presupuesto de alimentos a 75000",
                "chat_id": 123456,
            },
        }

        result = node.run(shared)

        # Should call set_budget with new amount
        mock_set_budget.assert_called_once()

    @patch("nodes.send_message", new_callable=AsyncMock)
    @patch("nodes.set_budget")
    def test_validates_amount_format(self, mock_set_budget, mock_send):
        """Test that SetBudgetNode validates amount format."""
        from nodes import SetBudgetNode

        mock_set_budget.return_value = True

        node = SetBudgetNode()
        shared = {
            "budget_details": {
                "category": "ocio",
                "amount": "25000.50",
            },
            "telegram_input": {
                "message_text": "presupuesto de 25000.50 para ocio",
                "chat_id": 123456,
            },
        }

        result = node.run(shared)

        # Should convert to float correctly
        mock_set_budget.assert_called_with("Ocio", 25000.50)

    @patch("nodes.send_message", new_callable=AsyncMock)
    @patch("nodes.set_budget")
    def test_sends_success_message(self, mock_set_budget, mock_send):
        """Test that SetBudgetNode sends success message."""
        from nodes import SetBudgetNode

        mock_set_budget.return_value = True

        node = SetBudgetNode()
        shared = {
            "budget_details": {
                "category": "ropa",
                "amount": "30000",
            },
            "telegram_input": {
                "message_text": "presupuesto de 30000 para ropa",
                "chat_id": 123456,
            },
        }

        result = node.run(shared)

        # Should send confirmation message
        mock_send.assert_called_once()
