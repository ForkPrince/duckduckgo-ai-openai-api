# 🚀 duckduckgo-ai-openai-api 
# Documentation

DuckDuckGo AI OpenAI API is a free, powerful AI chat completions service built with FastAPI. It mimics OpenAI's API while leveraging DuckDuckGo's AI models to deliver chat completions with both streaming and non-streaming responses.

🛡️ The API supports API key management and uses databases like SQLite or PostgreSQL to store API keys. Alternatively, API key validation can be bypassed, allowing the service to run without using any databases.

---

## 📂 Project Structure

```
project/
├── main.py          # 🚀 FastAPI application with chat completion and API key endpoints
├── test.py          # 🧪 Script to test the API endpoints
└── requirements.txt # 📜 Python dependencies
```

---

## 🌟 Features

- 💬 **Chat Completions Endpoint**: Processes chat requests using DuckDuckGo search and returns responses. Supports both streaming and non-streaming modes.
- 🔑 **API Key Management**: Create, list, and delete API keys to secure access to the chat endpoint.
- 🗄️ **Flexible Database Support**: Uses PostgreSQL or SQLite to store API keys. If API key validation is bypassed, no database is required.

---

## 🛠️ Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/dhiaaeddine16/duckduckgo-ai-openai-api.git
   cd duckduckgo-ai-openai-api
   ```

2. **Create a virtual environment** (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install the required dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

---

## ⚙️ Configuration

📄 Copy the `example.env` file to `.env` in the project root using the following command and configure the environment variables:

```bash
cp example.env .env
```

Then, open the `.env` file and update the necessary configurations:

```ini
# .env

# 🔄 When set to "True", bypasses database initialization for API keys
IGNPRE_API_KEYS=False

# 🔑 Admin token for managing API keys (required for admin endpoints)
ADMIN_TOKEN=your_admin_token_here

# 🗄️ Optional: PostgreSQL database connection URL. If not provided, SQLite is used.
DATABASE_URL=postgresql://user:password@host:port/dbname
```

> **🔔 Note:** If `DATABASE_URL` is not provided, the application defaults to using an SQLite database named `api_keys.db`.

## ▶️ Running the Application

You can run the FastAPI application using Uvicorn:

```bash
uvicorn main:app --host 0.0.0.0 --port 8080
```

Alternatively, you can run `main.py` directly:

```bash
python main.py
```

---

## 🌐 API Endpoints

### 1️⃣ Chat Completions

- **🛠️ Endpoint**: `/chat/completions`
- **📡 Method**: `POST`
- **📜 Description**: Returns a chat completion based on the provided messages. If `stream` is `True`, a streaming response (NDJSON format) is returned.
- **🔐 Security**: Requires a valid API key in the `Authorization` header (`Bearer <API_KEY>`), unless `IGNPRE_API_KEYS` is set to `True`.

#### 📥 Request Payload

| Field      | Type    | Description                                                      |
| ---------- | ------- | ---------------------------------------------------------------- |
| `model`    | string  | The model name. Defaults to `llama-3.3-70b` if not provided.     |
| `messages` | array   | A list of messages, each with `role` and `content`.              |
| `stream`   | boolean | Optional flag to enable streaming response. Defaults to `False`. |

📌 **Example Request**:

```json
{
  "model": "o3-mini",
  "messages": [
    { "role": "user", "content": "Who are you?" }
  ],
  "stream": false
}
```

#### 📤 Response

- **Non-Streaming**: Returns a JSON object containing the chat completion.
- **Streaming**: Returns a streaming response with data chunks in NDJSON format.

---

### 2️⃣ API Key Management

#### 🔍 a. List API Keys

- **🛠️ Endpoint**: `/api-keys`
- **📡 Method**: `GET`
- **📜 Description**: Retrieves all API keys stored in the database.
- **🔐 Security**: Requires admin authorization. Include the admin token in the header as `Authorization: Bearer <ADMIN_TOKEN>`.

#### ➕ b. Create API Key

- **🛠️ Endpoint**: `/api-keys`
- **📡 Method**: `POST`
- **📜 Description**: Generates a new API key along with an optional description, and stores it in the database.
- **🔐 Security**: Requires admin authorization.

📥 **Request Payload**:

| Field         | Type   | Description                           |
| ------------- | ------ | ------------------------------------- |
| `description` | string | Optional description for the API key. |

📌 **Example Request**:

```json
{
  "description": "Test key created via test.py"
}
```

#### ❌ c. Delete API Key

- **🛠️ Endpoint**: `/api-keys/{key}`
- **📡 Method**: `DELETE`
- **📜 Description**: Deletes a specific API key from the database.
- **🔐 Security**: Requires admin authorization.

📌 **Example**:

```bash
DELETE /api-keys/your_api_key_here
```

---

## 🧪 Testing the API

The `test.py` script demonstrates how to interact with the API endpoints. It performs the following actions:

1️⃣ **Create a new API key** using the admin endpoint.
2️⃣ **Initialize the client** with the newly created API key.
3️⃣ **Test non-streaming chat completion** by sending a request to `/chat/completions`.
4️⃣ **Test streaming chat completion** and output the streamed response.
5️⃣ **Retrieve all API keys** using the admin endpoint.
6️⃣ **Delete the created API key**.

### ▶️ Running the Test Script

Make sure your FastAPI server is running, then execute:

```bash
python test.py
```

---

## 🎯 Conclusion

The **duckduckgo-ai-openai-api** project offers a solid foundation for building a chat-completion API. With integrated API key management, flexible database support, and clear endpoint definitions, it is suitable for development, testing, and production environments.

For further customization or questions, feel free to explore the code or reach out for additional guidance. 🚀

