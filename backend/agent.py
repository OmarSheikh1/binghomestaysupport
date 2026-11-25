import os
import re
from dataclasses import dataclass
from datetime import date

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart, UserPromptPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

import data

load_dotenv()


class SupportReply(BaseModel):
    reply: str = Field(description="Message to show the guest")
    needs_human: bool = Field(description="True if a human staff member should follow up")
    suggested_actions: list[str] = Field(default_factory=list, description="Short follow-up actions/quick replies")


@dataclass
class Deps:
    rooms: dict
    reservations: list
    policies: dict
    bookings: dict
    tickets: list


def make_deps() -> Deps:
    return Deps(data.ROOMS, data.RESERVATIONS, data.POLICIES, data.BOOKINGS, data.TICKETS)


SYSTEM_PROMPT = (
    "You are the friendly customer-support assistant for Binghomestay, a homestay/guesthouse. "
    "Use the tools to answer questions about rooms, availability, policies and bookings; never invent "
    "prices, availability or policies. Dates are ISO format YYYY-MM-DD. If you cannot resolve an issue, "
    "the guest is upset, or asks for refunds/exceptions, create a support ticket (ask for their email "
    "first) and set needs_human=true. Keep replies concise and warm, and offer 2-3 suggested_actions."
)


def _build_agent(model) -> Agent:
    agent = Agent(model, deps_type=Deps, output_type=SupportReply, system_prompt=SYSTEM_PROMPT)

    @agent.tool
    def list_rooms(ctx: RunContext[Deps]) -> list[dict]:
        """List all rooms with price per night (USD), capacity and amenities."""
        return [{"name": n, **r} for n, r in ctx.deps.rooms.items()]

    @agent.tool
    def check_availability(ctx: RunContext[Deps], room: str, check_in: str, check_out: str) -> dict:
        """Check if a room is free between check_in and check_out (YYYY-MM-DD)."""
        match = next((n for n in ctx.deps.rooms if n.lower() == room.lower()), None)
        if not match:
            return {"error": f"Unknown room '{room}'", "rooms": list(ctx.deps.rooms)}
        try:
            ci, co = date.fromisoformat(check_in), date.fromisoformat(check_out)
        except ValueError:
            return {"error": "Dates must be YYYY-MM-DD"}
        if co <= ci:
            return {"error": "check_out must be after check_in"}
        clash = any(r == match and ci < e and s < co for r, s, e in ctx.deps.reservations)
        nights = (co - ci).days
        return {"room": match, "available": not clash, "nights": nights,
                "total_price": nights * ctx.deps.rooms[match]["price_per_night"]}

    @agent.tool
    def get_policies(ctx: RunContext[Deps], topic: str) -> str:
        """Get a policy. Topic is one of: check-in/out times, cancellation, house rules, wifi, payments."""
        t = topic.lower()
        for key, text in ctx.deps.policies.items():
            if t in key or key in t or any(w in key for w in re.split(r"\W+", t) if len(w) > 3):
                return text
        return f"Unknown topic. Available: {', '.join(ctx.deps.policies)}"

    @agent.tool
    def lookup_booking(ctx: RunContext[Deps], booking_id: str) -> dict:
        """Look up a booking by ID (e.g. BH1001)."""
        return ctx.deps.bookings.get(booking_id.upper().strip(), {"error": f"No booking found with ID {booking_id}"})

    @agent.tool
    def create_support_ticket(ctx: RunContext[Deps], summary: str, contact_email: str) -> dict:
        """Create a ticket for a human staff member to follow up."""
        tid = f"T{len(ctx.deps.tickets) + 1001}"
        ctx.deps.tickets.append({"id": tid, "summary": summary, "contact_email": contact_email})
        return {"ticket_id": tid, "status": "open"}

    return agent


def _mock_model() -> FunctionModel:
    """Offline rules-based model: answers straight from the mock data."""

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        text = ""
        for m in reversed(messages):
            for p in getattr(m, "parts", []):
                if isinstance(p, UserPromptPart) and isinstance(p.content, str):
                    text = p.content
                    break
            if text:
                break
        q = text.lower()
        human, actions = False, ["See rooms", "Check policies", "Look up a booking"]
        if m_id := re.search(r"bh\d+", q):
            b = data.BOOKINGS.get(m_id.group(0).upper())
            reply = (f"Booking {m_id.group(0).upper()}: {b['room']}, {b['check_in']} to {b['check_out']}, "
                     f"status {b['status']}, total ${b['total']}.") if b else "I couldn't find that booking ID."
        elif any(w in q for w in ("refund", "complain", "angry", "human", "manager")):
            reply = "I'm sorry about that. I'll pass this to our team; please share your email so they can follow up."
            human, actions = True, ["Share email", "Look up a booking"]
        elif "wifi" in q or "wi-fi" in q:
            reply = data.POLICIES["wifi"]
        elif "cancel" in q:
            reply = data.POLICIES["cancellation"]
        elif "check-in" in q or "check in" in q or "check-out" in q or "checkout" in q:
            reply = data.POLICIES["check-in/out times"]
        elif "rule" in q or "smok" in q or "pet" in q:
            reply = data.POLICIES["house rules"]
        elif "pay" in q or "deposit" in q:
            reply = data.POLICIES["payments"]
        elif any(w in q for w in ("room", "price", "available", "stay", "book")):
            reply = "Our rooms: " + "; ".join(
                f"{n} (${r['price_per_night']}/night, sleeps {r['capacity']})" for n, r in data.ROOMS.items())
            actions = ["Check availability", "Ask about policies"]
        else:
            reply = "Hi! Welcome to Binghomestay. I can help with rooms, availability, policies and bookings."
        out = SupportReply(reply=reply, needs_human=human, suggested_actions=actions)
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, out.model_dump())])

    return FunctionModel(respond)


def get_agent() -> Agent:
    if os.getenv("MOCK_LLM", "").strip().lower() in ("1", "true", "yes"):
        return _build_agent(_mock_model())
    return _build_agent(os.getenv("MODEL") or "anthropic:claude-sonnet-5-5")
