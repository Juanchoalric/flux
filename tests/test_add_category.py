# tests/test_add_category.py
"""
Tests for AddCategoryNode.
"""

import pytest
import json
from unittest.mock import patch, AsyncMock


class TestAddCategoryNode:
    """Tests for AddCategoryNode."""

    @patch("nodes.send_message", new_callable=AsyncMock)
    @patch("nodes.call_llm")
    @patch("nodes.add_category")
    def test_adds_new_category(self, mock_add_cat, mock_call_llm, mock_send):
        """Test that AddCategoryNode adds a new category."""
        from nodes import AddCategoryNode

        mock_call_llm.return_value = json.dumps({"category_names": ["gimnasio"]})
        mock_add_cat.return_value = True

        node = AddCategoryNode()
        shared = {
            "telegram_input": {
                "message_text": "agrega la categoria gimnasio",
                "chat_id": 123456,
            },
        }

        result = node.run(shared)

        # Verify add_category was called with "gimnasio"
        mock_add_cat.assert_called_once_with("gimnasio")

    @patch("nodes.send_message", new_callable=AsyncMock)
    @patch("nodes.call_llm")
    @patch("nodes.add_category")
    def test_handles_existing_category(self, mock_add_cat, mock_call_llm, mock_send):
        """Test that AddCategoryNode handles existing category (no-op)."""
        from nodes import AddCategoryNode

        mock_call_llm.return_value = json.dumps({"category_names": ["alimentos"]})
        mock_add_cat.return_value = False  # Category already exists

        node = AddCategoryNode()
        shared = {
            "telegram_input": {
                "message_text": "agrega la categoria alimentos",
                "chat_id": 123456,
            },
        }

        result = node.run(shared)

        # add_category returns False for existing category
        mock_add_cat.assert_called_once()

    @patch("nodes.send_message", new_callable=AsyncMock)
    @patch("nodes.call_llm")
    @patch("nodes.add_category")
    def test_extracts_category_from_llm(self, mock_add_cat, mock_call_llm, mock_send):
        """Test that AddCategoryNode extracts category from LLM response."""
        from nodes import AddCategoryNode

        mock_call_llm.return_value = json.dumps({"category_names": ["mascotas"]})
        mock_add_cat.return_value = True

        node = AddCategoryNode()
        shared = {
            "telegram_input": {
                "message_text": "quiero agregar categoria para mascotas",
                "chat_id": 123456,
            },
        }

        result = node.run(shared)

        # Verify LLM was called
        mock_call_llm.assert_called_once()

    @patch("nodes.send_message", new_callable=AsyncMock)
    @patch("nodes.call_llm")
    @patch("nodes.add_category")
    def test_handles_multiple_categories(self, mock_add_cat, mock_call_llm, mock_send):
        """Test that AddCategoryNode handles multiple categories."""
        from nodes import AddCategoryNode

        mock_call_llm.return_value = json.dumps(
            {"category_names": ["gimnasio", "mascotas", "deportes"]}
        )
        mock_add_cat.return_value = True

        node = AddCategoryNode()
        shared = {
            "telegram_input": {
                "message_text": "agrega gimnasio mascotas y deportes",
                "chat_id": 123456,
            },
        }

        result = node.run(shared)

        # Should call add_category 3 times
        assert mock_add_cat.call_count == 3
