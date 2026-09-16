# INTEGRATION_SPEC.md — Contract-First Rules, Team Boundaries, AI-Agent Guardrails
**Owner:** P1 (you). Every teammate and every AI coding agent working on this project should read this file before touching any other file — if you arrived here directly rather than via `AGENTS.md`, read `AGENTS.md` first; it's the canonical entry point and routes to this file as step 2.

---

## 1. Contract-first, always
Before implementation, the following must be defined and treated as fixed unless explicitly changed:
- API contracts (`API_SPEC.md`)
- Database schema (`DATA_SCHEMA.md`)
- ML input/output contract (`ML_GIS_CONTRACTS.md` §1)
- GIS/GeoJSON contract (`ML_GIS_CONTRACTS.md` §2)
- Alert structure (`API_SPEC.md` alerts group)

**If a proposed implementation conflicts with an established contract, the contract wins unless the architecture is intentionally changed via an ADR in `ADRS.md`.** AI coding agents must not independently invent request/response shapes, table columns, or model I/O formats "because it seemed reasonable."

## 2. Rule for AI coding agents specifically
If you are an AI agent (Claude Code, Cursor, Copilot, etc.) assigned to one of the role files (`BACKEND_SPEC.md`, `FRONTEND_SPEC.md`, `ML_SPEC.md`, `GIS_SPEC.md`):
1. Read your own role file fully before writing code.
2. Read `API_SPEC.md`, `DATA_SCHEMA.md`, and `ML_GIS_CONTRACTS.md` — these are shared, read-only for you unless you're P1/P5 on the shared files.
3. **Do not edit files outside your role's directory/scope.** If your task seems to require it (e.g., frontend needing a new API field), stop and flag it as a proposed contract change rather than editing the backend yourself.
4. If a contract file and the running code disagree, treat the contract as correct and the code as buggy — fix the code, don't silently redefine the contract to match a wrong implementation.
5. Never claim a `FUTURE`-tagged capability (real LEA/bank integration, streaming, PostGIS, etc.) is implemented. Use the IMPLEMENTED / MVP TARGET / FUTURE labels from `README.md` honestly in comments, PR descriptions, and docs.
6. Prefer the smallest change that satisfies the contract. Do not "improve" architecture by introducing new infra (queues, microservices, new DBs) without an ADR.

## 3. Team boundaries (recap — see `ARCHITECTURE.md` §17 for full detail)
| Role | Owns | Must not touch |
|---|---|---|
| P1 (you) | Overall architecture, integration, `ARCHITECTURE.md`, `INTEGRATION_SPEC.md`, `ADRS.md` | — (integrates everything, but implementation of others' modules stays with them) |
| P2 | ML feature pipeline, model, inference contract, evaluation | API routes, DB models, spatial code, React code |
| P3 | Spatial data, geospatial processing, hotspots, GeoJSON generation | Model internals, API routes, React code |
| P4 | React structure, components, dashboard, map UI, API consumption | Backend, ML, GIS internals; no client-side risk/distance computation |
| P5 | FastAPI, endpoints, configuration, integration, technical testing | ML model internals, spatial algorithm internals, React code |
| P6 | Requirements, operational workflow, domain validation, actionability, real-world scenarios | Technical architecture decisions |

## 4. Architecture Decision process
For any significant decision (new dependency, structural change, contract change), record it as an ADR in `ADRS.md` with: Decision, Reason, Alternatives considered, Why alternatives rejected, MVP impact, Future scalability impact. Do not let decisions live only in chat history.

## 5. Judge-Defensibility Checklist
Be ready to answer honestly (see `README.md`'s IMPLEMENTED / MVP TARGET / FUTURE categories for the split that underlies these answers, and `ARCHITECTURE.md` §12 for the scalability detail specifically):
- Why this architecture?
- Why this ML approach (RF/XGBoost, not something fancier)?
- How does prediction happen, step by step?
- Where does the data come from — is it real or synthetic?
- How does the system integrate with existing systems (NCRP, banks, I4C)? — **be honest that MVP does not have real integrations.**
- Why Top-K rather than one exact ATM?
- How do you handle false positives / low confidence?
- How do you handle missing data?
- How does this scale to nationwide usage?
- How is sensitive financial information protected?
- How do you prevent unauthorized access?
- How is a prediction explained?
- What happens if the model is wrong?
- Is this real-time? (No — MVP is synchronous/request-triggered, see `ARCHITECTURE.md` §6.)
- What is implemented vs proposed vs synthetic? (Always answer using the IMPLEMENTED / MVP TARGET / FUTURE labels.)

## 6. Anti-overengineering gate
Before adding any technology not in the fixed MVP stack (`README.md`), the proposer must answer in writing (in the PR or an ADR): **"What concrete problem does this solve that the current architecture cannot solve?"** No clear answer → rejected by default; escalate to P1 if you still believe it's needed.
