#!/usr/bin/env python3
"""
listener.py — watches the WhatsApp group for a keyword and fires the crawler.

It polls the WhatsApp bridge for new messages in the configured chat. When it
sees a line like:

    crawl @somehandle
    crawl @somehandle depth=2

...it launches crawler.py locally, then replies into the same chat when done.
Whoever types the keyword — you or Friday — is identical to this listener.

Config via listener_config.json (see template written alongside).
Run:  python listener.py
"""
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
CFG = ROOT / "listener_config.json"
STATE = ROOT / "logs" / "listener_state.json"
LOG = ROOT / "logs" / "listener.log"

TRIGGER = re.compile(r"\bcrawl\s+@?([A-Za-z0-9._]+)(?:\s+depth=(\d+))?", re.I)


def log(msg):
    line = f"[{datetime.now(timezone.utc).isoformat()}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def cfg():
    if not CFG.exists():
        log(f"FATAL: missing {CFG}")
        sys.exit(2)
    return json.loads(CFG.read_text())


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"last_ts": 0}


def save_state(s):
    STATE.write_text(json.dumps(s))


def fetch_messages(c):
    """Pull recent messages for the target chat from the WhatsApp bridge."""
    r = requests.get(
        f"{c['bridge_url']}/messages",
        params={"chatId": c["chat_id"], "limit": 20},
        headers={"Authorization": f"Bearer {c['bridge_token']}"},
        timeout=20,
    )
    r.raise_for_status()
    return r.json().get("messages", [])


def reply(c, text):
    requests.post(
        f"{c['bridge_url']}/send",
        json={"chatId": c["chat_id"], "text": text},
        headers={"Authorization": f"Bearer {c['bridge_token']}"},
        timeout=20,
    )


def run_crawl(c, handle, depth):
    log(f"firing crawler for @{handle} depth={depth}")
    reply(c, f"Crawler away — @{handle}, depth {depth}. I'll report back.")
    proc = subprocess.run(
        [sys.executable, str(ROOT / "crawler.py"), handle,
         "--depth", str(depth), "--max", str(c.get("max_per_account", 500))],
        capture_output=True, text=True,
    )
    tail = (proc.stdout or proc.stderr).strip().splitlines()
    summary = tail[-1] if tail else "no output"
    reply(c, f"Done, Boss. {summary}")
    log(f"crawl finished: {summary}")


def main():
    c = cfg()
    st = load_state()
    log(f"listener up. watching chat {c['chat_id']} for 'crawl @handle'")
    while True:
        try:
            for m in fetch_messages(c):
                ts = m.get("timestamp", 0)
                if ts <= st["last_ts"]:
                    continue
                st["last_ts"] = max(st["last_ts"], ts)
                # only obey allow-listed senders
                if c.get("allow_senders") and m.get("sender") not in c["allow_senders"]:
                    continue
                match = TRIGGER.search(m.get("text", ""))
                if match:
                    handle = match.group(1)
                    depth = int(match.group(2)) if match.group(2) else c.get("default_depth", 1)
                    run_crawl(c, handle, depth)
            save_state(st)
        except Exception as e:
            log(f"loop error: {e}")
        time.sleep(c.get("poll_seconds", 8))


if __name__ == "__main__":
    main()
