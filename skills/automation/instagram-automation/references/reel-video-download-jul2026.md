# Downloading a public IG reel/post video (yt-dlp)

Task: user drops an Instagram reel URL, wants the .mp4. This is NOT the API/enrich
path — use `yt-dlp`, not the friendships/profile endpoints.

## The one fix that actually matters: BUMP yt-dlp FIRST

Instagram changes its media response shape often. A yt-dlp older than ~1–2 months
fails with:

```
ERROR: [Instagram] <id>: Instagram sent an empty media response.
```

This is NOT a cookie problem and NOT "the post is private" — it's a stale
extractor. The reel can be fully public and still throw this. **Before anything
else, update yt-dlp:**

```bash
pip install -q -U --break-system-packages yt-dlp    # plain -U may no-op on PEP668 envs
~/.local/bin/yt-dlp --version                        # confirm it actually moved
```

Jul 2026: a Mar build threw "empty media response"; bumping to the Jul build made
the identical command download first try. If the version doesn't change after
`-U`, add `--break-system-packages` (the env is PEP 668 externally-managed and the
bare upgrade silently does nothing).

## Then just run it (cookies optional)

```bash
cd ~/scratch/ig
yt-dlp --no-update -o "%(id)s.%(ext)s" "https://www.instagram.com/reel/<ID>/"
```

Public reels often need no auth once the extractor is current. It downloads the
DASH video + audio streams separately and merges into one `<ID>.mp4`.

## If it still 404s / empties: add cookies (Netscape format)

Convert the saved IG cookie JSON (keyed by account handle) to the Netscape
cookies.txt yt-dlp expects:

```python
import json, time
d = json.load(open('/home/hermes/.hermes/instagrammer/mac/secrets/ig_cookies.json'))
acct = next(k for k,v in d.items() if v.get('sessionid'))   # first account with a session
c = d[acct]
lines = ["# Netscape HTTP Cookie File"]
exp = int(time.time()+3600*24*30)
for name, val in c.items():
    if name in ('wd','dpr'): continue            # viewport junk, skip
    lines.append("\t".join([".instagram.com","TRUE","/","TRUE",str(exp),name,str(val)]))
open("cookies.txt","w").write("\n".join(lines)+"\n")
```

Then `yt-dlp --no-update --cookies cookies.txt -o "%(id)s.%(ext)s" "<url>"`.

Note the cookie store shape: `~/.hermes/instagrammer/mac/secrets/ig_cookies.json`
is a dict of `{handle: {cookie_name: value, ...}}` — NOT a flat list. Pick an
account with a `sessionid`.

## Delivery

The WhatsApp bridge sends a video via `send_message` with `[img] <path>` in the
message. If it returns `401 Unauthorized`, the bridge session is down (not a
target/file problem) — the file is fine on disk, say so plainly, the fix is
re-linking the WhatsApp bridge (nothing the agent can do from its side). Use the
explicit DM target from `send_message action=list` (e.g. `whatsapp:Tanzim Ozer`),
not bare `whatsapp`, though a 401 fails on both.

## Don't over-engineer the debug

When yt-dlp throws "empty media response", the branch order is: (1) bump version,
(2) retry, (3) only THEN reach for cookies / gallery-dl / browser DOM scraping.
Jul 2026 burned several steps trying cookies, jina, browser-vision, and a BLS-style
mirror hunt before the version bump — which was the actual fix — proved trivial.
Version first.
