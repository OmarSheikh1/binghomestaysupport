from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart

from agent import SupportReply, get_agent, make_deps

app = FastAPI(title="Binghomestay Support")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

agent = get_agent()
deps = make_deps()


class HistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[HistoryItem] = []


def to_messages(history: list[HistoryItem]) -> list[ModelMessage]:
    out: list[ModelMessage] = []
    for h in history:
        if h.role == "user":
            out.append(ModelRequest(parts=[UserPromptPart(content=h.content)]))
        else:
            out.append(ModelResponse(parts=[TextPart(content=h.content)]))
    return out


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/chat", response_model=SupportReply)
async def chat(req: ChatRequest):
    try:
        result = await agent.run(req.message, deps=deps, message_history=to_messages(req.history))
    except Exception as e:  # e.g. missing API key
        raise HTTPException(status_code=502, detail=f"Agent error: {e}")
    return result.output


FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
