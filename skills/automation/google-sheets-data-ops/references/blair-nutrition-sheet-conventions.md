# Blair Grimes — Nutrition Sheet Conventions

Sheet ID: `1sNSE4gRkGMJW5lpTcIJYM69m88JAXks9qQADXmWY6dk`  
Tabs: Overview | Blair's Persona | Nutrition | Aug-Sep | Macro Builder

---

## Macro Formula (locked by Tanzim)

| Macro | Formula |
|---|---|
| Protein | 1g × bodyweight in lbs |
| Carbs | 0.7g × bodyweight in lbs |
| Fat | Remaining calories (flex macro) |

At 178 lbs: Protein = 178g · Carbs = 125g · Fat varies by day type.

---

## Day Tiers — TWO only (Blair's explicit preference)

Blair rejected three-tier breakdown (Heavy / Upper / Rest). Use two tiers only:

| Day Type | Calories | Protein | Carbs | Fat | Fibre |
|---|---|---|---|---|---|
| Training Day | ~1,800 | 178g | 125g | 60g | 25g |
| Rest Day | ~1,600 | 178g | 125g | 43g | 25g |

Protein and carbs are flat every day. Fat is the only variable.

---

## Nutrition Tab Layout Order

1. Title + last updated line
2. **Daily Macro Targets** — table first, always (Blair opens the tab for the numbers)
3. Macro Rules (one line per macro)
4. Carb Timing
5. TDEE Baseline
6. Core Protocol Rules
7. Protein Sources → Carb Sources → Fat Sources → Potassium Strategy → Foods to Avoid
8. Footer

When doing a full reorg: **clear the tab first** (`values:clear` POST) then re-write in one PUT. Avoids stale rows bleeding through.

---

## Macro Builder Tab

Separate tab for ingredient lookup. Three sections:

- **Protein sources** — each row = 40g protein (cooked weight)
- **Carb sources** — each row = 40g carbs
- **Fat sources** — each row = 20g fat (not 40g — fat is calorie-dense, keep serving sizes realistic)

Column headers: `Grams | Ingredient | Protein (g) | Carbs (g) | Fat (g)`

Each row shows full macro crossover so Blair can see e.g. salmon appearing in both protein and fat sections with different quantities.

---

## BFR References — Three Locations

When removing BFR from the programme, clear/replace ALL THREE:

1. **Overview row 37** — Progressive Overload Model section (`BFR Sets` row)
2. **Overview row 60** — General Protocols section (`BFR Band Tightness` row)
3. **Overview ~row 206** — Mexico Prep section (`AM: Fasted BFR session`) → replace with pump substitute

Substitute for fasted BFR session: `AM: Fasted pump session (high-rep machine work — 3×20 glutes / shoulders at 50–60% load)`

---

## Key Rules Blair Operates Under

- No dairy except 0% plain Greek yogurt
- No bread, pasta, wraps
- No high-sodium condiments
- Zero alcohol
- No potassium supplements (hyperkalemia risk) — hit 3,500–4,700mg/day via food
- Fat floor: 40g/day minimum (hormonal health)
- Protein minimum: 40g per meal across 3 meals
- Water: 3.5–4L training days / 2.5–3L rest days

---

## TDEE Baseline

- Apple Watch burn (daily + walking): ~1,926 cal
- Weight training (not captured by Watch): +300 cal/session
- Training day TDEE: ~2,226 cal
- Rest day TDEE: ~1,926 cal

---

## Readability Preferences (Tanzim)

- "Easy on the eye and readable" — when asked to reorg, use clear section headers, logical top-down flow, no duplication
- Macro table goes first because it's the most-used reference
- Food source tables stay below the actionable targets
- Section headers in ALL CAPS, data rows clean and concise
