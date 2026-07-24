# PII Image Filter Criteria

When filtering images for contact/PII data, the standard criteria from Tanzim:

## What qualifies as a PII contact image

Must have ALL THREE:
- **Name** — full name of a person
- **Email** — valid email address
- **Phone number** — phone number in any format

If ANY of these three are missing, the image is "noise" and can be deleted.

## "PII NEW" folder filtering

When Tanzim mentions a "PII NEW" folder is "very noisy", the task is:
1. Scan every image in that folder
2. If it doesn't have Name + Email + Phone → delete it
3. If it does have all three → keep it (or extract to sheet)

This is noise reduction, not PII collection. Most images will fail the filter.

## Common image types that look like PII but aren't

| Type | Has | Missing | Action |
|------|-----|---------|--------|
| Phone call log | Names, phones | Email | Delete (noise) |
| Zoom call screenshot | Names (in tiles) | Phone, email | Delete (noise) |
| Social media profile | Name, maybe email | Usually no phone | Check carefully |
| Business card | Name, phone, email | Often single person | Keep if 2+ people |
| Chat screenshot | Names | Phone, email | Delete (noise) |

## Target images (keep these)

- **Spreadsheet screenshots** — Excel, Google Sheets, Numbers with contact columns
- **Contact list exports** — Tables with Name, Phone, Email columns
- **CRM screenshots** — Customer records with all three fields
- **Form submissions** — Lists of form responses with contact info

## Typical structure of target images

```
| Name              | Phone        | Email                    |
|-------------------|--------------|--------------------------|
| Anna Stefanenko   | 206-693-9445 | ag.rogova@gmail.com     |
| Jennifer Brander  | 801-859-4432 | jennilynebrander@gmail.com |
```

Grid/table layout with:
- Multiple rows (2+ contacts)
- Distinct columns for each field
- Usually from a spreadsheet or database export

## Progressive refinement workflow

When user says "I know there are more", run multiple passes:

1. **OCR gating** — fast regex for emails/phones, misses ~50%
2. **Full vision scan** — every image gets AI analysis
3. **Deep reasoning** — inclusive matching, catches edge cases (but more false positives)
4. **Pattern scan** — sample images, find categorization patterns, check stragglers

No single pass catches everything. User knows their data better than any filter.

## False positive watch

Deep reasoning with "be inclusive if uncertain" will flag:
- **Zoom calls** — "multiple people in a grid"
- **Phone call logs** — "names and phone numbers in a list"
- **Social media profiles** — "name and contact info visible"

Always verify matches before bulk operations. A quick vision check of flagged images catches most false positives.

## Vision prompt for filtering

```
Is this a spreadsheet/table showing contact information with ALL THREE of: 
names, phone numbers, AND email addresses?
Must have at least 2 people's records visible.
Answer YES or NO, then briefly describe what you see.
```

## Output destination

Matches go to:
- **Google Sheet** named "PIIX collection"
- Columns: Serial | Name | Phone | Email
- Deduplicate by email address before adding
- Cross-match after extraction: re-extract from images and compare against sheet

## Extraction prompt

```
Extract ALL contact records from this spreadsheet image.
For each row, extract: full name, phone number (exactly as shown), email address.

Return ONLY a JSON array, no other text:
[{"name": "John Smith", "phone": "206-555-1234", "email": "john@email.com"}, ...]
```
