# Binghomestay Support Agent

A customer-support chatbot for Binghomestay, built with [Pydantic AI](https://github.com/pydantic/pydantic-ai), FastAPI and a plain HTML/JS chat UI.

```
backend/    FastAPI + Pydantic AI agent (agent.py, data.py, main.py)
frontend/   Chat UI (index.html, style.css, app.js), served by the backend
requirements.txt
.env.example
```

The agent has five tools over mock data: `list_rooms`, `check_availability`, `get_policies`, `lookup_booking` and `create_support_ticket`. It returns structured output (`reply`, `needs_human`, `suggested_actions`).

## Prerequisites
- Python 3.10+ (developed on 3.13)
- An Anthropic API key (only for the real model; offline mock mode needs none)

## Setup (PowerShell)

```powershell
cd C:\Users\sheik\source\repos\binghomestaysupport
python -m venv .venv                 # skip if .venv already exists
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
MODEL=anthropic:claude-sonnet-5-5   # optional, any Pydantic AI model string
MOCK_LLM=                            # set to 1 to run offline with no key
```

## Run

```powershell
cd backend
python -m uvicorn main:app --port 8000 --reload
```

Open **http://localhost:8000** in your browser. The backend serves the frontend and the API from the same origin, so don't open `index.html` directly from disk.

### Try it without an API key

```powershell
cd backend
$env:MOCK_LLM = "1"
python -m uvicorn main:app --port 8000
```

Mock mode uses a simple keyword-based model. It doesn't call tools, create tickets or use chat history. Use a real key to see the full agent.

Sample questions: "What rooms do you have?", "What time is check-in?", "Status of BH1001" (mock bookings BH1001 to BH1003), "I want to talk to a human".

## API

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | `{"status":"ok"}` |
| POST | `/api/chat` | Body `{message, history:[{role, content}]}`, returns `{reply, needs_human, suggested_actions}` |

Quick test:

```powershell
curl.exe -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d '{\"message\":\"wifi password?\",\"history\":[]}'
```

## Notes
- All data (rooms, bookings, tickets) is in memory and resets on restart. Replace `backend/data.py` with a real database for production.
- If the model call fails (for example no API key), `/api/chat` returns HTTP 502 and the UI shows an error.
- The default model id has not been tested against a live API. If it errors, set `MODEL` in `.env` to a model your key supports.
