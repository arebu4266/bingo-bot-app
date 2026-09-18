"""SQLite wallet storage. Swap for Postgres later if you outgrow SQLite."""

import sqlite3
from contextlib import closing

DB_PATH = "bingo.db"


def init_db():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance REAL DEFAULT 0
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                type TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        conn.commit()


def get_or_create_user(user_id: int, username: str = "") -> float:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        row = cur.fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO users (user_id, username, balance) VALUES (?,?,0)",
                (user_id, username),
            )
            conn.commit()
            return 0.0
        return row[0]


def get_balance(user_id: int) -> float:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        row = cur.fetchone()
        return row[0] if row else 0.0


def update_balance(user_id: int, delta: float, tx_type: str):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id=?", (delta, user_id)
        )
        conn.execute(
            "INSERT INTO transactions (user_id, amount, type) VALUES (?,?,?)",
            (user_id, delta, tx_type),
        )
        conn.commit()
