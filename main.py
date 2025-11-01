import time
from flow import create_expense_flow
import logging
from utils.logger_config import setup_logger

setup_logger() 
logger = logging.getLogger(__name__)

VALID_CATEGORIES = [
    "alimentos",
    "alquiler",
    "salidas",
    "expensas",
    "deuda visa",
    "deuda amex",
    "mascotas",  
    "servicios",
    "transporte", 
    "ocio", 
    "educacion", 
    "salud", 
    "ropa",
    "regalos",
    "otros"
]

def main():
    logger.info("🚀 Bot de Gastos iniciando...")
    
    expense_flow = create_expense_flow()
    
    while True:
        shared = {
            "telegram_input": {},
            "parsed_expenses": [],
            "valid_categories": VALID_CATEGORIES 
        }
        
        expense_flow.run(shared)
        
        if not shared.get("telegram_input"):
            time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nBot detenido manualmente.")