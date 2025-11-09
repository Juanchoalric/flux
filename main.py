import time
from flow import create_expense_flow
import logging
from utils.logger_config import setup_logger
from utils.gsheets_api import get_categories

setup_logger() 
logger = logging.getLogger(__name__)

"""
VALID_CATEGORIES = [
    "Alimentos", "Alquiler", "Salidas", "Expensas", "Deuda Visa",
    "Deuda Amex", "Mascotas", "Servicios", "Regalos", "Ocio",
    "Auto", "Educacion", "Medicamentos", "Ropa", "Otros"
]
"""

def main():
    logger.info("🚀 Finance Bot starting...")
    
    expense_flow = create_expense_flow()
    
    while True:
        valid_categories_from_sheet = get_categories()
        shared = {
            "telegram_input": {},
            "parsed_transactions": [],
            "valid_categories": valid_categories_from_sheet
        }
        
        expense_flow.run(shared)
        
        if not shared.get("telegram_input"):
            time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nBot stopped manually.")