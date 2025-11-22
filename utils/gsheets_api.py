import os
import gspread
import logging
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
SERVICE_ACCOUNT_FILE = "service_account.json"

if not GOOGLE_SHEET_ID:
    raise ValueError("GOOGLE_SHEET_ID not found in the .env file")

def get_gsheets_client():
    """
    Configures and returns an authenticated client for Google Sheets.
    """
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file"
    ]
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=scopes
    )
    return gspread.authorize(creds)

def append_row(data: list, sheet_name: str = "Gastos"):
    """
    Appends a new row with the provided data to the specified sheet.
    """
    try:
        client = get_gsheets_client()
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="20")
            headers = ["Fecha", "Monto", "Categoria", "Descripcion", "Quien", "Tipo"]
            worksheet.append_row(headers)
            logger.info(f"Sheet '{sheet_name}' not found. A new one was created with headers.")

        worksheet.append_row(data)
        return True
    except Exception as e:
        logger.error("Error appending row to Google Sheets.")
        logger.error(f"Exception Type: {type(e).__name__}")
        logger.error(f"Error Details: {repr(e)}")
        return False

def get_all_records(sheet_name: str = "Gastos") -> list[dict]:
    """
    Gets all records from a sheet and returns them as a list of dictionaries.
    """
    try:
        client = get_gsheets_client()
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        worksheet = spreadsheet.worksheet(sheet_name)
        
        all_values = worksheet.get_all_values()
        if not all_values:
            return []

        headers = [header.strip() for header in all_values[0]]
        
        records = []
        for row in all_values[1:]:
            record_dict = dict(zip(headers, row))
            records.append(record_dict)
            
        return records
    except Exception as e:
        logger.error(f"Error reading from Google Sheets: {e}")
        return []

def set_budget(category: str, amount: float) -> bool:
    """
    Sets or updates the budget for a specific category.
    """
    try:
        client = get_gsheets_client()
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        worksheet = spreadsheet.worksheet("Presupuestos")
        
        # Find if the category already has a budget
        cell = worksheet.find(category, in_column=1)
        
        if cell:
            # Update existing budget
            worksheet.update_cell(cell.row, 2, amount)
            logger.info(f"Updated budget for '{category}' to {amount}.")
        else:
            # Add new budget
            worksheet.append_row([category, amount])
            logger.info(f"Set new budget for '{category}' to {amount}.")
        return True
    except Exception as e:
        logger.error(f"Error setting budget for '{category}': {e}")
        return False

def get_budgets() -> dict:
    """
    Gets all budgets and returns them as a dictionary for easy lookup.
    """
    try:
        client = get_gsheets_client()
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        worksheet = spreadsheet.worksheet("Presupuestos")
        records = worksheet.get_all_records()
        # Convert list of dicts to a single dict: {'Category': Amount, ...}
        return {record['Categoria'].lower(): float(record['MontoMaximo']) for record in records}
    except Exception as e:
        logger.error(f"Error fetching budgets: {e}")
        return {}
    
def get_categories() -> list[str]:
    """
    Gets all valid categories from the 'Categorias' sheet.
    """
    try:
        records = get_all_records(sheet_name="Categorias")
        return [record['Nombre'].strip() for record in records if record.get('Nombre')]
    except Exception as e:
        logger.error(f"Error fetching categories: {e}", exc_info=True)
        # Fallback to a default list if the sheet can't be read
        return ["otros"]

def add_category(category_name: str) -> bool:
    """
    Adds a new category to the 'Categorias' sheet if it doesn't already exist.
    """
    try:
        existing_categories = get_categories()

        existing_lower = [c.strip().lower() for c in existing_categories]
        new_category_lower = category_name.strip().lower()

        category_name_capitalized = category_name.capitalize()
        
        if new_category_lower in existing_lower:
            logger.warning(f"Category '{category_name}' already exists (ignoring case).")
            return False

        category_name_capitalized = category_name.strip().capitalize()
        success = append_row([category_name_capitalized], sheet_name="Categorias")
        
        if success:
            logger.info(f"Successfully added new category: '{category_name_capitalized}'")
        return success

    except Exception as e:
        logger.error(f"Error adding category '{category_name}': {e}", exc_info=True)
        return False

def find_last_row_by_user(user_name: str, sheet_name: str = "Gastos") -> dict | None:
    """
    Finds the last entry for a specific user and returns its details and row number.
    """
    try:
        client = get_gsheets_client()
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        worksheet = spreadsheet.worksheet(sheet_name)
        
        all_values = worksheet.get_all_values()
        if not all_values: return None

        headers = [h.strip() for h in all_values[0]]
        # Asumimos que la columna 'Quien' es la quinta (índice 4)
        who_col_index = 4 

        # Iteramos hacia atrás para encontrar la última coincidencia
        for index, row in reversed(list(enumerate(all_values))):
            if len(row) > who_col_index and row[who_col_index] == user_name:
                row_number = index + 1 # gspread usa índices base 1
                record_data = dict(zip(headers, row))
                return {"row_number": row_number, "data": record_data}
        
        return None # No se encontraron entradas para ese usuario
    except Exception as e:
        logger.error(f"Error finding last row for user '{user_name}': {e}", exc_info=True)
        return None

def update_row(row_number: int, updates: dict, sheet_name: str = "Gastos") -> bool:
    """
    Updates specific cells in a given row.
    'updates' is a dictionary like {'Categoria': 'Salidas', 'Monto': 4500}.
    """
    try:
        client = get_gsheets_client()
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        worksheet = spreadsheet.worksheet(sheet_name)

        # Mapeo de nombres de columna a su número de columna (base 1)
        COL_MAP = {"Fecha": 1, "Monto": 2, "Categoria": 3, "Descripcion": 4, "Quien": 5, "Tipo": 6}
        
        cells_to_update = []
        for col_name, new_value in updates.items():
            if col_name in COL_MAP:
                col_number = COL_MAP[col_name]
                cells_to_update.append(gspread.Cell(row_number, col_number, str(new_value)))
        
        if cells_to_update:
            worksheet.update_cells(cells_to_update)
            logger.info(f"Successfully updated row {row_number} with {updates}")
        return True
    except Exception as e:
        logger.error(f"Error updating row {row_number}: {e}", exc_info=True)
        return False

def delete_row(row_number: int, sheet_name: str = "Gastos") -> bool:
    """
    Deletes a specific row from the sheet.
    """
    try:
        client = get_gsheets_client()
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        worksheet = spreadsheet.worksheet(sheet_name)
        worksheet.delete_rows(row_number)
        logger.info(f"Successfully deleted row {row_number}")
        return True
    except Exception as e:
        logger.error(f"Error deleting row {row_number}: {e}", exc_info=True)
        return False