---
name: ollama-local-setup
description: "Install and configure Ollama on a local Mac for use with Hermes — expose it on the network, pull models, connect via Tailscale."
tags: [ollama, local-llm, mac, hermes, cost-reduction]
triggers:
  - User wants to run local models to reduce API costs
  - User wants to add Ollama as a model provider to Hermes
  - User asks how to install Ollama on Mac
  - User wants to connect Hermes to a locally running LLM
---

# Ollama Local Setup for Hermes

## Install on Mac

```bash
# Option 1 — Direct download (easiest)
# Go to ollama.com → Download

# Option 2 — Script
curl -fsSL https://ollama.com/install.sh | sh

# Option 3 — Homebrew
brew install ollama
```

## Pull a Model

For Apple M-series Macs (M1/M2/M3/M4), recommended starting model:
```bash
ollama pull llama3.2   # 2GB, fast, good for routine tasks
```

Check what's installed:
```bash
ollama list
```

## Run Ollama Exposed on Network

Default runs on localhost only. To expose for Hermes or Tailscale access:
```bash
OLLAMA_HOST=0.0.0.0 ollama serve
```

To run permanently (starts on reboot):
```bash
brew services start ollama
# Note: brew services uses default localhost binding
# For network exposure, use a launchd plist with OLLAMA_HOST=0.0.0.0
```

## Connect Hermes on Same Machine

If Hermes is running on the same Mac as Ollama:
```bash
hermes config set model.provider ollama
hermes config set model.default llama3.2
hermes config set model.base_url http://localhost:11434
```

## Connect Hermes on Remote Machine via Tailscale

Get Mac's Tailscale IP:
```bash
tailscale ip -4
# Returns something like 100.89.245.12
```

On the remote Hermes machine, configure to point at Mac:
```bash
hermes config set model.provider ollama
hermes config set model.default llama3.2
hermes config set model.base_url http://100.89.245.12:11434
```

Note: Cloud VMs (like the Hermes gateway VM) don't have Tailscale installed by default — you'd need to install it there too for cross-network access.

## Tanzim's Setup (Mac Mini)

- Mac Mini: tanzimsm-mac-mini, Tailscale IP: 100.89.245.12
- Apple M4 chip, 11.8GB available VRAM
- Ollama installed, llama3.2 pulled (2GB)
- Hermes on Mac Mini configured: provider=ollama, model=llama3.2, base_url=http://localhost:11434
- Cloud VM Hermes (WhatsApp/Friday): cannot reach Mac Mini without Tailscale on the VM

## Model Selection by Task

| Task | Model | Cost |
|------|-------|------|
| Routine tasks, simple lookups | llama3.2 (Ollama local) | Free |
| Content writing, reasoning | Gemini Flash (Google AI Studio) | Near-free |
| Complex reasoning, code, strategy | Claude Sonnet | API cost |

## Adding Gemini as Provider

Get API key from aistudio.google.com → Get API Key → Create API key.

Add to Hermes .env:
```
GOOGLE_API_KEY=your_key_here
```

Then switch via `hermes model` picker or config set.

## Adding Gemini as Provider

Get API key from aistudio.google.com → Get API Key → Create API key.

Must be added manually — `.hermes/.env` is a protected file, Friday's sandbox cannot write to it:
```bash
# Run directly in terminal on the machine (not via Friday sandbox)
echo "GOOGLE_API_KEY=your_key_here" >> ~/.hermes/.env
echo "GEMINI_API_KEY=your_key_here" >> ~/.hermes/.env
```

Then restart Hermes.

## Pitfalls

- **`ollama serve` address already in use** — Ollama is already running. Fine, not an error.
- **`hermes chat "text"` fails** — `chat` is not a valid subcommand. Use just `hermes`.
- **Ollama not reachable from cloud VM** — cloud VMs don't have Tailscale by default. Tailscale install via curl pipe (`curl ... | sh`) also times out on restricted VMs. Either install Tailscale on both machines or skip Ollama for the cloud instance and use Gemini instead.
- **`.hermes/.env` write blocked from sandbox** — sed/echo/patch all fail on `.env`. User must edit manually in their own terminal session.
- **Claude Code OAuth token in .env** — if `CLAUDE_CODE_OAUTH_TOKEN` is set, Hermes uses the subscription not the API wallet. Check `.env` before assuming wallet spend is from Hermes.
