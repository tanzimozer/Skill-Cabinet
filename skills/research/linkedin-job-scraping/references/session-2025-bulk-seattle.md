# Bulk LinkedIn Job URL Retrieval — Seattle Feed (2025)

## Context
Tanzim sent ~25 screenshots of his LinkedIn "For You" feed. Mix of Seattle-area and remote roles.
Task: find the direct `linkedin.com/jobs/view/` URL for each visible listing.

## Confirmed job IDs (all verified via og:title)

| Job Title | Company | Job ID | URL |
|-----------|---------|--------|-----|
| Special Projects Coordinator | NetReputation.com | 4409594866 | https://www.linkedin.com/jobs/view/4409594866/ |
| Application Operations Lead | HealthierHere | 4416720473 | https://www.linkedin.com/jobs/view/4416720473/ |
| Client Services Associate | SPS (Seattle) | 4418283005 | https://www.linkedin.com/jobs/view/4418283005/ |
| Entry Level Workday Analyst | Optimum Healthcare IT | 4416838437 | https://www.linkedin.com/jobs/view/4416838437/ |
| Project Coordinator | D.A. Davidson Companies | 4408576386 | https://www.linkedin.com/jobs/view/4408576386/ |
| Project Coordinator | Brink's Inc | 4419530236 | https://www.linkedin.com/jobs/view/4419530236/ |
| Project Specialist | Emerald Clinical | 4419451425 | https://www.linkedin.com/jobs/view/4419451425/ |
| Jr AI Infrastructure Scheduler | MIGSO-PCUBED | 4410642534 | https://www.linkedin.com/jobs/view/4410642534/ |
| Program Manager – Music Industry Operations | IntePros | 4396659415 | https://www.linkedin.com/jobs/view/4396659415/ |
| IT Systems Business Analyst | Tanium | 4382204139 | https://www.linkedin.com/jobs/view/4382204139/ |
| Operations Analyst | Personified | 4414954693 | https://www.linkedin.com/jobs/view/4414954693/ |
| Hardware Lifecycle Coordinator | Pax8 | 4418447681 | https://www.linkedin.com/jobs/view/4418447681/ |
| Partner Enablement Program Specialist | Planet Technologies | 4412975635 | https://www.linkedin.com/jobs/view/4412975635/ |
| Project Controls Coordinator | Foss Maritime | 4417516086 | https://www.linkedin.com/jobs/view/4417516086/ |
| ERP Systems Analyst | STV | 4414019783 | https://www.linkedin.com/jobs/view/4414019783/ |
| Implementation Specialist | DealerBuilt | 4411409147 | https://www.linkedin.com/jobs/view/4411409147/ |
| Anaplan Consultant | ITC Infotech | 4413146719 | https://www.linkedin.com/jobs/view/4413146719/ |
| Customer Success Specialist | Sportworks | 4410319404 | https://www.linkedin.com/jobs/view/4410319404/ |
| Business Administrator | Microsoft | 4415848882 | https://www.linkedin.com/jobs/view/4415848882/ |
| FinCEN Support Coordinator I | Stewart Title | 4337084965 | https://www.linkedin.com/jobs/view/4337084965/ |
| Senior Customer Onboarding Specialist – Industry Cloud | Salesforce | 4409053117 | https://www.linkedin.com/jobs/view/4409053117/ |
| Program Coordinator, Gift Services & Data Management | Fred Hutch | 4409103057 | https://www.linkedin.com/jobs/view/4409103057/ |
| Client Project Coordinator (Contractor) | Wheel | 4419557438 | https://www.linkedin.com/jobs/view/4419557438/ |
| Operations & Outreach Coordinator | Zero Emission Vehicle Cooperative | 4413129944 | https://www.linkedin.com/jobs/view/4413129944/ |
| Solution Consultant | Fano (Fano Labs) | 4416201572 | https://www.linkedin.com/jobs/view/4416201572/ |
| Customer Experience Operations Analyst | Tines | 4414069272 | https://www.linkedin.com/jobs/view/4414069272/ |
| Product Support Specialist – Implementation | Lighthouse | 4414675026 | https://www.linkedin.com/jobs/view/4414675026/ |
| Ordering Onboarding Specialist | PAR Technology | 4410441556 | https://www.linkedin.com/jobs/view/4410441556/ |
| Dedicated Support Engineer | LiveRamp | 4414988904 | https://www.linkedin.com/jobs/view/4414988904/ |
| Functional Analyst – eCommerce | Tommy Bahama | 4408152147 | https://www.linkedin.com/jobs/view/4408152147/ |
| Associate, Tax GMS – Business Analyst | KPMG US (Seattle) | 4417441662 | https://www.linkedin.com/jobs/view/4417441662/ |
| IT Project Manager – Salesforce | Nintendo | 4398090833 | https://www.linkedin.com/jobs/view/4398090833/ |
| Oracle EPM Cloud Planning Consultant | Peloton Consulting Group | 4400532585 | https://www.linkedin.com/jobs/view/4400532585/ |
| Implementation Consultant | SeatGeek | 4405155982 | https://www.linkedin.com/jobs/view/4405155982/ |
| Customer Support Specialist | PitchBook | 4406751277 | https://www.linkedin.com/jobs/view/4406751277/ |
| Workday Student Records & Admissions Implementation Consultant | Deloitte | 4409101815 | https://www.linkedin.com/jobs/view/4409101815/ |

## False positives caught during verification
- `4412936837` — returned Google's "Escalation Specialist" not NetReputation (fixed to 4409594866)
- `4400017170` — returned UBS "Client Associate" not SPS (fixed to 4418283005)
- `4415732015` — returned KPMG "Senior Associate, Corporate Compliance" not GMS Business Analyst (fixed to 4417441662)
- `4302527185` — returned Amazon "Executive Support Eng" not LiveRamp (fixed to 4414988904)
- `4409104151` — returned Nintendo "Program Manager (Consumer Service)" not IntePros (fixed to 4396659415)

## Notes
- Google site: search was blocked (CAPTCHA). Bing also returned no LinkedIn results. LinkedIn guest search direct was the only working approach.
- SPS posts Client Services Associate under multiple job IDs simultaneously — 4418283005 was the most recent Seattle listing.
- KPMG Associate Tax GMS posted across 5+ cities; Seattle-specific was 4417441662.
