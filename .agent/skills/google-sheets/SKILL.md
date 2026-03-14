---
name: google-sheets
description: >
  Guía para Google Sheets API con gspread y google-auth.
  Trigger: Cuando se modifica gsheets_api.py o se agregan operaciones con Sheets.
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## When to Use

- Proyecto usa gspread para operar con Google Sheets
- Se agregan operaciones CRUD (append, read, update, delete)
- Troubleshooting de auth o service accounts
- Nuevas sheets o ranges

## Setup

```bash
pip install gspread google-auth-oauthlib google-auth
```

## Setup Service Account

1. Ir a Google Cloud Console → APIs → Enable Sheets API
2. Credentials → Create Service Account
3. Descargar JSON → guardar como `service_account.json`
4. Compartir la Sheet con el email del service account

```python
import gspread
from google.oauth2.service_account import Credentials

# Auth
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credentials = Credentials.from_service_account_file(
    "service_account.json",
    scopes=scopes
)

gc = gspread.authorize(credentials)
```

## Patterns Usados en Este Proyecto

### 1. Append Row (Insert)

```python
# utils/gsheets_api.py
def append_row(data: list) -> bool:
    """
    Appends a row to 'Gastos' sheet.
    data: [date, amount, category, description, who, type]
    """
    try:
        sheet = gc.open("FluxCostBot").sheet1
        sheet.append_row(data, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        logger.error(f"Error appending row: {e}")
        return False
```

### 2. Get All Records

```python
def get_all_records(sheet_name: str = None) -> list:
    """Returns all records from sheet as list of dicts."""
    try:
        if sheet_name:
            sheet = gc.open("FluxCostBot").worksheet(sheet_name)
        else:
            sheet = gc.open("FluxCostBot").sheet1
        
        return sheet.get_all_records()
    except Exception as e:
        logger.error(f"Error getting records: {e}")
        return []
```

### 3. Find Last Row by User

```python
def find_last_row_by_user(user_name: str):
    """Find the last expense entry for a specific user."""
    sheet = gc.open("FluxCostBot").sheet1
    all_values = sheet.get_all_values()
    
    # Buscar desde el final
    for i in range(len(all_values) - 1, 0, -1):
        row = all_values[i]
        if len(row) >= 5 and row[4].lower() == user_name.lower():
            return {
                "row_number": i + 1,  # gspread es 1-indexed
                "data": {
                    "Fecha": row[0],
                    "Monto": row[1],
                    "Categoria": row[2],
                    "Descripcion": row[3],
                    "Tipo": row[5]
                }
            }
    return None
```

### 4. Update Row

```python
def update_row(row_number: int, updates: dict) -> bool:
    """Update specific cells in a row."""
    try:
        sheet = gc.open("FluxCostBot").sheet1
        
        for key, value in updates.items():
            col_map = {
                "Fecha": 1, "Monto": 2, "Categoria": 3,
                "Descripcion": 4, "Who": 5, "Tipo": 6
            }
            if key in col_map:
                sheet.update_cell(row_number, col_map[key], value)
        return True
    except Exception as e:
        logger.error(f"Error updating row: {e}")
        return False
```

### 5. Delete Row

```python
def delete_row(row_number: int) -> bool:
    """Delete a specific row."""
    try:
        sheet = gc.open("FluxCostBot").sheet1
        sheet.delete_rows(row_number)
        return True
    except Exception as e:
        logger.error(f"Error deleting row: {e}")
        return False
```

### 6. Budgets (Worksheet separada)

```python
def get_budgets() -> dict:
    """Get all budgets from 'Presupuestos' sheet."""
    try:
        sheet = gc.open("FluxCostBot").worksheet("Presupuestos")
        records = sheet.get_all_records()
        
        budgets = {}
        for r in records:
            if r.get("Categoria") and r.get("Monto"):
                budgets[r["Categoria"].lower()] = float(r["Monto"])
        return budgets
    except Exception as e:
        logger.error(f"Error getting budgets: {e}")
        return {}

def set_budget(category: str, amount: float) -> bool:
    """Set or update budget for a category."""
    try:
        sheet = gc.open("FluxCostBot").worksheet("Presupuestos")
        
        # Buscar si existe
        all_records = sheet.get_all_records()
        for i, r in enumerate(all_records, start=2):  # starts at row 2
            if r.get("Categoria", "").lower() == category.lower():
                sheet.update_cell(i, 2, amount)
                return True
        
        # Si no existe, agregar
        sheet.append_row([category, amount])
        return True
    except Exception as e:
        logger.error(f"Error setting budget: {e}")
        return False
```

## Sheet Structure

| Column | Index | Example |
|--------|-------|---------|
| Fecha | A | 2024-01-15 |
| Monto | B | 5000 |
| Categoria | C | Alimentos |
| Descripcion | D | Compras |
| Who | E | Juan |
| Tipo | F | Gasto |

## Value Input Options

| Option | Effect |
|--------|--------|
| `RAW` | Escribe exactly as provided |
| `USER_ENTERED` | Parsea fechas, números, fórmulas |

## Common Errors

1. **SpreadsheetNotFound** → Verificar nombre exacto
2. **Permission denied** → Compartir sheet con service account email
3. **Invalid JSON** → Verificar service_account.json formato
4. **Rate limiting** → gspread tiene límites, usar batch cuando sea posible

## Tips

- Usar `get_all_records()` para datasets pequeños
- Para grandes datasets, usar `get()` con range específico
- Siempre envolver en try/except
- Logger para debugging

## Commands

```bash
# Test de conexión
python -c "
import gspread
gc = gspread.service_account('service_account.json')
print(gc.openall())
"
```

## Resources

- **gspread docs**: https://docs.gspread.org/
- **Sheets API**: https://developers.google.com/sheets/api
- **OAuth lib**: https://google-auth.readthedocs.io/
