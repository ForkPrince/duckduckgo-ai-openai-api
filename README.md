# DuckDuckGo AI OpenAI API - Documentation

## Overview

DuckDuckGo AI OpenAI API is a free ai chat completions FastAPI-based service that mimics OpenAI's API while using DuckDuckGo's AI models. The API supports both streaming and non-streaming responses and includes API key management. 
## Features

- Chat completion with DuckDuckGo AI models (o3-mini, gpt-4o-mini, claude-3-haiku-20240307, meta-llama/Llama-3.3-70B-Instruct-Turbo, mistralai/Mixtral-8x7B-Instruct-v0.1).
- Streaming and non-streaming response support.
- API key authentication and management.
- Admin authentication for API key creation and deletion.
- Option to bypass API key validation using the `IGNPRE_API_KEYS` environment variable.
- SQLite database for storing API keys.

---

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/dhiaaeddine16/duckduckgo-ai-openai-api.git
cd duckduckgo-ai-openai-api
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup Environment Variables

Create a `.env` file from `example.env` using the following command:

```bash
cp example.env .env
```
Then, edit the .env file to include the following required variables:

 - ADMIN_TOKEN: A secret token used for admin authentication.
 - IGNPRE_API_KEYS: A flag to bypass API key validation.

### 4. Run the API Server

```bash
python main.py
```

The API server will start at `http://0.0.0.0:8080`

---
### Example API Requests Using `python`

```python
from openai import OpenAI
BASE_URL = "http://0.0.0.0:8080"
api_key = "******"
client = OpenAI(
    api_key=api_key,
    base_url=BASE_URL
)
chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "who are you",
        }
    ],
    model="o3-mini",
)
```

### Example API Requests Using `curl`

#### Send a Chat Completion Request

```bash
curl -X POST "http://0.0.0.0:8080/chat/completions" -H "Authorization: Bearer <API_KEY>" -H "Content-Type: application/json" -d '{"model": "llama-3.3-70b", "messages": [{"role": "user", "content": "who are you?"}], "stream": false}'
```

#### Create an API Key

```bash
curl -X POST "http://0.0.0.0:8080/api-keys" -H "Authorization: Bearer <ADMIN_TOKEN>" -H "Content-Type: application/json" -d '{"description": "Test API Key"}'
```

#### Get All API Keys

```bash
curl -X GET "http://0.0.0.0:8080/api-keys" -H "Authorization: Bearer <ADMIN_TOKEN>"
```

#### Delete an API Key

```bash
curl -X DELETE "http://0.0.0.0:8080/api-keys/{key}" -H "Authorization: Bearer <ADMIN_TOKEN>"
```

---

## API Endpoints

### Chat Completion

#### Endpoint:

```http
POST /chat/completions
```

#### Request Headers:

```json
{
  "Authorization": "Bearer <API_KEY>"
}
```

#### Request Body:

```json
{
  "model": "llama-3.3-70b",
  "messages": [
    { "role": "user", "content": "who are you?" }
  ],
  "stream": false
}
```

#### Response:

```json
{
  "id": 123456,
  "object": "chat.completion",
  "created": 1700000000,
  "model": "llama-3.3-70b",
  "choices": [
    { "message": { "role": "assistant", "content": "I am a chatbot powered by DuckDuckGo AI." } }
  ]
}
```

### Create an API Key

#### Endpoint:

```http
POST /api-keys
```

#### Request Headers:

```json
{
  "Authorization": "Bearer <ADMIN_TOKEN>"
}
```

#### Request Body:

```json
{
  "description": "Test API Key"
}
```

#### Response:

```json
{
  "id": 1,
  "key": "your_generated_api_key",
  "description": "Test API Key"
}
```

### Get All API Keys

#### Endpoint:

```http
GET /api-keys
```

#### Request Headers:

```json
{
  "Authorization": "Bearer <ADMIN_TOKEN>"
}
```

#### Response:

```json
{
  "api_keys": [
    { "id": 1, "key": "your_api_key", "description": "Test API Key", "created_at": "2024-02-18 12:00:00" }
  ]
}
```

### Delete an API Key

#### Endpoint:

```http
DELETE /api-keys/{key}
```

#### Request Headers:

```json
{
  "Authorization": "Bearer <ADMIN_TOKEN>"
}
```

#### Response:

```json
{
  "detail": "API Key deleted"
}
```

---

## Running Tests

Use `test.py` to verify API functionality:

```bash
python test.py
```

This script:

- Creates a test API key.
- Tests non-streaming and streaming chat completions.
- Retrieves all API keys.
- Deletes the test API key after execution.

---

## License

This project is licensed under the MIT License.

