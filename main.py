import os
import secrets
from pathlib import Path

import httpx
from fastapi import FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

TOGETHER_URL = "https://api.together.ai/v1/chat/completions"
MODEL = os.environ.get("TOGETHER_MODEL", "Qwen/Qwen3.5-9B")
TOGETHER_API_KEY = os.environ["TOGETHER_API_KEY"]
CHAT_API_KEY = os.environ["CHAT_API_KEY"]
PUBLIC_DIR = Path(__file__).resolve().parent / "public"

app = FastAPI()


class ChatRequest(BaseModel):
    message: str


@app.get("/health")
def health():
    return {"ok": True, "model": MODEL}


@app.post("/chat")
async def chat(
    req: ChatRequest,
    authorization: str | None = Header(default=None),
):
    supplied_key = (
        authorization.removeprefix("Bearer ")
        if authorization and authorization.startswith("Bearer ")
        else ""
    )
    if not supplied_key or not secrets.compare_digest(
        supplied_key, CHAT_API_KEY
    ):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )

    message = req.message.strip()
    if not message or len(message) > 8000:
        raise HTTPException(
            status_code=400,
            detail='Field "message" must contain 1 to 8000 characters.',
        )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            upstream = await client.post(
                TOGETHER_URL,
                headers={"Authorization": f"Bearer {TOGETHER_API_KEY}"},
                json={
                    "model": MODEL,
                    "messages": [{"role": "user", "content": message}],
                    "reasoning": {"enabled": False},
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
        print("Together error", upstream.status_code, upstream.text[:500])
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
        "model": data.get("model", MODEL),
        "reply": reply,
        "usage": data.get("usage"),
    }


app.mount("/", StaticFiles(directory=PUBLIC_DIR, html=True), name="public")
