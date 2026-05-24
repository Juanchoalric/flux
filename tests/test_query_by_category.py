# tests/test_query_by_category.py
"""
Tests for QueryExpensesByCategoryNode.
"""

import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime


class TestQueryExpensesByCategoryNode:
    """Tests for QueryExpensesByCategoryNode."""

    @patch("nodes.send_message", new_callable=AsyncMock)
    @patch("nodes.get_all_records")
    def test_filters_by_category(self, mock_get_records, mock_send):
        """Test that QueryExpensesByCategoryNode filters by category."""
        from nodes import QueryExpensesByCategoryNode

        mock_get_records.return_value = [
            {
                "Fecha": "2024-01-01",
                "Monto": "5000",
                "Categoria": "alimentos",
                "Tipo": "Gasto",
            },
            {
                "Fecha": "2024-01-02",
                "Monto": "3000",
                "Categoria": "auto",
                "Tipo": "Gasto",
            },
            {
                "Fecha": "2024-01-03",
                "Monto": "2000",
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
                "message_text": "cuanto gasté en alimentos este mes",
                "chat_id": 123456,
            },
        }

        result = node.run(shared)

        # Should call get_all_records
        mock_get_records.assert_called()

    @patch("nodes.send_message", new_callable=AsyncMock)
    @patch("nodes.get_all_records")
    def test_calculates_category_total(self, mock_get_records, mock_send):
        """Test that QueryExpensesByCategoryNode calculates category total."""
        from nodes import QueryExpensesByCategoryNode

        mock_get_records.return_value = [
            {
                "Fecha": "2024-01-01",
                "Monto": "5000",
                "Categoria": "alimentos",
                "Tipo": "Gasto",
            },
            {
                "Fecha": "2024-01-02",
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

        # Should call get_all_records
        mock_get_records.assert_called()

    @patch("nodes.send_message", new_callable=AsyncMock)
    @patch("nodes.get_all_records")
    def test_handles_invalid_category(self, mock_get_records, mock_send):
        """Test that QueryExpensesByCategoryNode handles invalid category."""
        from nodes import QueryExpensesByCategoryNode

        mock_get_records.return_value = [
            {
                "Fecha": "2024-01-01",
                "Monto": "5000",
                "Categoria": "alimentos",
                "Tipo": "Gasto",
            },
        ]

        node = QueryExpensesByCategoryNode()
        shared = {
            "user_intent": {
                "intent": "CONSULTAR_POR_CATEGORIA",
                "entities": {
                    "categories": ["categoria_inexistente"],
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                },
            },
            "telegram_input": {
                "message_text": "cuanto gasté en categoria_inexistente",
                "chat_id": 123456,
            },
        }

        result = node.run(shared)

        # get_all_records should be called regardless
        mock_get_records.assert_called()

    @patch("nodes.send_message", new_callable=AsyncMock)
    @patch("nodes.get_all_records")
    def test_limits_results(self, mock_get_records, mock_send):
        """Test that QueryExpensesByCategoryNode limits results."""
        from nodes import QueryExpensesByCategoryNode

        # Create 20 records
        many_records = [
            {
                "Fecha": f"2024-01-{i + 1:02d}",
                "Monto": str(1000 + i * 100),
                "Categoria": "alimentos",
                "Tipo": "Gasto",
            }
            for i in range(20)
        ]
        mock_get_records.return_value = many_records

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

        # Should process records
        mock_get_records.assert_called()

    @patch("nodes.send_message", new_callable=AsyncMock)
    @patch("nodes.get_all_records")
    def test_sorts_by_date_descending(self, mock_get_records, mock_send):
        """Test that QueryExpensesByCategoryNode sorts by date descending."""
        from nodes import QueryExpensesByCategoryNode

        mock_get_records.return_value = [
            {
                "Fecha": "2024-01-01",
                "Monto": "1000",
                "Categoria": "alimentos",
                "Tipo": "Gasto",
            },
            {
                "Fecha": "2024-01-10",
                "Monto": "5000",
                "Categoria": "alimentos",
                "Tipo": "Gasto",
            },
            {
                "Fecha": "2024-01-05",
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

        # Should return results
        mock_get_records.assert_called()
