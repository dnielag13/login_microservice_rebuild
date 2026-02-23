"""
Login / User Microservice (CS361-friendly, Swagger-auth works)

Features:
- Create user (persisted to users.json)
- Login -> returns bearer token
- /me -> requires bearer token (Swagger "Authorize" works)
- /validate -> checks whether a token is currently valid (Sprint story friendly)
- /logout -> deletes a token (clean session lifecycle for demos)
- Public user profile endpoint
- /ping echo endpoint for CS361 demo

Run:
  pip install -r requirements.txt
  uvicorn main:app --host 127.0.0.1 --port 5002 --reload
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

DATA_FILE = "users.json"

# ----------------------------
# Password hashing utilities
# ----------------------------

PBKDF2_ROUNDS = 120_000
SALT_BYTES = 16


def _pbkdf2_hash(password: str, salt: bytes, rounds: int) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds)


def hash_password(password: str) -> str:
    """
    Format: pbkdf2_sha256$rounds$salt_b64$hash_b64
    """
    if len(password) < 4:
        raise ValueError("Password must be at least 4 characters.")
    salt = secrets.token_bytes(SALT_BYTES)
    dk = _pbkdf2_hash(password, salt, PBKDF2_ROUNDS)
    return (
        f"pbkdf2_sha256${PBKDF2_ROUNDS}$"
        f"{base64.b64encode(salt).decode()}$"
        f"{base64.b64encode(dk).decode()}"
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, rounds_s, salt_b64, dk_b64 = stored.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False

        rounds = int(rounds_s)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(dk_b64)
        actual = _pbkdf2_hash(password, salt, rounds)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


# ----------------------------
# Pydantic models
# ----------------------------

class CreateUserRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=4, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=64)


class UserPublic(BaseModel):
    user_id: str
    display_name: str


class CreateUserResponse(BaseModel):
    ok: bool
    user: UserPublic


class LoginRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=4, max_length=128)


class LoginResponse(BaseModel):
    ok: bool
    token: str
    user_id: str


class MeResponse(BaseModel):
    ok: bool
    user: UserPublic


class ValidateResponse(BaseModel):
    ok: bool
    user_id: str


class LogoutResponse(BaseModel):
    ok: bool
    message: str


class PingRequest(BaseModel):
    message: str


class PingResponse(BaseModel):
    message: str


# ----------------------------
# Session store (in memory)
# ----------------------------

@dataclass
class Session:
    user_id: str
    created_at: float


SESSIONS: Dict[str, Session] = {}

SESSION_TIMEOUT = 3600  # seconds (1 hour)

def is_session_expired(session: Session) -> bool:
    return time.time() - session.created_at > SESSION_TIMEOUT

# ----------------------------
# User storage (persisted)
# ----------------------------

# USERS[user_id] = {"display_name": "...", "password_hash": "..."}
USERS: Dict[str, Dict[str, str]] = {}


def _normalize_user_id(raw: str) -> str:
    user_id = raw.strip()
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id cannot be blank")
    if " " in user_id:
        raise HTTPException(status_code=400, detail="user_id cannot contain spaces")
    # Optional: uncomment if you want consistent IDs across the system
    # user_id = user_id.lower()
    return user_id


def load_users() -> None:
    global USERS
    if not os.path.exists(DATA_FILE):
        USERS = {}
        return
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        USERS = data if isinstance(data, dict) else {}
    except Exception:
        USERS = {}


def save_users() -> None:
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(USERS, f, indent=2)
    os.replace(tmp, DATA_FILE)


def public_user(user_id: str) -> UserPublic:
    u = USERS.get(user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return UserPublic(user_id=user_id, display_name=u["display_name"])


def _require_session(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=True))
) -> Session:
    token = credentials.credentials  # token WITHOUT "Bearer "
    sess = SESSIONS.get(token)

    if not sess:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Step 2: enforce session expiration
    if is_session_expired(sess):
        SESSIONS.pop(token, None)
        raise HTTPException(status_code=401, detail="Session expired")

    return sess


def _get_token(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=True))) -> str:
    return credentials.credentials


# ----------------------------
# FastAPI app
# ----------------------------

app = FastAPI(title="User/Login Microservice", version="1.1.0")


@app.on_event("startup")
def _startup() -> None:
    load_users()


# ----------------------------
# Endpoints
# ----------------------------

@app.get("/")
def root():
    return {"ok": True, "service": "login_microservice", "docs": "/docs"}


@app.post("/users", response_model=CreateUserResponse)
def create_user(req: CreateUserRequest) -> CreateUserResponse:
    user_id = _normalize_user_id(req.user_id)

    if user_id in USERS:
        raise HTTPException(status_code=409, detail="User already exists")

    display_name = req.display_name.strip()
    if not display_name:
        raise HTTPException(status_code=400, detail="display_name cannot be blank")

    try:
        pw_hash = hash_password(req.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    USERS[user_id] = {
        "display_name": display_name,
        "password_hash": pw_hash,
    }
    save_users()

    return CreateUserResponse(ok=True, user=public_user(user_id))


@app.get("/users/{user_id}", response_model=UserPublic)
def get_user(user_id: str) -> UserPublic:
    return public_user(user_id.strip())


@app.post("/login", response_model=LoginResponse)
def login(req: LoginRequest) -> LoginResponse:
    user_id = req.user_id.strip()
    u = USERS.get(user_id)
    if not u or not verify_password(req.password, u["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = secrets.token_urlsafe(32)
    SESSIONS[token] = Session(user_id=user_id, created_at=time.time())
    return LoginResponse(ok=True, token=token, user_id=user_id)


@app.get("/me", response_model=MeResponse)
def me(sess: Session = Depends(_require_session)) -> MeResponse:
    return MeResponse(ok=True, user=public_user(sess.user_id))


@app.get("/validate", response_model=ValidateResponse)
def validate(sess: Session = Depends(_require_session)) -> ValidateResponse:
    return ValidateResponse(ok=True, user_id=sess.user_id)


@app.post("/logout", response_model=LogoutResponse)
def logout(token: str = Depends(_get_token)) -> LogoutResponse:
    if token in SESSIONS:
        SESSIONS.pop(token, None)
        return LogoutResponse(ok=True, message="Logged out")
    raise HTTPException(status_code=401, detail="Invalid or expired token")


@app.post("/ping", response_model=PingResponse)
def ping(req: PingRequest) -> PingResponse:
    return PingResponse(message=req.message)
