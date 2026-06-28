import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .models import CalendarEvent, EventCategory

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

CATEGORY_KEYWORDS: dict[EventCategory, list[str]] = {
    EventCategory.WORK: [
        "reunião", "meeting", "projeto", "sprint", "review", "deploy",
        "daily", "planning", "retrospectiva", "entrega", "apresentação",
    ],
    EventCategory.STUDY: [
        "aula", "curso", "estudo", "faculdade", "cálculo", "prova",
        "workshop", "treinamento", "mentoria", "palestra",
    ],
    EventCategory.HEALTH: [
        "médico", "dentista", "consulta", "academia", "treino",
        "psicólogo", "exame", "saúde",
    ],
    EventCategory.TRAVEL: [
        "viagem", "voo", "aeroporto", "hotel", "check-in", "check-out",
    ],
    EventCategory.PERSONAL: [
        "aniversário", "família", "amigos", "lazer", "pessoal",
        "férias", "almoço", "jantar",
    ],
}


class CalendarService:
    def __init__(self) -> None:
        self._credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
        self._token_path = os.getenv("GOOGLE_TOKEN_PATH", "token.json")
        self._service = self._build_service()

    def _build_service(self):
        creds: Optional[Credentials] = None

        if os.path.exists(self._token_path):
            creds = Credentials.from_authorized_user_file(self._token_path, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self._credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(self._token_path, "w") as token_file:
                token_file.write(creds.to_json())

        return build("calendar", "v3", credentials=creds)

    def get_today_events(self) -> list[CalendarEvent]:
        now = datetime.now(timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        return self._fetch_events(start_of_day, end_of_day)

    def get_upcoming_events(self, minutes_ahead: int = 35) -> list[CalendarEvent]:
        now = datetime.now(timezone.utc)
        future = now + timedelta(minutes=minutes_ahead)
        return self._fetch_events(now, future)

    def _fetch_events(self, time_min: datetime, time_max: datetime) -> list[CalendarEvent]:
        try:
            result = (
                self._service.events()
                .list(
                    calendarId="primary",
                    timeMin=time_min.isoformat(),
                    timeMax=time_max.isoformat(),
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            raw_events = result.get("items", [])
            logger.info("Fetched %d events from Google Calendar", len(raw_events))
            return [self._parse_event(e) for e in raw_events]
        except HttpError as exc:
            logger.error("Google Calendar API error: %s", exc)
            raise

    def _parse_event(self, raw: dict) -> CalendarEvent:
        start_str = raw["start"].get("dateTime") or raw["start"].get("date")
        end_str = raw["end"].get("dateTime") or raw["end"].get("date")

        start = datetime.fromisoformat(start_str)
        end = datetime.fromisoformat(end_str)

        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)

        attendees = [
            a.get("email", "")
            for a in raw.get("attendees", [])
            if not a.get("self", False)
        ]

        meet_link: Optional[str] = None
        for entry_point in raw.get("conferenceData", {}).get("entryPoints", []):
            if entry_point.get("entryPointType") == "video":
                meet_link = entry_point.get("uri")
                break

        title = raw.get("summary", "Sem título")
        description = raw.get("description", "")
        location = raw.get("location", "")
        is_recurring = bool(raw.get("recurringEventId"))
        category = self._classify_event(title, description)

        return CalendarEvent(
            id=raw["id"],
            title=title,
            start=start,
            end=end,
            description=description or None,
            location=location or None,
            meet_link=meet_link,
            attendees=attendees,
            category=category,
            is_recurring=is_recurring,
        )

    @staticmethod
    def _classify_event(title: str, description: str) -> EventCategory:
        text = f"{title} {description}".lower()
        for category, keywords in CATEGORY_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return category
        return EventCategory.OTHER
