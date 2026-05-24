# tests/test_integration.py
"""
Integration tests for node flows.
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock


class TestExpenseRegistrationFlow:
    """Integration tests for expense registration flow."""

    @patch("nodes.call_llm")
    @patch("nodes.append_row")
    @patch("nodes.send_message", new_callable=AsyncMock)
    @patch("nodes.get_budgets")
    @patch("nodes.get_all_records")
    def test_detect_intent_flow(
        self, mock_get_all, mock_get_budgets, mock_send, mock_append, mock_llm
    ):
        """Test detect intent flow."""
        from nodes import DetectIntentNode

        # Setup mocks
        mock_llm.return_value = json.dumps(
            {
                "intent": "REGISTRAR_GASTO",
                "entities": {"amount": 5000, "category": "alimentos", "date": "today"},
            }
        )

        # Detect Intent
        detect_node = DetectIntentNode()
        shared = {
            "telegram_input": {
                "message_text": "gasté 5000 en alimentos",
                "user_name": "Juan",
                "chat_id": 123456,
            },
            "valid_categories": ["alimentos", "auto", "otros"],
        }
        detect_result = detect_node.run(shared)

        # Verify intent was detected
        assert shared.get("user_intent", {}).get("intent") == "REGISTRAR_GASTO"

    @patch("nodes.call_llm")
    @patch("nodes.append_row")
    @patch("nodes.send_message", new_callable=AsyncMock)
    @patch("nodes.get_budgets")
    @patch("nodes.get_all_records")
    def test_expense_with_budget_triggers_alert(
        self, mock_get_all, mock_get_budgets, mock_send, mock_append, mock_llm
    ):
        """Test that expense over budget triggers alert."""
        from nodes import ProcessTransactionBatchNode
        from datetime import datetime

        # Setup: budget is 5000, already spent 4500 (90%)
        mock_get_budgets.return_value = {"alimentos": 5000.0}
        mock_get_all.return_value = [
            {
                "Fecha": datetime.now().strftime("%Y-%m-01"),
                "Monto": "4500",
                "Categoria": "alimentos",
                "Tipo": "Gasto",
            }
        ]
        mock_append.return_value = True

        node = ProcessTransactionBatchNode()
        shared = {
            "parsed_transactions": [
                {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "amount": 1000,
                    "category": "alimentos",
                    "description": "test",
                    "who": "Juan",
                    "type": "Gasto",
                    "chat_id": 123456,
                }
            ]
        }

        result = node.run(shared)

        # Should trigger budget alert (send_message called)
        assert mock_send.call_count >= 1


class TestBudgetFlow:
    """Integration tests for budget management flow."""

    @patch("nodes.call_llm")
    @patch("nodes.set_budget")
    @patch("nodes.send_message", new_callable=AsyncMock)
    def test_set_budget_flow(self, mock_send, mock_set_budget, mock_llm):
        """Test set budget flow."""
        from nodes import ParseBudgetNode, SetBudgetNode

        # Setup mocks
        mock_set_budget.return_value = True
        mock_llm.return_value = json.dumps({"category": "alimentos", "amount": "50000"})

        # Step 1: Parse Budget
        parse_node = ParseBudgetNode()
        shared = {
            "telegram_input": {
                "message_text": "fijar presupuesto de 50000 para alimentos",
                "chat_id": 123456,
            },
        }
        parse_result = parse_node.run(shared)

        assert "budget_details" in shared

        # Step 2: Set Budget
        set_node = SetBudgetNode()
        set_result = set_node.run(shared)

        mock_set_budget.assert_called_once_with("Alimentos", 50000.0)

    @patch("nodes.get_all_records")
    @patch("nodes.send_message", new_callable=AsyncMock)
    @patch("nodes.get_budgets")
    @patch("nodes.calculate_monthly_spend")
    def test_query_budget_flow(
        self, mock_calc, mock_get_budgets, mock_send, mock_get_records
    ):
        """Test query budget flow."""
        from nodes import QueryBudgetNode

        mock_get_budgets.return_value = {"alimentos": 50000.0}
        mock_get_records.return_value = []
        mock_calc.return_value = 25000.0

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

        # Should complete successfully
        mock_get_budgets.assert_called()


class TestQueryFlow:
    """Integration tests for query flows."""

    @patch("nodes.get_all_records")
    @patch("nodes.send_message", new_callable=AsyncMock)
    def test_query_expenses_by_category_flow(self, mock_send, mock_get_records):
        """Test query expenses by category flow."""
        from nodes import QueryExpensesByCategoryNode

        mock_get_records.return_value = [
            {
                "Fecha": "2024-01-15",
                "Monto": "5000",
                "Categoria": "alimentos",
                "Tipo": "Gasto",
            },
            {
                "Fecha": "2024-01-16",
                "Monto": "3000",
                "Categoria": "alimentos",
                "Tipo": "Gasto",
            },
        ]

        node = QueryExpensesByCategoryNode()
        shared = {
            "user_intent": {
                "intent": "CONSULTAR_POR_CATEGORIA",
                "entities": {
                    "categories": ["alimentos"],
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                },
            },
            "telegram_input": {
                "message_text": "cuanto gasté en alimentos",
                "chat_id": 123456,
            },
        }

        result = node.run(shared)

        # Should have called get_all_records
        mock_get_records.assert_called()


class TestCategoryManagementFlow:
    """Integration tests for category management."""

    @patch("nodes.call_llm")
    @patch("nodes.add_category")
    @patch("nodes.send_message", new_callable=AsyncMock)
    def test_add_category_flow(self, mock_send, mock_add, mock_llm):
        """Test adding a new category."""
        from nodes import AddCategoryNode

        mock_llm.return_value = json.dumps({"category_names": ["gimnasio"]})
        mock_add.return_value = True

        node = AddCategoryNode()
        shared = {
            "telegram_input": {
                "message_text": "agrega la categoria gimnasio",
                "chat_id": 123456,
            },
        }

        result = node.run(shared)

        # Verify category was added
        mock_add.assert_called_once_with("gimnasio")


class TestEditDeleteFlow:
    """Integration tests for edit/delete flows."""

    @patch("nodes.find_last_row_by_user")
    @patch("nodes.delete_row")
    @patch("nodes.send_message", new_callable=AsyncMock)
    def test_delete_last_expense_flow(self, mock_send, mock_delete, mock_find):
        """Test deleting last expense."""
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

        # Verify delete was called
        mock_delete.assert_called_once_with(5)

    @patch("nodes.call_llm")
    @patch("nodes.find_last_row_by_user")
    @patch("nodes.update_row")
    @patch("nodes.send_message", new_callable=AsyncMock)
    def test_edit_last_expense_flow(self, mock_send, mock_update, mock_find, mock_llm):
        """Test editing last expense."""
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
                "message_text": "el ultimo gasto era 4500",
                "user_name": "Juan",
                "chat_id": 123456,
            },
            "valid_categories": ["alimentos", "auto", "otros"],
        }

        result = node.run(shared)

        # Verify update was called
        mock_update.assert_called_once()
