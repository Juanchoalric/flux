# tests/test_date_parsing.py
"""
Tests para la funcionalidad de parsing de fechas relatives.
"""

import pytest
from datetime import date, timedelta
from nodes import parse_relative_date


class TestParseRelativeDate:
    """Tests para la función parse_relative_date."""

    def test_today(self):
        """Test que 'today' retorna la fecha de hoy."""
        result = parse_relative_date("today")
        expected = date.today().strftime("%Y-%m-%d")
        assert result == expected

    def test_yesterday(self):
        """Test que 'yesterday' retorna ayer."""
        result = parse_relative_date("yesterday")
        expected = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        assert result == expected

    def test_2daysago(self):
        """Test que '2daysago' retorna hace 2 días."""
        result = parse_relative_date("2daysago")
        expected = (date.today() - timedelta(days=2)).strftime("%Y-%m-%d")
        assert result == expected

    def test_3daysago(self):
        """Test que '3daysago' retorna hace 3 días."""
        result = parse_relative_date("3daysago")
        expected = (date.today() - timedelta(days=3)).strftime("%Y-%m-%d")
        assert result == expected

    def test_3_days_ago_with_space(self):
        """Test que '3 days ago' retorna hace 3 días."""
        result = parse_relative_date("3 days ago")
        expected = (date.today() - timedelta(days=3)).strftime("%Y-%m-%d")
        assert result == expected

    def test_exact_date(self):
        """Test que una fecha exacta YYYY-MM-DD se pasa directo."""
        result = parse_relative_date("2024-01-15")
        assert result == "2024-01-15"

    def test_empty_string_returns_today(self):
        """Test que string vacío retorna hoy."""
        result = parse_relative_date("")
        expected = date.today().strftime("%Y-%m-%d")
        assert result == expected

    def test_none_returns_today(self):
        """Test que None retorna hoy."""
        result = parse_relative_date(None)
        expected = date.today().strftime("%Y-%m-%d")
        assert result == expected

    def test_invalid_string_returns_today(self):
        """Test que un string inválido retorna hoy."""
        result = parse_relative_date("invalid_date_xyz")
        expected = date.today().strftime("%Y-%m-%d")
        assert result == expected

    @pytest.mark.parametrize(
        "day_name,expected_weekday",
        [
            ("monday", 0),
            ("lunes", 0),
            ("tuesday", 1),
            ("martes", 1),
            ("wednesday", 2),
            ("miercoles", 2),
            ("thursday", 3),
            ("jueves", 3),
            ("friday", 4),
            ("viernes", 4),
            ("saturday", 5),
            ("sabado", 5),
            ("sunday", 6),
            ("domingo", 6),
        ],
    )
    def test_day_names(self, day_name, expected_weekday):
        """Test que los días de la semana retornan la fecha correcta."""
        result = parse_relative_date(day_name)

        # Verificar que es una fecha válida YYYY-MM-DD
        assert len(result) == 10
        assert result.count("-") == 2

        # Parsear y verificar el día de la semana
        parsed_date = date.fromisoformat(result)
        assert parsed_date.weekday() == expected_weekday


class TestNormalizeCategory:
    """Tests para la función normalize_category."""

    def test_exact_match(self):
        """Test que retorna la categoría exacta si coincide."""
        from nodes import normalize_category

        result = normalize_category("alimentos", ["alimentos", "transporte"])
        assert result == "alimentos"

    def test_case_insensitive(self):
        """Test que es case insensitive."""
        from nodes import normalize_category

        result = normalize_category("ALIMENTOS", ["alimentos", "transporte"])
        assert result == "alimentos"

    def test_no_match_returns_lowercase(self):
        """Test que si no encuentra coincidencia retorna lowercase."""
        from nodes import normalize_category

        result = normalize_category("gimnasio", ["alimentos", "transporte"])
        assert result == "gimnasio"

    def test_empty_returns_otros(self):
        """Test que string vacío retorna 'otros'."""
        from nodes import normalize_category

        result = normalize_category("", ["alimentos"])
        assert result == "otros"

    def test_none_returns_otros(self):
        """Test que None retorna 'otros'."""
        from nodes import normalize_category

        result = normalize_category(None, ["alimentos"])
        assert result == "otros"
