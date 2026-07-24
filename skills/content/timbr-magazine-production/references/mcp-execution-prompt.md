# TIMBR CHANGES Tab — MCP Execution Prompt

Use this prompt verbatim (updating the row range as needed) when handing the CHANGES tab to Claude for Canva MCP execution.

---

You are executing design changes for the TIMBR Workout Series magazine (5 issues). All instructions are pre-logged in a Google Sheet. Your job is to read each row and execute it against the correct Canva design.

**Sheet ID:** `1J4Rv-_NInf_jtjOHNYhTvVEfel0LK_uCfjjozshB2Ew`
**Tab:** CHANGES
**Rows to process:** CHG-001 to CHG-115 where column L (Status) = PENDING

**Column reference:**
- A = Change ID
- B = Tab (which magazine issue this belongs to)
- C = Canva Design ID (the design to open)
- D = Page (page number within that design, 1-indexed)
- E = Element (what element is being changed)
- F = Element Description (context on where it lives)
- G = Current Value (what it says now — use to locate the element)
- H = New Value (what it should say or become)
- I = Action Type: UPDATE_TEXT, ADD_ELEMENT, or REMOVE_ELEMENT
- J = MCP Instruction (your exact execution instruction — follow this precisely)
- K = Rationale (why — for your context only, do not act on this)
- L = Status (PENDING → update to DONE after successful execution, or FAILED if it errors)

**The 5 Canva Design IDs:**
- Glutes & Hamstring: DAHFfAiLO3E
- Shoulder & Core: DAHKu7sMKdE
- Quads & Calf: DAHKuy17o8s
- Chest & Tricep: DAHKuyPqxww
- Back & Bicep: DAHKu6XleTQ

**Execution rules:**
1. Read column J (MCP Instruction) for each row — that is your primary directive. Follow it exactly.
2. Use column G (Current Value) to locate the correct element when searching the design.
3. For UPDATE_TEXT: find the element, replace text only. Do not change font, size, colour, weight, or position unless column J explicitly says to.
4. For ADD_ELEMENT: add a new text block at the location described in column J. Match the surrounding design's typography style unless column J specifies otherwise.
5. For REMOVE_ELEMENT: delete the element described. Do not adjust surrounding layout unless column J says to.
6. Process in order — CHG-001 first, CHG-115 last. Complete all changes on one design before moving to the next.
7. After each successful execution, update column L for that row from PENDING to DONE.
8. If a change fails (element not found, design locked, API error), set column L to FAILED and log a one-line note in column K after the existing rationale text, starting with "FAILURE:".
9. Do not skip rows. Do not batch or combine changes unless they are on the same element of the same page of the same design.
10. When all rows are processed, return a summary: total executed, total DONE, total FAILED, and list any FAILED Change IDs.

**Important:** Canva's API cannot directly edit text content — if you are running this through the Canva MCP connector, use the available design editing endpoints and refer to column J for the exact element targeting logic. If text editing is blocked by API limitations, mark the row FAILED with note "FAILURE: Canva API text edit not supported — manual edit required."

---

*Last updated: May 27, 2026. Total records: CHG-001–CHG-115. Pages 7–8 static — no CHANGES entries.*
