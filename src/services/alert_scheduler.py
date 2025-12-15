"""
Alert Scheduler Service
Phase 2.5: Advanced Features & Polish

Service for scheduling and evaluating data alerts.
"""

from datetime import datetime
from typing import Callable

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.database import DataAlert

logger = structlog.get_logger()


class AlertScheduler:
    """Service for scheduling and evaluating data alerts."""

    def __init__(self, session_factory: Callable[[], AsyncSession]):
        """
        Initialize the alert scheduler.

        Args:
            session_factory: Async context manager that yields database sessions
        """
        self.scheduler = AsyncIOScheduler()
        self.session_factory = session_factory
        self._running = False

    async def start(self, check_interval_minutes: int = 1) -> None:
        """
        Start the alert scheduler.

        Args:
            check_interval_minutes: Interval in minutes between alert checks
        """
        if self._running:
            logger.warning("alert_scheduler_already_running")
            return

        # Add job to check alerts at the specified interval
        self.scheduler.add_job(
            self._check_alerts,
            IntervalTrigger(minutes=check_interval_minutes),
            id="alert_checker",
            replace_existing=True,
        )

        self.scheduler.start()
        self._running = True
        logger.info("alert_scheduler_started", interval_minutes=check_interval_minutes)

    async def stop(self) -> None:
        """Stop the alert scheduler."""
        if self._running:
            self.scheduler.shutdown(wait=False)
            self._running = False
            logger.info("alert_scheduler_stopped")

    @property
    def is_running(self) -> bool:
        """Check if the scheduler is running."""
        return self._running

    async def _check_alerts(self) -> None:
        """Check all active alerts."""
        logger.debug("checking_alerts")
        async with self.session_factory() as db:
            # Get active alerts
            query = select(DataAlert).where(DataAlert.is_active == True)  # noqa: E712
            result = await db.execute(query)
            alerts = result.scalars().all()

            for alert in alerts:
                try:
                    await self._evaluate_alert(db, alert)
                except Exception as e:
                    logger.error("alert_evaluation_error", alert_id=alert.id, error=str(e))

    async def _evaluate_alert(self, db: AsyncSession, alert: DataAlert) -> None:
        """Evaluate a single alert."""
        # Execute the query
        try:
            result = await db.execute(text(alert.query))
            row = result.fetchone()

            if not row:
                logger.debug("alert_query_no_results", alert_id=alert.id)
                return

            current_value = float(row[0])
        except Exception as e:
            logger.error("alert_query_error", alert_id=alert.id, error=str(e))
            return

        # Check condition
        threshold = float(alert.threshold) if alert.threshold else 0
        triggered = False

        if alert.condition == "greater_than":
            triggered = current_value > threshold
        elif alert.condition == "less_than":
            triggered = current_value < threshold
        elif alert.condition == "equals":
            triggered = abs(current_value - threshold) < 0.001
        elif alert.condition == "changes":
            if alert.last_value is not None:
                try:
                    last_val = float(alert.last_value)
                    triggered = abs(current_value - last_val) > 0.001
                except ValueError:
                    triggered = str(current_value) != alert.last_value

        # Update alert record
        alert.last_checked_at = datetime.utcnow()
        alert.last_value = str(current_value)

        if triggered:
            alert.last_triggered_at = datetime.utcnow()
            await self._send_notification(alert, current_value)
            logger.info(
                "alert_triggered",
                alert_id=alert.id,
                name=alert.name,
                value=current_value,
                threshold=threshold,
            )

        await db.commit()

    async def _send_notification(self, alert: DataAlert, value: float) -> None:
        """Send notification for triggered alert."""
        from src.services.notification_service import notification_service

        threshold = float(alert.threshold) if alert.threshold else 0
        await notification_service.send_alert(
            alert_id=alert.id,
            alert_name=alert.name,
            condition=alert.condition,
            threshold=threshold,
            current_value=value,
        )

    async def check_alert_now(self, alert_id: int) -> dict:
        """
        Manually trigger a check for a specific alert.

        Args:
            alert_id: ID of the alert to check

        Returns:
            Dictionary with check results
        """
        async with self.session_factory() as db:
            alert = await db.get(DataAlert, alert_id)
            if not alert:
                return {"error": "Alert not found"}

            try:
                result = await db.execute(text(alert.query))
                row = result.fetchone()

                if not row:
                    return {"alert_id": alert_id, "status": "no_results"}

                current_value = float(row[0])
                threshold = float(alert.threshold) if alert.threshold else 0

                # Check condition
                triggered = False
                if alert.condition == "greater_than":
                    triggered = current_value > threshold
                elif alert.condition == "less_than":
                    triggered = current_value < threshold
                elif alert.condition == "equals":
                    triggered = abs(current_value - threshold) < 0.001
                elif alert.condition == "changes":
                    if alert.last_value is not None:
                        try:
                            triggered = abs(current_value - float(alert.last_value)) > 0.001
                        except ValueError:
                            triggered = str(current_value) != alert.last_value

                return {
                    "alert_id": alert_id,
                    "name": alert.name,
                    "current_value": current_value,
                    "threshold": threshold,
                    "condition": alert.condition,
                    "triggered": triggered,
                    "status": "checked",
                }
            except Exception as e:
                return {"alert_id": alert_id, "status": "error", "error": str(e)}
