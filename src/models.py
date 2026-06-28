from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class EventCategory(str, Enum):
    WORK = "Trabalho"
    STUDY = "Estudos"
    PERSONAL = "Pessoal"
    HEALTH = "Saúde"
    TRAVEL = "Viagem"
    OTHER = "Outros"


class WorkloadLevel(str, Enum):
    LIGHT = "Leve"
    MODERATE = "Moderada"
    HEAVY = "Pesada"


@dataclass
class CalendarEvent:
    id: str
    title: str
    start: datetime
    end: datetime
    description: Optional[str] = None
    location: Optional[str] = None
    meet_link: Optional[str] = None
    attendees: list[str] = field(default_factory=list)
    category: EventCategory = EventCategory.OTHER
    is_recurring: bool = False

    @property
    def duration_minutes(self) -> int:
        delta = self.end - self.start
        return int(delta.total_seconds() / 60)

    @property
    def duration_hours(self) -> float:
        return round(self.duration_minutes / 60, 2)


@dataclass
class DailySummary:
    date: datetime
    events: list[CalendarEvent]
    free_blocks: list[tuple[datetime, datetime]]
    total_meeting_hours: float
    workload: WorkloadLevel
    conflicts: list[tuple[CalendarEvent, CalendarEvent]]
    user_name: str

    @property
    def event_count(self) -> int:
        return len(self.events)
