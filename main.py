from typing import List, Optional
from pydantic import BaseModel
import time
import json
import sqlite3
import os  # Added for environment variables
from fastapi import FastAPI, Header, HTTPException, Depends
from starlette.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv  # Added for .env loading

from duckduckgo_search import DDGS

# Load environment variables from .env file
load_dotenv()

# Check for required admin token
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
if not ADMIN_TOKEN:
    raise ValueError("ADMIN_TOKEN environment variable not found in .env file")

# --- SQLite Setup for API Keys ---
DB_FILE = "api_keys.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    return sqlite3.connect(DB_FILE)

# --- Dependency to validate Admin Key ---
async def get_admin_key(authorization: str = Header(...)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")
    token = authorization.split(" ")[1]
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    return token

# --- Existing API Key Validation ---
async def get_api_key(authorization: str = Header(...)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")
    token = authorization.split(" ")[1]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM api_keys WHERE key = ?", (token,))
    result = cursor.fetchone()
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

# --- Protected API Keys Management Routes ---
@app.get("/api-keys", dependencies=[Depends(get_admin_key)])
async def list_api_keys():
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, key, description, created_at FROM api_keys")
    rows = cursor.fetchall()
    conn.close()
    keys = [dict(row) for row in rows]
    return {"api_keys": keys}

@app.post("/api-keys", dependencies=[Depends(get_admin_key)])
async def create_api_key_endpoint(api_key_create: ApiKeyCreate):
    import secrets
    new_key = secrets.token_hex(16)
    description = api_key_create.description
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO api_keys (key, description) VALUES (?, ?)",
            (new_key, description),
        )
        conn.commit()
        key_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="API Key already exists")
    conn.close()
    return {"id": key_id, "key": new_key, "description": description}

@app.delete("/api-keys/{key}", dependencies=[Depends(get_admin_key)])
async def delete_api_key(key: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM api_keys WHERE key = ?", (key,))
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="API Key not found")
    conn.close()
    return {"detail": "API Key deleted"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)