"""Accounts for the TakRouter site: users, login sessions, API keys, preferences, credit.

SQLite under runs/gateway/ (git-ignored). Passwords: scrypt with a per-user salt. Sessions and
API keys: random tokens; only their SHA-256 is stored. The first account becomes the admin.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SESSION_DAYS = 14
DEFAULT_CREDIT_USD = 0.50  # a new user's credit; the admin changes it
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DEFAULT_PREFS = {"show_trace": False, "lang": "fa", "theme": None}


class AuthError(ValueError):
    """A user-facing problem: the message is a short code the site translates."""


def _hash_password(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@dataclass
class User:
    id: int
    email: str
    name: str
    role: str  # admin | user
    credit_usd: float
    created: float
    prefs: dict[str, Any] = field(default_factory=dict)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    def public(self) -> dict[str, Any]:
        return {"id": self.id, "email": self.email, "name": self.name, "role": self.role,
                "credit_usd": self.credit_usd, "prefs": {**DEFAULT_PREFS, **self.prefs}}


class Accounts:
    def __init__(self, path: str | Path = ":memory:", clock=time.time):
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.lock = threading.Lock()
        self.clock = clock
        with self.lock:
            self.db.executescript("""
                CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT,
                    pw_hash BLOB NOT NULL, salt BLOB NOT NULL, role TEXT NOT NULL, credit_usd REAL NOT NULL,
                    created REAL NOT NULL, prefs TEXT NOT NULL DEFAULT '{}');
                CREATE TABLE IF NOT EXISTS sessions (digest TEXT PRIMARY KEY, user_id INTEGER NOT NULL, expires REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS api_keys (digest TEXT PRIMARY KEY, user_id INTEGER NOT NULL, name TEXT,
                    prefix TEXT NOT NULL, created REAL NOT NULL, last_used REAL);
            """)
            self.db.commit()

    # ------------------------------------------------------------- users
    def _user(self, row) -> User | None:
        if row is None:
            return None
        uid, email, name, role, credit, created, prefs = row
        return User(uid, email, name or "", role, credit, created, json.loads(prefs or "{}"))

    _COLS = "id, email, name, role, credit_usd, created, prefs"

    def get(self, user_id: int) -> User | None:
        with self.lock:
            return self._user(self.db.execute(f"SELECT {self._COLS} FROM users WHERE id = ?", (user_id,)).fetchone())

    def users(self) -> list[User]:
        with self.lock:
            return [self._user(r) for r in self.db.execute(f"SELECT {self._COLS} FROM users ORDER BY id")]

    def signup(self, email: str, password: str, name: str = "") -> User:
        email = email.strip().lower()
        if not EMAIL.match(email):
            raise AuthError("bad_email")
        if len(password) < 8:
            raise AuthError("short_password")
        salt = secrets.token_bytes(16)
        with self.lock:
            first = self.db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0
            try:
                cur = self.db.execute(
                    "INSERT INTO users (email, name, pw_hash, salt, role, credit_usd, created) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (email, name.strip()[:60], _hash_password(password, salt), salt, "admin" if first else "user",
                     DEFAULT_CREDIT_USD, self.clock()))
            except sqlite3.IntegrityError:
                raise AuthError("email_taken") from None
            self.db.commit()
            uid = cur.lastrowid
        return self.get(uid)

    def check_password(self, email: str, password: str) -> User:
        with self.lock:
            row = self.db.execute("SELECT id, pw_hash, salt FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
        # Same work whether or not the account exists.
        salt = row[2] if row else b"0" * 16
        ok = hmac.compare_digest(_hash_password(password, salt), row[1] if row else b"")
        if not (row and ok):
            raise AuthError("bad_login")
        return self.get(row[0])

    def update(self, user_id: int, *, name: str | None = None, prefs: dict[str, Any] | None = None,
               role: str | None = None, credit_usd: float | None = None) -> User:
        user = self.get(user_id)
        if user is None:
            raise AuthError("no_user")
        merged = {**user.prefs, **{k: v for k, v in (prefs or {}).items() if k in DEFAULT_PREFS}}
        with self.lock:
            self.db.execute("UPDATE users SET name = ?, prefs = ?, role = ?, credit_usd = ? WHERE id = ?", (
                user.name if name is None else name.strip()[:60], json.dumps(merged),
                user.role if role is None else role, user.credit_usd if credit_usd is None else float(credit_usd), user_id))
            self.db.commit()
        return self.get(user_id)

    # ----------------------------------------------------------- sessions
    def start_session(self, user: User) -> str:
        token = secrets.token_urlsafe(32)
        with self.lock:
            self.db.execute("INSERT INTO sessions VALUES (?, ?, ?)", (_digest(token), user.id, self.clock() + SESSION_DAYS * 86400))
            self.db.commit()
        return token

    def end_session(self, token: str) -> None:
        with self.lock:
            self.db.execute("DELETE FROM sessions WHERE digest = ?", (_digest(token),))
            self.db.commit()

    def session_user(self, token: str | None) -> User | None:
        if not token:
            return None
        with self.lock:
            row = self.db.execute("SELECT user_id, expires FROM sessions WHERE digest = ?", (_digest(token),)).fetchone()
        if row is None or row[1] < self.clock():
            return None
        return self.get(row[0])

    # ----------------------------------------------------------- API keys
    def create_key(self, user: User, name: str = "") -> str:
        """Returns the key once; only its hash is kept."""
        key = "tk-" + secrets.token_urlsafe(28)
        with self.lock:
            self.db.execute("INSERT INTO api_keys VALUES (?, ?, ?, ?, ?, NULL)",
                            (_digest(key), user.id, name.strip()[:40], key[:7], self.clock()))
            self.db.commit()
        return key

    def keys(self, user: User) -> list[dict[str, Any]]:
        with self.lock:
            rows = self.db.execute("SELECT digest, name, prefix, created, last_used FROM api_keys WHERE user_id = ? ORDER BY created",
                                   (user.id,)).fetchall()
        return [{"id": d[:12], "name": n, "prefix": p, "created": c, "last_used": u} for d, n, p, c, u in rows]

    def delete_key(self, user: User, key_id: str) -> bool:
        with self.lock:
            cur = self.db.execute("DELETE FROM api_keys WHERE user_id = ? AND substr(digest, 1, 12) = ?", (user.id, key_id))
            self.db.commit()
        return cur.rowcount > 0

    def key_user(self, key: str | None) -> User | None:
        if not key or not key.startswith("tk-"):
            return None
        d = _digest(key)
        with self.lock:
            row = self.db.execute("SELECT user_id FROM api_keys WHERE digest = ?", (d,)).fetchone()
            if row:
                self.db.execute("UPDATE api_keys SET last_used = ? WHERE digest = ?", (self.clock(), d))
                self.db.commit()
        return self.get(row[0]) if row else None
