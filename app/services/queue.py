from __future__ import annotations

from datetime import datetime
from pathlib import Path
import threading
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from app.db import create_session_factory
from app.domain import CallView, Priority, TicketStatus, TicketView
from app.models import CallRecord, Ticket


class QueueEmptyError(RuntimeError):
    pass


class NoPreviousCallError(RuntimeError):
    pass


class QueueService:
    def __init__(
        self,
        db_path: Path | str,
        business_tz: str = "Asia/Shanghai",
        session_factory: sessionmaker | None = None,
    ) -> None:
        self.business_tz = ZoneInfo(business_tz)
        self._session_factory = session_factory or create_session_factory(db_path)
        self._lock = threading.RLock()
        self._clock_override: datetime | None = None

    def set_clock(self, value: str | datetime | None) -> None:
        if value is None:
            self._clock_override = None
            return
        if isinstance(value, datetime):
            self._clock_override = value.astimezone(self.business_tz) if value.tzinfo else value.replace(tzinfo=self.business_tz)
            return
        parsed = datetime.fromisoformat(value)
        self._clock_override = parsed.astimezone(self.business_tz) if parsed.tzinfo else parsed.replace(tzinfo=self.business_tz)

    def take_number(self, priority: str) -> TicketView:
        with self._lock:
            now = self._now()
            business_date = self._business_date(now)
            self.rollover_if_needed(now)
            parsed_priority = Priority(priority)
            with self._session_factory() as session:
                max_sequence = session.scalar(
                    select(func.max(Ticket.sequence)).where(
                        Ticket.business_date == business_date,
                        Ticket.priority == parsed_priority.value,
                    )
                )
                sequence = int(max_sequence or 0) + 1
                ticket = Ticket(
                    ticket_no=f"{parsed_priority.prefix}-{sequence:03d}",
                    priority=parsed_priority.value,
                    priority_weight=parsed_priority.weight,
                    status=TicketStatus.waiting.value,
                    business_date=business_date,
                    sequence=sequence,
                    created_at=now,
                )
                session.add(ticket)
                session.commit()
                session.refresh(ticket)
                return self._ticket_view(ticket)

    def call_next(self, station_id: str) -> CallView:
        with self._lock:
            now = self._now()
            self.rollover_if_needed(now)
            with self._session_factory() as session:
                ticket = session.scalar(
                    select(Ticket)
                    .where(
                        Ticket.business_date == self._business_date(now),
                        Ticket.status == TicketStatus.waiting.value,
                    )
                    .order_by(Ticket.priority_weight.desc(), Ticket.created_at.asc(), Ticket.id.asc())
                    .limit(1)
                )
                if ticket is None:
                    raise QueueEmptyError("当前没有等待叫号的客户")
                ticket.status = TicketStatus.called.value
                ticket.called_at = now
                ticket.station_id = station_id
                call = CallRecord(
                    station_id=station_id,
                    ticket_id=ticket.id,
                    ticket_no=ticket.ticket_no,
                    priority=ticket.priority,
                    announcement_text=self._announcement_text(ticket.ticket_no, station_id),
                    called_at=now,
                )
                session.add(call)
                session.commit()
                session.refresh(call)
                return self._call_view(call)

    def repeat_last(self, station_id: str) -> CallView:
        with self._lock:
            with self._session_factory() as session:
                call = session.scalar(
                    select(CallRecord)
                    .where(CallRecord.station_id == station_id)
                    .order_by(CallRecord.called_at.desc(), CallRecord.id.desc())
                    .limit(1)
                )
                if call is None:
                    raise NoPreviousCallError("当前窗口还没有叫号记录")
                return self._call_view(call)

    def rollover_if_needed(self, now: datetime | None = None) -> None:
        current_date = self._business_date(now or self._now())
        with self._session_factory() as session:
            session.query(Ticket).filter(
                Ticket.business_date != current_date,
                Ticket.status == TicketStatus.waiting.value,
            ).update({Ticket.status: TicketStatus.expired.value}, synchronize_session=False)
            session.commit()

    def get_ticket(self, ticket_id: int) -> TicketView:
        with self._session_factory() as session:
            ticket = session.get(Ticket, ticket_id)
            if ticket is None:
                raise KeyError(ticket_id)
            return self._ticket_view(ticket)

    def get_queue_snapshot(self) -> dict:
        self.rollover_if_needed()
        business_date = self._business_date(self._now())
        with self._session_factory() as session:
            waiting_tickets = list(
                session.scalars(
                    select(Ticket)
                    .where(Ticket.business_date == business_date, Ticket.status == TicketStatus.waiting.value)
                    .order_by(Ticket.priority_weight.desc(), Ticket.created_at.asc(), Ticket.id.asc())
                )
            )
            called_tickets = list(
                session.scalars(
                    select(Ticket)
                    .where(Ticket.business_date == business_date, Ticket.status == TicketStatus.called.value)
                    .order_by(Ticket.called_at.desc(), Ticket.id.desc())
                )
            )
            last_calls = list(
                session.scalars(select(CallRecord).order_by(CallRecord.called_at.desc(), CallRecord.id.desc()))
            )
            last_by_station: dict[str, dict] = {}
            for call in last_calls:
                if call.station_id not in last_by_station:
                    last_by_station[call.station_id] = self._call_view(call).__dict__
            return {
                "business_date": business_date,
                "waiting_count": len(waiting_tickets),
                "called_count": len(called_tickets),
                "waiting_tickets": [self._ticket_view(ticket).__dict__ for ticket in waiting_tickets],
                "last_calls": last_by_station,
            }

    def _now(self) -> datetime:
        return self._clock_override or datetime.now(self.business_tz)

    def _business_date(self, now: datetime) -> str:
        if now.tzinfo is None:
            now = now.replace(tzinfo=self.business_tz)
        return now.astimezone(self.business_tz).date().isoformat()

    def _announcement_text(self, ticket_no: str, station_id: str) -> str:
        station_name = station_id.replace("station-", "")
        return f"请 {ticket_no} 号客户到 {station_name} 号窗口办理业务"

    def _ticket_view(self, ticket: Ticket) -> TicketView:
        priority = Priority(ticket.priority)
        return TicketView(
            ticket_id=ticket.id,
            ticket_no=ticket.ticket_no,
            priority=ticket.priority,
            priority_label=priority.label,
            status=ticket.status,
            business_date=ticket.business_date,
            created_at=ticket.created_at,
            called_at=ticket.called_at,
            station_id=ticket.station_id,
        )

    def _call_view(self, call: CallRecord) -> CallView:
        return CallView(
            call_id=call.id,
            station_id=call.station_id,
            ticket_id=call.ticket_id,
            ticket_no=call.ticket_no,
            priority=call.priority,
            announcement_text=call.announcement_text,
            called_at=call.called_at,
        )
