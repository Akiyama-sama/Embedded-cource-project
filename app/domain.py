from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Priority(str, Enum):
    vip = "vip"
    normal = "normal"

    @property
    def weight(self) -> int:
        return {Priority.vip: 2, Priority.normal: 1}[self]

    @property
    def prefix(self) -> str:
        return {Priority.vip: "VIP", Priority.normal: "A"}[self]

    @property
    def label(self) -> str:
        return {Priority.vip: "优先业务", Priority.normal: "普通业务"}[self]


class TicketStatus(str, Enum):
    waiting = "waiting"
    called = "called"
    expired = "expired"


@dataclass(frozen=True)
class TicketView:
    ticket_id: int
    ticket_no: str
    priority: str
    priority_label: str
    status: str
    business_date: str
    created_at: datetime
    called_at: datetime | None = None
    station_id: str | None = None


@dataclass(frozen=True)
class CallView:
    call_id: int
    station_id: str
    ticket_id: int
    ticket_no: str
    priority: str
    announcement_text: str
    called_at: datetime
