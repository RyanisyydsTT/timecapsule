from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import uuid
from datetime import datetime, UTC, timezone
from pydantic import BaseModel, field_validator
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import logging

logger = logging.getLogger(__name__)

class CapsuleInput(BaseModel):
    content: str
    unlock_at: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        if len(v) > 100000:
            raise ValueError("Content exceeds maximum length of 100000 characters")
        return v

    @field_validator("unlock_at")
    @classmethod
    def validate_unlock_at(cls, v):
        if not v or not v.strip():
            raise ValueError("Unlock date cannot be empty")
        return v

class ObtainRequest(BaseModel):
    username: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not v or not v.strip():
            raise ValueError("Username cannot be empty")
        if len(v) > 50:
            raise ValueError("Username exceeds maximum length of 50 characters")
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters long")
        return v.strip()

security = HTTPBearer()

def verify_token(credentials = Depends(security)) -> str:
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = credentials.credentials.strip()
    if not token:
        raise HTTPException(status_code=401, detail="Token cannot be empty")

    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE token = ?", (token,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=401, detail="Invalid token")

        return row[0]
    except sqlite3.Error as e:
        logger.error(f"Database error verifying token: {e}")
        raise HTTPException(status_code=500, detail="Authentication service error")
    finally:
        if conn:
            conn.close()

def parse_flexible_dates(date_str: str) -> str:
    parts = date_str.replace("-", "/").split("/")

    if len(parts) != 3:
        raise ValueError("Invalid date format. Use YYYY/MM/DD, MM/DD/YYYY, or DD/MM/YYYY")

    a, b, c = parts

    try:
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
            raise ValueError("Cannot determine year position in date string")

        dt = datetime(year, month, day)

        if dt < datetime.now():
            raise ValueError("Unlock date cannot be in the past")

    except ValueError as e:
        raise ValueError(f"Invalid date: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error parsing date: {e}")
        raise ValueError("Invalid date values")

    return dt.strftime("%Y-%m-%d")


DB_PATH = "capsule.db"

def init_db():
    try:
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
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")
        raise

def get_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise


def insert_capsule(owner_username: str, content: str, unlock_at: str):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO capsules (id, owner_username, content, created_at, unlock_at)
        VALUES (?, ?, ?, ?, ?)""", (str(uuid.uuid4()), owner_username, content, datetime.now(UTC).isoformat(), unlock_at))

        conn.commit()
    except sqlite3.IntegrityError as e:
        logger.error(f"Data integrity error inserting capsule: {e}")
        raise ValueError("Failed to store capsule due to data validation error")
    except sqlite3.Error as e:
        logger.error(f"Database error inserting capsule: {e}")
        raise ValueError("Failed to store capsule due to database error")
    finally:
        if conn:
            conn.close()

app = FastAPI(
    title="Time Capsule",
    description="A secure API service that stores stories and memories in a capsule database. Send your messages now and retrieve them on the unlock date.",
    version="1.0.0"
)

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
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

@app.post("/obtain", summary="Create Account & Obtain Token")
def obtain_token(data: ObtainRequest):
    """Generate a unique authentication token for a new user account."""
    username = data.username
    conn = None

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()

        if row:
            return {
                "success": False,
                "message": "username already exists"
            }

        token = str(uuid.uuid4())

        cursor.execute("INSERT INTO users (username, token, created_at) VALUES (?, ?, ?)",
                      (username, token, datetime.now(UTC).isoformat()))

        conn.commit()

        return {
            "success": True,
            "message": "account created!",
            "token": token
        }

    except sqlite3.IntegrityError:
        return {
            "success": False,
            "message": "username already exists"
        }
    except sqlite3.Error as e:
        logger.error(f"Database error creating account: {e}")
        raise HTTPException(status_code=500, detail="Failed to create account")
    finally:
        if conn:
            conn.close()

@app.post("/store", summary="Store a Capsule")
def store(data: CapsuleInput, username: str = Depends(verify_token)):
    """Save a message to be unlocked on a specified date."""
    try:
        parsed_date = parse_flexible_dates(data.unlock_at)
        insert_capsule(username, data.content, parsed_date)

        return {
            "success": True,
            "message": "Capsule stored successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error storing capsule: {e}")
        raise HTTPException(status_code=500, detail="Failed to store capsule")

@app.get("/list", summary="List All Capsules")
def list_capsules(username: str = Depends(verify_token)):
    """Retrieve all capsules created by the authenticated user."""
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT id, created_at, unlock_at FROM capsules WHERE owner_username = ? ORDER BY created_at DESC", (username,))

        rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "created_at": row[1],
                "unlock_at": row[2]
            }
            for row in rows
        ]
    except sqlite3.Error as e:
        logger.error(f"Database error listing capsules: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve capsules")
    finally:
        if conn:
            conn.close()

@app.get("/view", summary="View Unlocked Capsules")
def unlock_capsule(username: str = Depends(verify_token)):
    """Retrieve all capsules that have reached their unlock date."""
    conn = None
    try:
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

        rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "created_at": row[1],
                "unlock_at": row[2],
                "content": row[3]
            }
            for row in rows
        ]
    except sqlite3.Error as e:
        logger.error(f"Database error retrieving unlocked capsules: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve capsules")
    finally:
        if conn:
            conn.close()


@app.get("/stats", summary="View Server Statistics")
def getstat(username: str = Depends(verify_token)):
    """Display total capsule count and current server timestamp."""
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM capsules")
        result = cursor.fetchone()
        count = result[0] if result else 0

        return {
            "time": datetime.now(timezone.utc).isoformat(),
            "counts": count
        }
    except sqlite3.Error as e:
        logger.error(f"Database error retrieving stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
