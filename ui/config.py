import os

TOGETHER_MODELS_URL = "https://api.together.ai/v1/models"
TOGETHER_CHAT_URL = "https://api.together.ai/v1/chat/completions"
DEFAULT_MODEL = os.environ.get("TOGETHER_MODEL", "Qwen/Qwen3.5-9B")
TOGETHER_API_KEY = os.environ["TOGETHER_API_KEY"]
TEXT_MODEL_TYPES = ("chat", "language", "code")
