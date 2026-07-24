# Voice Assistant — User Intent & Preferences

## What Tanzim wants
Tanzim explicitly wants to use Friday via voice the way Tony Stark interacts with FRIDAY in Iron Man — fully conversational, hands-free, back-and-forth. "I want to use you in a similar way Tony interacts with Friday. Voice to voice."

His preferred setup: **iPhone Shortcut** (Option 1 — not Mac app, not desktop).
Pipeline: voice → STT → WhatsApp to Friday → TTS reply read back aloud.

The "read reply back aloud" path requires either:
- Polling for my WhatsApp response (complex)
- Siri reading the notification aloud when it arrives (simpler, native)
- Sync voice server on port 8645 with Speak step in Shortcut (best UX)

The sync voice server (port 8645) approach is already built and documented in the main SKILL.md. This is the path to complete.

## Status (May 2026)
In progress — not yet set up on Tanzim's iPhone. Next step: build and install the iPhone Shortcut using the instructions in the main SKILL.md Step 3.
