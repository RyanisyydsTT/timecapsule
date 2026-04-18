from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import uuid
from datetime import datetime

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
    CREATE TABLE IF NOT EXISTS capsules (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    create_at TEXT NOT NULL,
    unlock_at TEXT NOT NULL,
    )
                   """)

def get_db():
    return sqlite3.connect(DB_PATH)


def insert_capsule(content: str, unlock_at: str):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    EXECUTE INTO capsules (id, content, created_at unlock_at)
    VALUES (?, ?, ?, ?)""", (str(uuid.uuid4()), content, datetime.utcnow(), isoformat(), unlock_at))

    conn.commit()
    conn.close()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # customize this to only allow certain domains!
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("statup")
def startup():
    init_db()


@app.get("/store")
def hello():
    return {"message": "hello"}

uvicorn.run(app)
