from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parents[1] / "templates")


@router.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="take_number.html", context={})


@router.get("/take-number")
async def take_number_page(request: Request):
    return templates.TemplateResponse(request=request, name="take_number.html", context={})


@router.get("/station/{station_id}")
async def call_station_page(request: Request, station_id: str):
    station_label = station_id.replace("station-", "")
    return templates.TemplateResponse(
        request=request,
        name="call_station.html",
        context={"station_id": station_id, "station_label": station_label},
    )
