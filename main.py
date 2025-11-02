import time
from flow import create_expense_flow
import logging
from utils.logger_config import setup_logger

setup_logger() 
logger = logging.getLogger(__name__)

VALID_CATEGORIES = [
    "Alimentos", "Alquiler", "Salidas", "Expensas", "Deuda Visa",
    "Deuda Amex", "Mascotas", "Servicios", "Regalos", "Ocio",
    "Auto", "Educacion", "Medicamentos", "Ropa", "Otros"
]

def main():
    logger.info("🚀 Expense Bot starting...")
    
    expense_flow = create_expense_flow()
    
    while True:
        shared = {
            "telegram_input": {},
            "parsed_expenses": [],
            "valid_categories": VALID_CATEGORIES 
        }
        
        expense_flow.run(shared)
        
        # If no message was processed, wait before polling again
        if not shared.get("telegram_input"):
            time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nBot stopped manually.")