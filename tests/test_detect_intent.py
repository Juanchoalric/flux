# tests/test_detect_intent.py
"""
Tests for DetectIntentNode.

Tests the intent classification and routing for:
- REGISTRAR_GASTO
- REGISTRAR_INGRESO
- CONSULTAR_GASTOS
- DEFINIR_PRESUPUESTO
- CONSULTAR_PRESUPUESTO
- AGREGAR_CATEGORIA
- CONSULTAR_GASTOS_POR_CATEGORIA
- PEDIR_AYUDA
- EDITAR_ULTIMO_GASTO
- ELIMINAR_ULTIMO_GASTO
- OTRO (fallback)
"""

import pytest
import json
from unittest.mock import patch


class TestDetectIntentNode:
    """Tests for DetectIntentNode intent detection and routing."""

    @patch("nodes.call_llm")
    def test_detects_registrar_gasto(self, mock_call_llm):
        """Test that it detects REGISTRAR_GASTO intent."""
        from nodes import DetectIntentNode

        # Mock LLM response for expense registration
        mock_call_llm.return_value = json.dumps(
            {"intent": "REGISTRAR_GASTO", "entities": {"amount": 5000}}
        )

        node = DetectIntentNode()
        shared = {
            "telegram_input": {
                "message_text": "gaste 5000 en super",
                "user_name": "Juan",
                "chat_id": 123456,
            }
        }

        result = node.run(shared)

        assert result == "log_expense"
        assert shared["user_intent"]["intent"] == "REGISTRAR_GASTO"

    @patch("nodes.call_llm")
    def test_detects_registrar_ingreso(self, mock_call_llm):
        """Test that it detects REGISTRAR_INGRESO intent."""
        from nodes import DetectIntentNode

        mock_call_llm.return_value = json.dumps(
            {"intent": "REGISTRAR_INGRESO", "entities": {"amount": 150000}}
        )

        node = DetectIntentNode()
        shared = {
            "telegram_input": {
                "message_text": "cobré 150000 de alquiler",
                "user_name": "Juan",
                "chat_id": 123456,
            }
        }

        result = node.run(shared)

        assert result == "log_income"
        assert shared["user_intent"]["intent"] == "REGISTRAR_INGRESO"

    @patch("nodes.call_llm")
    def test_detects_consultar_gastos(self, mock_call_llm):
        """Test that it detects CONSULTAR_GASTOS intent."""
        from nodes import DetectIntentNode

        mock_call_llm.return_value = json.dumps(
            {"intent": "CONSULTAR_GASTOS", "entities": {}}
        )

        node = DetectIntentNode()
        shared = {
            "telegram_input": {
                "message_text": "cuánto gasté este mes",
                "user_name": "Juan",
                "chat_id": 123456,
            }
        }

        result = node.run(shared)

        assert result == "query_expense"
        assert shared["user_intent"]["intent"] == "CONSULTAR_GASTOS"

    @patch("nodes.call_llm")
    def test_detects_definir_presupuesto(self, mock_call_llm):
        """Test that it detects DEFINIR_PRESUPUESTO intent."""
        from nodes import DetectIntentNode

        mock_call_llm.return_value = json.dumps(
            {
                "intent": "DEFINIR_PRESUPUESTO",
                "entities": {"category": "alimentos", "amount": 50000},
            }
        )

        node = DetectIntentNode()
        shared = {
            "telegram_input": {
                "message_text": "quiero poner presupuesto de alimentos 50000",
                "user_name": "Juan",
                "chat_id": 123456,
            }
        }

        result = node.run(shared)

        assert result == "set_budget"
        assert shared["user_intent"]["intent"] == "DEFINIR_PRESUPUESTO"

    @patch("nodes.call_llm")
    def test_detects_consultar_presupuesto(self, mock_call_llm):
        """Test that it detects CONSULTAR_PRESUPUESTO intent."""
        from nodes import DetectIntentNode

        mock_call_llm.return_value = json.dumps(
            {"intent": "CONSULTAR_PRESUPUESTO", "entities": {}}
        )

        node = DetectIntentNode()
        shared = {
            "telegram_input": {
                "message_text": "cuál es mi presupuesto",
                "user_name": "Juan",
                "chat_id": 123456,
            }
        }

        result = node.run(shared)

        assert result == "query_budget"
        assert shared["user_intent"]["intent"] == "CONSULTAR_PRESUPUESTO"

    @patch("nodes.call_llm")
    def test_detects_agregar_categoria(self, mock_call_llm):
        """Test that it detects AGREGAR_CATEGORIA intent."""
        from nodes import DetectIntentNode

        mock_call_llm.return_value = json.dumps(
            {"intent": "AGREGAR_CATEGORIA", "entities": {"category": "veterinario"}}
        )

        node = DetectIntentNode()
        shared = {
            "telegram_input": {
                "message_text": "agregar categoría veterinario",
                "user_name": "Juan",
                "chat_id": 123456,
            }
        }

        result = node.run(shared)

        assert result == "add_category"
        assert shared["user_intent"]["intent"] == "AGREGAR_CATEGORIA"

    @patch("nodes.call_llm")
    def test_detects_consultar_gastos_por_categoria(self, mock_call_llm):
        """Test that it detects CONSULTAR_GASTOS_POR_CATEGORIA intent."""
        from nodes import DetectIntentNode

        mock_call_llm.return_value = json.dumps(
            {
                "intent": "CONSULTAR_GASTOS_POR_CATEGORIA",
                "entities": {"category": "alimentos"},
            }
        )

        node = DetectIntentNode()
        shared = {
            "telegram_input": {
                "message_text": "cuánto gasté en alimentos este mes",
                "user_name": "Juan",
                "chat_id": 123456,
            }
        }

        result = node.run(shared)

        assert result == "query_by_category"
        assert shared["user_intent"]["intent"] == "CONSULTAR_GASTOS_POR_CATEGORIA"

    @patch("nodes.call_llm")
    def test_detects_pedir_ayuda(self, mock_call_llm):
        """Test that it detects PEDIR_AYUDA intent."""
        from nodes import DetectIntentNode

        mock_call_llm.return_value = json.dumps(
            {"intent": "PEDIR_AYUDA", "entities": {}}
        )

        node = DetectIntentNode()
        shared = {
            "telegram_input": {
                "message_text": "ayuda qué puedes hacer",
                "user_name": "Juan",
                "chat_id": 123456,
            }
        }

        result = node.run(shared)

        assert result == "show_help"
        assert shared["user_intent"]["intent"] == "PEDIR_AYUDA"

    @patch("nodes.call_llm")
    def test_detects_editar_ultimo_gasto(self, mock_call_llm):
        """Test that it detects EDITAR_ULTIMO_GASTO intent."""
        from nodes import DetectIntentNode

        mock_call_llm.return_value = json.dumps(
            {
                "intent": "EDITAR_ULTIMO_GASTO",
                "entities": {"field": "category", "value": "ocio"},
            }
        )

        node = DetectIntentNode()
        shared = {
            "telegram_input": {
                "message_text": "cambiar categoría del último gasto a ocio",
                "user_name": "Juan",
                "chat_id": 123456,
            }
        }

        result = node.run(shared)

        assert result == "edit_last"
        assert shared["user_intent"]["intent"] == "EDITAR_ULTIMO_GASTO"

    @patch("nodes.call_llm")
    def test_detects_eliminar_ultimo_gasto(self, mock_call_llm):
        """Test that it detects ELIMINAR_ULTIMO_GASTO intent."""
        from nodes import DetectIntentNode

        mock_call_llm.return_value = json.dumps(
            {"intent": "ELIMINAR_ULTIMO_GASTO", "entities": {}}
        )

        node = DetectIntentNode()
        shared = {
            "telegram_input": {
                "message_text": "borrar último gasto",
                "user_name": "Juan",
                "chat_id": 123456,
            }
        }

        result = node.run(shared)

        assert result == "delete_last"
        assert shared["user_intent"]["intent"] == "ELIMINAR_ULTIMO_GASTO"

    @patch("nodes.call_llm")
    def test_detects_exportar_reporte(self, mock_call_llm):
        """Test that it detects EXPORTAR_REPORTE intent."""
        from nodes import DetectIntentNode

        mock_call_llm.return_value = json.dumps(
            {
                "intent": "EXPORTAR_REPORTE",
                "entities": {"export_type": "monthly"},
            }
        )

        node = DetectIntentNode()
        shared = {
            "telegram_input": {
                "message_text": "dame un reporte en pdf de este mes",
                "user_name": "Juan",
                "chat_id": 123456,
            }
        }

        result = node.run(shared)

        assert result == "export_report"
        assert shared["user_intent"]["intent"] == "EXPORTAR_REPORTE"
        assert shared["user_intent"]["entities"]["export_type"] == "monthly"

    @patch("nodes.call_llm")
    def test_falls_back_to_otro_for_unknown_intent(self, mock_call_llm):
        """Test that unknown intents fallback to OTRO."""
        from nodes import DetectIntentNode

        # Mock LLM returning an unknown intent
        mock_call_llm.return_value = json.dumps(
            {"intent": "UNKNOWN_INTENT", "entities": {}}
        )

        node = DetectIntentNode()
        shared = {
            "telegram_input": {
                "message_text": "algo rarísimo que no entiendo",
                "user_name": "Juan",
                "chat_id": 123456,
            }
        }

        result = node.run(shared)

        assert result == "fallback"
        assert shared["user_intent"]["intent"] == "UNKNOWN_INTENT"

    @patch("nodes.call_llm")
    def test_handles_invalid_json_from_llm(self, mock_call_llm):
        """Test that it handles invalid JSON from LLM gracefully."""
        from nodes import DetectIntentNode

        # Mock LLM returning invalid JSON
        mock_call_llm.return_value = "invalid json response"

        node = DetectIntentNode()
        shared = {
            "telegram_input": {
                "message_text": "gaste 1000",
                "user_name": "Juan",
                "chat_id": 123456,
            }
        }

        result = node.run(shared)

        # Should fallback to OTRO when JSON is invalid
        assert result == "fallback"
        assert shared["user_intent"]["intent"] == "OTRO"

    @patch("nodes.call_llm")
    def test_handles_empty_message(self, mock_call_llm):
        """Test that it handles empty message gracefully."""
        from nodes import DetectIntentNode

        node = DetectIntentNode()
        shared = {
            "telegram_input": {
                "message_text": "",
                "user_name": "Juan",
                "chat_id": 123456,
            }
        }

        result = node.run(shared)

        # Should return None for empty message (no routing)
        assert result is None
        assert "user_intent" not in shared

    @patch("nodes.call_llm")
    def test_stores_entities_in_shared(self, mock_call_llm):
        """Test that entities are stored in shared state."""
        from nodes import DetectIntentNode

        mock_call_llm.return_value = json.dumps(
            {
                "intent": "REGISTRAR_GASTO",
                "entities": {"amount": 5000, "category": "alimentos"},
            }
        )

        node = DetectIntentNode()
        shared = {
            "telegram_input": {
                "message_text": "gaste 5000 en alimentos",
                "user_name": "Juan",
                "chat_id": 123456,
            }
        }

        result = node.run(shared)

        assert result == "log_expense"
        assert shared["user_intent"]["entities"]["amount"] == 5000
        assert shared["user_intent"]["entities"]["category"] == "alimentos"
