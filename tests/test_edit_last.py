# tests/test_edit_last.py
"""
Tests for EditLastExpenseNode.
"""

import pytest
import json
from unittest.mock import patch


class TestEditLastExpenseNode:
    """Tests for EditLastExpenseNode."""

    @patch("nodes.send_message")
    @patch("nodes.call_llm")
    @patch("nodes.find_last_row_by_user")
    @patch("nodes.update_row")
    def test_finds_last_expense(self, mock_update, mock_find, mock_llm, mock_send):
        """Test that EditLastExpenseNode finds last expense."""
        from nodes import EditLastExpenseNode

        mock_find.return_value = {
            "row_number": 5,
            "data": {"Descripcion": "supermercado", "Monto": "5000"},
        }
        mock_llm.return_value = json.dumps({"amount": "4500"})

        node = EditLastExpenseNode()
        shared = {
            "telegram_input": {
                "message_text": "el ultimo gasto no era 5000, eran 4500",
                "user_name": "Juan",
                "chat_id": 123456,
            },
            "valid_categories": ["alimentos", "auto", "otros"],
        }

        result = node.run(shared)

        # Verify find_last_row_by_user was called
        mock_find.assert_called_once_with("Juan")

    @patch("nodes.send_message")
    @patch("nodes.call_llm")
    @patch("nodes.find_last_row_by_user")
    @patch("nodes.update_row")
    def test_updates_amount_field(self, mock_update, mock_find, mock_llm, mock_send):
        """Test that EditLastExpenseNode updates amount field."""
        from nodes import EditLastExpenseNode

        mock_find.return_value = {
            "row_number": 5,
            "data": {"Descripcion": "supermercado", "Monto": "5000"},
        }
        mock_llm.return_value = json.dumps({"amount": "4500"})
        mock_update.return_value = True

        node = EditLastExpenseNode()
        shared = {
            "telegram_input": {
                "message_text": "el ultimo gasto no era 5000, eran 4500",
                "user_name": "Juan",
                "chat_id": 123456,
            },
            "valid_categories": ["alimentos", "auto", "otros"],
        }

        result = node.run(shared)

        # Verify update_row was called
        mock_update.assert_called_once()

    @patch("nodes.send_message")
    @patch("nodes.call_llm")
    @patch("nodes.find_last_row_by_user")
    @patch("nodes.update_row")
    def test_updates_category_field(self, mock_update, mock_find, mock_llm, mock_send):
        """Test that EditLastExpenseNode updates category field."""
        from nodes import EditLastExpenseNode

        mock_find.return_value = {
            "row_number": 5,
            "data": {
                "Descripcion": "supermercado",
                "Monto": "5000",
                "Categoria": "alimentos",
            },
        }
        mock_llm.return_value = json.dumps({"amount": "5000", "category": "auto"})
        mock_update.return_value = True

        node = EditLastExpenseNode()
        shared = {
            "telegram_input": {
                "message_text": "cambia la categoria del ultimo gasto a auto",
                "user_name": "Juan",
                "chat_id": 123456,
            },
            "valid_categories": ["alimentos", "auto", "otros"],
        }

        result = node.run(shared)

        # Verify update_row was called
        mock_update.assert_called_once()

    @patch("nodes.send_message")
    @patch("nodes.call_llm")
    @patch("nodes.find_last_row_by_user")
    @patch("nodes.update_row")
    def test_handles_empty_edit_request(
        self, mock_update, mock_find, mock_llm, mock_send
    ):
        """Test that EditLastExpenseNode handles empty edit request."""
        from nodes import EditLastExpenseNode

        mock_find.return_value = {
            "row_number": 5,
            "data": {"Descripcion": "supermercado", "Monto": "5000"},
        }
        mock_llm.return_value = json.dumps({})  # Empty request

        node = EditLastExpenseNode()
        shared = {
            "telegram_input": {
                "message_text": "edita el ultimo gasto",
                "user_name": "Juan",
                "chat_id": 123456,
            },
            "valid_categories": ["alimentos", "auto", "otros"],
        }

        result = node.run(shared)

        # Should still call LLM
        mock_llm.assert_called_once()

    @patch("nodes.send_message")
    @patch("nodes.call_llm")
    @patch("nodes.find_last_row_by_user")
    @patch("nodes.update_row")
    def test_sends_confirmation(self, mock_update, mock_find, mock_llm, mock_send):
        """Test that EditLastExpenseNode sends confirmation."""
        from nodes import EditLastExpenseNode

        mock_find.return_value = {
            "row_number": 5,
            "data": {"Descripcion": "supermercado", "Monto": "5000"},
        }
        mock_llm.return_value = json.dumps({"amount": "4500"})
        mock_update.return_value = True

        node = EditLastExpenseNode()
        shared = {
            "telegram_input": {
                "message_text": "el ultimo gasto no era 5000, eran 4500",
                "user_name": "Juan",
                "chat_id": 123456,
            },
            "valid_categories": ["alimentos", "auto", "otros"],
        }

        result = node.run(shared)

        # Verify send_message was called
        mock_send.assert_called_once()
