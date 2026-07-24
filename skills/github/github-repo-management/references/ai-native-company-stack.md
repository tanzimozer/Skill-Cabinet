# AI-Native Autonomous Company — Open Source Stack Research
*Researched July 2026 · tanzimozer GitHub account*

Tanzim's objective: run a fully AI-native, autonomous company.
Already forked: `garrytan/gstack` (124K★) → `tanzimozer/gstack`
Already forked: `gsd-build/get-shit-done` (30K★) → `tanzimozer/get-shit-done`

---

## Orchestration
| Repo | Stars | Notes |
|------|-------|-------|
| `crewAIInc/crewAI` | 56K | Role-based autonomous agents |
| `langchain-ai/langgraph` | 38K | Stateful multi-agent workflows |
| `OpenHands/OpenHands` | 82K | AI dev agent — plans + executes autonomously |
| `langchain-ai/langchain` | 143K | Agent engineering platform |
| `microsoft/autogen` | 60K | Microsoft's agentic AI framework |

## Memory
| Repo | Stars | Notes |
|------|-------|-------|
| `thedotmack/claude-mem` | 88K | Persistent context across sessions |
| `mem0ai/mem0` | 62K | Universal memory layer for agents |
| `letta-ai/letta` | 24K | Stateful agents with memory, self-improve |

## Browser & Web Automation
| Repo | Stars | Notes |
|------|-------|-------|
| `browser-use/browser-use` | 107K | Web automation for AI agents |
| `Skyvern-AI/skyvern` | 23K | Browser workflow automation via AI |
| `SWE-agent/SWE-agent` | 20K | Autonomously resolves GitHub issues |
| `bytedance/UI-TARS-desktop` | 38K | Multimodal AI agent stack |

## MCP Layer
| Repo | Stars | Notes |
|------|-------|-------|
| `tadata-org/fastapi_mcp` | 12K | Expose FastAPI endpoints as MCP tools |
| `mcp-use/mcp-use` | 10K | Fullstack MCP framework |
| `awslabs/mcp` | 9.5K | AWS infra via AI agents |
| `hangwin/mcp-chrome` | 12K | Chrome extension MCP server |

## Workflow Automation
| Repo | Stars | Notes |
|------|-------|-------|
| `n8n-io/n8n` | 104K | Self-hosted backbone — wires everything |
| `bytedance/deer-flow` | 78K | Long-horizon super-agent harness |

## CRM & Customer Ops
| Repo | Stars | Notes |
|------|-------|-------|
| `twentyhq/twenty` | 54K | Open Salesforce alternative, AI-designed |
| `chatwoot/chatwoot` | 35K | Omnichannel support desk |
| `evolution-foundation/evolution-api` | 9K | WhatsApp integration API |
| `mhenry3164/twenty-crm-mcp-server` | — | MCP bridge for Twenty CRM |

## Project Management
| Repo | Stars | Notes |
|------|-------|-------|
| `makeplane/plane` | 55K | Open Jira/Linear alternative |
| `Paca-AI/paca` | 1.6K | AI-native board — humans + agents share workspace |

## Sales & Marketing
- **Gap**: weak OSS ecosystem. Best play = `browser-use` + `n8n` + `mem0` for custom outreach
- `buildingopen/opengtm` — open Clay/Apollo alternative (lead gen, ICP scoring)

## Finance & Accounting
- **Gap**: mostly proprietary (Pilot, Ramp). Use ERPNext as base with AI hooks
- `frappe/erpnext` — 18K★ — only serious open option

## DevOps / Infra Automation
- `OpenHands/OpenHands` — 82K★
- `SWE-agent/SWE-agent` — 20K★
- `awslabs/mcp` — 9.5K★

---

## Recommended Core Stack (Start Here)
```
n8n                → workflow backbone
crewAI / langgraph → agent orchestration
mem0               → persistent memory
browser-use        → web automation
twenty             → CRM
plane              → project management
fastapi_mcp        → expose internal tools to agents
gstack + GSD       → Claude Code productivity layer (already forked)
```

## Key Gaps to Watch
1. **Sales/marketing** — no strong OSS player; build custom
2. **Finance** — ERPNext is the only base; AI-native finance is proprietary
3. **Context rot** — GSD specifically addresses this for Claude Code sessions
