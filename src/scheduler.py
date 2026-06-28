import logging
from datetime import datetime, timezone

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .ai_summary_service import AISummaryService
from .calendar_service import CalendarService
from .email_service import EmailService
from .slack_service import SlackService

logger = logging.getLogger(__name__)


class MeetingGuardianScheduler:
    def __init__(self) -> None:
        self._calendar = CalendarService()
        self._ai = AISummaryService()
        self._slack = SlackService()
        self._email = EmailService()
        self._scheduler = BlockingScheduler(timezone="America/Sao_Paulo")
        self._reminded_events: set[str] = set()

    def run_daily_summary(self) -> None:
        logger.info("Running daily summary job")
        try:
            events = self._calendar.get_today_events()
            summary = self._ai.generate_daily_summary(events)
            message = self._ai.generate_daily_message(summary)
            self._slack.send_direct_message(message)
            self._email.send(
                subject=f"📅 Agenda do dia — {summary.date.strftime('%d/%m/%Y')}",
                plain_body=message,
                subtitle=f"{summary.event_count} eventos • Carga {summary.workload.value}",
            )
            logger.info("Daily summary dispatched successfully")
        except Exception as exc:
            logger.error("Daily summary job failed: %s", exc, exc_info=True)

    def run_reminder_check(self) -> None:
        logger.info("Running reminder check")
        try:
            upcoming = self._calendar.get_upcoming_events(minutes_ahead=35)
            now = datetime.now(timezone.utc)
            for event in upcoming:
                minutes_until = (event.start - now).total_seconds() / 60
                if event.id in self._reminded_events:
                    continue
                if 25 <= minutes_until <= 35:
                    self._send_reminder(event)
                    self._reminded_events.add(event.id)
        except Exception as exc:
            logger.error("Reminder check failed: %s", exc, exc_info=True)

    def _send_reminder(self, event) -> None:
        logger.info("Sending reminder for event: %s", event.title)
        message = self._ai.generate_reminder_message(event)
        self._slack.send_direct_message(message)
        self._email.send(
            subject=f"⏰ Lembrete: {event.title} em 30 minutos",
            plain_body=message,
            subtitle=f"Começa às {event.start.strftime('%H:%M')}",
        )

    def start(self) -> None:
        self._scheduler.add_job(
            self.run_daily_summary,
            CronTrigger(hour=6, minute=0),
            id="daily_summary",
            name="Daily Summary",
            replace_existing=True,
        )
        self._scheduler.add_job(
            self.run_reminder_check,
            IntervalTrigger(minutes=5),
            id="reminder_check",
            name="Reminder Check",
            replace_existing=True,
        )
        logger.info("Meeting Guardian scheduler started")
        self._scheduler.start()
