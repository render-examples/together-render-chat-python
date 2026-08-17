<div align="center">

# Together chat API on Render (Python)

Authenticated single-turn `POST /chat` backed by [Together AI](https://docs.together.ai/docs/render-chat-api), running as a Render web service. FastAPI forwards one user message to chat completions and returns the reply, model ID, and token usage.

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
  <a href="https://github.com/ojusave/together-render-chat-ts">
    <img src="https://img.shields.io/badge/TypeScript-Express%20sibling-3178C6?logo=typescript&logoColor=white" alt="TypeScript sibling" />
  </a>
</p>

</div>

## What This Template Shows

The Blueprint is the Python path from Together's [Build a chat API on Render](https://docs.together.ai/docs/render-chat-api) guide, flattened into its own repo so the Deploy button can point at a single `render.yaml`.

| Piece | Role |
| --- | --- |
| **[Together AI chat completions](https://docs.together.ai/docs/inference/chat/overview)** | Server-side inference with `TOGETHER_API_KEY` |
| **[Render web service](https://render.com/docs/web-services)** | Public HTTPS, health checks, `0.0.0.0:$PORT` |
| **`CHAT_API_KEY`** | Separate bearer token for callers of `POST /chat` |

## Architecture

![Architecture diagram](static/images/architecture-diagram.png)

![Pipeline flow](static/images/pipeline-flow.png)

### How It Works

1. A trusted client sends `Authorization: Bearer $CHAT_API_KEY` and `{"message":"..."}` to `POST /chat`.
2. The service rejects missing or oversized messages before it spends Together credits.
3. It calls `https://api.together.ai/v1/chat/completions` with a 60 second timeout.
4. It returns `{ model, reply, usage }` or an explicit 401 / 400 / 502 / 504.

| Resource | Type | Plan | Notes |
| --- | --- | --- | --- |
| `together-chat-python` | Web service | Free | Spins down after 15 minutes idle |

Default region: **Oregon** unless you change it in the Dashboard. This service stores no chat history.

## Quick Start

### Prerequisites

- A [Render account](https://dashboard.render.com/register?utm_source=github&utm_medium=referral&utm_campaign=ojus_demos&utm_content=readme_link)
- A [Together AI](https://api.together.ai/) account with an active credit balance and a project API key
- A caller secret: `openssl rand -hex 32` (this is `CHAT_API_KEY`, not the Together key)

### Deploy

1. Click **Deploy to Render** above.
2. Paste `TOGETHER_API_KEY` and `CHAT_API_KEY` when Render prompts for secrets.
3. Wait until the service is **Live** (about 2 to 4 minutes on first build).
4. Open the service URL. The page should show the configured model from `GET /health`.
5. Send one authenticated request (or use the form on `/` and paste `CHAT_API_KEY` there).

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

Do not embed `CHAT_API_KEY` in browser or mobile app code. The shared token is a server-to-server guard for this demo.

## Features

| Feature | Description |
| --- | --- |
| **Authenticated chat** | `POST /chat` compares the bearer token with `secrets.compare_digest` |
| **Public health check** | `GET /health` is unauthenticated so Render can probe it |
| **Upstream mapping** | Together failures become 502; 60s timeouts become 504 |
| **Swap the model** | Change `TOGETHER_MODEL` in the Dashboard and redeploy |

## Configuration

| Variable | Source | Description |
| --- | --- | --- |
| `TOGETHER_API_KEY` | Required | Project-scoped Together API key |
| `CHAT_API_KEY` | Required | Bearer token callers use against this service |
| `TOGETHER_MODEL` | Optional | Defaults to `Qwen/Qwen3.5-9B` |
| `PYTHON_VERSION` | Optional | Blueprint pins `3.14.3` |
| `PORT` | Wired | Set by Render; uvicorn binds `0.0.0.0:$PORT` |

## Cost

| Resource | Approx. monthly |
| --- | ---: |
| Web service (Free) | $0 |
| Together inference | Billed by Together |

A free Render web service sleeps after 15 minutes without traffic. The next request can take about a minute to start. Together usage is separate from Render hosting.

## Troubleshooting

| Problem | Solution |
| --- | --- |
| Deploy asks for secrets | `TOGETHER_API_KEY` and `CHAT_API_KEY` are `sync: false`. Enter them on first Blueprint apply. |
| Health check fails | Confirm uvicorn listens on `0.0.0.0` and `$PORT`, and that both secrets are set so the process can start. |
| `401` on `/chat` | Send `Authorization: Bearer` plus the same `CHAT_API_KEY` value stored on the service. |
| `502` with `upstream_status` | Together rejected the call. Check the key, model ID, and Together credit balance. |
| Slow first request | Free instances spin down. Use a paid instance if you need consistent latency. |

## Project Structure

```
render.yaml       Render Blueprint
main.py           FastAPI health + chat handler
public/           Landing page (Deploy / Sign up / tester)
static/images/    Architecture diagrams
requirements.txt  FastAPI, uvicorn, httpx
```

## Learn More

**Render:**
- [Web services](https://render.com/docs/web-services)
- [Deploy to Render button](https://render.com/docs/deploy-to-render-button)
- [Free plan limits](https://render.com/docs/free)

**Upstream:**
- [Build a chat API on Render](https://docs.together.ai/docs/render-chat-api)
- [Chat completions](https://docs.together.ai/docs/inference/chat/overview)

TypeScript sibling: [together-render-chat-ts](https://github.com/ojusave/together-render-chat-ts).

## License

[MIT](LICENSE)
