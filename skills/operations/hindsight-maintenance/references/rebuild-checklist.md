# Post-Wipe Rebuild Checklist

Run hindsight_retain for each. Verify count at end.

## Mandatory (always)
- [ ] Tanzim Ozer — owner profile (location, role, company, emails, WhatsApp IDs)
- [ ] Identity map — ALL known WhatsApp sender IDs with tiers
- [ ] Active integrations — all credentials and file paths
- [ ] Infrastructure — VM, WhatsApp routing, bridge status
- [ ] Security log — SOUL changes, codeword rotations, permission fixes
- [ ] Backup system — cron IDs, locations, Drive folder IDs

## TIMBR business
- [ ] TIMBR LLC — company overview, products, pricing, platform
- [ ] Magazine production state (Blair/Shumon/Taylor)
- [ ] Foundation Series status
- [ ] Website known issues
- [ ] Editorial Bible summary
- [ ] Webflow state (paused)
- [ ] Wix MCP notes

## People profiles
- [ ] Blair Grimes (trainee, magazine subject, groups, no auth)
- [ ] Tahmeed Ozer (brother, AI student, limited scopes)
- [ ] Towsif (Canva collaborator)
- [ ] Irissa Lucas (contact, minimal context)

## Job search
- [ ] TerraJob system
- [ ] Linked Engine
- [ ] Active interviews
- [ ] Foundation AI interview (specific)

## Automation
- [ ] Cron jobs (all 19, with IDs)
- [ ] Trello boards and credentials
- [ ] MAGPROD Engine Drive structure
- [ ] Blackwire project (brief)
- [ ] Substack status

## Optional (if relevant to current state)
- [ ] Disk-fix operational markers
- [ ] Kanban/MAGPROD Engine detail

## Verification query
```sql
SELECT COUNT(*) FROM documents;
```
Expected: ~25-30 documents after clean rebuild.
