from __future__ import annotations

from pathlib import Path

from app.services.queue import QueueService


def make_service(tmp_path: Path, business_date: str = "2026-06-14") -> QueueService:
    service = QueueService(tmp_path / "queue.sqlite3")
    service.set_clock(f"{business_date} 09:00:00")
    return service


def test_call_orders_high_priority_then_oldest_waiting(tmp_path: Path):
    service = make_service(tmp_path)
    service.take_number("normal")
    service.take_number("vip")
    service.take_number("vip")

    result = service.call_next("station-1")

    assert result.ticket_no == "VIP-001"


def test_yesterday_waiting_tickets_are_expired_on_rollover(tmp_path: Path):
    service = make_service(tmp_path, business_date="2026-06-13")
    ticket = service.take_number("normal")
    service.set_clock("2026-06-14 08:00:00")

    service.rollover_if_needed()

    assert service.get_queue_snapshot()["waiting_count"] == 0
    assert service.get_ticket(ticket.ticket_id).status == "expired"
