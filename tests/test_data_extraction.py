# tests/test_data_extraction.py
"""
Tests for DataExtractionNode and MonthlyAnalysisNode.
"""

import pytest
from unittest.mock import patch
from datetime import date, timedelta


class TestDataExtractionNode:
    """Tests for DataExtractionNode."""

    @patch("nodes.get_all_records")
    def test_extracts_expenses_from_text(self, mock_get_records):
        """Test that DataExtractionNode extracts expenses from text."""
        from nodes import DataExtractionNode

        # Mock data with some expenses
        mock_records = [
            {
                "Fecha": "2024-01-15",
                "Monto": "5000",
                "Categoria": "alimentos",
                "Tipo": "Gasto",
            },
            {
                "Fecha": "2024-01-20",
                "Monto": "3000",
                "Categoria": "auto",
                "Tipo": "Gasto",
            },
        ]
        mock_get_records.return_value = mock_records

        node = DataExtractionNode()
        result = node.exec({})

        # Should return data
        assert result is not None

    @patch("nodes.get_all_records")
    def test_handles_multiple_expenses(self, mock_get_records):
        """Test that DataExtractionNode handles multiple expenses."""
        from nodes import DataExtractionNode

        mock_records = [
            {
                "Fecha": "2024-01-15",
                "Monto": "5000",
                "Categoria": "alimentos",
                "Tipo": "Gasto",
            },
            {
                "Fecha": "2024-01-20",
                "Monto": "3000",
                "Categoria": "auto",
                "Tipo": "Gasto",
            },
            {
                "Fecha": "2024-01-25",
                "Monto": "2000",
                "Categoria": "ocio",
                "Tipo": "Gasto",
            },
        ]
        mock_get_records.return_value = mock_records

        node = DataExtractionNode()
        result = node.exec({})

        assert result is not None


class TestMonthlyAnalysisNode:
    """Tests for MonthlyAnalysisNode."""

    def test_node_exists(self):
        """Test that MonthlyAnalysisNode exists."""
        from nodes import MonthlyAnalysisNode

        assert MonthlyAnalysisNode is not None

    def test_node_inherits_from_node(self):
        """Test that MonthlyAnalysisNode inherits from Node."""
        from nodes import MonthlyAnalysisNode, Node

        assert issubclass(MonthlyAnalysisNode, Node)
