# tests/test_helpers.py
"""
Tests for helper functions in nodes.py.
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import patch


class TestCalculateMonthlySpend:
    """Tests for the calculate_monthly_spend helper function."""

    def test_calculate_monthly_spend_current_month(
        self, sample_sheet_records, current_month_year
    ):
        """Test that it sums expenses from the current month only."""
        from nodes import calculate_monthly_spend

        result = calculate_monthly_spend("alimentos", sample_sheet_records)

        # Should include records from current month only
        # Count records with "alimentos" (case insensitive) in current month
        expected = 0.0
        for record in sample_sheet_records:
            if (
                record.get("Tipo") == "Gasto"
                and record.get("Categoria", "").lower() == "alimentos"
            ):
                try:
                    record_date = datetime.strptime(record.get("Fecha", ""), "%Y-%m-%d")
                    if (
                        record_date.month == current_month_year["month"]
                        and record_date.year == current_month_year["year"]
                    ):
                        expected += float(record.get("Monto", 0))
                except (ValueError, TypeError):
                    continue

        assert result == expected

    def test_calculate_monthly_spend_ignores_other_months(self, sample_sheet_records):
        """Test that it ignores expenses from other months."""
        from nodes import calculate_monthly_spend

        result = calculate_monthly_spend("alimentos", sample_sheet_records)

        # Should NOT include last_month (8000) or next_month (2000) expenses
        # Should include same_month expenses: 5000 (alimentos) + 3000 (ALIMENTOS) = 8000
        assert result == 8000.0  # Sum of current month only

    def test_calculate_monthly_spend_case_insensitive_category(
        self, sample_sheet_records
    ):
        """Test that category matching is case insensitive."""
        from nodes import calculate_monthly_spend

        # "ALIMENTOS" uppercase should match "alimentos"
        result = calculate_monthly_spend("ALIMENTOS", sample_sheet_records)
        result_lower = calculate_monthly_spend("alimentos", sample_sheet_records)
        result_title = calculate_monthly_spend("Alimentos", sample_sheet_records)

        # All should return the same result
        assert result == result_lower == result_title

    def test_calculate_monthly_spend_ignores_income(self, sample_sheet_records):
        """Test that it ignores 'Ingreso' type records."""
        from nodes import calculate_monthly_spend

        # Get all records for alimentos (including income)
        all_alimentos = [
            r
            for r in sample_sheet_records
            if r.get("Categoria", "").lower() == "alimentos"
        ]

        # Calculate with all records
        result = calculate_monthly_spend("alimentos", sample_sheet_records)

        # Should not include income
        for record in all_alimentos:
            if record.get("Tipo") == "Ingreso":
                assert float(record.get("Monto", 0)) not in [result]

    def test_calculate_monthly_spend_empty_records(self):
        """Test with empty list of records."""
        from nodes import calculate_monthly_spend

        result = calculate_monthly_spend("alimentos", [])

        assert result == 0.0

    def test_calculate_monthly_spend_no_matching_category(self, sample_sheet_records):
        """Test with a category that has no records."""
        from nodes import calculate_monthly_spend

        result = calculate_monthly_spend("nonexistent", sample_sheet_records)

        assert result == 0.0

    def test_calculate_monthly_spend_invalid_date_format(self):
        """Test that it handles invalid date formats gracefully."""
        from nodes import calculate_monthly_spend

        records_with_bad_date = [
            {
                "Fecha": "not-a-date",
                "Monto": "1000",
                "Categoria": "alimentos",
                "Tipo": "Gasto",
            },
            {"Fecha": "", "Monto": "2000", "Categoria": "alimentos", "Tipo": "Gasto"},
            {
                "Fecha": "2024-13-45",
                "Monto": "3000",
                "Categoria": "alimentos",
                "Tipo": "Gasto",
            },
        ]

        # Should not raise, should return 0
        result = calculate_monthly_spend("alimentos", records_with_bad_date)

        assert result == 0.0

    def test_calculate_monthly_spend_missing_fields(self):
        """Test that it handles records with missing fields gracefully."""
        from nodes import calculate_monthly_spend

        records_with_missing = [
            {
                "Monto": "1000",
                "Categoria": "alimentos",
                "Tipo": "Gasto",
            },  # Missing Fecha
            {
                "Fecha": "2024-01-01",
                "Categoria": "alimentos",
                "Tipo": "Gasto",
            },  # Missing Monto
            {
                "Fecha": "2024-01-01",
                "Monto": "2000",
                "Tipo": "Gasto",
            },  # Missing Categoria
            {
                "Fecha": "2024-01-01",
                "Monto": "3000",
                "Categoria": "alimentos",
            },  # Missing Tipo
        ]

        result = calculate_monthly_spend("alimentos", records_with_missing)

        assert result == 0.0

    def test_calculate_monthly_spend_with_current_month_dates(self):
        """Test with records from current month only."""
        from nodes import calculate_monthly_spend

        # Use today's date to create records in current month
        today = datetime.now()

        # Records with known dates in current month
        test_records = [
            {
                "Fecha": today.strftime("%Y-%m-15"),
                "Monto": "5000",
                "Categoria": "alimentos",
                "Tipo": "Gasto",
            },
            {
                "Fecha": today.strftime("%Y-%m-10"),
                "Monto": "3000",
                "Categoria": "alimentos",
                "Tipo": "Gasto",
            },
            {
                "Fecha": today.strftime("%Y-%m-20"),
                "Monto": "2000",
                "Categoria": "auto",
                "Tipo": "Gasto",
            },
        ]

        result = calculate_monthly_spend("alimentos", test_records)

        # Should include all alimentos records from current month
        assert result == 8000.0

    def test_calculate_monthly_spend_zero_amount(self):
        """Test with zero amount records."""
        from nodes import calculate_monthly_spend

        records = [
            {
                "Fecha": datetime.now().strftime("%Y-%m-%d"),
                "Monto": "0",
                "Categoria": "alimentos",
                "Tipo": "Gasto",
            },
            {
                "Fecha": datetime.now().strftime("%Y-%m-%d"),
                "Monto": "5000",
                "Categoria": "alimentos",
                "Tipo": "Gasto",
            },
        ]

        result = calculate_monthly_spend("alimentos", records)

        assert result == 5000.0

    def test_calculate_monthly_spend_float_conversion(self):
        """Test that it correctly converts string amounts to float."""
        from nodes import calculate_monthly_spend

        records = [
            {
                "Fecha": datetime.now().strftime("%Y-%m-%d"),
                "Monto": "5000.50",
                "Categoria": "alimentos",
                "Tipo": "Gasto",
            },
            {
                "Fecha": datetime.now().strftime("%Y-%m-%d"),
                "Monto": "2500.25",
                "Categoria": "alimentos",
                "Tipo": "Gasto",
            },
        ]

        result = calculate_monthly_spend("alimentos", records)

        assert result == 7500.75
