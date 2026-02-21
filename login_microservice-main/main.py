"""
Login / User Microservice (CS361-friendly, Swagger-auth works)

Features:
- Create user (saved to users.json)
- Login -> returns bearer token
- /me -> requires bearer token (Swagger "Authorize" works)
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
from typing import Dict

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

DATA_FILE = "users.json"

# ----------------------------
# Password hashing utilities
# ----------------------------

def _pbkdf2_hash(password: str, salt: bytes, rounds: int = 120_000) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds)

def hash_password(password: str) -> str:
    """
    Returns: "pbkdf2_sha256$rounds$salt_b64$hash_b64"
    """
    if len(password) < 4:
        raise ValueError("Password must be at least 4 characters.")
    rounds = 120_000
    salt = secrets.token_bytes(16)
    dk = _pbkdf2_hash(password, salt, rounds)
    return f"pbkdf2_sha256${rounds}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"

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

# ----------------------------
# User storage (persisted)
# ----------------------------

# USERS[user_id] = {"display_name": "...", "password_hash": "..."}
USERS: Dict[str, Dict[str, str]] = {}

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

# ----------------------------
# FastAPI app + security
# ----------------------------

app = FastAPI(title="User/Login Microservice", version="1.0.0")

security = HTTPBearer(auto_error=True)

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
    user_id = req.user_id.strip()
    if user_id == "":
        raise HTTPException(status_code=400, detail="user_id cannot be blank")

    if user_id in USERS:
        raise HTTPException(status_code=409, detail="User already exists")

    try:
        pw_hash = hash_password(req.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    USERS[user_id] = {
        "display_name": req.display_name.strip(),
        "password_hash": pw_hash,
    }
    save_users()

    return CreateUserResponse(ok=True, user=public_user(user_id))

@app.get("/users/{user_id}", response_model=UserPublic)
def get_user(user_id: str) -> UserPublic:
    return public_user(user_id)

@app.post("/login", response_model=LoginResponse)
def login(req: LoginRequest) -> LoginResponse:
    user_id = req.user_id.strip()
    u = USERS.get(user_id)
    if not u:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(req.password, u["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = secrets.token_urlsafe(32)
    SESSIONS[token] = Session(user_id=user_id, created_at=time.time())

    return LoginResponse(ok=True, token=token, user_id=user_id)

@app.get("/me", response_model=MeResponse)
def me(credentials: HTTPAuthorizationCredentials = Depends(security)) -> MeResponse:
    token = credentials.credentials  # NOTE: this is the token WITHOUT "Bearer "
    sess = SESSIONS.get(token)
    if not sess:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return MeResponse(ok=True, user=public_user(sess.user_id))

@app.post("/ping", response_model=PingResponse)
def ping(req: PingRequest) -> PingResponse:
    return PingResponse(message=req.message)
