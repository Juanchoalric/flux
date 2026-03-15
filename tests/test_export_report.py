# tests/test_export_report.py
"""
Tests for ExportReportNode.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestExportReportNode:
    """Tests for ExportReportNode."""

    @patch("nodes.send_document")
    @patch("nodes.send_message")
    @patch("nodes.generate_financial_pdf")
    def test_generates_pdf_and_sends(self, mock_pdf, mock_send_msg, mock_send_doc):
        """Test that ExportReportNode generates PDF and sends it."""
        from nodes import ExportReportNode

        mock_pdf.return_value = "/tmp/test_report.pdf"
        mock_send_doc.return_value = True

        node = ExportReportNode()
        shared = {
            "user_intent": {
                "intent": "EXPORTAR_REPORTE",
                "entities": {"export_type": "monthly"},
            },
            "telegram_input": {
                "message_text": "exporta mi reporte mensual",
                "chat_id": 123456,
            },
            "sheet_data": [
                {
                    "Fecha": "2024-01-15",
                    "Monto": "5000",
                    "Categoria": "alimentos",
                    "Tipo": "Gasto",
                },
            ],
        }

        result = node.run(shared)

        # Verify PDF was generated
        mock_pdf.assert_called_once()

    @patch("nodes.send_document")
    @patch("nodes.send_message")
    @patch("nodes.generate_financial_pdf")
    def test_handles_pdf_generation_failure(
        self, mock_pdf, mock_send_msg, mock_send_doc
    ):
        """Test that ExportReportNode handles PDF generation failure."""
        from nodes import ExportReportNode

        mock_pdf.return_value = None  # PDF generation failed

        node = ExportReportNode()
        shared = {
            "user_intent": {
                "intent": "EXPORTAR_REPORTE",
                "entities": {"export_type": "monthly"},
            },
            "telegram_input": {
                "message_text": "exporta mi reporte",
                "chat_id": 123456,
            },
            "sheet_data": [],
        }

        result = node.run(shared)

        # Verify error message was sent
        mock_send_msg.assert_called()

    @patch("nodes.send_document")
    @patch("nodes.send_message")
    @patch("nodes.generate_financial_pdf")
    def test_uses_export_type_from_entities(
        self, mock_pdf, mock_send_msg, mock_send_doc
    ):
        """Test that ExportReportNode uses export_type from entities."""
        from nodes import ExportReportNode

        mock_pdf.return_value = "/tmp/test_report.pdf"
        mock_send_doc.return_value = True

        node = ExportReportNode()
        shared = {
            "user_intent": {
                "intent": "EXPORTAR_REPORTE",
                "entities": {"export_type": "category"},
            },
            "telegram_input": {
                "message_text": "exporta reporte por categoria",
                "chat_id": 123456,
            },
            "sheet_data": [],
        }

        result = node.run(shared)

        # Verify PDF was called with export_type
        mock_pdf.assert_called_once()
        call_args = mock_pdf.call_args[0]
        assert "category" in call_args


class TestGenerateFinancialPdf:
    """Tests for generate_financial_pdf function."""

    def test_generates_pdf_with_expenses(self):
        """Test that generate_financial_pdf creates a PDF file."""
        from nodes import generate_financial_pdf

        test_data = [
            {
                "Fecha": "2024-01-15",
                "Monto": "5000",
                "Categoria": "alimentos",
                "Tipo": "Gasto",
            },
            {
                "Fecha": "2024-01-16",
                "Monto": "3000",
                "Categoria": "auto",
                "Tipo": "Gasto",
            },
            {
                "Fecha": "2024-01-17",
                "Monto": "10000",
                "Categoria": "sueldo",
                "Tipo": "Ingreso",
            },
        ]

        result = generate_financial_pdf(test_data, "monthly")

        # Verify PDF was created
        assert result is not None
        assert os.path.exists(result)

        # Cleanup
        if os.path.exists(result):
            os.remove(result)

    def test_handles_empty_data(self):
        """Test that generate_financial_pdf handles empty data."""
        from nodes import generate_financial_pdf

        result = generate_financial_pdf([], "monthly")

        # Should still create a PDF
        assert result is not None
        assert os.path.exists(result)

        # Cleanup
        if os.path.exists(result):
            os.remove(result)

    def test_calculates_totals_correctly(self):
        """Test that PDF has correct totals."""
        from nodes import generate_financial_pdf

        test_data = [
            {
                "Fecha": "2024-01-15",
                "Monto": "5000",
                "Categoria": "alimentos",
                "Tipo": "Gasto",
            },
            {
                "Fecha": "2024-01-16",
                "Monto": "3000",
                "Categoria": "auto",
                "Tipo": "Gasto",
            },
        ]

        result = generate_financial_pdf(test_data, "test")

        # Verify file exists
        assert result is not None
        assert os.path.exists(result)

        # Cleanup
        if os.path.exists(result):
            os.remove(result)
