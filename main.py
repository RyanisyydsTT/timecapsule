from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import uuid
from datetime import datetime, UTC, timezone
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time

class CapsuleInput(BaseModel):
    content: str
    unlock_at: str

class ObtainRequest(BaseModel):
    username: str

security = HTTPBearer()

def verify_token(credentials = Depends(security)) -> str:
    token = credentials.credentials
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE token = ?", (token,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid token")

    return row[0]

def parse_flexible_dates(date_str: str) -> str:
    parts = date_str.replace("-", "/").split("/")

    if len(parts) != 3:
        raise ValueError("Invalid date format")

    a, b, c = parts

    if len(a) == 4:
        year = int(a)
        x = int(b)
        y = int(c)

        if x > 12:
            day = x 
            month = y
        elif y > 12:
            month = x
            day = y
        else:
            #assume MM/DD
            month = x
            day = y

    elif len(c) == 4:
        year = int(c)
        x = int(a)
        y = int(b)

        if x > 12:
            day = x
            month = y
        else:
            month = x 
            day = y 

    else:
        raise ValueError("Cannot determine")

    try:
        dt = datetime(year, month, day)
    except:
        raise ValueError("Invalid date values")

    return dt.strftime("%Y-%m-%d")


DB_PATH = "capsule.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, token TEXT NOT NULL, created_at TEXT NOT NULL)
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS capsules (id TEXT PRIMARY KEY, owner_username TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL, unlock_at TEXT NOT NULL, FOREIGN KEY (owner_username) REFERENCES users(username))
    """)
    conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect(DB_PATH)


def insert_capsule(owner_username: str,content: str, unlock_at: str):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO capsules (id, owner_username, content, created_at, unlock_at)
    VALUES (?, ?, ?, ?, ?)""", (str(uuid.uuid4()), owner_username, content, datetime.now(UTC).isoformat(), unlock_at))

    conn.commit()
    conn.close()

app = FastAPI()

request_counter: int = 0
last_request_time: float = time.time()
rate_limit_window: int = 60
max_requests_per_window: int = 100

class RateLimiterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        global last_request_time, request_counter

        current_time = time.time()
        if current_time - last_request_time > rate_limit_window:
            request_counter = 0
            last_request_time = current_time

        request_counter += 1

        if request_counter > max_requests_per_window:
            return Response("Rate limit exceeded", status_code=429)

        response = await call_next(request)
        return response

app.add_middleware(RateLimiterMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # customize this to only allow certain domains!
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

@app.post("/obtain")
def obtain_token(data: ObtainRequest):
    conn = get_db()
    cursor = conn.cursor()

    username = data.username.strip()
    cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()

    if row:
        conn.close()
        return {
            "success": False,
            "message": "username existed"
        }

    token = str(uuid.uuid4())

    cursor.execute("INSERT INTO users (username, token, created_at) VALUES (?, ?, ?)", (username, token, datetime.now().isoformat()))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "account created!",
        "token": token
    }

@app.post("/store")
def store(data: CapsuleInput, username: str = Depends(verify_token)):
    content = data.content
    unlock_raw = data.unlock_at

    try:
        parsed_date = parse_flexible_dates(unlock_raw)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    insert_capsule(username, content, parsed_date)

    return {
        "success": True,
        "message": "Capsule stored successfully"
    }

@app.get("/list")
def list_capsules(username: str = Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, created_at, unlock_at FROM capsules WHERE owner_username = ? ORDER BY created_at DESC", (username,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "created_at": row[1],
            "unlock_at": row[2]
        }
        for row in rows
    ]

@app.get("view")
def unlock_capsule(username: str = Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
    """
    SELECT id, created_at, unlock_at, content
    FROM capsules
    WHERE owner_username = ?
      AND unlock_at <= ?
    ORDER BY created_at DESC
    """,(username, datetime.now(timezone.utc).isoformat()))
    
    return [
        {
            "id": row[0],
            "created_at": row[1],
            "unlock_at": row[2],
            "content": row[3]
        }
        for row in rows
    ]


@app.get("/stats")
def getstat(username: str = Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM capsules")
    count = cursor.fetchone()[0]

    return {
        "time": datetime.now(timezone.utc).isoformat(),
        "counts": count
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
