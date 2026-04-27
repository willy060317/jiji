from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3, json
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB 초기화
conn = sqlite3.connect("applications.db", check_same_thread=False)
conn.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        region TEXT,
        name TEXT,
        phone TEXT,
        products TEXT,
        created_at TEXT
    )
""")
conn.commit()

class Application(BaseModel):
    region: str
    name: str
    phone: str
    products: list[str]

@app.post("/apply")
def apply(data: Application):
    conn.execute(
        "INSERT INTO applications (region, name, phone, products, created_at) VALUES (?,?,?,?,?)",
        (data.region, data.name, data.phone, json.dumps(data.products), datetime.now().isoformat())
    )
    conn.commit()
    return {"ok": True}

@app.get("/counts")
def counts():
    rows = conn.execute(
        "SELECT region, COUNT(*) as cnt FROM applications GROUP BY region"
    ).fetchall()
    return {row[0]: row[1] for row in rows}