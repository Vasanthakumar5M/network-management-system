"""
Time-Based Blocking Schedules.

Allows blocking content based on:
- Time of day (e.g., no gaming during homework hours)
- Day of week (e.g., stricter on school days)
- Date ranges (e.g., exam periods)
- Custom recurring schedules
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class DayOfWeek(Enum):
    """Days of the week."""
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class ScheduleType(Enum):
    """Types of schedules."""
    ALWAYS_BLOCK = "always_block"  # Always blocked
    NEVER_BLOCK = "never_block"  # Never blocked
    TIME_RANGE = "time_range"  # Blocked during specific times
    ALLOW_RANGE = "allow_range"  # Only allowed during specific times
    CUSTOM = "custom"  # Custom rules


@dataclass
class TimeRange:
    """A time range for blocking."""
    start_hour: int
    start_minute: int
    end_hour: int
    end_minute: int
    
    def contains(self, t: time) -> bool:
        """Check if a time falls within this range."""
        start = time(self.start_hour, self.start_minute)
        end = time(self.end_hour, self.end_minute)
        
        if start <= end:
            # Normal range (e.g., 9:00 - 17:00)
            return start <= t <= end
        else:
            # Overnight range (e.g., 22:00 - 06:00)
            return t >= start or t <= end
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "start": f"{self.start_hour:02d}:{self.start_minute:02d}",
            "end": f"{self.end_hour:02d}:{self.end_minute:02d}"
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TimeRange":
        """Create from dictionary."""
        start = data["start"].split(":")
        end = data["end"].split(":")
        return cls(
            start_hour=int(start[0]),
            start_minute=int(start[1]),
            end_hour=int(end[0]),
            end_minute=int(end[1])
        )
    
    def __str__(self) -> str:
        return f"{self.start_hour:02d}:{self.start_minute:02d}-{self.end_hour:02d}:{self.end_minute:02d}"


@dataclass
class Schedule:
    """
    A blocking schedule.
    
    Defines when blocking rules are active.
    """
    id: str
    name: str
    schedule_type: ScheduleType
    enabled: bool = True
    
    # Categories/domains this schedule applies to
    categories: Set[str] = field(default_factory=set)
    domains: Set[str] = field(default_factory=set)
    
    # Time-based rules
    time_ranges: Dict[DayOfWeek, List[TimeRange]] = field(default_factory=dict)
    
    # Date-based rules (for special periods like exams)
    start_date: Optional[str] = None  # YYYY-MM-DD
    end_date: Optional[str] = None  # YYYY-MM-DD
    
    # Priority (higher = more important)
    priority: int = 0
    
    # Metadata
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def is_active_now(self, dt: Optional[datetime] = None) -> bool:
        """
        Check if this schedule is currently active.
        
        Args:
            dt: Datetime to check (defaults to now)
            
        Returns:
            True if the schedule is active
        """
        if not self.enabled:
            return False
        
        if dt is None:
            dt = datetime.now()
        
        # Check date range
        if self.start_date:
            start = datetime.strptime(self.start_date, "%Y-%m-%d")
            if dt.date() < start.date():
                return False
        
        if self.end_date:
            end = datetime.strptime(self.end_date, "%Y-%m-%d")
            if dt.date() > end.date():
                return False
        
        # Handle schedule types
        if self.schedule_type == ScheduleType.ALWAYS_BLOCK:
            return True
        
        if self.schedule_type == ScheduleType.NEVER_BLOCK:
            return False
        
        # Check time ranges
        day = DayOfWeek(dt.weekday())
        current_time = dt.time()
        
        day_ranges = self.time_ranges.get(day, [])
        
        if self.schedule_type == ScheduleType.TIME_RANGE:
            # Block if current time is in any range
            for time_range in day_ranges:
                if time_range.contains(current_time):
                    return True
            return False
        
        elif self.schedule_type == ScheduleType.ALLOW_RANGE:
            # Block if current time is NOT in any range
            for time_range in day_ranges:
                if time_range.contains(current_time):
                    return False
            return True
        
        return False
    
    def should_block(self, domain: str = "", category: str = "") -> bool:
        """
        Check if this schedule blocks the given domain/category.
        
        Args:
            domain: Domain to check
            category: Category to check
            
        Returns:
            True if should be blocked
        """
        if not self.is_active_now():
            return False
        
        # Check if domain matches
        if domain:
            domain = domain.lower()
            for blocked in self.domains:
                if domain == blocked or domain.endswith('.' + blocked):
                    return True
        
        # Check if category matches
        if category:
            if category.lower() in {c.lower() for c in self.categories}:
                return True
        
        # If no specific targets, applies to all
        if not self.domains and not self.categories:
            return True
        
        return False
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "schedule_type": self.schedule_type.value,
            "enabled": self.enabled,
            "categories": list(self.categories),
            "domains": list(self.domains),
            "time_ranges": {
                day.name: [tr.to_dict() for tr in ranges]
                for day, ranges in self.time_ranges.items()
            },
            "start_date": self.start_date,
            "end_date": self.end_date,
            "priority": self.priority,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Schedule":
        """Create from dictionary."""
        time_ranges = {}
        for day_name, ranges in data.get("time_ranges", {}).items():
            day = DayOfWeek[day_name]
            time_ranges[day] = [TimeRange.from_dict(r) for r in ranges]
        
        return cls(
            id=data["id"],
            name=data["name"],
            schedule_type=ScheduleType(data["schedule_type"]),
            enabled=data.get("enabled", True),
            categories=set(data.get("categories", [])),
            domains=set(data.get("domains", [])),
            time_ranges=time_ranges,
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            priority=data.get("priority", 0),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


class ScheduleManager:
    """
    Manages blocking schedules.
    
    Provides methods to create, update, and evaluate schedules.
    """
    
    def __init__(self, schedule_file: Optional[str] = None):
        """
        Initialize the schedule manager.
        
        Args:
            schedule_file: Path to JSON file storing schedules
        """
        if schedule_file is None:
            project_root = Path(__file__).parent.parent.parent
            schedule_file = project_root / "config" / "schedules.json"
        
        self.schedule_file = Path(schedule_file)
        self.schedules: Dict[str, Schedule] = {}
        self._load_schedules()
    
    def _load_schedules(self):
        """Load schedules from file."""
        if self.schedule_file.exists():
            try:
                data = json.loads(self.schedule_file.read_text())
                for sched_data in data.get("schedules", []):
                    schedule = Schedule.from_dict(sched_data)
                    self.schedules[schedule.id] = schedule
            except Exception as e:
                print(json.dumps({"error": f"Failed to load schedules: {e}"}))
    
    def _save_schedules(self):
        """Save schedules to file."""
        self.schedule_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "schedules": [s.to_dict() for s in self.schedules.values()]
        }
        self.schedule_file.write_text(json.dumps(data, indent=2))
    
    def add_schedule(self, schedule: Schedule) -> bool:
        """
        Add a new schedule.
        
        Args:
            schedule: Schedule to add
            
        Returns:
            True if added successfully
        """
        schedule.created_at = datetime.now().isoformat()
        schedule.updated_at = schedule.created_at
        self.schedules[schedule.id] = schedule
        self._save_schedules()
        return True
    
    def update_schedule(self, schedule_id: str, updates: dict) -> bool:
        """
        Update an existing schedule.
        
        Args:
            schedule_id: ID of schedule to update
            updates: Dictionary of fields to update
            
        Returns:
            True if updated successfully
        """
        if schedule_id not in self.schedules:
            return False
        
        schedule = self.schedules[schedule_id]
        
        for key, value in updates.items():
            if hasattr(schedule, key):
                setattr(schedule, key, value)
        
        schedule.updated_at = datetime.now().isoformat()
        self._save_schedules()
        return True
    
    def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule."""
        if schedule_id in self.schedules:
            del self.schedules[schedule_id]
            self._save_schedules()
            return True
        return False
    
    def get_schedule(self, schedule_id: str) -> Optional[Schedule]:
        """Get a schedule by ID."""
        return self.schedules.get(schedule_id)
    
    def list_schedules(self) -> List[Schedule]:
        """List all schedules."""
        return list(self.schedules.values())
    
    def should_block(
        self,
        domain: str = "",
        category: str = "",
        dt: Optional[datetime] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a domain/category should be blocked right now.
        
        Args:
            domain: Domain to check
            category: Category to check
            dt: Datetime to check (defaults to now)
            
        Returns:
            Tuple of (should_block, schedule_id that matched)
        """
        # Sort by priority (higher first)
        sorted_schedules = sorted(
            self.schedules.values(),
            key=lambda s: s.priority,
            reverse=True
        )
        
        for schedule in sorted_schedules:
            if schedule.should_block(domain, category):
                return True, schedule.id
        
        return False, None
    
    def get_active_schedules(self, dt: Optional[datetime] = None) -> List[Schedule]:
        """Get all currently active schedules."""
        return [s for s in self.schedules.values() if s.is_active_now(dt)]


# Preset schedules
PRESET_SCHEDULES = {
    "school_hours": Schedule(
        id="preset_school_hours",
        name="School Hours",
        schedule_type=ScheduleType.TIME_RANGE,
        categories={"gaming", "streaming", "social_media"},
        time_ranges={
            DayOfWeek.MONDAY: [TimeRange(8, 0, 15, 0)],
            DayOfWeek.TUESDAY: [TimeRange(8, 0, 15, 0)],
            DayOfWeek.WEDNESDAY: [TimeRange(8, 0, 15, 0)],
            DayOfWeek.THURSDAY: [TimeRange(8, 0, 15, 0)],
            DayOfWeek.FRIDAY: [TimeRange(8, 0, 15, 0)],
        }
    ),
    "homework_time": Schedule(
        id="preset_homework",
        name="Homework Time",
        schedule_type=ScheduleType.TIME_RANGE,
        categories={"gaming", "streaming", "social_media"},
        time_ranges={
            DayOfWeek.MONDAY: [TimeRange(16, 0, 18, 0)],
            DayOfWeek.TUESDAY: [TimeRange(16, 0, 18, 0)],
            DayOfWeek.WEDNESDAY: [TimeRange(16, 0, 18, 0)],
            DayOfWeek.THURSDAY: [TimeRange(16, 0, 18, 0)],
            DayOfWeek.FRIDAY: [TimeRange(16, 0, 18, 0)],
        }
    ),
    "bedtime": Schedule(
        id="preset_bedtime",
        name="Bedtime",
        schedule_type=ScheduleType.TIME_RANGE,
        categories={"gaming", "streaming", "social_media"},
        time_ranges={
            day: [TimeRange(21, 0, 7, 0)]
            for day in DayOfWeek
        }
    ),
    "weekday_strict": Schedule(
        id="preset_weekday_strict",
        name="Weekday Strict Mode",
        schedule_type=ScheduleType.ALLOW_RANGE,
        categories={"gaming", "streaming"},
        time_ranges={
            DayOfWeek.MONDAY: [TimeRange(18, 0, 20, 0)],
            DayOfWeek.TUESDAY: [TimeRange(18, 0, 20, 0)],
            DayOfWeek.WEDNESDAY: [TimeRange(18, 0, 20, 0)],
            DayOfWeek.THURSDAY: [TimeRange(18, 0, 20, 0)],
            DayOfWeek.FRIDAY: [TimeRange(18, 0, 21, 0)],
        }
    ),
}


def get_preset_schedule(preset_name: str) -> Optional[Schedule]:
    """Get a preset schedule by name."""
    return PRESET_SCHEDULES.get(preset_name)


def list_presets() -> List[dict]:
    """List available preset schedules."""
    return [
        {
            "id": s.id,
            "name": s.name,
            "type": s.schedule_type.value,
            "categories": list(s.categories)
        }
        for s in PRESET_SCHEDULES.values()
    ]


def output_json(data: dict) -> None:
    """Output data as JSON to stdout for Tauri IPC."""
    print(json.dumps(data, default=str), flush=True)


def main():
    """CLI entry point for schedule management."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage blocking schedules")
    parser.add_argument("--action", choices=["list", "presets", "add", "check"],
                       default="list", help="Action to perform")
    parser.add_argument("--preset", help="Preset schedule to add")
    parser.add_argument("--domain", help="Domain to check")
    parser.add_argument("--category", help="Category to check")
    
    args = parser.parse_args()
    
    manager = ScheduleManager()
    
    try:
        if args.action == "list":
            schedules = [s.to_dict() for s in manager.list_schedules()]
            output_json({
                "success": True,
                "schedules": schedules
            })
        
        elif args.action == "presets":
            output_json({
                "success": True,
                "presets": list_presets()
            })
        
        elif args.action == "add":
            if args.preset:
                preset = get_preset_schedule(args.preset)
                if preset:
                    manager.add_schedule(preset)
                    output_json({
                        "success": True,
                        "message": f"Added preset: {args.preset}"
                    })
                else:
                    output_json({
                        "success": False,
                        "error": f"Unknown preset: {args.preset}"
                    })
            else:
                output_json({
                    "success": False,
                    "error": "No preset specified"
                })
        
        elif args.action == "check":
            should_block, schedule_id = manager.should_block(
                domain=args.domain or "",
                category=args.category or ""
            )
            output_json({
                "success": True,
                "should_block": should_block,
                "matched_schedule": schedule_id
            })
    
    except Exception as e:
        output_json({
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        })


if __name__ == "__main__":
    main()
