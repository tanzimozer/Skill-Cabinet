# PII Detection Prompts

Prompts tested for detecting contact information in image libraries.

## Inclusive Detection (catches edge cases, needs post-filtering)

```
Analyze this image with research-level reasoning.

QUESTION: Does this image contain a list, spreadsheet, or collection of CONTACT INFORMATION?

Contact information means: names paired with phone numbers, email addresses, or both.

Think step by step:
1. What type of image is this?
2. Is there text visible?
3. Is the text organized in a list or table format?
4. Does it contain multiple people's names?
5. Are there phone numbers or email addresses?

If this COULD BE a contact list (even partially visible, handwritten, or screenshot of contacts app), answer: MATCH
If this is clearly NOT contact information, answer: NO_MATCH

Answer with ONLY "MATCH" or "NO_MATCH"
```

## Strict Detection (fewer false positives)

```
Does this image contain a spreadsheet or list showing contact information (names with phone numbers or email addresses)?

Answer ONLY: YES or NO
```

## Extraction Prompt (after match confirmed)

```
Extract all contact information from this image.

For each person, provide:
- Name (first and last if visible)
- Phone number (with country code if shown)
- Email address (if visible)

Format as JSON array:
[{"name": "...", "phone": "...", "email": "..."}]

If a field is not visible, use null.
Only include entries where at least name AND (phone OR email) are present.
```

## False Positive Categories

Images that match "contact list" detection but aren't:
- Zoom/video call participant grids
- Phone call history/recents
- App notification lists with names
- Social media follower lists
- Restaurant/business review lists
