# scheduler.py
"""
Scheduler for automated monthly tasks.
"""

import os
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

# Global scheduler instance
scheduler = None


def create_scheduler():
    """
    Creates and returns the APScheduler instance.
    """
    global scheduler
    scheduler = AsyncIOScheduler()
    return scheduler


def schedule_monthly_report(flow_func, admin_chat_id: str = None):
    """
    Schedules the monthly report to run on the 1st of each month at 9 AM.

    Args:
        flow_func: Function that creates and runs the monthly flow
        admin_chat_id: Chat ID to send the report to (from env if not provided)
    """
    global scheduler

    if scheduler is None:
        scheduler = create_scheduler()

    # Get admin chat ID from environment if not provided
    if not admin_chat_id:
        admin_chat_id = os.getenv("ADMIN_CHAT_ID")

    if not admin_chat_id:
        logger.error("ADMIN_CHAT_ID not set. Cannot schedule monthly report.")
        return

    def run_monthly_task():
        """Wrapper to run the monthly analysis flow."""
        logger.info("Running scheduled monthly report...")
        try:
            flow = flow_func()
            # The flow needs admin_chat_id in shared
            # We'll handle this in the flow execution
            from nodes import DataExtractionNode, MonthlyAnalysisNode

            # Create a simple execution
            data_node = DataExtractionNode()
            analysis_node = MonthlyAnalysisNode()

            data_node >> analysis_node

            # Execute the flow
            flow.run({})
            logger.info("Monthly report executed successfully.")
        except Exception as e:
            logger.error(f"Error running monthly report: {e}")

    # Schedule for 1st of each month at 9 AM
    trigger = CronTrigger(day=1, hour=9, minute=0)
    scheduler.add_job(
        run_monthly_task,
        trigger,
        id="monthly_report",
        name="Monthly Financial Report",
        replace_existing=True,
    )

    logger.info(
        f"Monthly report scheduled for 1st of each month at 9 AM. Admin chat: {admin_chat_id}"
    )


def start_scheduler():
    """
    Starts the scheduler if it exists.
    """
    global scheduler
    if scheduler and not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started.")


def stop_scheduler():
    """
    Stops the scheduler if it's running.
    """
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped.")


def get_scheduler():
    """
    Returns the global scheduler instance.
    """
    global scheduler
    return scheduler


def remove_monthly_job():
    """
    Removes the monthly report job from the scheduler.
    """
    global scheduler
    if scheduler:
        scheduler.remove_job("monthly_report")
        logger.info("Monthly report job removed.")
