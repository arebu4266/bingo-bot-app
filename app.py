"""
Hager Bingo - Telegram Mini App backend (FastAPI)
====================================================
Single service that:
  1. Serves the Mini App frontend (static/index.html)
  2. Exposes a small JSON API the frontend polls for game state
  3. Receives Telegram bot updates via webhook and replies with a
     "Play" button that opens the Mini App

DEPLOY: see README.md for Render.com free-tier deployment steps.

SECURITY NOTE: every API call that touches money (join/deposit/bingo)
verifies the Telegram WebApp `initData` signature using BOT_TOKEN, so a
user cannot forge another user's Telegram ID. See verify_init_data().
Before handling real payments, still wire /api/deposit to a licensed
payment provider - it is a demo stub right now.
"""

import asyncio
import hashlib
import hmac
import os
import random
import time
from urllib.parse import parse_qsl

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

import db
import bingo_logic

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBAPP_URL = os.environ.get("WEBAPP_URL")  # e.g. https://your-app.onrender.com
CARD_PRICE = float(os.environ.get("CARD_PRICE", "10"))
NUMBER_CALL_INTERVAL = float(os.environ.get("NUMBER_CALL_INTERVAL", "4"))
COMMISSION = float(os.environ.get("COMMISSION", "0.2"))  # 20% house cut

if not BOT_TOKEN:
    raise RuntimeError("Set BOT_TOKEN in your environment / .env file")

db.init_db()

app = FastAPI(title="Hager Bingo")
telegram_app = Application.builder().token(BOT_TOKEN).job_queue(None).build()


# ---------------------------------------------------------------------------
# Telegram WebApp initData verification
# https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
# ---------------------------------------------------------------------------

def verify_init_data(init_data: str, max_age_seconds: int = 86400) -> dict:
    """Validates Telegram WebApp initData and returns the parsed fields.
    Raises HTTPException(401) if the signature is invalid or expired."""
    try:
        pairs = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError:
        raise HTTPException(401, "Malformed init data")

    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise HTTPException(401, "Missing hash")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise HTTPException(401, "Invalid signature")

    auth_date = int(pairs.get("auth_date", "0"))
    if time.time() - auth_date > max_age_seconds:
        raise HTTPException(401, "Init data expired")

    return pairs


def get_user_id_from_init_data(init_data: str) -> int:
    import json

    pairs = verify_init_data(init_data)
    user = json.loads(pairs["user"])
    return int(user["id"])


# ---------------------------------------------------------------------------
# Single global game room (simplest possible version - one game at a time).
# Good enough for a first launch; shard by chat_id/room_id later if needed.
# ---------------------------------------------------------------------------

class GameRoom:
    def __init__(self):
        self.reset()

    def reset(self):
        self.game_id = random.randint(10000, 99999)
        self.players: dict[int, list] = {}   # user_id -> card (list of 25)
        self.marked: list[int] = []
        self.pool = list(range(1, 76))
        random.shuffle(self.pool)
        self.call_index = 0
        self.status = "waiting"  # waiting -> running -> finished
        self.winner: dict | None = None
        self.start_at: float | None = None

    def prize_pool(self) -> float:
        return round(CARD_PRICE * len(self.players) * (1 - COMMISSION), 2)


room = GameRoom()
room_lock = asyncio.Lock()


async def game_loop():
    """Background task: waits for players, then calls numbers until someone
    wins or the pool runs out."""
    global room
    while True:
        await asyncio.sleep(1)
        async with room_lock:
            if room.status == "waiting" and room.players and room.start_at is None:
                room.start_at = time.time() + 20  # 20s to gather players

            if room.status == "waiting" and room.start_at and time.time() >= room.start_at:
                if len(room.players) >= 1:
                    room.status = "running"
                else:
                    room.reset()

            if room.status == "running":
                if room.call_index < len(room.pool):
                    room.marked.append(room.pool[room.call_index])
                    room.call_index += 1
                else:
                    room.status = "finished"


@app.on_event("startup")
async def on_startup():
    asyncio.create_task(game_loop())
    await telegram_app.initialize()
    if WEBAPP_URL:
        await telegram_app.bot.set_webhook(f"{WEBAPP_URL}/telegram-webhook")


@app.on_event("shutdown")
async def on_shutdown():
    await telegram_app.shutdown()


# ---------------------------------------------------------------------------
# Telegram bot handlers (just enough to open the Mini App)
# ---------------------------------------------------------------------------

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.get_or_create_user(update.effective_user.id, update.effective_user.username or "")
    if WEBAPP_URL:
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Play Hager Bingo", web_app=WebAppInfo(url=WEBAPP_URL))]]
        )
        await update.message.reply_text(
            "Welcome to Hager Bingo! Tap below to play.", reply_markup=keyboard
        )
    else:
        await update.message.reply_text(
            "Welcome! (WEBAPP_URL is not configured yet - see README.md)"
        )


telegram_app.add_handler(CommandHandler("start", start_cmd))


@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}


# ---------------------------------------------------------------------------
# Game / wallet API used by the Mini App frontend
# ---------------------------------------------------------------------------

class InitDataBody(BaseModel):
    init_data: str


class DepositBody(InitDataBody):
    amount: float


@app.get("/api/state")
async def api_state():
    async with room_lock:
        last_called = room.marked[-1] if room.marked else None
        recent = list(reversed(room.marked[-4:-1])) if len(room.marked) > 1 else []
        return {
            "game_id": room.game_id,
            "status": room.status,
            "players": len(room.players),
            "bet": CARD_PRICE,
            "prize": room.prize_pool(),
            "called_count": len(room.marked),
            "last_called": last_called,
            "last_called_letter": bingo_logic.letter_for_number(last_called) if last_called else None,
            "recent_called": recent,
            "marked": room.marked,
            "starts_in": max(0, int(room.start_at - time.time())) if room.start_at else None,
            "winner": room.winner,
        }


@app.post("/api/join")
async def api_join(body: InitDataBody):
    user_id = get_user_id_from_init_data(body.init_data)
    db.get_or_create_user(user_id)

    async with room_lock:
        if room.status == "running" or room.status == "finished":
            raise HTTPException(400, "A game is already in progress, please wait for the next round")
        if user_id in room.players:
            return {"card": room.players[user_id], "game_id": room.game_id}

        balance = db.get_balance(user_id)
        if balance < CARD_PRICE:
            raise HTTPException(400, "Insufficient balance")

        db.update_balance(user_id, -CARD_PRICE, "card_purchase")
        card = bingo_logic.generate_card()
        room.players[user_id] = card
        return {"card": card, "game_id": room.game_id}


@app.post("/api/bingo")
async def api_bingo(body: InitDataBody):
    user_id = get_user_id_from_init_data(body.init_data)

    async with room_lock:
        if room.status != "running" or user_id not in room.players:
            raise HTTPException(400, "No active game for this user")

        card = room.players[user_id]
        if not bingo_logic.check_win(card, set(room.marked)):
            raise HTTPException(400, "Not a winning card yet")

        prize = room.prize_pool()
        db.update_balance(user_id, prize, "prize")
        room.status = "finished"
        room.winner = {"user_id": user_id, "prize": prize}
        result = {"prize": prize}

    # start a fresh room shortly after so the frontend can show the result first
    async def delayed_reset():
        await asyncio.sleep(6)
        async with room_lock:
            room.reset()

    asyncio.create_task(delayed_reset())
    return result


@app.get("/api/balance")
async def api_balance(user_id: int, init_data: str):
    verify_init_data(init_data)  # just proves the request came from Telegram
    return {"balance": db.get_balance(user_id)}


@app.post("/api/deposit")
async def api_deposit(body: DepositBody):
    """STUB endpoint - wire this to your licensed payment provider (Telebirr,
    CBE Birr, etc.) and only call update_balance after verifying the payment
    server-side (e.g. via the provider's webhook/callback), not on user say-so."""
    user_id = get_user_id_from_init_data(body.init_data)
    if body.amount <= 0:
        raise HTTPException(400, "Invalid amount")
    db.update_balance(user_id, body.amount, "deposit")
    return {"balance": db.get_balance(user_id)}


# Serve the Mini App frontend last, so it doesn't shadow the /api routes above
app.mount("/", StaticFiles(directory="static", html=True), name="static")
