from typing import List, Optional
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import time
import json
import os
import sqlite3
import logging

from fastapi import FastAPI, Header, HTTPException, Depends
from starlette.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
import psycopg2
from duckduckgo_search import DDGS

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

IGNPRE_API_KEYS = os.getenv("IGNPRE_API_KEYS")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# Determine and log the current mode
if IGNPRE_API_KEYS == "True":
    db_mode = "IGNPRE_API_KEYS"
elif DATABASE_URL:
    db_mode = "Postgres"
else:
    db_mode = "SQLite"
logger.info("Database mode: %s", db_mode)

# --- Database Connection Setup ---
def get_db_connection():
    if DATABASE_URL:
        logger.info("Connecting to PostgreSQL.")
        return psycopg2.connect(DATABASE_URL)
    else:
        logger.info("Connecting to SQLite.")
        return sqlite3.connect("api_keys.db")

# --- Initialize Database ---
def init_db():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if DATABASE_URL:
            # PostgreSQL: table named openai_api_keys
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS openai_api_keys (
                    id SERIAL PRIMARY KEY,
                    key TEXT UNIQUE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            # SQLite: table named openai_api_keys
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS openai_api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        conn.commit()
        logger.info("Database initialized successfully.")
    finally:
        conn.close()

if IGNPRE_API_KEYS != "True":
    init_db()
else:
    logger.info("IGNPRE_API_KEYS is active; bypassing database initialization.")

# --- Dependency to Validate Admin Key ---
async def get_admin_key(authorization: str = Header(...)):
    if IGNPRE_API_KEYS == "True":
        return ""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing Authorization header")
    token = authorization.split(" ")[1]
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    return token

# --- Dependency for API Key Validation ---
async def get_api_key(authorization: str = Header(...)):
    if IGNPRE_API_KEYS == "True":
        return ""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing Authorization header")
    token = authorization.split(" ")[1]
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if DATABASE_URL:
            cursor.execute("SELECT id FROM openai_api_keys WHERE key = %s", (token,))
        else:
            cursor.execute("SELECT id FROM openai_api_keys WHERE key = ?", (token,))
        result = cursor.fetchone()
    finally:
        conn.close()
    if not result:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return token

# --- Pydantic Models ---
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    stream: Optional[bool] = False

class ApiKeyCreate(BaseModel):
    description: Optional[str] = None

# --- FastAPI App Setup ---
app = FastAPI(title="duckduckgo-ai-openai-api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def serve_html():
    with open("website.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)

# --- Chat Completion Endpoint ---
@app.post("/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    api_key: str = Depends(get_api_key)
):
    prompt = request.messages[-1].content if request.messages else ""
    model = request.model if request.model else "llama-3.3-70b"
    if request.stream:
        def ddgs_streamer():
            for token in DDGS().chat_yield(prompt, model=model):
                chunk = {
                    "id": int(time.time()),
                    "object": "chat.completion.chunk",
                    "created": time.time(),
                    "model": model,
                    "choices": [{"delta": {"content": token}}]
                }
                yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(ddgs_streamer(), media_type="application/x-ndjson")
    else:
        result = DDGS().chat(prompt, model=model)
        return {
            "id": int(time.time()),
            "object": "chat.completion",
            "created": time.time(),
            "model": model,
            "choices": [{
                "message": ChatMessage(role="assistant", content=result)
            }]
        }

# --- API Key Management Endpoints ---
@app.get("/api-keys", dependencies=[Depends(get_admin_key)])
async def list_api_keys():
    if IGNPRE_API_KEYS == "True":
        return ""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if DATABASE_URL:
            cursor.execute("SELECT id, key, description, created_at FROM openai_api_keys")
            rows = cursor.fetchall()
            keys = [{"id": r[0], "key": r[1], "description": r[2], "created_at": str(r[3])} for r in rows]
        else:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, key, description, created_at FROM openai_api_keys")
            rows = cursor.fetchall()
            keys = [dict(row) for row in rows]
    finally:
        conn.close()
    return {"api_keys": keys}

@app.post("/api-keys", dependencies=[Depends(get_admin_key)])
async def create_api_key_endpoint(api_key_create: ApiKeyCreate):
    if IGNPRE_API_KEYS == "True":
        return ""
    import secrets
    new_key = secrets.token_hex(16)
    description = api_key_create.description
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if DATABASE_URL:
            cursor.execute("INSERT INTO openai_api_keys (key, description) VALUES (%s, %s)", (new_key, description))
        else:
            cursor.execute("INSERT INTO openai_api_keys (key, description) VALUES (?, ?)", (new_key, description))
        conn.commit()
        if DATABASE_URL:
            cursor.execute("SELECT currval(pg_get_serial_sequence('openai_api_keys','id'))")
            key_id = cursor.fetchone()[0]
        else:
            key_id = cursor.lastrowid
    except Exception:
        conn.close()
        raise HTTPException(status_code=400, detail="API Key already exists")
    finally:
        conn.close()
    return {"id": key_id, "key": new_key, "description": description}

@app.delete("/api-keys/{key}", dependencies=[Depends(get_admin_key)])
async def delete_api_key(key: str):
    if IGNPRE_API_KEYS == "True":
        return ""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if DATABASE_URL:
            cursor.execute("DELETE FROM openai_api_keys WHERE key = %s", (key,))
        else:
            cursor.execute("DELETE FROM openai_api_keys WHERE key = ?", (key,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="API Key not found")
    finally:
        conn.close()
    return {"detail": "API Key deleted"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
