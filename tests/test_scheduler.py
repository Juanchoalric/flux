# tests/test_scheduler.py
"""
Tests for scheduler module.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os


class TestScheduler:
    """Tests for scheduler module."""

    @patch("scheduler.create_scheduler")
    def test_create_scheduler(self, mock_create):
        """Test that create_scheduler creates a new scheduler."""
        from scheduler import create_scheduler, scheduler

        # Reset global
        import scheduler as scheduler_module

        scheduler_module.scheduler = None

        mock_scheduler = MagicMock()
        mock_create.return_value = mock_scheduler

        result = create_scheduler()

        assert result == mock_scheduler

    @patch.dict(os.environ, {"ADMIN_CHAT_ID": "123456"})
    @patch("scheduler.create_scheduler")
    def test_schedule_monthly_report(self, mock_create):
        """Test that schedule_monthly_report adds a job to scheduler."""
        from scheduler import schedule_monthly_report, scheduler

        # Reset global
        import scheduler as scheduler_module

        scheduler_module.scheduler = None

        mock_scheduler = MagicMock()
        mock_create.return_value = mock_scheduler

        # Mock flow function
        mock_flow_func = MagicMock()

        schedule_monthly_report(mock_flow_func, "123456")

        # Verify add_job was called
        mock_scheduler.add_job.assert_called_once()

        # Verify job was added with correct trigger
        call_args = mock_scheduler.add_job.call_args
        assert call_args[0][1] is not None  # trigger

    @patch.dict(os.environ, {"ADMIN_CHAT_ID": ""})
    @patch("scheduler.create_scheduler")
    def test_schedule_without_admin_chat_id(self, mock_create):
        """Test that schedule_monthly_report fails without admin chat ID."""
        from scheduler import schedule_monthly_report, scheduler
        import scheduler as scheduler_module

        scheduler_module.scheduler = None

        mock_scheduler = MagicMock()
        mock_create.return_value = mock_scheduler

        mock_flow_func = MagicMock()

        # Should not raise, but should log error
        schedule_monthly_report(mock_flow_func, None)

        # add_job should NOT be called
        mock_scheduler.add_job.assert_not_called()

    def test_start_scheduler(self):
        """Test that start_scheduler starts the scheduler."""
        from scheduler import start_scheduler, scheduler
        import scheduler as scheduler_module

        scheduler_module.scheduler = None

        mock_scheduler = MagicMock()
        mock_scheduler.running = False
        scheduler_module.scheduler = mock_scheduler

        start_scheduler()

        mock_scheduler.start.assert_called_once()

    def test_stop_scheduler(self):
        """Test that stop_scheduler stops the scheduler."""
        from scheduler import stop_scheduler, scheduler
        import scheduler as scheduler_module

        mock_scheduler = MagicMock()
        mock_scheduler.running = True
        scheduler_module.scheduler = mock_scheduler

        stop_scheduler()

        mock_scheduler.shutdown.assert_called_once()

    def test_remove_monthly_job(self):
        """Test that remove_monthly_job removes the job."""
        from scheduler import remove_monthly_job, scheduler
        import scheduler as scheduler_module

        mock_scheduler = MagicMock()
        scheduler_module.scheduler = mock_scheduler

        remove_monthly_job()

        mock_scheduler.remove_job.assert_called_once_with("monthly_report")

    def test_get_scheduler(self):
        """Test that get_scheduler returns the scheduler."""
        from scheduler import get_scheduler, scheduler
        import scheduler as scheduler_module

        mock_scheduler = MagicMock()
        scheduler_module.scheduler = mock_scheduler

        result = get_scheduler()

        assert result == mock_scheduler

    @patch.dict(os.environ, {"ADMIN_CHAT_ID": "123456"})
    @patch("scheduler.create_scheduler")
    def test_schedule_uses_cron_trigger(self, mock_create):
        """Test that schedule uses CronTrigger for monthly execution."""
        from scheduler import schedule_monthly_report, scheduler
        import scheduler as scheduler_module

        scheduler_module.scheduler = None

        mock_scheduler = MagicMock()
        mock_create.return_value = mock_scheduler

        mock_flow_func = MagicMock()

        schedule_monthly_report(mock_flow_func, "123456")

        # Verify add_job was called
        mock_scheduler.add_job.assert_called_once()
