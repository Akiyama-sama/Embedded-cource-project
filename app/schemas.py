from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TakeTicketRequest(BaseModel):
    priority: str = Field(pattern="^(vip|normal)$")


class TicketResponse(BaseModel):
    ticket_id: int
    ticket_no: str
    priority: str
    priority_label: str
    status: str
    business_date: str
    created_at: datetime
    called_at: datetime | None = None
    station_id: str | None = None


class CallResponse(BaseModel):
    call_id: int
    station_id: str
    ticket_id: int
    ticket_no: str
    priority: str
    announcement_text: str
    called_at: datetime


class StateResponse(BaseModel):
    business_date: str
    waiting_count: int
    called_count: int
    waiting_tickets: list[dict]
    last_calls: dict[str, dict]
