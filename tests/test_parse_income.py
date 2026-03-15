# tests/test_parse_income.py
"""
Tests for ParseIncomeNode.
"""

import pytest
import json
from unittest.mock import patch
from datetime import date


class TestParseIncomeNode:
    """Tests for ParseIncomeNode."""

    @patch("nodes.call_llm")
    def test_extracts_amount_correctly(self, mock_call_llm):
        """Test that ParseIncomeNode extracts amount correctly."""
        from nodes import ParseIncomeNode

        mock_call_llm.return_value = json.dumps(
            {
                "amount": 150000,
                "description": "sueldo",
            }
        )

        node = ParseIncomeNode()
        shared = {
            "telegram_input": {
                "message_text": "cobré 150000 de sueldo",
                "user_name": "Juan",
                "chat_id": 123456,
            },
        }

        result = node.run(shared)

        assert result == "default"
        assert len(shared["parsed_transactions"]) == 1
        assert shared["parsed_transactions"][0]["amount"] == 150000
        assert shared["parsed_transactions"][0]["type"] == "Ingreso"

    @patch("nodes.call_llm")
    def test_extracts_description(self, mock_call_llm):
        """Test that ParseIncomeNode extracts description correctly."""
        from nodes import ParseIncomeNode

        mock_call_llm.return_value = json.dumps(
            {
                "amount": 50000,
                "description": "freelance",
            }
        )

        node = ParseIncomeNode()
        shared = {
            "telegram_input": {
                "message_text": "me pagaron 50000 por freelance",
                "user_name": "Juan",
                "chat_id": 123456,
            },
        }

        result = node.run(shared)

        assert result == "default"
        assert shared["parsed_transactions"][0]["description"] == "freelance"

    @patch("nodes.call_llm")
    def test_uses_today_if_no_date(self, mock_call_llm, today_str):
        """Test that ParseIncomeNode uses today's date if no date provided."""
        from nodes import ParseIncomeNode

        mock_call_llm.return_value = json.dumps(
            {
                "amount": 25000,
                "description": "venta",
            }
        )

        node = ParseIncomeNode()
        shared = {
            "telegram_input": {
                "message_text": "vendí algo y cobré 25000",
                "user_name": "Juan",
                "chat_id": 123456,
            },
        }

        result = node.run(shared)

        assert result == "default"
        assert shared["parsed_transactions"][0]["date"] == today_str

    @patch("nodes.call_llm")
    def test_handles_sueldo_keyword(self, mock_call_llm):
        """Test that ParseIncomeNode handles 'sueldo' keyword correctly."""
        from nodes import ParseIncomeNode

        mock_call_llm.return_value = json.dumps(
            {
                "amount": 200000,
                "description": "sueldo",
            }
        )

        node = ParseIncomeNode()
        shared = {
            "telegram_input": {
                "message_text": "me llegó el sueldo",
                "user_name": "Juan",
                "chat_id": 123456,
            },
        }

        result = node.run(shared)

        assert result == "default"
        assert shared["parsed_transactions"][0]["amount"] == 200000
        assert shared["parsed_transactions"][0]["category"] == "Ingreso"

    @patch("nodes.call_llm")
    def test_handles_invalid_json_from_llm(self, mock_call_llm):
        """Test that ParseIncomeNode handles invalid JSON from LLM gracefully."""
        from nodes import ParseIncomeNode

        mock_call_llm.return_value = "not valid json response"

        node = ParseIncomeNode()
        shared = {
            "telegram_input": {
                "message_text": "cobré 10000",
                "user_name": "Juan",
                "chat_id": 123456,
            },
        }

        result = node.run(shared)

        # Should return empty list and not crash
        assert shared["parsed_transactions"] == []
