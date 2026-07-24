# Instagrammer-lite — WhatsApp-triggered dumb scroller (Jul 3 2026)

Context: Tanzim wanted to step back from the full v2 engine and reimagine the crawler
as something deliberately dumb — "not intelligent, a script that scrolls through
handles" — triggered from his phone over WhatsApp. Explicitly open to a clean rebuild,
not building on the existing foundation. This is a NEW, simpler artifact alongside the
`Instagrammer` v2 repo, not a replacement of it.

## Repo
`github.com/tanzimozer/instagrammer-lite` (private, created + pushed this session).
Built on the server; must be cloned onto the Mac to run (residential IP). Two files:

- **crawler.py** — the dumb follower-graph scroller. Real IG cookies → open a target's
  followers modal → scroll → scrape every handle → append to `out/handles.csv`. Chains
  each handle as the next target, depth-limited. No filtering, no scoring, no cleverness.
  Filtering is deliberately a SEPARATE later stage. `python crawler.py <handle>
  --depth 1 --max 500 [--headful]`.
- **listener.py** — always-on poller that watches the WhatsApp group for `crawl @handle`
  (optional `depth=N`), fires crawler.py locally, replies into the same chat when done.
  Sender allow-list locked to Tanzim's WhatsApp `@lid`.

Secrets (`secrets/ig_cookies.json`, `listener_config.json` with bridge token + chat_id)
are gitignored — pasted in on the Mac, never committed. README carries the one-line clone
+ venv + `playwright install chromium` bootstrap.

## The durable idea: chat message = command bus, Friday's keystroke == Tanzim's

Tanzim's realisation, worth keeping as a control-plane pattern:
**an always-on listener watching a shared chat doesn't care WHO typed the keyword.**
So once the listener exists, "you trigger it when I tell you" and "I trigger it myself"
are the SAME action — Friday just posts the keyword into the same group and the Mac fires.
No separate command channel, no extra auth. The chat IS the command bus.

This is simpler than the v2 HMAC-over-Sheet `Control` tab (see
`instagrammer-server-side-deploy-jun2026.md`): no signing, no TTL, no nonce — just a
sender allow-list + a keyword regex. Trade-off: less tamper-proof, but the group is
already trusted and the only side-effect is a local scrape. Right tool for a lite build;
use the HMAC bus when the command surface is broader or the chat isn't fully trusted.

## The honest-capability answer that mattered

Tanzim asked "if I told you to trigger, could you trigger it?" The correct answer was
**not today** — Friday can post on WhatsApp but has no hands on the Mac unless something
is *listening* there. Don't overstate reach. The path to "yes" is: build the listener
first; then Friday relaying the keyword == Tanzim typing it. Say the limitation plainly,
then name exactly what closes the gap.

## Seed decision (consistent with v2, re-confirmed)

Hashtag seed KILLED again — "that seed is not working." Same call as the v2 chase: seed
from the follower graph (a person's followers list), chain outward account-to-account.
Hashtag pages are shadowbanned/throttled/dead-account-heavy. This is now a firmly locked
preference across two separate rebuilds — do NOT propose hashtag seeding for his crawlers.

## Meta-block posture (his words)

"I don't care about how much Meta restrictions are there. I'll build through those." He
owns the anti-block problem. Build the crawler local-on-real-cookies (trusted IP), pace it
(randomised pauses + cool-downs are already in crawler.py), and document the escape hatch
(residential proxies + small account rotation) as a bolt-on that doesn't touch the core
script. Don't over-engineer the block defence up front — he wants the scroller working first.

## GitHub push mechanics (reusable)
No `gh` CLI on the box, but stored creds at `~/.git-credentials`
(`https://tanzimozer:<PAT>@github.com`). Create a private repo via REST with the PAT, then
push:
```bash
TOKEN=$(sed -E 's#https://[^:]+:([^@]+)@github.com#\1#' ~/.git-credentials)
curl -s -H "Authorization: token $TOKEN" -H "Accept: application/vnd.github+json" \
  -d '{"name":"REPO","private":true}' https://api.github.com/user/repos
git remote add origin https://github.com/tanzimozer/REPO.git && git push -u origin main
```
