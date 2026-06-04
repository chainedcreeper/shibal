import os
import sqlite3
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = os.environ.get("SECRET_KEY", "woosong-ai-tutor-secret-change-me")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

DB_PATH = "students.db"
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def _conn():
    return sqlite3.connect(DB_PATH)


def init_auth_db():
    conn = _conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            student_id  TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            password    TEXT NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def register_user(student_id: str, name: str, password: str):
    conn = _conn()
    exists = conn.execute(
        "SELECT 1 FROM users WHERE student_id=?", (student_id,)
    ).fetchone()
    if exists:
        conn.close()
        raise HTTPException(status_code=400, detail="이미 등록된 학번입니다.")
    conn.execute(
        "INSERT INTO users (student_id, name, password) VALUES (?,?,?)",
        (student_id, name, pwd_ctx.hash(password)),
    )
    conn.commit()
    conn.close()


def authenticate_user(student_id: str, password: str):
    conn = _conn()
    row = conn.execute(
        "SELECT name, password FROM users WHERE student_id=?", (student_id,)
    ).fetchone()
    conn.close()
    if not row or not pwd_ctx.verify(password, row[1]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="학번 또는 비밀번호가 올바르지 않습니다.",
        )
    return {"student_id": student_id, "name": row[0]}


def create_token(student_id: str, name: str) -> str:
    payload = {
        "sub": student_id,
        "name": name,
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        student_id = payload.get("sub")
        name = payload.get("name")
        if not student_id:
            raise ValueError
        return {"student_id": student_id, "name": name}
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
