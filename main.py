from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import sqlite3 

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

def get_db()
           return sqlite3.connect(DB_PATH)

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
