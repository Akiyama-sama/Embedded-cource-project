from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder

from app.realtime import ConnectionManager
from app.schemas import CallResponse, StateResponse, TakeTicketRequest, TicketResponse
from app.services.queue import NoPreviousCallError, QueueEmptyError, QueueService

router = APIRouter()


def get_service(request: Request) -> QueueService:
    return request.app.state.queue_service


def get_realtime(request: Request) -> ConnectionManager:
    return request.app.state.realtime


def _jsonable_snapshot(service: QueueService) -> dict[str, Any]:
    return service.get_queue_snapshot()


async def broadcast_snapshot(request: Request, event: str, payload: dict[str, Any] | None = None) -> None:
    service = get_service(request)
    message = {"type": "queue_snapshot", "event": event, "state": _jsonable_snapshot(service)}
    if payload is not None:
        message["payload"] = payload
    await get_realtime(request).broadcast(jsonable_encoder(message))


@router.post("/api/tickets", response_model=TicketResponse)
async def take_ticket(request: Request, body: TakeTicketRequest) -> Any:
    ticket = get_service(request).take_number(body.priority)
    payload = ticket.__dict__
    await broadcast_snapshot(request, "ticket_created", payload)
    return payload


@router.post("/api/stations/{station_id}/next", response_model=CallResponse)
async def call_next(request: Request, station_id: str) -> Any:
    try:
        call = get_service(request).call_next(station_id)
    except QueueEmptyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    payload = call.__dict__
    await broadcast_snapshot(request, "ticket_called", payload)
    return payload


@router.post("/api/stations/{station_id}/repeat", response_model=CallResponse)
async def repeat_call(request: Request, station_id: str) -> Any:
    try:
        call = get_service(request).repeat_last(station_id)
    except NoPreviousCallError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    payload = call.__dict__
    await broadcast_snapshot(request, "call_repeated", payload)
    return payload


@router.get("/api/state", response_model=StateResponse)
async def get_state(request: Request) -> Any:
    return _jsonable_snapshot(get_service(request))


async def websocket_endpoint(websocket: WebSocket) -> None:
    manager: ConnectionManager = websocket.app.state.realtime
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
