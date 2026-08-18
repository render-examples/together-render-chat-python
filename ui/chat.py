from fastapi import HTTPException
from pydantic import BaseModel
import httpx

from ui.config import DEFAULT_MODEL, TOGETHER_API_KEY, TOGETHER_CHAT_URL


class ChatTurn(BaseModel):
    role: str
    content: str


class UiChatRequest(BaseModel):
    messages: list[ChatTurn]
    model: str | None = None


def require_messages(turns: list[ChatTurn]) -> list[dict[str, str]]:
    cleaned: list[dict[str, str]] = []
    for turn in turns[-40:]:
        role = turn.role.strip()
        content = turn.content.strip()
        if role not in ("user", "assistant") or not content or len(content) > 8000:
            raise HTTPException(
                status_code=400,
                detail='Each message needs role "user" or "assistant" and 1 to 8000 characters.',
            )
        cleaned.append({"role": role, "content": content})
    if not cleaned or cleaned[-1]["role"] != "user":
        raise HTTPException(
            status_code=400,
            detail="Conversation must end with a user message.",
        )
    return cleaned


def require_model(raw: str | None) -> str:
    model = (raw or DEFAULT_MODEL).strip()
    if not model or len(model) > 200:
        raise HTTPException(status_code=400, detail="Field \"model\" is invalid.")
    return model


async def complete_ui_chat(model: str, messages: list[dict[str, str]]) -> dict:
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            upstream = await client.post(
                TOGETHER_CHAT_URL,
                headers={"Authorization": f"Bearer {TOGETHER_API_KEY}"},
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": 512,
                },
            )
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail="Together timed out after 60 seconds.",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not reach Together.",
        ) from exc

    if not upstream.is_success:
        print("Together error", upstream.status_code, upstream.text)
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Upstream inference failed",
                "upstream_status": upstream.status_code,
            },
        )

    try:
        data = upstream.json()
        reply = data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Together returned an invalid response.",
        ) from exc

    if not isinstance(reply, str) or not reply:
        raise HTTPException(
            status_code=502,
            detail="Together returned an empty response.",
        )

    return {
        "model": data.get("model", model),
        "reply": reply,
        "usage": data.get("usage"),
    }
