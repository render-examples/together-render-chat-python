from fastapi import APIRouter, HTTPException

from ui.chat import UiChatRequest, complete_ui_chat, require_messages, require_model
from ui.config import DEFAULT_MODEL
from ui.models import is_known_text_model, list_text_models

router = APIRouter()


@router.get("/ui/models")
async def ui_models():
    return {"default": DEFAULT_MODEL, "models": await list_text_models()}


@router.post("/ui/chat")
async def ui_chat(req: UiChatRequest):
    model = require_model(req.model)
    if not await is_known_text_model(model):
        raise HTTPException(
            status_code=400,
            detail="Unknown model. Pick one from GET /ui/models.",
        )
    return await complete_ui_chat(model, require_messages(req.messages))
