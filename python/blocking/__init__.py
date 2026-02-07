"""
Website/Content Blocking Module.

Provides comprehensive blocking capabilities:
- Category-based blocking (adult, gambling, etc.)
- Domain/URL blocking
- Time-based schedules (school hours, bedtime, etc.)
- Keyword filtering
"""

from .blocker import (
    BlockDecision,
    BlockingEngine,
    BlockRule,
)
from .categories import (
    BlockCategory,
    CategoryDefinition,
    CATEGORY_DEFINITIONS,
    check_domain_category,
    check_url_keywords,
    get_all_categories,
    get_category,
    get_category_definition,
)
from .schedules import (
    DayOfWeek,
    PRESET_SCHEDULES,
    Schedule,
    ScheduleManager,
    ScheduleType,
    TimeRange,
    get_preset_schedule,
    list_presets,
)

__all__ = [
    # Blocker Engine
    "BlockingEngine",
    "BlockDecision",
    "BlockRule",
    # Categories
    "BlockCategory",
    "CategoryDefinition",
    "CATEGORY_DEFINITIONS",
    "get_category",
    "get_category_definition",
    "get_all_categories",
    "check_domain_category",
    "check_url_keywords",
    # Schedules
    "Schedule",
    "ScheduleManager",
    "ScheduleType",
    "DayOfWeek",
    "TimeRange",
    "PRESET_SCHEDULES",
    "get_preset_schedule",
    "list_presets",
]
