from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import uuid
from datetime import datetime

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
