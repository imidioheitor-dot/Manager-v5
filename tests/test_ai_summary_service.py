from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from src.models import CalendarEvent, EventCategory, WorkloadLevel
from src.ai_summary_service import AISummaryService


@pytest.fixture
def service():
    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key", "USER_NAME": "Heitor"}):
        with patch("src.ai_summary_service.Anthropic"):
            return AISummaryService()


def make_event(start_hour: int, end_hour: int, title: str = "Test") -> CalendarEvent:
    tz = timezone.utc
    return CalendarEvent(
        id=f"evt_{start_hour}",
        title=title,
        start=datetime(2025, 1, 15, start_hour, 0, tzinfo=tz),
        end=datetime(2025, 1, 15, end_hour, 0, tzinfo=tz),
        category=EventCategory.WORK,
    )


def test_workload_light(service):
    assert service._compute_workload(1.5, 1) == WorkloadLevel.LIGHT


def test_workload_heavy(service):
    assert service._compute_workload(7.0, 8) == WorkloadLevel.HEAVY


def test_no_conflicts(service):
    assert service._detect_conflicts([make_event(9, 10), make_event(11, 12)]) == []


def test_detect_conflict(service):
    assert len(service._detect_conflicts([make_event(9, 11), make_event(10, 12)])) == 1


def test_free_blocks(service):
    blocks = service._compute_free_blocks([make_event(9, 10), make_event(12, 13)])
    assert len(blocks) == 1
    assert blocks[0][0].hour == 10
    assert blocks[0][1].hour == 12
