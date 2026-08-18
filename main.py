from pathlib import Path

from fastapi.staticfiles import StaticFiles

from server import app
from ui.routes import router

PUBLIC_DIR = Path(__file__).resolve().parent / "public"

app.include_router(router)
app.mount("/", StaticFiles(directory=PUBLIC_DIR, html=True), name="public")
