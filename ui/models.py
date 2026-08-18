from __future__ import annotations

import time
from typing import Any

import httpx
from ui.config import (
    DEFAULT_MODEL,
    TEXT_MODEL_TYPES,
    TOGETHER_API_KEY,
    TOGETHER_MODELS_URL,
)

TTL_SECONDS = 10 * 60
_cache: dict[str, Any] | None = None


def _normalize(row: Any) -> dict[str, str] | None:
    if not isinstance(row, dict):
        return None
    model_id = str(row.get("id") or "").strip()
    model_type = str(row.get("type") or "").strip()
    if not model_id or model_type not in TEXT_MODEL_TYPES:
        return None
    return {
        "id": model_id,
        "type": model_type,
        "displayName": str(row.get("display_name") or model_id).strip(),
        "organization": str(row.get("organization") or "Together").strip(),
    }


async def _fetch_catalog() -> list[dict[str, str]]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        upstream = await client.get(
            TOGETHER_MODELS_URL,
            headers={"Authorization": f"Bearer {TOGETHER_API_KEY}"},
        )
    if not upstream.is_success:
        raise RuntimeError(f"Together models list failed ({upstream.status_code}).")
    payload = upstream.json()
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        rows = payload.get("data", [])
    else:
        rows = []
    models = [item for item in (_normalize(row) for row in rows) if item]
    models.sort(key=lambda item: item["id"])
    if not any(item["id"] == DEFAULT_MODEL for item in models):
        models.insert(
            0,
            {
                "id": DEFAULT_MODEL,
                "type": "chat",
                "displayName": DEFAULT_MODEL,
                "organization": "Default",
            },
        )
    return models


async def list_text_models() -> list[dict[str, str]]:
    global _cache
    now = time.monotonic()
    if _cache and now - _cache["at"] < TTL_SECONDS:
        return _cache["models"]
    try:
        models = await _fetch_catalog()
        _cache = {"at": now, "models": models}
        return models
    except Exception as exc:
        print("Could not list Together models", exc)
        if _cache:
            return _cache["models"]
        return [
            {
                "id": DEFAULT_MODEL,
                "type": "chat",
                "displayName": DEFAULT_MODEL,
                "organization": "Default",
            }
        ]


async def is_known_text_model(model_id: str) -> bool:
    models = await list_text_models()
    return any(item["id"] == model_id for item in models)
