# Swing Trade Filter — Buy-Low Setup Logic

Used in the morning brief crypto section to surface top-50 coins near their 24h lows with weekly pullbacks.

## Logic (session-derived, Jul 2026)

```python
# Filter criteria for a "buy-low swing candidate":
# 1. Price within 5% of its 24h low (sitting at floor)
# 2. Down 3–25% on the 7-day window (pulled back meaningfully but not in freefall)
# 3. Market cap rank ≤ 50 (liquid, established — not micro-caps)

candidates = []
for c in coins:
    low_24h = c.get('low_24h', 0) or 0
    current = c.get('current_price', 0) or 0
    change_7d = c.get('price_change_percentage_7d_in_currency', 0) or 0

    if low_24h <= 0:
        continue
    near_low_pct = (current - low_24h) / low_24h * 100

    if (near_low_pct < 5
            and -25 < change_7d < -3
            and (c.get('market_cap_rank') or 999) <= 50):
        candidates.append({
            'symbol': c['symbol'].upper(),
            'price': current,
            'change_24h': c.get('price_change_percentage_24h', 0) or 0,
            'change_7d': change_7d,
            'near_low_pct': near_low_pct,
            'rank': c.get('market_cap_rank')
        })

candidates.sort(key=lambda x: x['near_low_pct'])
top3 = candidates[:3]
```

## Example output (Jul 13 2026)

| # | Coin | Price | 24h | 7d | Near low by |
|---|------|-------|-----|----|-------------|
| 7 | SOL | $77.52 | -1.2% | -4.4% | 2.1% |
| 34 | AVAX | $6.46 | -4.3% | -6.4% | 2.4% |
| 19 | ADA | $0.16 | -2.5% | -12.6% | 1.5% |

## Market context that day

- Total market cap: $2.29T, +0.03% 24h (essentially flat)
- BTC dominance: 56.2%
- Market tone: "flat as a board" — low volatility, not trending

## Framing note

Keep the swing rationale to one short phrase — don't over-explain. E.g.:
- "near the floor, strong fundamentals for a bounce"
- "sitting right at support, decent risk/reward"
- "deeper pullback but higher risk — for the patient"

Tanzim reads this at 8am. He doesn't need a thesis; he needs a trigger and a price.
