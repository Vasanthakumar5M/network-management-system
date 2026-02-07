"""
Alert and Notification Module.

Provides comprehensive alerting capabilities:
- Keyword detection (including fuzzy/leetspeak matching)
- Alert generation and management
- Desktop notifications (toast, sound, email, webhook)
- Predefined keywords for concerning content
"""

from .alert_engine import (
    Alert,
    AlertEngine,
    AlertRule,
)
from .keywords import (
    AlertCategory,
    AlertSeverity,
    Keyword,
    KeywordMatch,
    KeywordMatcher,
    MatchType,
    PREDEFINED_KEYWORDS,
)
from .notifier import (
    NotificationConfig,
    NotificationType,
    Notifier,
)

__all__ = [
    # Alert Engine
    "AlertEngine",
    "Alert",
    "AlertRule",
    # Keywords
    "KeywordMatcher",
    "Keyword",
    "KeywordMatch",
    "MatchType",
    "AlertCategory",
    "AlertSeverity",
    "PREDEFINED_KEYWORDS",
    # Notifier
    "Notifier",
    "NotificationConfig",
    "NotificationType",
]
