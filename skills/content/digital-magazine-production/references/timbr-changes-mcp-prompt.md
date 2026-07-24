# TIMBR Workout Series — MCP Execution Prompt
Generated: May 2026. Use this verbatim when handing Claude a Canva MCP session to execute the CHANGES tab.

---

You are executing design changes for the TIMBR Workout Series magazine (5 issues). All instructions are pre-logged in a Google Sheet. Your job is to read each row and execute it against the correct Canva design.

**Sheet ID:** `1J4Rv-_NInf_jtjOHNYhTvVEfel0LK_uCfjjozshB2Ew`
**Tab:** CHANGES
**Rows to process:** CHG-001 to CHG-115 where column L (Status) = PENDING

**Column reference:**
- A = Change ID
- B = Tab (which magazine issue)
- C = Canva Design ID (the design to open)
- D = Page (1-indexed)
- E = Element (what element is being changed)
- F = Element Description (context on where it lives)
- G = Current Value (what it says now — use to locate the element)
- H = New Value (what it should say or become)
- I = Action Type: UPDATE_TEXT, ADD_ELEMENT, or REMOVE_ELEMENT
- J = MCP Instruction (your exact execution instruction — follow this precisely)
- K = Rationale (context only — do not act on this)
- L = Status (PENDING → update to DONE after success, FAILED if it errors)

**The 5 Canva Design IDs:**
- Glutes & Hamstring: `DAHFfAiLO3E`
- Shoulder & Core: `DAHKu7sMKdE`
- Quads & Calf: `DAHKuy17o8s`
- Chest & Tricep: `DAHKuyPqxww`
- Back & Bicep: `DAHKu6XleTQ`

**Execution rules:**
1. Column J (MCP Instruction) is your primary directive. Follow it exactly.
2. Use column G (Current Value) to locate the correct element.
3. UPDATE_TEXT: replace text only. Do not change font, size, colour, weight, or position unless column J explicitly says to.
4. ADD_ELEMENT: add a new text block at the location described in column J. Match surrounding design typography unless column J specifies otherwise.
5. REMOVE_ELEMENT: delete the described element. Do not adjust surrounding layout unless column J says to.
6. Process in order — CHG-001 first, CHG-115 last. Complete all changes on one design before moving to the next.
7. After each successful execution, update column L from PENDING to DONE.
8. If a change fails, set column L to FAILED and append "FAILURE: [reason]" to the existing text in column K.
9. Do not skip rows. Do not batch or combine changes unless on the same element of the same page of the same design.
10. When all rows are processed, return a summary: total executed, total DONE, total FAILED, and list any FAILED Change IDs.

**Important:** Canva's API cannot directly edit text content. If text editing is blocked by API limitations, mark the row FAILED with note "FAILURE: Canva API text edit not supported — manual edit required."

---

## Page 4 Gym Spotlight Pattern
Each issue's Page 4 follows a 4-change pattern:
1. **Headline** (UPDATE_TEXT) — `Where to Train This Week — [Neighbourhood]`
2. **Body copy** (UPDATE_TEXT) — Equipment callout tied to that issue's muscle group
3. **Best window callout** (ADD_ELEMENT) — Time-of-day tip (pull-quote or tip box style)
4. **Credibility line** (ADD_ELEMENT) — "Featured because: [specific reasons]" at bottom, small italic

Series 01 neighbourhood pairings:
- Glutes & Hamstring → South Lake Union
- Shoulder & Core → Fremont
- Quads & Calf → Queen Anne
- Chest & Tricep → South Lake Union (different gym from G&H)
- Back & Bicep → Capitol Hill
