import logging
import os
from datetime import datetime, timezone

from anthropic import Anthropic

from .models import CalendarEvent, DailySummary, EventCategory, WorkloadLevel

logger = logging.getLogger(__name__)


class AISummaryService:
    def __init__(self) -> None:
        self._client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self._model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
        self._user_name = os.getenv("USER_NAME", "Usuário")

    def generate_daily_summary(self, events: list[CalendarEvent]) -> DailySummary:
        now = datetime.now(timezone.utc)
        free_blocks = self._compute_free_blocks(events)
        total_hours = round(sum(e.duration_hours for e in events), 2)
        workload = self._compute_workload(total_hours, len(events))
        conflicts = self._detect_conflicts(events)

        return DailySummary(
            date=now,
            events=events,
            free_blocks=free_blocks,
            total_meeting_hours=total_hours,
            workload=workload,
            conflicts=conflicts,
            user_name=self._user_name,
        )

    def generate_daily_message(self, summary: DailySummary) -> str:
        events_text = self._format_events_for_prompt(summary.events)
        free_text = self._format_free_blocks(summary.free_blocks)
        conflicts_text = (
            "Nenhum conflito detectado."
            if not summary.conflicts
            else f"{len(summary.conflicts)} conflito(s) detectado(s)."
        )

        prompt = f"""
Você é um assistente pessoal executivo. Gere um resumo diário profissional,
caloroso e objetivo para {summary.user_name}.

Data: {summary.date.strftime('%d/%m/%Y')}
Total de eventos: {summary.event_count}
Horas em reuniões: {summary.total_meeting_hours}h
Carga de trabalho: {summary.workload.value}
Conflitos: {conflicts_text}

Eventos do dia:
{events_text}

Blocos livres:
{free_text}

Escreva uma mensagem de bom dia com:
1. Saudação personalizada com o nome
2. Lista formatada de todos os eventos com horários
3. Pontos importantes (carga, blocos livres, conflitos)
4. Uma frase motivacional ao final

Use emojis com moderação. Seja conciso e direto.
"""

        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        message = response.content[0].text
        logger.info("Daily summary generated successfully")
        return message

    def generate_reminder_message(self, event: CalendarEvent) -> str:
        attendees_str = (
            ", ".join(event.attendees[:5]) if event.attendees else "Nenhum convidado"
        )
        prompt = f"""
Gere um lembrete de reunião conciso e útil para {os.getenv('USER_NAME', 'o usuário')}.

Evento: {event.title}
Horário: {event.start.strftime('%H:%M')}
Duração: {event.duration_minutes} minutos
Categoria: {event.category.value}
Descrição: {event.description or 'Sem descrição'}
Local/Link: {event.meet_link or event.location or 'Não informado'}
Participantes: {attendees_str}

Escreva um lembrete contextual de 30 minutos antes, incluindo todas as
informações relevantes. Seja direto e inclua o link se disponível.
"""

        response = self._client.messages.create(
            model=self._model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text

    @staticmethod
    def _format_events_for_prompt(events: list[CalendarEvent]) -> str:
        lines = []
        for event in events:
            lines.append(
                f"- {event.start.strftime('%H:%M')}–{event.end.strftime('%H:%M')}: "
                f"{event.title} [{event.category.value}]"
            )
        return "\n".join(lines) if lines else "Nenhum evento hoje."

    @staticmethod
    def _format_free_blocks(blocks: list[tuple[datetime, datetime]]) -> str:
        if not blocks:
            return "Nenhum bloco livre significativo."
        return "\n".join(
            f"- {s.strftime('%H:%M')}–{e.strftime('%H:%M')}" for s, e in blocks
        )

    @staticmethod
    def _compute_free_blocks(
        events: list[CalendarEvent], min_block_minutes: int = 30
    ) -> list[tuple[datetime, datetime]]:
        if not events:
            return []
        sorted_events = sorted(events, key=lambda e: e.start)
        blocks: list[tuple[datetime, datetime]] = []
        prev_end = sorted_events[0].end
        for event in sorted_events[1:]:
            gap_minutes = (event.start - prev_end).total_seconds() / 60
            if gap_minutes >= min_block_minutes:
                blocks.append((prev_end, event.start))
            prev_end = max(prev_end, event.end)
        return blocks

    @staticmethod
    def _compute_workload(total_hours: float, event_count: int) -> WorkloadLevel:
        if total_hours <= 2 and event_count <= 2:
            return WorkloadLevel.LIGHT
        if total_hours <= 5 and event_count <= 5:
            return WorkloadLevel.MODERATE
        return WorkloadLevel.HEAVY

    @staticmethod
    def _detect_conflicts(
        events: list[CalendarEvent],
    ) -> list[tuple[CalendarEvent, CalendarEvent]]:
        conflicts: list[tuple[CalendarEvent, CalendarEvent]] = []
        sorted_events = sorted(events, key=lambda e: e.start)
        for i, event_a in enumerate(sorted_events):
            for event_b in sorted_events[i + 1:]:
                if event_b.start >= event_a.end:
                    break
                conflicts.append((event_a, event_b))
        return conflicts
