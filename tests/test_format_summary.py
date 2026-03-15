# tests/test_format_summary.py
"""
Tests for FormatSummaryNode.
"""

import pytest
from unittest.mock import patch
from datetime import datetime


class TestFormatSummaryNode:
    """Tests for FormatSummaryNode."""

    def test_formats_total_expenses(self):
        """Test that FormatSummaryNode formats total expenses correctly."""
        from nodes import FormatSummaryNode

        node = FormatSummaryNode()
        # Don't use run() - test the exec method directly
        prep_data = {
            "records": [
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
                    "Monto": "10000",
                    "Categoria": "Ingreso",
                    "Tipo": "Ingreso",
                },
            ],
            "intent": {
                "intent": "CONSULTAR_GASTOS",
                "entities": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
            },
        }

        result = node.exec(prep_data)

        # Should contain expense total (formatted with comma)
        assert "8,000" in result or "8000" in result

    def test_breaks_down_by_category(self):
        """Test that FormatSummaryNode breaks down expenses by category."""
        from nodes import FormatSummaryNode

        node = FormatSummaryNode()
        prep_data = {
            "records": [
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
                {
                    "Fecha": "2024-01-03",
                    "Monto": "2000",
                    "Categoria": "auto",
                    "Tipo": "Gasto",
                },
            ],
            "intent": {
                "intent": "CONSULTAR_GASTOS",
                "entities": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
            },
        }

        result = node.exec(prep_data)

        # Should show category breakdown
        assert "alimentos" in result.lower()

    def test_shows_top_spending_categories(self):
        """Test that FormatSummaryNode shows top spending categories."""
        from nodes import FormatSummaryNode

        node = FormatSummaryNode()
        prep_data = {
            "records": [
                {
                    "Fecha": "2024-01-01",
                    "Monto": "5000",
                    "Categoria": "alimentos",
                    "Tipo": "Gasto",
                },
                {
                    "Fecha": "2024-01-02",
                    "Monto": "8000",
                    "Categoria": "auto",
                    "Tipo": "Gasto",
                },
                {
                    "Fecha": "2024-01-03",
                    "Monto": "1000",
                    "Categoria": "ocio",
                    "Tipo": "Gasto",
                },
            ],
            "intent": {
                "intent": "CONSULTAR_GASTOS",
                "entities": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
            },
        }

        result = node.exec(prep_data)

        # Should show top spending categories
        assert "auto" in result.lower()

    def test_includes_budget_status(self):
        """Test that FormatSummaryNode includes budget status."""
        from nodes import FormatSummaryNode

        node = FormatSummaryNode()
        prep_data = {
            "records": [
                {
                    "Fecha": "2024-01-01",
                    "Monto": "5000",
                    "Categoria": "alimentos",
                    "Tipo": "Gasto",
                },
            ],
            "intent": {
                "intent": "CONSULTAR_GASTOS",
                "entities": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
            },
        }

        result = node.exec(prep_data)

        # Should contain summary text
        assert "resumen" in result.lower() or "gastado" in result.lower()

    def test_handles_empty_records(self):
        """Test that FormatSummaryNode handles empty records."""
        from nodes import FormatSummaryNode

        node = FormatSummaryNode()
        prep_data = {
            "records": [],
            "intent": {
                "intent": "CONSULTAR_GASTOS",
                "entities": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
            },
        }

        result = node.exec(prep_data)

        # Should indicate no transactions
        assert (
            "no tienes transacciones" in result.lower()
            or "no se encontraron" in result.lower()
        )

    def test_formats_currency_correctly(self):
        """Test that FormatSummaryNode formats currency correctly."""
        from nodes import FormatSummaryNode

        node = FormatSummaryNode()
        prep_data = {
            "records": [
                {
                    "Fecha": "2024-01-01",
                    "Monto": "1234.56",
                    "Categoria": "alimentos",
                    "Tipo": "Gasto",
                },
            ],
            "intent": {
                "intent": "CONSULTAR_GASTOS",
                "entities": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
            },
        }

        result = node.exec(prep_data)

        # Should format number - it uses format with comma
        assert "1,234" in result or "1234" in result
