from fastapi import FastAPI, HTTPException
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

# DB 연결 + dict 형태 row 설정
conn = sqlite3.connect("applications.db", check_same_thread=False)
conn.row_factory = sqlite3.Row  # 🔥 중요

# DB 초기화 (applications + products)
conn.executescript("""
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    region TEXT,
    name TEXT,
    phone TEXT,
    products TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    label TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0
);
""")

# 기본 상품 시드
if conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
    conn.executemany(
        "INSERT INTO products (key, label, sort_order) VALUES (?,?,?)",
        [
            ("aircon","에어컨",0),
            ("tv","TV 벽걸이",1),
            ("cctv","CCTV",2),
            ("led","LED 조명",3),
            ("shelf","선반·수납",4)
        ]
    )
conn.commit()

# =========================
# 신청 관련
# =========================
class Application(BaseModel):
    region: str
    name: str
    phone: str
    products: list[str]

@app.post("/apply")
def apply(data: Application):
    conn.execute(
        "INSERT INTO applications (region, name, phone, products, created_at) VALUES (?,?,?,?,?)",
        (
            data.region,
            data.name,
            data.phone,
            json.dumps(data.products),
            datetime.now().isoformat()
        )
    )
    conn.commit()
    return {"ok": True}

@app.get("/counts")
def counts():
    rows = conn.execute(
        "SELECT region, COUNT(*) as cnt FROM applications GROUP BY region"
    ).fetchall()
    return {row["region"]: row["cnt"] for row in rows}

# =========================
# 상품 관리
# =========================
class ProductIn(BaseModel):
    key: str
    label: str
    sort_order: int = 0

@app.get("/products")
def get_products():
    rows = conn.execute(
        "SELECT * FROM products ORDER BY sort_order"
    ).fetchall()
    return [dict(r) for r in rows]

@app.post("/products")
def add_product(p: ProductIn):
    try:
        conn.execute(
            "INSERT INTO products (key, label, sort_order) VALUES (?,?,?)",
            (p.key, p.label, p.sort_order)
        )
        conn.commit()
        return {"ok": True}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="이미 존재하는 key입니다")

@app.put("/products/{key}")
def update_product(key: str, p: ProductIn):
    conn.execute(
        "UPDATE products SET label=?, sort_order=? WHERE key=?",
        (p.label, p.sort_order, key)
    )
    conn.commit()
    return {"ok": True}

@app.delete("/products/{key}")
def delete_product(key: str):
    conn.execute(
        "DELETE FROM products WHERE key=?",
        (key,)
    )
    conn.commit()
    return {"ok": True}