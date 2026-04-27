from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os, json
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id SERIAL PRIMARY KEY,
            region TEXT,
            name TEXT,
            phone TEXT,
            products TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

init_db()

class Application(BaseModel):
    region: str
    name: str
    phone: str
    products: list[str]

@app.get("/")
def root():
    return FileResponse("index.html")

@app.post("/apply")
def apply(data: Application):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO applications (region, name, phone, products, created_at) VALUES (%s,%s,%s,%s,%s)",
        (data.region, data.name, data.phone, json.dumps(data.products), datetime.now().isoformat())
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"ok": True}

@app.get("/counts")
def counts():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT region, COUNT(*) as cnt FROM applications GROUP BY region")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {row[0]: row[1] for row in rows}