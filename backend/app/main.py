import asyncio
import logging
from typing import AsyncIterator

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from . import bootstrap
from .api import routes_config, routes_crud, routes_inbox, routes_web
from .config import settings
from .reminders import reminders_loop
from .telegram_bot import (
    TelegramClient,
    ensure_webhook,
    handle_telegram_update,
    polling_loop,
)


logger = logging.getLogger(__name__)


app = FastAPI(title="Neuro-Salesman API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(routes_config.router)
app.include_router(routes_inbox.router)
app.include_router(routes_crud.router)
app.include_router(routes_web.router)


@app.on_event("startup")
async def on_startup() -> None:
    bootstrap.run_bootstrap()
    if settings.telegram_mode == "webhook":
        await ensure_webhook()
    else:
        asyncio.create_task(polling_loop())
    if settings.reminder_enabled:
        asyncio.create_task(reminders_loop())


async def _telegram_client_dep() -> AsyncIterator[TelegramClient]:
    if not settings.telegram_bot_token:
        raise HTTPException(status_code=503, detail="Telegram bot is not configured")
    yield TelegramClient(settings.telegram_bot_token)


@app.post(settings.telegram_webhook_path)
async def telegram_webhook(
    request: Request,
    client: TelegramClient = Depends(_telegram_client_dep),
    x_telegram_bot_api_secret_token: str | None = Header(None),
) -> dict:
    if settings.telegram_webhook_secret and (
        x_telegram_bot_api_secret_token != settings.telegram_webhook_secret
    ):
        raise HTTPException(status_code=403, detail="Invalid Telegram secret token")
    data = await request.json()
    await handle_telegram_update(data, client)
    return {"ok": True}

