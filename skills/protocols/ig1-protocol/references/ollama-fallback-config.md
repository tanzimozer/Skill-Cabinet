# Ollama Fallback — Config Notes (June 2026)

## Setup confirmed working
- Ollama server: `http://localhost:11434` — running as daemon on VM
- Models pulled: `llama3.1:8b`, `llama3.2:latest`
- OpenAI-compatible endpoint: `http://localhost:11434/v1/chat/completions`

## Hermes config.yaml — required fields
The custom provider entry MUST include `api_key` even though Ollama doesn't require auth.
Without it, Hermes silently skips the fallback entry:

```yaml
fallback_providers:
- provider: anthropic
  model: claude-haiku-4-5
  base_url: https://api.anthropic.com
- provider: custom
  model: llama3.1:8b
  base_url: http://127.0.0.1:11434/v1
  api_key: ollama   # ← required, any non-empty string works
  display_name: Ollama (local)
```

## Switching primary model temporarily
To run on Ollama as primary (e.g. during Claude usage limit):
```yaml
model: llama3.1:8b
providers:
  default:
    provider: custom
    base_url: http://127.0.0.1:11434/v1
    api_key: ollama
```
Revert with:
```yaml
model: claude-sonnet-4-6
providers: {}
```

## Testing the endpoint
```bash
curl -s http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ollama" \
  -d '{"model":"llama3.1:8b","messages":[{"role":"user","content":"say hi"}]}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['choices'][0]['message']['content'])"
```

## Fallback chain
Sonnet 4.6 → Haiku 4.5 → Ollama llama3.1:8b

## Scheduling a timed revert
Use `schedule_task` with `repeat: 1` and `schedule: 30m` to auto-revert after a timed Ollama session.
