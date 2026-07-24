---
name: voice-assistant-ios
description: "Voice assistant pipeline: Apple Watch/iPhone trigger → STT → Hermes AI → TTS → AirPods/speaker via Tailscale tunnel."
version: 1.0.0
author: Friday
metadata:
  hermes:
    tags: [voice, ios, apple-watch, shortcuts, tailscale, tts, stt, audio]
---

# Voice Assistant — iOS + Hermes Integration

Connect an Apple Watch or iPhone trigger to Hermes for a fully hands-free voice assistant experience: press Watch → speak → AI replies through AirPods or active audio device.

## Architecture

```
Apple Watch (press-and-hold)
  → iPhone Shortcut (record mic)
  → STT (Apple on-device or Whisper)
  → POST to Hermes webhook (over Tailscale)
  → Hermes processes → TTS audio reply
  → Audio plays through active device (AirPods / speaker)
```

## Prerequisites

- Tailscale installed on Mac Mini (Hermes host) AND iPhone — both signed into same account
- Mac Mini Tailscale IP: 100.89.245.12
- Hermes webhook platform enabled on port 8644

## Step 1 — Enable Hermes Webhook Platform

Add to `~/.hermes/config.yaml`:
```yaml
platforms:
  webhook:
    enabled: true
    extra:
      host: "0.0.0.0"
      port: 8644
      secret: "your-strong-secret-here"
```

Restart gateway:
```bash
systemctl --user restart hermes-gateway
# or
hermes gateway run
```

Verify:
```bash
curl http://localhost:8644/health
```

## Architecture Choice: Async Webhook vs Sync Voice Server

Two modes available:

| Mode | Port | Use when |
|------|------|----------|
| Async webhook (fire & forget) | 8644 | Delivery to WhatsApp only, no spoken reply |
| Sync voice server (spoken reply) | 8645 | Voice-in / voice-out via Shortcut Speak step |

For true voice conversation, use the **sync voice server (port 8645)**. Skip to Step 2b.

## Step 2a — Create Hermes Voice Webhook (async, WhatsApp delivery only) (async, delivers to WhatsApp)

```bash
hermes webhook subscribe voice \
  --prompt "The user said: {message}. Reply conversationally and concisely as Friday." \
  --deliver whatsapp \
  --deliver-chat-id "160799431606497@lid" \
  --description "Voice input from iPhone/Watch — respond as Friday"
```

Webhook URL: `http://100.89.245.12:8644/webhooks/voice`
Webhook secret (auto-generated): `Y_eGalDVaw-ZQbrO1vYBR3xqddcknyPUfro1GCKsEu8`
Global platform secret: `210222661269d9cd967407e1ba558cecd24cc54d87bb4f16d69a4af082d01d31`

## Step 2b — Synchronous Voice Server (voice-in / voice-out via Shortcut)

For true voice-in → voice-out (reply spoken back on iPhone), use a separate FastAPI server on port 8645.
File: `/home/hermes/voice_server.py`
Systemd service: `friday-voice.service` (enabled, auto-starts)

The server calls Anthropic API directly (claude-haiku for speed) — NOT via `hermes -z` subprocess (too slow, 5-10s).
Uses `CLAUDE_CODE_OAUTH_TOKEN` from `~/.hermes/.env` as the API key.

Start/restart: `systemctl --user restart friday-voice.service`
Health check: `curl http://localhost:8645/health`
Test: `curl -X POST http://localhost:8645/ask -H "Content-Type: application/json" -d '{"message": "hello"}'`

socat forward on Mac (port 8645, alongside 8644):
```
sudo socat TCP-LISTEN:8645,bind=100.89.245.12,fork TCP:127.0.0.1:8645
```

**NOTE:** The webhook is fire-and-forget — returns `{"status":"accepted"}` immediately and delivers the reply to WhatsApp, NOT back to the Shortcut. For true voice-in/voice-out (Shortcut speaks the reply aloud), use the sync server below instead.

## Step 2b — Sync Voice Server (voice-in/voice-out, reply spoken aloud)

This is the preferred setup for watch-triggered voice assistant. Runs on port 8645.

Script at `/home/hermes/voice_server.py`:

```python
"""Friday Voice Server — synchronous AI endpoint for Apple Shortcuts"""
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

SYSTEM_PREFIX = (
    "You are Friday, Tanzim's personal AI assistant (Iron Man reference). "
    "Reply conversationally, concisely, and directly — like a smart friend. "
    "Skip filler phrases. This is a voice query — keep it 1-3 sentences max. "
    "The reply will be spoken aloud. User said: "
)

@app.post("/ask")
async def ask(request: Request):
    try:
        body = await request.json()
        message = body.get("message", "").strip()
        if not message:
            return JSONResponse({"error": "No message provided"}, status_code=400)
        prompt = SYSTEM_PREFIX + message
        proc = await asyncio.create_subprocess_exec(
            "hermes", "-z", prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
        reply = stdout.decode().strip()
        if not reply:
            return JSONResponse({"error": "No reply", "detail": stderr.decode()}, status_code=500)
        return JSONResponse({"reply": reply})
    except asyncio.TimeoutError:
        return JSONResponse({"error": "Timed out"}, status_code=504)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "friday-voice"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8645, log_level="info")
```

Uses `hermes -z` as AI backend — no separate API key needed, avoids rate limits.

Systemd service at `~/.config/systemd/user/friday-voice.service`:
```ini
[Unit]
Description=Friday Voice Server
After=network.target

[Service]
ExecStart=/home/hermes/.hermes/hermes-agent/venv/bin/python3 /home/hermes/voice_server.py
Restart=always
RestartSec=5
WorkingDirectory=/home/hermes
EnvironmentFile=/home/hermes/.hermes/.env

[Install]
WantedBy=default.target
```

Enable: `systemctl --user daemon-reload && systemctl --user enable --now friday-voice.service`

Mac socat for port 8645 (run in Terminal, leave open):
```bash
sudo socat TCP-LISTEN:8645,bind=100.89.245.12,fork TCP:127.0.0.1:8645
```

## Step 2b — Deploy Sync Voice Server (port 8645)

File: `/home/hermes/voice_server.py`

Two modes inside the server:
- **Quick replies** (≤25s): spoken back directly via Shortcut
- **Long tasks** (>25s): returns "On it, I'll send you the result on WhatsApp" immediately; agent continues in background

Uses `hermes --continue voice_session -z` for full tool access (runs jobs, edits sheets, writes code, etc.) with persistent session memory.

```python
"""
Friday Voice Server — full agent integration for Apple Shortcuts
POST /ask  { "message": "..." }  → { "reply": "..." }
Runs on port 8645
"""
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()
QUICK_TIMEOUT = 25

VOICE_PREFIX = (
    "You are responding to a voice query from Tanzim via his iPhone. "
    "Keep your spoken reply SHORT (1-4 sentences max) — it will be read aloud. "
    "If the task needs tools or will take time, say something brief like "
    "'On it, I\\'ll send you the results on WhatsApp' and then do the work. "
    "Voice query: "
)

async def run_agent(message: str) -> str:
    prompt = VOICE_PREFIX + message
    proc = await asyncio.create_subprocess_exec(
        "hermes", "--continue", "voice_session", "-z", prompt,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, _ = await proc.communicate()
    return stdout.decode().strip()

@app.post("/ask")
async def ask(request: Request):
    try:
        body = await request.json()
        message = body.get("message", "").strip()
        if not message:
            return JSONResponse({"error": "No message provided"}, status_code=400)
        try:
            reply = await asyncio.wait_for(run_agent(message), timeout=QUICK_TIMEOUT)
            if not reply:
                reply = "Got it, working on it — I'll send you the result on WhatsApp."
        except asyncio.TimeoutError:
            asyncio.create_task(run_agent(message))
            reply = "On it. I'll send you the result on WhatsApp."
        return JSONResponse({"reply": reply})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "friday-voice-full"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8645, log_level="warning")
```

Start: `python3 /home/hermes/voice_server.py`

Systemd service: `/home/hermes/.config/systemd/user/friday-voice.service` (enabled, auto-starts on boot)

socat bridge needed on macOS host (both ports):
```
sudo socat TCP-LISTEN:8644,bind=100.89.245.12,fork TCP:127.0.0.1:8644
sudo socat TCP-LISTEN:8645,bind=100.89.245.12,fork TCP:127.0.0.1:8645
```

## Step 3 — Build iPhone Shortcut (sync version — speaks reply aloud)

Shortcut flow:
1. **Dictate Text** (Apple on-device STT)
2. **Set Variable** — name: `VoiceInput`, value: Dictated Text
3. **Get Contents of URL** — POST to `http://100.89.245.12:8645/ask`
   - Method: POST
   - Body: JSON `{"message": VoiceInput}`
   - Headers: none
4. **Get Dictionary Value** — key: `reply`, from: Contents of URL
5. **Speak** — speak the Dictionary Value
   - Voice: use a Siri voice (smoother than default "Bubbles")
   - "Wait Until Finished": ON

**Debug tip:** Add "Show Content" after step 3 to see raw JSON. If you see `{"detail": "Not Found"}` — check the URL for a trailing backtick (common Shortcuts bug when editing URLs; delete it). Remove Show Content once working.

**For async WhatsApp delivery instead**

**For async WhatsApp delivery instead**, use `http://100.89.245.12:8644/webhooks/voice` with no Dictionary Value step (just Speak Contents of URL, but note it speaks raw JSON `{"status":"accepted"}`).

## Step 4 — Add to Apple Watch

**Enable Watch visibility first (required):**
1. Open Shortcuts on iPhone
2. Long-press the shortcut → tap **Details**
3. Toggle on **Show on Apple Watch**
4. The shortcut now appears in the Watch Shortcuts app and is selectable as a complication

Without this toggle, the shortcut will NOT appear in the Watch face complication picker even if the Shortcuts complication slot is added.

**Add as Watch face complication:**
1. Long-press the Apple Watch face → tap **Edit**
2. Swipe to the Complications screen
3. Tap an empty complication slot
4. Scroll to **Shortcuts** and select it
5. Pick the **Friday** shortcut from the list

Trigger: tap the complication on the watch face.

## Tailscale Notes

- Mac Mini IP: `100.89.245.12` (Tailscale private IP)
- Both devices must be online and connected to Tailscale
- iPhone must have Tailscale VPN active when away from home
- Test reachability: `curl http://100.89.245.12:8644/health` from iPhone browser (when Tailscale is on)

## Sync Mode — Voice-In / Voice-Out (Real-Time Reply)

The default webhook is fire-and-forget (reply goes to WhatsApp). For true voice-out response spoken back through the Shortcut:

### Voice Server (`/home/hermes/voice_server.py`)

Runs on port 8645. POST `/ask` → returns `{"reply": "..."}` synchronously.
Uses `hermes -z` subprocess — **do NOT use CLAUDE_CODE_OAUTH_TOKEN directly**, it hits rate limits.

```python
proc = await asyncio.create_subprocess_exec(
    "hermes", "-z", SYSTEM_PREFIX + message,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE
)
stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
reply = stdout.decode().strip()
```

### Auto-start via systemd user service

`~/.config/systemd/user/friday-voice.service`:
```ini
[Unit]
Description=Friday Voice Server
After=network.target

[Service]
ExecStart=/home/hermes/.hermes/hermes-agent/venv/bin/python3 /home/hermes/voice_server.py
Restart=always
RestartSec=5
WorkingDirectory=/home/hermes
EnvironmentFile=/home/hermes/.hermes/.env

[Install]
WantedBy=default.target
```

Enable: `systemctl --user daemon-reload && systemctl --user enable friday-voice.service`

### socat forward on macOS (add alongside port 8644 line)

```bash
sudo socat TCP-LISTEN:8645,bind=100.89.245.12,fork TCP:127.0.0.1:8645
```

### Shortcut changes for sync mode

1. Change URL to `http://100.89.245.12:8645/ask`
2. After "Get Contents of URL", add **Get Dictionary Value** — key: `reply`, from: Contents of URL
3. Plug the dictionary value into Speak step (not raw Contents of URL — that reads the JSON)

## Hybrid Fast/Tool Routing

For sub-2s conversational replies AND full tool access for commands, use a hybrid voice server:

- **Fast path**: Direct Anthropic API call with `claude-haiku-4-5` + local conversation history JSON (sub-1s)
- **Tool path**: `hermes --continue voice_session -z` for commands (run scrapers, check sheets, etc.)

Route based on keyword detection:
```python
COMMAND_PATTERNS = re.compile(
    r"\b(run|start|scrape|crawl|search|find jobs|send|email|schedule|create|delete|update|"
    r"open|check jobs|job scraper|activate|execute|fetch|pull|download|upload|"
    r"remind|set|cancel|stop|restart|deploy|push|sheet|spreadsheet|whatsapp)\b",
    re.IGNORECASE
)
```

Conversation history: store last N exchanges in `/home/hermes/voice_history.json`, pass with every Haiku request. Cap at `MAX_HISTORY = 10` turns.

Direct Haiku API call (no subprocess overhead):
```python
headers = {
    "x-api-key": os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", ""),
    "anthropic-version": "2023-06-01",
    "content-type": "application/json",
}
# Do NOT include "anthropic-beta" header — causes 400 error
```

**Pitfall:** `anthropic-beta: oauth-2023-05-10` header causes `400 invalid_request_error` — omit it entirely.
**Pitfall:** systemd service needs `Environment="PATH=/home/hermes/.local/bin:..."` or `hermes` binary won't be found (tool path will fail with `[Errno 2] No such file or directory`).

## Hybrid Voice Server (recommended — fast + full tools)

The best production setup routes requests based on intent:
- **Fast path** — Haiku + conversation history JSON (sub-2s) for questions/chat
- **Tool path** — `hermes --continue voice_session` (full tools) for commands

### Command detection regex
```python
COMMAND_PATTERNS = re.compile(
    r"\b(run|start|scrape|crawl|search|find jobs|send|email|schedule|create|delete|update|"
    r"open|check jobs|job scraper|job crawler|activate|execute|fetch|pull|download|upload|"
    r"remind|set|cancel|stop|restart|deploy|push|sheet|spreadsheet|whatsapp)\b",
    re.IGNORECASE
)
```

### Conversation history (fast path only)
Store last N exchanges in `/home/hermes/voice_history.json`. Pass full history to Haiku on every fast-path request — this gives the voice assistant memory between queries.

```python
HISTORY_FILE = "/home/hermes/voice_history.json"
MAX_HISTORY = 10  # last N exchanges

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE) as f:
                return json.load(f)
        except: pass
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history[-MAX_HISTORY * 2:], f)
```

### Haiku API call (fast path)
```python
async def call_haiku(message: str) -> str:
    history = load_history()
    history.append({"role": "user", "content": message})
    token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", "")
    headers = {
        "x-api-key": token,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": "claude-haiku-4-5",
        "max_tokens": 256,
        "system": SYSTEM_PROMPT,
        "messages": history[-MAX_HISTORY * 2:],
    }
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
        resp.raise_for_status()
        reply = resp.json()["content"][0]["text"].strip()
    history.append({"role": "assistant", "content": reply})
    save_history(history)
    return reply
```

**Pitfall:** Do NOT pass `anthropic-beta: oauth-2023-05-10` header — it causes a 400 error. Use bare auth headers only.

**Pitfall:** CLAUDE_CODE_OAUTH_TOKEN works fine for Haiku direct calls (no rate limit issues at low voice query volumes).

**Live script:** `/home/hermes/voice_server.py` (hybrid version, port 8645)

## TTS Options

| Option | Notes |
|--------|-------|
| Apple Siri TTS (Shortcut "Speak Text") | Free, on-device, good quality |
| ElevenLabs API | High quality, costs money |
| Hermes built-in TTS | Check if audio_cache is being used |

## Systemd Service — Recommended Unit File

The service needs two critical additions beyond the bare minimum:

1. **PATH environment** — systemd doesn't inherit user PATH, so `hermes` won't be found
2. **ExecStartPre port cleanup** — prevents 682-restart crash loops when old process holds port

```ini
[Unit]
Description=Friday Voice Server (sync AI endpoint for Apple Shortcuts)
After=network.target

[Service]
Environment="PATH=/home/hermes/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStartPre=-/bin/bash -c "fuser -k 8645/tcp || true"
ExecStart=/home/hermes/.hermes/hermes-agent/venv/bin/python3 /home/hermes/voice_server.py
Restart=always
RestartSec=5
WorkingDirectory=/home/hermes
EnvironmentFile=/home/hermes/.hermes/.env

[Install]
WantedBy=default.target
```

## Low-Latency Mode — Direct Haiku API (Recommended)

Using `hermes -z` subprocess adds 5-10s overhead per voice query. For sub-1s responses, call Anthropic API directly with `claude-haiku-4-5`. Trade-off: no tool access — pure conversational replies only (long tasks still fall back to WhatsApp).

Key implementation notes:
- Use `CLAUDE_CODE_OAUTH_TOKEN` from `.env` as `x-api-key`
- Do NOT include `anthropic-beta: oauth-2023-05-10` header — causes 400 error
- `max_tokens: 256` is sufficient for short voice replies
- Achieved ~0.7s end-to-end response time in testing

```python
headers = {
    "x-api-key": os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", ""),
    "anthropic-version": "2023-06-01",
    "content-type": "application/json",
}
payload = {
    "model": "claude-haiku-4-5",
    "max_tokens": 256,
    "system": SYSTEM_PROMPT,
    "messages": [{"role": "user", "content": message}],
}
async with httpx.AsyncClient(timeout=20) as client:
    resp = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()["content"][0]["text"].strip()
```

## Hybrid Routing Architecture (voice_server.py — current implementation)

The voice server uses two paths based on keyword detection:

**Fast path (Haiku + history, sub-2s):** Conversational queries — questions, follow-ups, general chat
**Tool path (hermes --continue voice_session, ~5-25s):** Commands — run, scrape, search, send, schedule, create, update, fetch, etc.

Keyword regex triggers tool path:
```python
COMMAND_PATTERNS = re.compile(
    r"\b(run|start|scrape|crawl|search|find jobs|send|email|schedule|create|delete|update|"
    r"open|check jobs|job scraper|job crawler|activate|execute|fetch|pull|download|upload|"
    r"remind|set|cancel|stop|restart|deploy|push|sheet|spreadsheet|whatsapp)\b",
    re.IGNORECASE
)
```

Conversation history stored at `/home/hermes/voice_history.json` — last 10 exchanges kept, passed with every Haiku request for continuity.

Tool path: 25s timeout. If exceeded, fires task in background and returns "On it, I'll send results to WhatsApp."

## Hybrid Voice Server (BUILT — 2026-05-03)

Current architecture at `/home/hermes/voice_server.py` is a hybrid router:

- **Fast path (Haiku, sub-2s):** conversational queries — calls Anthropic API directly, maintains conversation history in `/home/hermes/voice_history.json` (last 10 exchanges)
- **Tool path (hermes --continue voice_session, ~5-25s):** commands detected by keyword regex — runs full agent with tool access, delivers result to WhatsApp if it times out

**Command detection regex (triggers tool path):**
```python
COMMAND_PATTERNS = re.compile(
    r"\b(run|start|scrape|crawl|search|find jobs|send|email|schedule|create|delete|update|"
    r"open|check jobs|job scraper|job crawler|activate|execute|fetch|pull|download|upload|"
    r"remind|set|cancel|stop|restart|deploy|push|sheet|spreadsheet|whatsapp)\b",
    re.IGNORECASE
)
```

**Conversation history** stored as JSON list of `{role, content}` dicts — passed as `messages` array to Haiku on every fast-path call. Capped at last 20 entries (10 exchanges).

**API call (Haiku direct):**
```python
headers = {
    "x-api-key": os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", ""),
    "anthropic-version": "2023-06-01",
    "content-type": "application/json",
}
# NO anthropic-beta header — causes 400 error
```

**Critical fixes applied:**
- `ExecStartPre=-/bin/bash -c "fuser -k 8645/tcp || true"` added to systemd unit — prevents "address already in use" crash loop on restart
- `Environment="PATH=/home/hermes/.local/bin:/usr/local/sbin:..."` added to systemd unit — hermes binary not found without it (causes "No such file or directory" error)

## Hybrid Voice Server Architecture (BUILT — 2026-05-03)

The voice server at `/home/hermes/voice_server.py` uses a hybrid routing approach:

- **Fast path (Haiku, sub-2s):** Conversational queries → direct Anthropic API call with conversation history stored in `/home/hermes/voice_history.json`. Last 10 exchanges kept and passed with every request for continuity.
- **Tool path (hermes, ~5-25s):** Command queries (run, scrape, find, send, search, etc.) → `hermes --continue voice_session -z` with full tool access. Returns "On it, I'll send you the result on WhatsApp" if >25s.

Routing is done by regex keyword match (`COMMAND_PATTERNS`) on the incoming message. If a command keyword is detected → hermes. Otherwise → Haiku + history.

**API call format for Haiku (direct):**
```python
headers = {
    "x-api-key": os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"),
    "anthropic-version": "2023-06-01",
    "content-type": "application/json",
    # NO anthropic-beta header — causes 400 error
}
payload = {
    "model": "claude-haiku-4-5",
    "max_tokens": 256,
    "system": SYSTEM_PROMPT,
    "messages": history[-20:],  # last 10 exchanges = 20 messages
}
```

**Pitfall — do NOT include `anthropic-beta` header** when using CLAUDE_CODE_OAUTH_TOKEN directly. It causes a 400 `invalid_request_error: Unexpected value(s) for the anthropic-beta header`.

## Systemd Service Fixes (2026-05-03)

Two critical fixes applied to `/home/hermes/.config/systemd/user/friday-voice.service`:

**1. PATH fix** — systemd doesn't include `/home/hermes/.local/bin` by default, so `hermes` binary wasn't found, causing "No such file or directory" on every tool-path request:
```ini
Environment="PATH=/home/hermes/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
```

**2. Port conflict fix** — when the server crashed, the old process held port 8645 and systemd's restart loop would fail 100s of times with "address already in use":
```ini
ExecStartPre=-/bin/bash -c "fuser -k 8645/tcp || true"
```
The `-` prefix means systemd continues even if the pre-start command fails (e.g. nothing on the port). The `|| true` is a belt-and-suspenders safety.

Full working service file:
```ini
[Unit]
Description=Friday Voice Server (sync AI endpoint for Apple Shortcuts)
After=network.target

[Service]
Environment="PATH=/home/hermes/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStartPre=-/bin/bash -c "fuser -k 8645/tcp || true"
ExecStart=/home/hermes/.hermes/hermes-agent/venv/bin/python3 /home/hermes/voice_server.py
Restart=always
RestartSec=5
WorkingDirectory=/home/hermes
EnvironmentFile=/home/hermes/.hermes/.env

[Install]
WantedBy=default.target
```

## Hybrid Voice Server Architecture (BUILT — 2026-05-03)

The voice server at `/home/hermes/voice_server.py` now runs a hybrid routing model:

**Fast path (Haiku, sub-2s):** Conversational queries — questions, follow-ups, casual chat. Uses direct Anthropic API call with `claude-haiku-4-5`. Maintains conversation history in `/home/hermes/voice_history.json` (last 10 exchanges) so follow-up questions have context.

**Tool path (hermes --continue voice_session, ~5s):** Command queries — anything matching keywords like run, scrape, search, send, schedule, create, delete, check jobs, sheet, etc. Routes to full hermes agent with complete tool access. Long tasks (>25s) return "On it, I'll send you the result on WhatsApp" immediately and continue in background.

**Routing detection:** Regex on COMMAND_PATTERNS. If match → hermes. Else → Haiku + history.

**History file:** `/home/hermes/voice_history.json` — stores last 20 messages (10 exchanges). Persists across requests. Fast path reads + appends; tool path does not use history (hermes has its own session).

**Critical — systemd PATH fix:** The hermes binary lives at `/home/hermes/.local/bin/hermes` but systemd's default PATH doesn't include it. Without this, tool-path requests fail with `[Errno 2] No such file or directory`. Fix — add to service file:
```ini
Environment="PATH=/home/hermes/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
```

**Critical — port lock fix:** Added `ExecStartPre=-/bin/bash -c "fuser -k 8645/tcp || true"` to the systemd unit to kill any lingering process on 8645 before each start. Prevents the 682-restart crash loop caused by "address already in use" when the old process doesn't release the port fast enough.

**Current service file** (`~/.config/systemd/user/friday-voice.service`):
```ini
[Unit]
Description=Friday Voice Server (sync AI endpoint for Apple Shortcuts)
After=network.target

[Service]
Environment="PATH=/home/hermes/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStartPre=-/bin/bash -c "fuser -k 8645/tcp || true"
ExecStart=/home/hermes/.hermes/hermes-agent/venv/bin/python3 /home/hermes/voice_server.py
Restart=always
RestartSec=5
WorkingDirectory=/home/hermes
EnvironmentFile=/home/hermes/.hermes/.env

[Install]
WantedBy=default.target
```

**OAuth token for Haiku calls:** Uses `CLAUDE_CODE_OAUTH_TOKEN` from `~/.hermes/.env` as `x-api-key`. Do NOT include `anthropic-beta: oauth-2023-05-10` header — it causes a 400 error. Standard headers only.

**Model:** `claude-haiku-4-5` for fast path. Confirmed sub-1s response time locally.

## Hybrid Voice Server Architecture (Recommended)

For best results, use a hybrid server that routes fast queries to Haiku and commands to full hermes:

- **Fast path**: Direct Anthropic API call with `claude-haiku-4-5`, conversation history stored in `/home/hermes/voice_history.json` (last 10 exchanges). Sub-2s response.
- **Command path**: `hermes --continue voice_session -z` for tool access (run scrapers, sheets, etc.). ~5-25s, returns "On it, sending to WhatsApp" if over timeout.
- **Detection**: regex on keywords like run/start/scrape/send/search/schedule/check jobs/etc.
- **History format**: list of `{role, content}` dicts, appended after each Haiku exchange, max 20 entries kept.

Key: use `CLAUDE_CODE_OAUTH_TOKEN` from `.env` as `x-api-key`. Do NOT include `anthropic-beta: oauth-2023-05-10` header — it causes 400 errors.

## Systemd Service Pitfalls & Fixes

**Crash loop fix — "address already in use"**: Add `ExecStartPre` to kill lingering process before each start:
```ini
ExecStartPre=-/bin/bash -c "fuser -k 8645/tcp || true"
```
The `-` prefix means systemd continues even if this step fails (nothing to kill).

**PATH fix — "No such file or directory" when spawning hermes**: Systemd user services don't inherit shell PATH. `hermes` lives at `/home/hermes/.local/bin/hermes` which is not in default systemd PATH. Fix: add to service file:
```ini
Environment="PATH=/home/hermes/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
```

Full working service file:
```ini
[Unit]
Description=Friday Voice Server (sync AI endpoint for Apple Shortcuts)
After=network.target

[Service]
Environment="PATH=/home/hermes/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStartPre=-/bin/bash -c "fuser -k 8645/tcp || true"
ExecStart=/home/hermes/.hermes/hermes-agent/venv/bin/python3 /home/hermes/voice_server.py
Restart=always
RestartSec=5
WorkingDirectory=/home/hermes
EnvironmentFile=/home/hermes/.hermes/.env

[Install]
WantedBy=default.target
```

## Hybrid Routing Pattern (fast + full tool access)

For the best of both worlds — sub-2s for questions, full tools for commands:

```python
COMMAND_PATTERNS = re.compile(
    r"\b(run|start|scrape|crawl|search|find jobs|send|email|schedule|create|delete|update|"
    r"open|check jobs|job scraper|activate|execute|fetch|pull|download|upload|"
    r"remind|set|cancel|stop|restart|deploy|push|sheet|spreadsheet|whatsapp)\b",
    re.IGNORECASE
)

def is_command(message): return bool(COMMAND_PATTERNS.search(message))

# Fast path: direct Haiku API call with conversation history (~0.7s)
# Tool path: hermes --continue voice_session (full tools, ~5-10s)
```

Conversation history stored in `/home/hermes/voice_history.json` — load/save on every fast-path request. Keep last 10 exchanges (MAX_HISTORY = 10).

Current voice_server.py at `/home/hermes/voice_server.py` implements this pattern.

## Critical: systemd PATH fix

Systemd user services don't inherit shell PATH. If voice_server spawns `hermes`, add to service file:
```ini
Environment="PATH=/home/hermes/.local/bin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
```
Without this: `[Errno 2] No such file or directory` on every hermes subprocess call.

## Hybrid Mode (BUILT — 2026-05-03)

voice_server.py now uses a hybrid routing model:
- **Fast path** (Haiku + conversation history): questions, conversation — sub-2s
- **Tool path** (hermes --continue voice_session): commands like "run scraper", "send", "check jobs" — full tool access, ~5-25s, falls back to WhatsApp for long tasks

Conversation history stored at `/home/hermes/voice_history.json` (last 10 exchanges).
Command detection via regex on keywords: run, start, scrape, crawl, search, send, email, schedule, create, delete, update, open, check jobs, job scraper, activate, execute, fetch, pull, download, upload, remind, set, cancel, stop, restart, deploy, push, sheet, spreadsheet, whatsapp.

Uses `CLAUDE_CODE_OAUTH_TOKEN` from `.env` for Haiku calls. Model: `claude-haiku-4-5`.

## Critical Fixes Found (2026-05-03)

### systemd PATH issue
The Hermes venv python runs the voice server, but `hermes` binary lives at `/home/hermes/.local/bin/hermes` — NOT in systemd's default PATH. Without this, every voice command fails with `[Errno 2] No such file or directory`.

**Fix — add to friday-voice.service [Service] section:**
```ini
Environment="PATH=/home/hermes/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
```

### Port conflict crash loop
When the service crashes hard, the old process holds port 8645. Systemd restarts every 5s, fails 600+ times until the old process dies.

**Fix — add ExecStartPre to kill port before each start:**
```ini
ExecStartPre=-/bin/bash -c "fuser -k 8645/tcp || true"
```
The `-` prefix tells systemd to continue even if ExecStartPre fails (nothing on port = no error).

### Full working service file
```ini
[Unit]
Description=Friday Voice Server (sync AI endpoint for Apple Shortcuts)
After=network.target

[Service]
Environment="PATH=/home/hermes/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStartPre=-/bin/bash -c "fuser -k 8645/tcp || true"
ExecStart=/home/hermes/.hermes/hermes-agent/venv/bin/python3 /home/hermes/voice_server.py
Restart=always
RestartSec=5
WorkingDirectory=/home/hermes
EnvironmentFile=/home/hermes/.hermes/.env

[Install]
WantedBy=default.target
```

## Pitfalls

- **systemd service missing PATH** — systemd user services don't inherit `~/.local/bin` in PATH. The `hermes` binary lives at `/home/hermes/.local/bin/hermes` which is NOT in the default systemd PATH. Fix: add `Environment="PATH=/home/hermes/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"` to the `[Service]` block. Without this, `hermes` subprocess calls fail with `[Errno 2] No such file or directory`.
- **Port binding crash loop** — if the voice server crashes while holding port 8645, systemd restarts immediately and fails with "address already in use", looping hundreds of times. Fix: add `ExecStartPre=-/bin/bash -c "fuser -k 8645/tcp || true"` before `ExecStart`. The `-` prefix makes it non-fatal if nothing is on the port.
- Tailscale must be active on iPhone for this to work outside home WiFi
- Apple Shortcuts mic recording requires user permission
- Webhook port 8644 must not be blocked by Mac Mini firewall
- Apple Watch can trigger Shortcuts but cannot record audio directly — mic is always iPhone
- Nothing earbuds / AirPods become active audio device automatically when connected; Shortcut "Speak Text" routes to them
- **Shortcuts "Dictated Text" variable insertion is unreliable** — tapping "Dictate text" in the Select Variable list often does nothing or inserts the wrong value. The reliable workaround: insert a **Set Variable** action between Dictate Text and Get Contents of URL. Name it `VoiceInput`. Then in the JSON body "Text" field, use Select Variable → VoiceInput. This bypasses the Dictated Text variable selection bug entirely.
- **"Select Variable" shows URL instead of Dictated Text** — this happens when the text field already has content. Clear the field first, then use Select Variable.
- **Tailscale on Mac Mini is Mac App Store GUI app only** — no `tailscale` CLI available inside Hermes Linux environment. Do not attempt `tailscale status` or `tailscale ip` from terminal.
- **Hermes runs inside a Linux container on the Mac Mini** — the Tailscale 100.x IP is bound to macOS host, not the Linux env. Direct curl from Hermes to `100.89.245.12:8644` will time out. Need port forwarding to bridge macOS Tailscale → Linux container. Use `socat` on macOS: `sudo socat TCP-LISTEN:8644,bind=100.89.245.12,fork TCP:127.0.0.1:8644` (requires socat installed via Homebrew on macOS side).
- **Homebrew IS installed on Tanzim's Mac Mini** — `brew install socat` works directly, no need to install Homebrew first.
- **socat command must stay running** — run `sudo socat TCP-LISTEN:8644,bind=100.89.245.12,fork TCP:127.0.0.1:8644` in a Mac Terminal tab (NO `&` or `nohup`) and leave it open. It should sit with a blinking cursor — that's correct. If the tab is closed, iPhone loses access to Hermes. Consider setting it up as a launchd service for persistence.
- **systemd PATH missing hermes binary** — systemd user services don't inherit the user's shell PATH. If the voice server spawns `hermes` and gets `[Errno 2] No such file or directory`, add `Environment="PATH=/home/hermes/.local/bin:/usr/local/bin:/usr/bin:/bin"` to the `[Service]` block.
- **Port binding crash loop** — if systemd restarts the service before the old process releases the port, add `ExecStartPre=-/bin/bash -c "fuser -k 8645/tcp || true"` before `ExecStart`. The `-` prefix tells systemd to continue even if the pre-start step fails.
- **Trailing backtick in URL causes 404** — when editing the URL in Shortcuts, a backtick (`) can get appended silently. The response will be `{"detail": "Not Found"}` instead of `{"reply": "..."}`. Tap the URL field and delete the backtick at the end.
- **"Bubbles" voice sounds shaky/robotic** — in the Speak step, change Voice from "Bubbles" to a Siri voice (Siri Voice 1 or 2) for natural-sounding TTS.
- **Do NOT use `hermes -z` subprocess for quick conversational replies** — spawning a full hermes process per request takes 5-10 seconds. Call Anthropic API directly via httpx with claude-haiku-4-5 for sub-2s responses. Use hermes only for command/tool requests.
- **Haiku model name**: `claude-haiku-4-5` (not `claude-haiku-3` or `claude-haiku`).
- **No anthropic-beta header with OAuth token**: sending `anthropic-beta: oauth-2023-05-10` causes 400 invalid_request_error. Omit it entirely.
- **PATH not set in systemd service** — hermes binary lives at /home/hermes/.local/bin/hermes which is NOT in systemd's default PATH. Add `Environment="PATH=/home/hermes/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"` to the [Service] block or tool-path calls silently fail with "No such file or directory".
- **Port already in use crash loop** — if the service crashes without releasing port 8645, systemd will loop hundreds of times. Fix: add `ExecStartPre=-/bin/bash -c "fuser -k 8645/tcp || true"` before ExecStart.
- **Hybrid routing is the recommended architecture** — use keyword regex to detect commands (run/scrape/send/search/sheet/whatsapp etc.) → hermes tool path; everything else → Haiku fast path with conversation history saved to /home/hermes/voice_history.json (last 10 exchanges, passed as messages array).
- **Conversation history** — store as JSON array of {role, content} dicts. Load on every fast-path call, append user+assistant turns, trim to MAX_HISTORY*2, save back. This gives continuity across voice queries without full session overhead.
- **Conversation history**: store as JSON list of `{role, content}` at `/home/hermes/voice_history.json`. Load on each request, append user+assistant turns, trim to last 20 entries, save back. This gives voice assistant memory across queries.
- **Systemd PATH missing hermes**: default systemd PATH doesn't include `/home/hermes/.local/bin`. Always add `Environment="PATH=..."` line to service file or hermes subprocess will fail with "No such file or directory".
- **Crash loop from port conflict**: if service crashes without releasing port, systemd restart loop hits "address already in use" hundreds of times. Fix with `ExecStartPre=-/bin/bash -c "fuser -k 8645/tcp || true"`.
- **Wix login blocked by reCAPTCHA**: headless Playwright/Firefox cannot log into Wix — reCAPTCHA Enterprise blocks all headless browser attempts regardless of correct credentials.
- **systemd PATH is missing `/home/hermes/.local/bin`** — hermes CLI lives there; without it the server crashes with `[Errno 2] No such file or directory` on every request. Add `Environment="PATH=/home/hermes/.local/bin:..."` to the service unit.
- **Port conflict crash loop** — if a previous process holds port 8645 when systemd restarts the service, it fails and retries every 5s indefinitely (observed: 682 restarts). Fix: add `ExecStartPre=-/bin/bash -c "fuser -k 8645/tcp || true"` to the unit file.
- **Do NOT include `anthropic-beta: oauth-2023-05-10` header** when using CLAUDE_CODE_OAUTH_TOKEN for direct API calls — causes 400 invalid_request_error. Just use standard headers.
- **CLAUDE_CODE_OAUTH_TOKEN is rate-limited** — if direct Anthropic API calls fail with 429, the OAuth token is being throttled. Fall back to `hermes -z` temporarily or add a real ANTHROPIC_API_KEY to ~/.hermes/.env.
- **Do NOT background socat with `&` or `nohup`** — macOS sudo can't prompt for password when backgrounded, causing it to suspend immediately.
- **socat suspends before password prompt** — this is normal macOS sudo behavior. Just wait for the password prompt and enter Mac login password.
- **Webhook health check from iPhone** — visit `http://100.89.245.12:8644/health` in iPhone Safari (with Tailscale active) to verify end-to-end connectivity before building the Shortcut.
- **CLAUDE_CODE_OAUTH_TOKEN hits rate limits for direct API calls** — do not use it in voice_server.py. Use `hermes -z "prompt"` subprocess instead; it routes through the configured provider without OAuth rate limits.
- **Shortcut not appearing in Watch complication picker** — must enable "Show on Apple Watch" via long-press → Details in the Shortcuts app on iPhone first. Simply having the Shortcuts complication slot on the watch face is not enough.
- **Watch Shortcuts still empty after enabling "Show on Apple Watch"** — toggle it off, wait 5s, toggle back on. If still not working: restart the Watch (hold side button → Power Off). If still failing, check Watch app on iPhone → My Watch → ensure Shortcuts app is installed on Watch. Also verify iPhone Settings → Apple ID → iCloud → Shortcuts is toggled ON (iCloud sync required for Watch delivery). As a last resort, unpair and re-pair the Watch (Watch app → All Watches → (i) icon → Unpair — takes 15-20 min, restores from backup). Alternative: skip Watch entirely and run shortcut from iPhone lock screen or home screen.
- **Nothing earbuds / third-party earbuds cannot directly trigger Shortcuts** — they can only map press-and-hold to Siri. Workaround: map to Siri, set a Siri phrase that runs the shortcut ("Hey Siri, run Friday"). Or use iPhone lock screen shortcut button instead.
- **friday-voice.service crash loop (682+ restarts, "address already in use")** — when the server crashes, the old process holds port 8645 long enough that systemd's next restart attempt fails immediately, creating a tight crash loop. Fix: add `ExecStartPre=-/bin/bash -c "fuser -k 8645/tcp || true"` to the `[Service]` block. The `-` prefix means systemd ignores failure (nothing on the port). This kills any lingering process before each start. Reload with `systemctl --user daemon-reload && systemctl --user restart friday-voice.service`.
- **Speak step is silent** — most likely Dictate Text captured nothing (empty string). Server returns an error JSON with no `reply` key → Dictionary Value is empty → silence. Debug by adding a "Show Content" action between "Get Contents of URL" and "Get Dictionary Value" to see the raw server response.
- **Webhook signature — Apple Shortcuts CANNOT compute HMAC** — Hermes validates signatures using HMAC-SHA256, not a raw secret header. It checks `X-Hub-Signature-256` (GitHub format) or `X-Webhook-Signature` (generic), NOT `X-Webhook-Secret`. Apple Shortcuts has no HMAC action, so the raw secret header will always return `{"error": "Invalid signature"}`. **Solution: set the webhook secret to `INSECURE_NO_AUTH` in config.yaml to disable signature validation.** This is acceptable because the webhook is only reachable via Tailscale (private encrypted tunnel). Update config: `secret: "INSECURE_NO_AUTH"` under `webhook.extra`, then restart the gateway. Do NOT add any auth header in the Shortcut — just omit it entirely.
- **X-Webhook-Secret header does NOT work** — confirmed via source inspection of `gateway/platforms/webhook.py`. The platform only recognizes `X-Hub-Signature-256` and `X-Webhook-Signature` (HMAC digest). Sending the raw secret string in any header will always fail validation.
