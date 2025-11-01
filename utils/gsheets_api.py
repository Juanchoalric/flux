# utils/gsheets_api.py
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
    raise ValueError("No se encontró el GOOGLE_SHEET_ID en el archivo .env")

def get_gsheets_client():
    """
    Configura y devuelve un cliente autenticado para Google Sheets.
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
    Añade una nueva fila con los datos proporcionados a la hoja especificada.
    """
    try:
        client = get_gsheets_client()
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="20")
            headers = ["Fecha", "Monto", "Categoria", "Descripcion", "Quien"]
            worksheet.append_row(headers)
            logger.info(f"Hoja '{sheet_name}' no encontrada. Se ha creado una nueva con encabezados.")

        worksheet.append_row(data)
        return True
    except Exception as e:
        logger.error(f"Error al añadir fila a Google Sheets.")
        logger.error(f"Tipo de Excepción: {type(e).__name__}")
        logger.error(f"Detalles del Error: {repr(e)}")
        return False

def get_all_records(sheet_name: str = "Gastos") -> list[dict]:
    """
    Obtiene todos los registros de una hoja y los devuelve como una lista de diccionarios.
    """
    try:
        client = get_gsheets_client()
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        worksheet = spreadsheet.worksheet(sheet_name)
        return worksheet.get_all_records()
    except Exception as e:
        logger.error(f"Error al leer la hoja de Google Sheets: {e}")
        return []