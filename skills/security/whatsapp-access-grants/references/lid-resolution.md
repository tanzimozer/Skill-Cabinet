# LID ↔ Phone Number Resolution

## The problem
When Tanzim tags someone in a message (e.g. `@90345106862172`), that's the `@lid` format.
But when that person actually sends a message, WhatsApp delivers it with their phone-number-based ID (`@s.whatsapp.net`).

Grants keyed only to `@lid` will fail — messages arrive as `@s.whatsapp.net` and get default-denied.

## Resolution lookup
```bash
cat ~/.hermes/whatsapp/session/lid-mapping-<lid_number>_reverse.json
```
Returns the raw phone number (e.g. `"8801789840112"`).

Then construct: `8801789840112@s.whatsapp.net`

## Real example (Tahmeed, May 2026)
- LID given by Tanzim: `90345106862172@lid`
- Reverse mapping file: `lid-mapping-90345106862172_reverse.json`
- Content: `"8801789840112"`
- Phone ID added: `8801789840112@s.whatsapp.net`

Both entries now exist in grants.json under the same label.
