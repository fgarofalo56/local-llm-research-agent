"""
Query Scheduler Service
Phase 2.5: Advanced Features & Polish

Service for scheduling automated query execution.
"""

from collections.abc import Callable
from datetime import datetime

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.database import ScheduledQuery

logger = structlog.get_logger()


class QueryScheduler:
    """Service for scheduling query execution."""

    def __init__(self, session_factory: Callable[[], AsyncSession]):
        """
        Initialize the query scheduler.

        Args:
            session_factory: Async context manager that yields database sessions
        """
        self.scheduler = AsyncIOScheduler()
        self.session_factory = session_factory
        self._running = False

    async def start(self) -> None:
        """Start the query scheduler and load existing scheduled queries."""
        if self._running:
            logger.warning("query_scheduler_already_running")
            return

        # Load existing scheduled queries
        job_count = 0
        async with self.session_factory() as db:
            query = select(ScheduledQuery).where(ScheduledQuery.is_active == True)  # noqa: E712
            result = await db.execute(query)
            queries = result.scalars().all()

            for sq in queries:
                if self._add_job(sq):
                    job_count += 1

        self.scheduler.start()
        self._running = True
        logger.info("query_scheduler_started", job_count=job_count)

    async def stop(self) -> None:
        """Stop the query scheduler."""
        if self._running:
            self.scheduler.shutdown(wait=False)
            self._running = False
            logger.info("query_scheduler_stopped")

    @property
    def is_running(self) -> bool:
        """Check if the scheduler is running."""
        return self._running

    def _add_job(self, scheduled_query: ScheduledQuery) -> bool:
        """
        Add a job for a scheduled query.

        Args:
            scheduled_query: The scheduled query to add

        Returns:
            True if job was added successfully
        """
        try:
            trigger = CronTrigger.from_crontab(scheduled_query.cron_expression)
            self.scheduler.add_job(
                self._execute_query,
                trigger,
                args=[scheduled_query.id],
                id=f"scheduled_query_{scheduled_query.id}",
                replace_existing=True,
            )
            logger.debug("scheduled_query_job_added", query_id=scheduled_query.id)
            return True
        except Exception as e:
            logger.error(
                "scheduled_query_add_error",
                query_id=scheduled_query.id,
                error=str(e),
            )
            return False

    def _remove_job(self, query_id: int) -> None:
        """
        Remove a scheduled query job.

        Args:
            query_id: ID of the scheduled query
        """
        job_id = f"scheduled_query_{query_id}"
        try:
            self.scheduler.remove_job(job_id)
            logger.debug("scheduled_query_job_removed", query_id=query_id)
        except Exception:
            pass  # Job may not exist

    async def _execute_query(self, query_id: int) -> None:
        """
        Execute a scheduled query.

        Args:
            query_id: ID of the scheduled query to execute
        """
        async with self.session_factory() as db:
            sq = await db.get(ScheduledQuery, query_id)
            if not sq or not sq.is_active:
                logger.warning("scheduled_query_not_found_or_inactive", query_id=query_id)
                return

            try:
                result = await db.execute(text(sq.query))
                rows = result.fetchall()

                sq.last_run_at = datetime.utcnow()
                # Calculate next run time
                trigger = CronTrigger.from_crontab(sq.cron_expression)
                next_fire = trigger.get_next_fire_time(None, datetime.utcnow())
                sq.next_run_at = next_fire

                await db.commit()

                logger.info(
                    "scheduled_query_executed",
                    query_id=query_id,
                    name=sq.name,
                    rows=len(rows),
                )

                # Optionally send notification about execution
                from src.services.notification_service import notification_service

                await notification_service.send_notification(
                    notification_type="scheduled_query_complete",
                    title=f"Scheduled Query: {sq.name}",
                    message=f"Query executed successfully, returned {len(rows)} rows",
                    data={"query_id": query_id, "row_count": len(rows)},
                )

            except Exception as e:
                logger.error("scheduled_query_error", query_id=query_id, error=str(e))

    async def add_scheduled_query(self, scheduled_query: ScheduledQuery) -> bool:
        """
        Add a new scheduled query to the scheduler.

        Args:
            scheduled_query: The scheduled query to add

        Returns:
            True if added successfully
        """
        if not self._running:
            logger.warning("query_scheduler_not_running")
            return False
        return self._add_job(scheduled_query)

    async def update_scheduled_query(self, scheduled_query: ScheduledQuery) -> None:
        """
        Update an existing scheduled query in the scheduler.

        Args:
            scheduled_query: The updated scheduled query
        """
        self._remove_job(scheduled_query.id)
        if scheduled_query.is_active:
            self._add_job(scheduled_query)

    async def remove_scheduled_query(self, query_id: int) -> None:
        """
        Remove a scheduled query from the scheduler.

        Args:
            query_id: ID of the scheduled query to remove
        """
        self._remove_job(query_id)

    async def run_query_now(self, query_id: int) -> dict:
        """
        Manually trigger a scheduled query execution.

        Args:
            query_id: ID of the scheduled query to run

        Returns:
            Dictionary with execution results
        """
        async with self.session_factory() as db:
            sq = await db.get(ScheduledQuery, query_id)
            if not sq:
                return {"error": "Scheduled query not found"}

            try:
                result = await db.execute(text(sq.query))
                rows = result.fetchall()

                # Update last run time
                sq.last_run_at = datetime.utcnow()
                await db.commit()

                return {
                    "query_id": query_id,
                    "name": sq.name,
                    "row_count": len(rows),
                    "status": "executed",
                }
            except Exception as e:
                return {"query_id": query_id, "status": "error", "error": str(e)}

    def get_job_info(self, query_id: int) -> dict | None:
        """
        Get information about a scheduled job.

        Args:
            query_id: ID of the scheduled query

        Returns:
            Job information dictionary or None if not found
        """
        job_id = f"scheduled_query_{query_id}"
        job = self.scheduler.get_job(job_id)
        if job:
            return {
                "job_id": job.id,
                "next_run_time": job.next_run_time,
                "trigger": str(job.trigger),
            }
        return None
