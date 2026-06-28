from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.calendar_service import CalendarService
from src.models import EventCategory


@pytest.fixture
def mock_service():
    with patch("src.calendar_service.build"), \
         patch("src.calendar_service.Credentials"), \
         patch("os.path.exists", return_value=False), \
         patch("src.calendar_service.InstalledAppFlow") as mock_flow:
        mock_flow.from_client_secrets_file.return_value.run_local_server \
            .return_value = MagicMock()
        service = CalendarService.__new__(CalendarService)
        service._service = MagicMock()
        service._credentials_path = "credentials.json"
        service._token_path = "token.json"
        yield service


RAW_EVENT = {
    "id": "abc123",
    "summary": "Reunião de Projeto",
    "start": {"dateTime": "2025-01-15T14:00:00-03:00"},
    "end":   {"dateTime": "2025-01-15T15:00:00-03:00"},
    "description": "Discussão do protótipo",
    "location": "",
    "attendees": [
        {"email": "ana@example.com", "self": False},
        {"email": "me@example.com",  "self": True},
    ],
    "conferenceData": {
        "entryPoints": [
            {"entryPointType": "video", "uri": "https://meet.google.com/abc-123"}
        ]
    },
    "recurringEventId": "",
}


def test_parse_event_basic(mock_service):
    event = mock_service._parse_event(RAW_EVENT)
    assert event.title == "Reunião de Projeto"
    assert event.duration_minutes == 60
    assert "ana@example.com" in event.attendees
    assert event.meet_link == "https://meet.google.com/abc-123"


def test_classify_work_event(mock_service):
    assert mock_service._classify_event("Daily Standup", "sprint review") == EventCategory.WORK


def test_classify_study_event(mock_service):
    assert mock_service._classify_event("Aula de Cálculo", "") == EventCategory.STUDY


def test_classify_health_event(mock_service):
    assert mock_service._classify_event("Consulta médico", "") == EventCategory.HEALTH


def test_classify_other_event(mock_service):
    assert mock_service._classify_event("Evento sem categoria", "") == EventCategory.OTHER
