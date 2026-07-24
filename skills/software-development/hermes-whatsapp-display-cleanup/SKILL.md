---
name: hermes-whatsapp-display-cleanup
description: Suppress Hermes backend noise (tool calls, memory ops, status messages) from appearing in any WhatsApp chat — groups or DMs with trainees/non-owner users.
triggers:
  - Tool call output or memory operations are appearing as messages in a WhatsApp group or DM
  - Status messages like Still working or Interrupting current task appear in any chat
  - Permission approval prompts are visible to any non-owner user
  - User reports backend or technical messages leaking into WhatsApp (groups OR trainee DMs)
  - Session reset notification (context cleared, model info) appears in any chat
  - Setting up Friday in a new WhatsApp group or trainee DM and want clean output from the start
  - Backend noise (timer, token count, model name, bridge errors) leaks to a trainee like Blair
  - API error messages appear in WhatsApp (⚠️ Non-retryable error, ❌ Non-retryable error, Error code: 400)
  - Fallback attempt messages ("trying fallback...") visible in WhatsApp chat
  - Thinking block errors or any raw Anthropic API error JSON appears in chat
---

# Hermes WhatsApp Display Cleanup

## What this covers
Suppressing all backend activity (tool progress, memory saves, interim status, permission prompts) from appearing as visible messages in WhatsApp group chats. The global `display` config is often not enough — WhatsApp has its own platform-level tier defaults that override global settings.

## Root cause
`display_config.py` resolves settings in this order:
1. `display.platforms.<platform>.<key>` — explicit per-platform override (highest priority)
2. `display.<key>` — global setting
3. Built-in platform tier defaults
4. Built-in global defaults

WhatsApp's built-in default is `_TIER_MEDIUM` (`tool_progress: "new"`). Setting only the global `display.tool_progress: none` is NOT enough — the platform-level tier default for WhatsApp overrides it. You must set the WhatsApp-specific override.

## Fix — run all of these

```bash
# Global suppressions (belt)
hermes config set display.tool_progress none
hermes config set display.interim_assistant_messages false
hermes config set display.busy_input_mode queue
hermes config set display.background_process_notifications off

# WhatsApp-specific overrides (suspenders — these take priority)
hermes config set display.platforms.whatsapp.tool_progress off
hermes config set display.platforms.whatsapp.interim_assistant_messages false

# Auto-approve terminal commands so permission prompts don't surface
hermes config set terminal.auto_approve true
```

## Verify config
```bash
grep -A6 "display:" ~/.hermes/config.yaml
```

Expected output should include:
```yaml
display:
  tool_progress: none
  interim_assistant_messages: false
  busy_input_mode: queue
  background_process_notifications: off
  platforms:
    whatsapp:
      tool_progress: false
      interim_assistant_messages: false
```

## Pitfalls

### Config doesn't help: Assistant narration leaking into groups
If messages like "I'll send that message now" or "Sent accountability check-in to X" appear in WhatsApp groups, this is NOT a config issue — it's **behavioral**. These are the assistant's own responses (conversational narration), not tool output or interim status.

**Symptom:** Gray "You" bubbles in WhatsApp showing assistant's action announcements.

**Root cause:** The assistant is verbosely narrating what it's about to do or just did, and those responses get delivered to the chat.

**Fix:** The assistant must execute actions silently in group chats — no "I'll do X", no "Done, sent Y". Just do the action and don't comment on it. This is a prompt/behavior change, not a config change.

**Memory note to add:** "In groups: execute silently. No action narration."

### Config-related pitfalls
- Setting only the global display.tool_progress is insufficient — WhatsApp platform defaults override it
- tool_progress value must be off at the platform level — none is a valid global value but off is the canonical platform-level value
- Memory save operations appearing in chat are covered by tool_progress: off at the platform level
- busy_input_mode: queue prevents Interrupting current task messages
- background_process_notifications valid values are: all, result, error, off — NOT none (none will be silently ignored and default to all)
- terminal.auto_approve: true prevents permission approval prompts from surfacing in chat
- Changes take effect on the next message — existing open sessions may need to expire first

## Source files (for deeper debugging)
- ~/.hermes/hermes-agent/gateway/display_config.py — tier defaults and resolution logic
- ~/.hermes/hermes-agent/gateway/run.py — where tool_progress_enabled and interim_assistant_messages_enabled are resolved per-message
- ~/.hermes/hermes-agent/run_agent.py — _emit_status() at line ~2355, which fires status_callback("lifecycle", message)
- ~/.hermes/hermes-agent/agent/error_classifier.py — classifies API errors into FailoverReason enums

---

## API Error Messages Leaking into WhatsApp

### What it looks like
Three rapid messages appear in chat:
```
⚠️ Non-retryable error (HTTP 400) — trying fallback...
❌ Non-retryable error (HTTP 400): HTTP 400: messages.1: The final block in an assistant message cannot be `thinking`.
⚠️ Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': '...'}, 'request_id': 'req_...'}
```

### Root cause — why display config doesn't stop it
These errors travel through a separate code path that **bypasses display config entirely**:

1. API call fails → `run_agent.py` catches the error
2. Calls `self._emit_status(f"⚠️ Non-retryable error...")` → fires `status_callback("lifecycle", message)`
3. `gateway/run.py:_status_callback_sync` (line ~10060) receives it
4. Calls `_status_adapter.send(_status_chat_id, message, ...)` unconditionally
5. No check against `tool_progress: off` or any display config — it always sends

`tool_progress: off` suppresses tool progress events (tool.started, tool.completed etc.) but does NOT gate `status_callback` lifecycle messages. They are treated as a separate channel.

### The two types of errors and how they behave differently

**Type A — classified as `thinking_signature`** (e.g., "signature" + "thinking" in error message):
- Handled by `run_agent.py` line ~11308: strips thinking blocks, retries silently
- Does NOT call `_emit_status` → does NOT leak to WhatsApp
- These are self-healing

**Type B — "final block cannot be `thinking`"** (matches `messages.N: The final block in an assistant message cannot be thinking`):
- As of May 2026, this pattern is NOT classified as `thinking_signature` (classifier checks for "signature" keyword, which is absent)
- Falls through to generic 400 handling → IS_CLIENT_ERROR path → calls `_emit_status` → leaks to WhatsApp
- This is the bug: the error classifier misses this variant

### Fix A — Patch error_classifier.py to catch the missing pattern
In `~/.hermes/hermes-agent/agent/error_classifier.py`, find the thinking_signature block (~line 429) and expand the condition:

```python
# BEFORE:
if (
    status_code == 400
    and "signature" in error_msg
    and "thinking" in error_msg
):

# AFTER (also catch "final block cannot be thinking"):
if (
    status_code == 400
    and "thinking" in error_msg
    and ("signature" in error_msg or "final block" in error_msg)
):
```

This makes the "final block" error classify as `thinking_signature`, which triggers silent strip-and-retry instead of `_emit_status`.

### Fix B — Gate _status_callback_sync behind display config (structural fix)
In `~/.hermes/hermes-agent/gateway/run.py`, find `_status_callback_sync` (~line 10060) and add a display config gate:

```python
def _status_callback_sync(event_type: str, message: str) -> None:
    if not _status_adapter or not _run_still_current():
        return
    # Gate lifecycle/warn events behind tool_progress display setting
    from .display_config import resolve_display_setting
    _tp_mode = resolve_display_setting(
        user_config, source.platform.value if hasattr(source.platform, 'value') else str(source.platform),
        "tool_progress"
    )
    if _tp_mode in ("off", False, "false", "none", None) and event_type in ("lifecycle", "warn"):
        return
    try:
        asyncio.run_coroutine_threadsafe(
            _status_adapter.send(
                _status_chat_id,
                message,
                metadata=_status_thread_metadata,
            ),
            _loop_for_step,
        )
    except Exception as _e:
        logger.debug("status_callback error (%s): %s", event_type, _e)
```

After either patch, restart the gateway: `systemctl --user restart hermes-gateway`

### Which fix to apply
- Fix A is surgical and low-risk — fixes the specific error pattern that leaked
- Fix B is structural — prevents any future lifecycle error from leaking when tool_progress is off
- Apply both for full protection

---

## Cron Job Output Leaking into WhatsApp

### What it looks like
After a cron job runs, a second message appears with job metadata:
```
Cronjob Response: Substack reminder (job_id: cae21a89a272)
------------
✅ WhatsApp reminder sent successfully to Tanzim (DM).
Message delivered: "..."
Message ID: 3EB055598BAB5DCC0254A8
To stop or manage this job, send me a new message...
```

### Root cause
The cron system wraps every delivery with a header (job name, job_id) and footer ("To stop or manage..."). This is controlled by `cron.wrap_response` in config.yaml, which defaults to `true`.

### Fix (confirmed working)
Two steps:

1. **Disable the wrapper globally** — one-time config change:
```bash
hermes config set cron.wrap_response false
```

2. **Write clean cron prompts** — structure the prompt so the agent outputs only the message text:
```
Output this message exactly, with zero additions, confirmations, or metadata: "Your message here."
```

Keep `deliver: origin` — this is required for the message to reach the user. Do NOT set `deliver: local` (see pitfalls).

### Critical pitfalls
- `deliver: local` saves output to file only — nothing reaches the user. Do not use it for reminder/message jobs.
- `deliver: local` + `send_message` in prompt also fails: the cron system injects a prompt override that explicitly blocks `send_message` calls. The agent will respond `[SILENT]` and nothing is sent.
- The only working pattern: `deliver: origin` + `cron.wrap_response: false` + clean prompt.

### Verify
Run the job manually with `mcp_cronjob(action='run', job_id='...')` and confirm:
1. The user receives just the clean message text
2. No job_id, metadata, or "To stop or manage..." footer appears

---

## Session Reset Notifications in Group Chats

This is a separate mechanism from the display layer — it lives in `run.py` and is not controllable via `display.*` config.

### What it looks like
A message like:
```
◐ Session automatically reset (previous session was stopped or interrupted). Conversation history cleared.
Use /resume to browse and restore a previous session.
Model: claude-sonnet-4-6 | Provider: anthropic | Context: 1.0M tokens
```

### Config-only option (suppress entirely)
```bash
hermes config set session_reset.reset_by_type.group.notify false
```
This silences it completely for group chat sessions.

### Code patch option (redirect to owner DM instead of suppressing)
The better UX: keep the notification but route it to the owner's DM with a group label.

In `~/.hermes/hermes-agent/gateway/run.py`, find the `await adapter.send(source.chat_id, notice, ...)` block inside the `if should_notify:` branch (search for `"◐ Session automatically reset"`). Replace it with:

```python
# For group chats, redirect notice to the owner's DM
# instead of posting in the group.
chat_type = getattr(source, 'chat_type', 'dm')
delivery_chat_id = source.chat_id
delivery_meta = getattr(event, 'metadata', None)
if chat_type in ("group", "forum"):
    owner_chat_id = None
    if hasattr(adapter, '_owner_chat_id'):
        owner_chat_id = adapter._owner_chat_id()
    if owner_chat_id:
        chat_name = getattr(source, 'chat_name', None) or source.chat_id
        notice = f"[Group session reset: {chat_name}]\n{notice}"
        delivery_chat_id = owner_chat_id
        delivery_meta = None  # no thread context for DM
await adapter.send(
    delivery_chat_id, notice,
    metadata=delivery_meta,
)
```

### Key facts
- `session_reset.reset_by_type.group.notify` controls whether groups get notified at all
- `whatsapp._owner_chat_id()` reads from `config.yaml` key `whatsapp.owner_chat_id` or env `WHATSAPP_HOME_CHANNEL`
- `source.chat_type` is `"group"` for WhatsApp groups, `"dm"` for direct messages
- The policy lookup uses `get_reset_policy(platform, session_type)` — platform overrides beat type overrides beat default
- Restart the gateway after any `run.py` code change
