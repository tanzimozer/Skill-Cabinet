---
name: market-data-briefs
description: Fetching and formatting live market data (crypto, equities) for Tanzim's morning briefs and on-demand snapshots
category: finance
tags: [crypto, coingecko, market, morning-brief, swing-trade]
---

# Market Data Briefs

## When to use
Any task requiring live crypto or market data — morning brief crypto section, on-demand price checks, swing trade candidate identification.

## CoinGecko API (no key required for public endpoints)

### Global market tone
```python
import requests

global_resp = requests.get("https://api.coingecko.com/api/v3/global")
data = global_resp.json().get("data", {})
market_cap_change_24h = data.get("market_cap_change_percentage_24h_usd", 0)
btc_dominance = data.get("market_cap_percentage", {}).get("btc", 0)
# btc_dominance rising → Bitcoin strength / alt weakness
# btc_dominance falling → alt-season conditions
```

One-liner format: `Market up/down ~X% in 24h — risk-on/off tone. BTC dominance: Y%.`

### Swing trade candidates (buy-low setups)

Screen for coins near cycle lows that are showing early recovery momentum:

```python
coins_resp = requests.get(
    "https://api.coingecko.com/api/v3/coins/markets",
    params={
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
        "sparkline": False,
        "price_change_percentage": "7d,30d"
    }
)
coins = coins_resp.json()

EXCLUDE = {"usdt","usdc","usds","dai","busd","fdusd","figr_heloc","rain","wbtc","steth","lido"}

swing_candidates = []
for c in coins:
    if c.get("symbol","").lower() in EXCLUDE:
        continue
    ath_change = c.get("ath_change_percentage", 0) or 0
    change_7d  = c.get("price_change_percentage_7d_in_currency", 0) or 0
    mcap       = c.get("market_cap", 0) or 0
    # Filter: deeply discounted + positive weekly momentum + liquid
    if ath_change < -60 and change_7d > 2 and mcap > 500_000_000:
        swing_candidates.append({
            "symbol": c["symbol"].upper(),
            "name":   c["name"],
            "price":  c["current_price"],
            "7d":     change_7d,
            "30d":    c.get("price_change_percentage_30d_in_currency", 0) or 0,
            "ath_pct":ath_change,
        })

swing_candidates.sort(key=lambda x: x["ath_pct"])  # most discounted first
top3 = swing_candidates[:3]
```

**Thresholds (July 2026, Tanzim's preference):**
- ATH discount: `< -60%` (cycle-low territory)
- 7d change: `> +2%` (momentum signal, not just cheap)
- Market cap floor: `> $500M` (liquid enough to trade)

**Brief format — one line per coin:**
`*TICKER* $PRICE | -X% from ATH | +Y% 7d — [one-clause thesis]`

Example: `*INJ* $5.29 | -90% from ATH | +5.3% 7d — Injective recovering off its floor with consistent buys`

Keep the thesis to one clause. Specific, not generic. Not financial advice language.

## WhatsApp brief formatting (crypto section)

```
*CRYPTO*
Market is up ~X% across the board in 24h — [tone phrase]. Three swing setups near cycle lows showing early momentum:
- *TICKER* $PRICE | -X% from ATH | +Y% 7d — [thesis]
- *TICKER* $PRICE | -X% from ATH | +Y% 7d — [thesis]
- *TICKER* $PRICE | -X% from ATH | +Y% 7d — [thesis]
```

## Rate limits
CoinGecko free tier: ~30 calls/min. Morning brief makes 2 calls (global + markets). No concern.

## Reference files
- `references/coingecko_swing_filter.md` — full filter logic with worked example from July 2026 session
