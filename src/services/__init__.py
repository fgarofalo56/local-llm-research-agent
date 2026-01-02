"""
Services Module
Phase 2.5: Advanced Features & Polish

Contains background services for alerts and scheduled queries,
and service layer for business logic separation.
"""

from src.services.alert_scheduler import AlertScheduler
from src.services.config_service import ConfigService, get_config
from src.services.dashboard_service import DashboardService
from src.services.document_service import DocumentService
from src.services.notification_service import NotificationService
from src.services.query_scheduler import QueryScheduler
from src.services.query_service import QueryService

__all__ = [
    "AlertScheduler",
    "ConfigService",
    "DashboardService",
    "DocumentService",
    "NotificationService",
    "QueryScheduler",
    "QueryService",
    "get_config",
]
