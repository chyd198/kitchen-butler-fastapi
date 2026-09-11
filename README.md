# Kitchen Butler — FastAPI Backend 🍳

FastAPI backend for the AI Kitchen Butler: send a fridge photo and/or a text description
of your ingredients, get back a ranked, illustrated Markdown recipe report. Backed by
the multimodal **Kimi (kimi-k2.6)** model and **Tavily** web search, deployable anywhere
Docker runs.

This is the deployable service layer for the prompt-driven agent developed in
[Kitchen-Agent](https://github.com/chyd198/Kitchen-Agent) (the notebook-based
LangChain/LangGraph project) — same agent logic, packaged as a real HTTP API + a
minimal web page instead of a notebook.

## Scoring

Each recipe is scored on three axes and ranked by total:

- 营养价值 (nutrition): 1–10
- 制作难度 (ease of cooking): 1–5
- 美味程度 (deliciousness): 1–15
- **Total: out of 30**

## Run locally

```bash
uv sync
cp .env.example .env   # fill in your Moonshot + Tavily keys
uv run uvicorn app.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000` — upload a photo and/or type a message, submit, wait
(a full recommendation takes roughly 1–3 minutes; it's a multi-step agent making
several model and search calls).

Or hit the API directly:

```bash
curl -F "message=我有番茄和鸡蛋，帮我推荐几个食谱" \
     -F "image=@sample_fridge.jpg" \
     http://127.0.0.1:8000/api/recommend
```

## API

| Endpoint | Method | Notes |
|---|---|---|
| `/` | GET | Serves the minimal web page |
| `/api/recommend` | POST (`multipart/form-data`) | Fields: `message` (optional), `image` (optional file), `thread_id` (optional, for follow-up questions) |
| `/healthz` | GET | Health check |

Images are compressed (longest side 1024px) and sent to the model as a base64 data
URI — Kimi's vision endpoint only accepts inline image data, not external URLs.

## Deploy with Docker

```bash
docker compose up -d --build
```

Serves on port 8000. Put an Nginx reverse proxy + TLS cert in front of it for a
real domain/HTTPS setup — not included here.

## Notes

- Conversation memory (`MemorySaver`) is in-process only — it resets on restart.
  Fine for small-scale personal use; swap in a persistent LangGraph checkpointer
  (Redis/Postgres) if you need history to survive restarts.
- The system prompt (in `app/agent.py`) carries all the business logic —
  ingredient recognition, freshness filtering, scoring rubric, report format —
  and is intentionally in Chinese, since the target users and recipe corpus
  searched are Chinese.
