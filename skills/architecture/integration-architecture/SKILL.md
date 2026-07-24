---
name: integration-architecture
description: "Tanzim's complete integration architecture: vault credential management, service routing, four-layer memory framework, token lifecycle, and multi-service orchestration."
version: 1.0.0
author: Friday
license: MIT
tags:
  - architecture
  - integrations
  - credentials
  - vault
  - service-routing
  - memory-framework
---

# Integration Architecture

**Purpose:** Governs how all external services (Google, GitHub, Instagram, iCloud, WhatsApp, Trello, Webflow, Wix, Calendar, Drive) are discovered, authenticated, routed, and executed. This is the foundational layer for any new integration, automation, or cross-service workflow.

**Status:** Production-ready (June 5, 2026). Locked architecture — no new infrastructure layers being added unless explicitly requested.

---

## Quick Reference

**11 Services Integrated:**
- Google Workspace (Gmail, Sheets, Drive, Calendar — shared OAuth)
- GitHub (PAT)
- Instagram (session cookies)
- iCloud (app-password IMAP)
- WhatsApp Bridge (bearer token)
- Trello (API key + token)
- Webflow (site token)
- Wix (editor token)

**Credential Strategy:**
- All secrets in `~/.hermes/vault.json` (600 perms)
- Hindsight holds routing map only (never secrets)
- Ask once, store forever; auto-refresh on expiry

**Four Layers:**
1. Discovery — identify available services
2. Registry — catalog with metadata
3. Access — query & validate credentials
4. Execution — route request to handler

---

## Core Principles

### 1. Vault as Source of Truth

All secrets live in `~/.hermes/vault.json` with 600 permissions (owner read/write only). Hindsight retains only the routing map — service names, credential locations, scopes, TTL. No secrets stored in Hindsight.

**Retrieval workflow:**
1. Check vault first
2. If missing → ask user once
3. Write to vault immediately
4. Never ask again (until expiry)

**Format:**
```json
{
  "google_oauth_token": "eyJ...",
  "github_pat": "ghp_...",
  "instagram_session": {
    "datr": "...",
    "ds_user_id": "...",
    "csrf_token": "..."
  },
  "icloud_app_password": "xxxx-xxxx-xxxx-xxxx",
  "env_vars": {
    "OPENROUTER_API_KEY": "sk-...",
    "ANTHROPIC_API_KEY": "sk-ant-..."
  }
}
```

### 2. Service Registry (Connection Metadata)

Centralized lookup table per service:

| Service | Auth | Scope | TTL / Refresh | Cache Key |
|---------|------|-------|---------------|-----------|
| Gmail | OAuth2 | modify, Drive, Calendar, Sheets | Auto 401 | gmail_auth |
| GitHub | PAT | repos (r/w) | Manual 30d | github_pat |
| Instagram | Session | API + HTML | Browser re-auth 30d | ig_session |
| iCloud | AppPass | IMAP r/w/flag | Manual ∞ | icloud_pass |
| Trello | Key+Token | Boards, cards | Manual | trello_key |
| Webflow | SiteToken | Collections | Manual | webflow_token |
| Wix | EditorToken | Editor API | Manual | wix_token |
| WhatsApp | BearerToken | /send, /edit | Static | whatsapp_token |

---

## 3. Task Router Pattern

Routes incoming requests to service-specific handlers:

```
User Request
    ↓
[Identify Service Type]
    ↓
[Look Up in Connection Registry]
    ↓
[Validate Credential (TTL check)]
    ↓
[Authenticate with Vault Credential]
    ↓
[Execute Service Handler]
    ↓
[Log + Return Result]
```

**Handlers per service:**
- **Gmail:** IMAP + API (list, send, flag, search, trash)
- **Sheets:** Read, append, update, batch operations
- **Drive:** Upload, download, share, trash
- **GitHub:** Repo ops, gist, branch, PR
- **Instagram:** Tag API discovery, profile enrichment, filtering
- **Trello:** Board/card CRUD
- **iCloud:** IMAP-only (calendar/contacts read-only via web)
- **Calendar:** Create, list, delete events
- **WhatsApp:** Send message, edit, media

---

## 4. Four-Layer Memory Framework (LOCKED)

### Discovery Layer
Identify all available integrations:
- Public APIs (Instagram, GitHub, Google)
- Session-based (Instagram, iCloud, Webflow, Wix)
- Static tokens (Trello, WhatsApp)
- Shared OAuth (Google suite)

### Registry Layer
Catalog connections with metadata:
- Service name
- Auth method (OAuth, PAT, token, password, session)
- Credential location (vault.json, local file, keychain)
- Scopes/permissions
- Last refresh timestamp
- Status (active, expired, revoked, failing)

### Access Layer
Query registry to locate & validate credentials:
- Search by service name
- Check expiration against current time
- Load from vault (decrypt if needed)
- Return authenticated client (OAuth token, session, etc.)

### Execution Layer
Route requests to service-specific handler:
- Dispatch to correct API endpoint
- Inject authenticated credentials
- Handle errors (retry, degrade, alert)
- Log all activity (service, timestamp, status, tokens used)

**Note:** No new QA, audit, or degradation layers being added. Use what we have.

---

## 5. Credential Refresh Strategies

| Service | Method | Trigger | Manual? | Notes |
|---------|--------|---------|---------|-------|
| **Google OAuth** | Auto | 401 Unauthorized | No | google-auth library handles |
| **GitHub PAT** | Manual | Expiry (30 days default) | Yes | Schedule re-auth 29 days in |
| **Instagram Session** | Re-auth | 30 days or 401 | Yes | Browser login required |
| **iCloud AppPass** | Manual | Expiry (Apple setting) | Yes | No automation, must update manually |
| **Trello Key+Token** | Manual | Revocation (no expiry) | Yes | Can revoke anytime, test before use |
| **Webflow SiteToken** | Manual | Revocation (no expiry) | Yes | Regenerate in Webflow UI |
| **Wix EditorToken** | Manual | Revocation (no expiry) | Yes | Regenerate in Wix OAuth |
| **WhatsApp Bearer** | Static | Revocation (no expiry) | Yes | Bridge manages internally |

**Auto-refresh logic:**
```python
if http_status == 401 and service == 'gmail':
    refresh_google_oauth()  # Auto-retry
elif http_status == 401 and service in ['instagram', 'trello']:
    notify_user("Credential expired, ask user")
```

---

## 6. Error Handling & Graceful Degradation

### Rate Limit Strategy

| Service | Limit | Fallback |
|---------|-------|----------|
| Gmail | 50/s, 500k/day | iCloud IMAP (backup) |
| Sheets | 500/100s | Local cache + retry 6am |
| Instagram API | 200/hr | HTML scraping (unlimited) |
| GitHub | 5k/hr (auth) | None, pause & wait |
| Trello | 30/sec | Exponential backoff |

### Retry Logic

```
401 Unauthorized        → Refresh token immediately
429 Too Many Requests   → Exponential backoff (8s, 16s, 32s)
503 Service Unavailable → Retry in 2 hours
Temporary network error → Retry 3x with 30s spacing
Timeout (>60s)         → Fail over or skip
```

### Fallback Chains

- **Email:** Gmail → iCloud
- **Profile enrichment:** Instagram API → HTML scraping
- **File upload:** Drive → local temp + manual sync
- **Messaging:** WhatsApp → Slack (if configured)

---

## 7. Security Boundaries

**Vault (Encrypted)**
- All secrets at rest
- 600 permissions (owner read/write only)
- Used by Hermes process only
- No credential leakage to logs

**Hindsight (Routing Map)**
- Credential locations & names
- No actual secrets stored
- Accessible for service discovery

**WhatsApp Bridge (Authenticated)**
- Bearer token required on all endpoints
- Token in vault, never in config
- localhost:3000, restricted firewall
- No body logging (prevents token exposure)

**GitHub Token (Read/Write)**
- PAT in vault or `~/.github_credentials`
- No credentials in git history
- Scoped to needed repos only

---

## 8. When Adding a New Service

**Checklist:**

1. **Credential storage** — where does it go? (vault, local file, env var)
2. **Auth method** — OAuth, PAT, API key, session, password?
3. **Scope/permissions** — what can it do?
4. **TTL/expiry** — manual refresh or auto?
5. **Endpoint** — API base URL or IMAP server?
6. **Error handling** — rate limits, retry logic, fallback?
7. **Hindsight entry** — add to service registry (metadata only)
8. **Handler** — create service-specific function
9. **Task router** — update dispatcher
10. **Documentation** — link in ARCHITECTURE_COMPLETE.md

**Minimal example:**
```python
# vault.json
"new_service_token": "sk_..."

# hindsight registry
{
  "service": "new_service",
  "auth_type": "bearer_token",
  "credential_path": "vault.json/new_service_token",
  "endpoint": "https://api.newservice.com",
  "scope": ["read", "write"],
  "ttl": "manual",
  "cache_key": "new_service_auth"
}

# handler
def new_service_handler(action: str, **kwargs):
    token = vault_access.get("new_service_token")
    client = NewServiceAPI(token)
    return client.execute(action, **kwargs)

# task router
elif service_type == "new_service":
    return new_service_handler(action, **kwargs)
```

---

## 9. Testing & Verification

### Pre-Flight Checklist

- [ ] Vault file exists at `~/.hermes/vault.json` (600 perms)
- [ ] All 8+ services migrated (Google, GitHub, iCloud, Webflow, Wix, Instagram, env)
- [ ] Google OAuth verified live (Sheets accessible)
- [ ] GitHub PAT in vault or `~/.github_credentials`
- [ ] Instagram session cookies fresh (within 30 days)
- [ ] WhatsApp bridge running (localhost:3000)
- [ ] Trello API key + token valid (test board accessible)
- [ ] iCloud app password working (IMAP login succeeds)

### Health Check (Daily Cron)

```
3:00 AM  — Vault integrity + Hindsight sync
9:00 AM  — Email systems status (Gmail, iCloud)
11:45 PM — Gmail junk sweep + session cleanup
```

---

## 10. Future Expansions (Optional)

These are NOT being built unless explicitly requested:

- **Phase 1:** QA layer (health checks, cost tracking, audit trails)
- **Phase 2:** New services (Apollo.io, Substack, Canva, n8n)
- **Phase 3:** Load balancing (primary → secondary → tertiary routing)
- **Phase 4:** Concurrency queue (parallel requests with rate-limit sharing)

---

## Reference Files

- **`ARCHITECTURE_COMPLETE.md`** — Full locked architecture (11 services, credentials, decision log)
- **`references/ig1-female-signal-detection.md`** — IG-1 Protocol female scoring weights and thresholds
- **`references/job-hammer-staging.md`** — Job Hammer crawler architecture and sync workflow
- **`references/gmail-automation.md`** — Email cron jobs (9am brief, 11:45pm sweep, 3am audit)
- **`references/service-endpoints.md`** — API URLs and IMAP servers per service

---

**Last Updated:** June 5, 2026  
**Status:** LOCKED — Production-ready, no new layers being added  
**Maintainer:** Friday (AI assistant for Tanzim)
