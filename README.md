<div align="center">

# Together Chat API

An authenticated chat API on **Render**, backed by **Together AI** chat completions. FastAPI accepts a bearer token and a message, calls Together, and returns the reply, model ID, and token usage.

<p>
  <a href="https://render.com/deploy?repo=https://github.com/ojusave/together-render-chat-python">
    <img src="https://render.com/images/deploy-to-render-button.svg" alt="Deploy to Render" />
  </a>
</p>

<p>
  <a href="https://render.com">
    <img src="https://img.shields.io/badge/Render-Web%20Service-46e3b7?logo=render&logoColor=white" alt="Render" />
  </a>
  <a href="https://docs.together.ai/docs/render-chat-api">
    <img src="https://img.shields.io/badge/Together-Chat%20API-0f6fff" alt="Together AI" />
  </a>
  <a href="https://discord.gg/gvC7ceS9YS">
    <img src="https://img.shields.io/badge/Discord-Render%20Developers-5865F2?logo=discord&logoColor=white" alt="Discord" />
  </a>
  <a href="https://discord.gg/9Rk6sSeWEG">
    <img src="https://img.shields.io/badge/Discord-Together%20AI-5865F2?logo=discord&logoColor=white" alt="Together AI Discord" />
  </a>
</p>

</div>

## What This Demo Shows

This repo is the Python path from Together's [Build a chat API on Render](https://docs.together.ai/docs/render-chat-api) guide. `server.py` matches that guide. The landing page and model picker live in `ui/` so the documented handler stays small.

| Platform | Role |
| --- | --- |
| **[Render Web Services](https://render.com/docs/web-services)** | Hosts the FastAPI app, health checks, and landing page on `0.0.0.0:$PORT` |
| **[Together AI](https://docs.together.ai/docs/inference/chat/overview)** | Chat completions, plus [GET /models](https://docs.together.ai/reference/models) for the picker |
| **`CHAT_API_KEY`** | Separate bearer token for `POST /chat`, so the Together key never leaves the server |

TypeScript sibling: [together-render-chat-ts](https://github.com/ojusave/together-render-chat-ts).

### How It Works

1. **Browser** loads chat/language/code models from `GET /ui/models` (Together's live catalog) and sends the thread to `POST /ui/chat` with the selected model.
2. A trusted API client calls documented `POST /chat` with `Authorization: Bearer $CHAT_API_KEY`. That route always uses `TOGETHER_MODEL`.
3. FastAPI validates the body, then calls `https://api.together.ai/v1/chat/completions` (60 second timeout).
4. The service returns `{ model, reply, usage }`, or an explicit 401 / 400 / 502 / 504.

The service stores no chat history. The browser keeps the thread in memory.

Image, embedding, moderation, and rerank models are omitted from the picker: this demo only calls chat completions.

## Quick Start

### Prerequisites

- [Render account](https://dashboard.render.com/register?utm_source=github&utm_medium=referral&utm_campaign=ojus_demos&utm_content=readme_link)
- [Together AI account](https://api.together.ai/) with an active credit balance and a project API key
- A caller secret: `openssl rand -hex 32` (this becomes `CHAT_API_KEY`, not the Together key)

### Deploy

1. Click **Deploy to Render** above
2. You'll be prompted for:
   - `TOGETHER_API_KEY` — [Get one here](https://api.together.ai/)
   - `CHAT_API_KEY` — the hex secret you generated
3. Wait until the service is **Live**
4. Open the web service URL, pick a model, and send a message

## Features

| Feature | Description |
| --- | --- |
| **Authenticated chat** | `POST /chat` compares the bearer token with `secrets.compare_digest` |
| **Model picker** | The page lists Together text models from `GET /v1/models` |
| **Browser thread** | The landing page sends conversation history to `POST /ui/chat` |
| **Public health check** | `GET /health` is unauthenticated so Render can probe it |
| **Upstream mapping** | Together failures become 502; 60s timeouts become 504 |

## Configuration

| Variable | Where | Description |
| --- | --- | --- |
| `TOGETHER_API_KEY` | Web service | [Together project API key](https://api.together.ai/) |
| `CHAT_API_KEY` | Web service | Bearer token for `POST /chat` |
| `TOGETHER_MODEL` | Web service | Default picker value and the only model `POST /chat` uses (`Qwen/Qwen3.5-9B`) |
| `PYTHON_VERSION` | Web service | Blueprint pins `3.14.3` |
| `PORT` | Web service | Set by Render; uvicorn binds `0.0.0.0:$PORT` |

> [!WARNING]
> Do not embed `CHAT_API_KEY` in browser or mobile app code. The shared token is a server-to-server guard for this demo. The landing page uses `POST /ui/chat` for that reason.

## Project Structure

```
server.py            Documented FastAPI /health and /chat handler
main.py              Includes UI routes and serves public/
ui/                  Model catalog + /ui/chat
public/              Landing page
public/js/           Browser chat + model picker
render.yaml          Render Blueprint
requirements.txt     FastAPI, uvicorn, httpx
```

## API Routes

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/` | Landing page |
| `GET` | `/health` | `{ ok, model }` using `TOGETHER_MODEL` |
| `POST` | `/chat` | Single-turn chat. Requires `Authorization: Bearer $CHAT_API_KEY` and `{"message":"..."}` |
| `GET` | `/ui/models` | `{ default, models }` from Together `GET /v1/models` |
| `POST` | `/ui/chat` | Multi-turn helper. Body is `{"model":"...","messages":[{"role","content"}, ...]}` |

```bash
export SERVICE_URL="https://together-chat-python-xxxx.onrender.com"

curl "$SERVICE_URL/health"

read -s CHAT_API_KEY
export CHAT_API_KEY

curl -X POST "$SERVICE_URL/chat" \
  -H "Authorization: Bearer $CHAT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message":"In one sentence, what is a vector database?"}'

unset CHAT_API_KEY
```

## Troubleshooting

| Problem | Solution |
| --- | --- |
| Deploy asks for secrets | `TOGETHER_API_KEY` and `CHAT_API_KEY` are `sync: false`. Enter them on first Blueprint apply. |
| Health check fails | Confirm uvicorn listens on `0.0.0.0` and `$PORT`, and that both secrets are set so the process can start. |
| `401` on `/chat` | Send `Authorization: Bearer` plus the same `CHAT_API_KEY` value stored on the service. |
| `502` with `upstream_status` | Together rejected the call. Check the key, model ID, and Together credit balance. |
| Picker only shows the default model | Together `GET /models` failed. Check `TOGETHER_API_KEY` and Together status. |
| Image model missing from the picker | This demo only lists `chat`, `language`, and `code` models. |
| Follow-ups forget earlier turns | Use the landing page (`POST /ui/chat`). Documented `POST /chat` is single-turn. |

## Learn More

**Render:**
- [Render Web Services](https://render.com/docs/web-services)
- [Deploy to Render button](https://render.com/docs/deploy-to-render-button)
- [Render Developers Discord](https://discord.gg/gvC7ceS9YS)

**Together AI:**
- [Build a chat API on Render](https://docs.together.ai/docs/render-chat-api)
- [Chat completions](https://docs.together.ai/docs/inference/chat/overview)
- [List models](https://docs.together.ai/reference/models)
- [Together AI Discord](https://discord.gg/9Rk6sSeWEG)

## License

[MIT](LICENSE)
