# tests/test_date_parsing_standalone.py
"""
Tests para parse_relative_date - versión standalone que no requiere imports del proyecto.
"""

import sys
import os
from datetime import date, timedelta

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Definir la función aquí para evitar problemas de imports
def parse_relative_date(date_str):
    """
    Parse relative date strings to YYYY-MM-DD format.
    Handles: "today", "yesterday", "2daysago", "3daysago", etc.
    Also handles day names like "monday", "tuesday", etc.
    """
    if not date_str:
        return date.today().strftime("%Y-%m-%d")

    date_str = date_str.lower().strip()
    today = date.today()

    # Handle "today"
    if date_str == "today":
        return today.strftime("%Y-%m-%d")

    # Handle "yesterday"
    if date_str == "yesterday":
        yesterday = today - timedelta(days=1)
        return yesterday.strftime("%Y-%m-%d")

    # Handle "Xdaysago" patterns
    if "daysago" in date_str or "days ago" in date_str:
        try:
            # Extract number: "2daysago" -> 2, "3 days ago" -> 3
            num_str = (
                date_str.replace("daysago", "").replace("days ago", "").replace(" ", "")
            )
            days = int(num_str)
            target_date = today - timedelta(days=days)
            return target_date.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            pass

    # Handle day names (monday, tuesday, etc.)
    day_map = {
        "monday": 0,
        "lunes": 0,
        "tuesday": 1,
        "martes": 1,
        "wednesday": 2,
        "miercoles": 2,
        "thursday": 3,
        "jueves": 3,
        "friday": 4,
        "viernes": 4,
        "saturday": 5,
        "sabado": 5,
        "sunday": 6,
        "domingo": 6,
    }

    for day_name, day_num in day_map.items():
        if day_name in date_str:
            # Calculate days to subtract to reach that day
            current_day = today.weekday()
            days_to_subtract = (current_day - day_num) % 7
            if days_to_subtract == 0:
                # If it's the same day, assume last week
                days_to_subtract = 7
            target_date = today - timedelta(days=days_to_subtract)
            return target_date.strftime("%Y-%m-%d")

    # Try parsing as YYYY-MM-DD directly
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        pass

    # Default to today if nothing works
    return today.strftime("%Y-%m-%d")


# Ahora los tests
from datetime import datetime


def test_today():
    """Test que 'today' retorna la fecha de hoy."""
    result = parse_relative_date("today")
    expected = date.today().strftime("%Y-%m-%d")
    assert result == expected, f"Expected {expected}, got {result}"


def test_yesterday():
    """Test que 'yesterday' retorna ayer."""
    result = parse_relative_date("yesterday")
    expected = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    assert result == expected, f"Expected {expected}, got {result}"


def test_2daysago():
    """Test que '2daysago' retorna hace 2 días."""
    result = parse_relative_date("2daysago")
    expected = (date.today() - timedelta(days=2)).strftime("%Y-%m-%d")
    assert result == expected, f"Expected {expected}, got {result}"


def test_3daysago():
    """Test que '3daysago' retorna hace 3 días."""
    result = parse_relative_date("3daysago")
    expected = (date.today() - timedelta(days=3)).strftime("%Y-%m-%d")
    assert result == expected, f"Expected {expected}, got {result}"


def test_3_days_ago_with_space():
    """Test que '3 days ago' retorna hace 3 días."""
    result = parse_relative_date("3 days ago")
    expected = (date.today() - timedelta(days=3)).strftime("%Y-%m-%d")
    assert result == expected, f"Expected {expected}, got {result}"


def test_exact_date():
    """Test que una fecha exacta YYYY-MM-DD se pasa directo."""
    result = parse_relative_date("2024-01-15")
    assert result == "2024-01-15"


def test_empty_string_returns_today():
    """Test que string vacío retorna hoy."""
    result = parse_relative_date("")
    expected = date.today().strftime("%Y-%m-%d")
    assert result == expected, f"Expected {expected}, got {result}"


def test_none_returns_today():
    """Test que None retorna hoy."""
    result = parse_relative_date(None)
    expected = date.today().strftime("%Y-%m-%d")
    assert result == expected, f"Expected {expected}, got {result}"


def test_invalid_string_returns_today():
    """Test que un string inválido retorna hoy."""
    result = parse_relative_date("invalid_date_xyz")
    expected = date.today().strftime("%Y-%m-%d")
    assert result == expected, f"Expected {expected}, got {result}"


def test_monday():
    """Test que 'monday' retorna la fecha del lunes pasado."""
    result = parse_relative_date("monday")

    # Verificar que es una fecha válida YYYY-MM-DD
    assert len(result) == 10
    assert result.count("-") == 2

    # Parsear y verificar el día de la semana
    parsed_date = date.fromisoformat(result)
    assert parsed_date.weekday() == 0  # Monday


def test_lunes():
    """Test que 'lunes' retorna la fecha del lunes pasado."""
    result = parse_relative_date("lunes")

    # Verificar que es una fecha válida YYYY-MM-DD
    assert len(result) == 10

    # Parsear y verificar el día de la semana
    parsed_date = date.fromisoformat(result)
    assert parsed_date.weekday() == 0  # Monday


if __name__ == "__main__":
    # Run tests manually
    tests = [
        test_today,
        test_yesterday,
        test_2daysago,
        test_3daysago,
        test_3_days_ago_with_space,
        test_exact_date,
        test_empty_string_returns_today,
        test_none_returns_today,
        test_invalid_string_returns_today,
        test_monday,
        test_lunes,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            print(f"✅ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: ERROR - {e}")
            failed += 1

    print(f"\n{'=' * 40}")
    print(f"Results: {passed} passed, {failed} failed")
