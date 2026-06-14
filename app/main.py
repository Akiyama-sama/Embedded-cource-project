from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.realtime import ConnectionManager
from app.routers.api import router as api_router
from app.routers.api import websocket_endpoint
from app.routers.pages import router as pages_router
from app.services.queue import QueueService


def create_app(db_path: str | Path | None = None) -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="银行营业大厅排队叫号系统")
    app.state.settings = settings
    app.state.queue_service = QueueService(db_path or settings.db_path, business_tz=settings.business_tz)
    app.state.realtime = ConnectionManager()
    app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
    app.include_router(api_router)
    app.include_router(pages_router)

    @app.websocket("/ws")
    async def websocket_route(websocket: WebSocket) -> None:
        await websocket_endpoint(websocket)

    return app


app = create_app()
