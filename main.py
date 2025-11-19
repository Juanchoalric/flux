import time
import os
from flow import create_expense_flow, create_monthly_summary_flow
from apscheduler.schedulers.background import BackgroundScheduler
import logging
from utils.logger_config import setup_logger
from utils.gsheets_api import get_categories

setup_logger() 
logger = logging.getLogger(__name__)

def run_monthly_summary_flow():
    logger.info("🤖 Kicking off scheduled monthly summary flow...")
    summary_flow = create_monthly_summary_flow()
    
    admin_chat_id = os.getenv("ADMIN_CHAT_ID")
    if not admin_chat_id:
        logger.error("ADMIN_CHAT_ID not set. Cannot send monthly summary.")
        return

    shared = {
        "admin_chat_id": admin_chat_id
    }
    summary_flow.run(shared)
    logger.info("✅ Monthly summary flow finished.")

def main():
    logger.info("🚀 Finance Bot starting...")

    scheduler = BackgroundScheduler()
    scheduler.add_job(run_monthly_summary_flow, 'cron', day='1', hour='8')
    scheduler.start()
    logger.info("📅 Monthly summary job scheduled for the 1st of each month at 8:00 AM.")
    
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