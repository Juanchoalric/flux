import time
import os
from flow import create_expense_flow, create_monthly_summary_flow
from apscheduler.schedulers.background import BackgroundScheduler
from zoneinfo import ZoneInfo
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

def check_and_run_missed_report() -> None:
    """Run monthly report if it was missed due to restart (scheduler is in-memory)."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    today = datetime.now(ZoneInfo('America/Buenos_Aires'))
    if today.day > 1:
        logger.warning("⚠️ Reinicio después del día 1 — ejecutando reporte mensual pendiente...")
        try:
            run_monthly_summary_flow()
        except Exception as e:
            logger.error(f"Error al ejecutar reporte pendiente: {e}")


def main():
    logger.info("🚀 Finance Bot starting...")

    tz_ba = ZoneInfo('America/Buenos_Aires')

    job_defaults = {
        'coalesce': True,
        'max_instances': 1,
        'misfire_grace_time': 3600 
    }

    scheduler = BackgroundScheduler(timezone=tz_ba, job_defaults=job_defaults)
    scheduler.add_job(
        run_monthly_summary_flow, 
        'cron', 
        day='1', 
        hour='8',
        timezone=tz_ba,
        id='monthly_summary')
    
    scheduler.start()
    logger.info("📅 Scheduler iniciado. Próximos trabajos:")
    scheduler.print_jobs()

    logger.info("📅 Monthly summary job scheduled for the 1st of each month at 8:00 AM.")

    # Check for missed monthly report (scheduler is in-memory, lost on restart)
    check_and_run_missed_report()

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