# tests/test_delete_last.py
"""
Tests for DeleteLastExpenseNode.
"""

import pytest
from unittest.mock import patch, AsyncMock


class TestDeleteLastExpenseNode:
    """Tests for DeleteLastExpenseNode."""

    @patch("nodes.send_message", new_callable=AsyncMock)
    @patch("nodes.find_last_row_by_user")
    @patch("nodes.delete_row")
    def test_finds_users_last_expense(self, mock_delete, mock_find, mock_send):
        """Test that DeleteLastExpenseNode finds user's last expense."""
        from nodes import DeleteLastExpenseNode

        mock_find.return_value = {
            "row_number": 5,
            "data": {"Descripcion": "supermercado", "Monto": "5000"},
        }
        mock_delete.return_value = True

        node = DeleteLastExpenseNode()
        shared = {
            "telegram_input": {
                "message_text": "borra el ultimo gasto",
                "user_name": "Juan",
                "chat_id": 123456,
            },
        }

        result = node.run(shared)

        # Verify find_last_row_by_user was called
        mock_find.assert_called_once_with("Juan")

    @patch("nodes.send_message", new_callable=AsyncMock)
    @patch("nodes.find_last_row_by_user")
    @patch("nodes.delete_row")
    def test_deletes_row_successfully(self, mock_delete, mock_find, mock_send):
        """Test that DeleteLastExpenseNode deletes row successfully."""
        from nodes import DeleteLastExpenseNode

        mock_find.return_value = {
            "row_number": 5,
            "data": {"Descripcion": "supermercado", "Monto": "5000"},
        }
        mock_delete.return_value = True

        node = DeleteLastExpenseNode()
        shared = {
            "telegram_input": {
                "message_text": "borra el ultimo gasto",
                "user_name": "Juan",
                "chat_id": 123456,
            },
        }

        result = node.run(shared)

        # Verify delete_row was called with row number
        mock_delete.assert_called_once_with(5)

    @patch("nodes.send_message", new_callable=AsyncMock)
    @patch("nodes.find_last_row_by_user")
    @patch("nodes.delete_row")
    def test_handles_no_expenses_found(self, mock_delete, mock_find, mock_send):
        """Test that DeleteLastExpenseNode handles no expenses found."""
        from nodes import DeleteLastExpenseNode

        mock_find.return_value = None  # No expenses found

        node = DeleteLastExpenseNode()
        shared = {
            "telegram_input": {
                "message_text": "borra el ultimo gasto",
                "user_name": "Juan",
                "chat_id": 123456,
            },
        }

        result = node.run(shared)

        # Verify find was called
        mock_find.assert_called_once()

    @patch("nodes.send_message", new_callable=AsyncMock)
    @patch("nodes.find_last_row_by_user")
    @patch("nodes.delete_row")
    def test_sends_confirmation(self, mock_delete, mock_find, mock_send):
        """Test that DeleteLastExpenseNode sends confirmation."""
        from nodes import DeleteLastExpenseNode

        mock_find.return_value = {
            "row_number": 5,
            "data": {"Descripcion": "supermercado", "Monto": "5000"},
        }
        mock_delete.return_value = True

        node = DeleteLastExpenseNode()
        shared = {
            "telegram_input": {
                "message_text": "borra el ultimo gasto",
                "user_name": "Juan",
                "chat_id": 123456,
            },
        }

        result = node.run(shared)

        # Verify send_message was called
        mock_send.assert_called_once()
