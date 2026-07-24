#!/usr/bin/env python3
"""
crawler.py — dumb follower-graph scroller for Instagrammer-lite.

No intelligence. It logs in with your real Instagram cookies, opens a target
account's followers modal, scrolls it, and scrapes every handle that loads.
Each collected handle can be chained as the next target (depth-limited).
Handles are appended to out/handles.csv. Filtering happens later, elsewhere.

Usage:
    python crawler.py <target_handle> [--depth 1] [--max 500] [--headful]

Requires:
    pip install playwright && playwright install chromium
    secrets/ig_cookies.json  (exported Instagram cookies, array form)
"""
import argparse
import csv
import json
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
COOKIES = ROOT / "secrets" / "ig_cookies.json"
OUT = ROOT / "out" / "handles.csv"
LOG = ROOT / "logs" / "crawler.log"


def log(msg: str) -> None:
    line = f"[{datetime.now(timezone.utc).isoformat()}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def load_cookies():
    if not COOKIES.exists():
        log(f"FATAL: no cookies at {COOKIES}")
        sys.exit(2)
    raw = json.loads(COOKIES.read_text())
    # Accept either a raw array or {"cookies": [...]}
    cookies = raw["cookies"] if isinstance(raw, dict) else raw
    for c in cookies:
        c.setdefault("domain", ".instagram.com")
        c.setdefault("path", "/")
        # Playwright wants sameSite in {Strict,Lax,None}
        ss = c.get("sameSite", "Lax")
        c["sameSite"] = {"strict": "Strict", "lax": "Lax", "no_restriction": "None",
                          "none": "None", "unspecified": "Lax"}.get(str(ss).lower(), "Lax")
    return cookies


def seen_handles():
    if not OUT.exists():
        return set()
    with open(OUT) as f:
        return {row[0] for row in csv.reader(f) if row}


def append_handles(rows):
    new = not OUT.exists()
    with open(OUT, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["handle", "source", "collected_at"])
        w.writerows(rows)


def scrape_followers(page, target, max_handles):
    """Open <target>'s followers modal and scroll until we stop growing."""
    page.goto(f"https://www.instagram.com/{target}/", wait_until="domcontentloaded")
    human_pause(2, 4)
    # Click the followers link
    try:
        page.locator("a[href$='/followers/']").first.click(timeout=15000)
    except Exception:
        log(f"  could not open followers modal for @{target} (private/blocked?)")
        return []
    human_pause(2, 3)

    # The scrollable container inside the dialog
    dialog = page.locator("div[role='dialog']")
    handles, stale = set(), 0
    while len(handles) < max_handles and stale < 8:
        links = dialog.locator("a[href^='/'][role='link']")
        before = len(handles)
        for i in range(links.count()):
            href = links.nth(i).get_attribute("href") or ""
            h = href.strip("/").split("/")[0]
            if h and "." not in h[:1] and h not in ("explore", "reels", "p"):
                handles.add(h)
        # scroll the last row into view to trigger lazy load
        try:
            links.last.scroll_into_view_if_needed(timeout=4000)
        except Exception:
            pass
        human_pause(1.2, 2.6)
        stale = stale + 1 if len(handles) == before else 0
    return sorted(handles)


def human_pause(lo, hi):
    time.sleep(random.uniform(lo, hi))


def run(seed, depth, max_handles, headful):
    cookies = load_cookies()
    already = seen_handles()
    queue = [(seed, 0)]
    total_new = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not headful)
        ctx = browser.new_context(
            user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0 Safari/537.36"),
            viewport={"width": 1280, "height": 900},
        )
        ctx.add_cookies(cookies)
        page = ctx.new_page()

        while queue:
            target, d = queue.pop(0)
            log(f"crawling @{target} (depth {d})")
            found = scrape_followers(page, target, max_handles)
            fresh = [h for h in found if h not in already]
            ts = datetime.now(timezone.utc).isoformat()
            append_handles([[h, target, ts] for h in fresh])
            already.update(fresh)
            total_new += len(fresh)
            log(f"  +{len(fresh)} new (total collected: {len(already)})")
            if d < depth:
                for h in fresh:
                    queue.append((h, d + 1))
            human_pause(4, 9)  # cool-down between accounts
        browser.close()

    log(f"DONE. {total_new} new handles this run. File: {OUT}")
    return total_new


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="seed handle, e.g. tanzim_ozer")
    ap.add_argument("--depth", type=int, default=1, help="how many hops to chain")
    ap.add_argument("--max", type=int, default=500, help="max handles per account")
    ap.add_argument("--headful", action="store_true", help="show the browser")
    a = ap.parse_args()
    run(a.target.lstrip("@"), a.depth, a.max, a.headful)
