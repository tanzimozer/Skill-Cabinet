#!/usr/bin/env python3
"""
watcher.py — self-updating CI/CD agent for the Mac.

Polls the private GitHub repo. When main moves AND CI is green, it pulls the new
code and restarts the listener via launchd. This is the "deploy from your phone"
mechanism: you (or Friday) commit a change from anywhere, CI gates it, the Mac
pulls it live. You never touch the machine.

Flow:
    push -> GitHub Action (ci.yml) runs -> green
    watcher sees new green SHA on main -> git pull -> restart listener

Config: reuses listener_config.json for `github` block:
    "github": {
      "repo": "tanzimozer/instagrammer-lite",
      "branch": "main",
      "token": "PASTE_GH_TOKEN",            // repo + read checks scope
      "launchd_label": "com.tanzim.instagrammer-lite.listener"
    }
Run: python watcher.py   (or wrap in its own launchd job, poll every 60s)
"""
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
CFG = ROOT / "listener_config.json"
LOG = ROOT / "logs" / "watcher.log"


def log(msg):
    line = f"[{datetime.now(timezone.utc).isoformat()}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def gh(cfg):
    return cfg.get("github", {})


def api(cfg, path):
    g = gh(cfg)
    r = requests.get(
        f"https://api.github.com/repos/{g['repo']}{path}",
        headers={"Authorization": f"token {g['token']}",
                 "Accept": "application/vnd.github+json"},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


def latest_green_sha(cfg):
    """Head SHA of branch, but only if its CI check suite concluded success."""
    g = gh(cfg)
    branch = api(cfg, f"/branches/{g['branch']}")
    sha = branch["commit"]["sha"]
    runs = api(cfg, f"/commits/{sha}/check-runs") if False else \
        api(cfg, f"/actions/runs?branch={g['branch']}&per_page=1")
    wr = runs.get("workflow_runs", [])
    if wr and wr[0]["head_sha"] == sha and wr[0]["conclusion"] == "success":
        return sha
    return None


def current_sha():
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()


def deploy(cfg, sha):
    log(f"green SHA {sha[:8]} — pulling")
    subprocess.run(["git", "fetch", "--all", "-q"], cwd=ROOT, check=True)
    subprocess.run(["git", "reset", "--hard", f"origin/{gh(cfg)['branch']}", "-q"],
                   cwd=ROOT, check=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r",
                    str(ROOT / "requirements.txt")], cwd=ROOT)
    label = gh(cfg).get("launchd_label")
    if label:
        subprocess.run(["launchctl", "kickstart", "-k", f"gui/$(id -u)/{label}"],
                       shell=False, cwd=ROOT)
    log(f"deployed {sha[:8]} and restarted listener")


def main():
    cfg = json.loads(CFG.read_text())
    poll = gh(cfg).get("poll_seconds", 60)
    log(f"watcher up. tracking {gh(cfg)['repo']}@{gh(cfg)['branch']}")
    while True:
        try:
            sha = latest_green_sha(cfg)
            if sha and sha != current_sha():
                deploy(cfg, sha)
        except Exception as e:
            log(f"loop error: {e}")
        time.sleep(poll)


if __name__ == "__main__":
    main()
