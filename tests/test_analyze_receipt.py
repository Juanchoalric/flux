# tests/test_analyze_receipt.py
"""
Tests for AnalyzeReceiptNode.
"""

import pytest
import json
from unittest.mock import patch, MagicMock


class TestAnalyzeReceiptNode:
    """Tests for AnalyzeReceiptNode."""

    def test_node_exists(self):
        """Test that AnalyzeReceiptNode exists."""
        from nodes import AnalyzeReceiptNode

        assert AnalyzeReceiptNode is not None

    def test_prep_returns_photo_path(self):
        """Test that prep returns photo_path."""
        from nodes import AnalyzeReceiptNode

        node = AnalyzeReceiptNode()
        shared = {
            "telegram_input": {
                "photo_path": "/tmp/test.jpg",
            },
            "valid_categories": ["alimentos", "auto"],
        }

        result = node.prep(shared)

        assert result["photo_path"] == "/tmp/test.jpg"
        assert "alimentos" in result["valid_categories"]

    def test_prep_handles_missing_photo_path(self):
        """Test that prep handles missing photo_path."""
        from nodes import AnalyzeReceiptNode

        node = AnalyzeReceiptNode()
        shared = {
            "telegram_input": {},
            "valid_categories": ["alimentos"],
        }

        result = node.prep(shared)

        assert result["photo_path"] is None

    def test_valid_categories_default(self):
        """Test that valid_categories has default."""
        from nodes import AnalyzeReceiptNode

        node = AnalyzeReceiptNode()
        shared = {
            "telegram_input": {
                "photo_path": "/tmp/test.jpg",
            },
        }

        result = node.prep(shared)

        assert "otros" in result["valid_categories"]

    def test_node_inherits_from_node(self):
        """Test that AnalyzeReceiptNode inherits from Node."""
        from nodes import AnalyzeReceiptNode, Node

        assert issubclass(AnalyzeReceiptNode, Node)
