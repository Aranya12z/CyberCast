# AGENTS.md — entry point for every AI coding agent on this project

**Read this file first, before opening any other file or writing any code.**
If you are a human teammate, `README.md` is your starting point instead —
this file exists specifically to make AI agent behavior on this repo
predictable and bounded.

---

## 1. Read order — always, regardless of task

1. **This file.**
2. `INTEGRATION_SPEC.md` — contract-first rules, team boundaries, AI-agent
   guardrails. Non-negotiable.
3. `README.md` — project overview, the IMPLEMENTED / MVP TARGET / FUTURE
   categories, fixed tech stack.
4. `ARCHITECTURE.md` — system design context. Read-only for you unless
   you are specifically operating as P1.

Do not skip to your role file before these four. The role files assume
you already know the boundaries set here.

## 2. Route to your role file

| Your task is about... | Role file | Shared contracts (read-only) | Never edit |
|---|---|---|---|
| React dashboard, GIS map UI, any component | `FRONTEND_SPEC.md` | `API_SPEC.md`, `ML_GIS_CONTRACTS.md` §2 | backend/, ml/, gis/ — no client-side risk/distance math |
| FastAPI routes, orchestration, DB models, auth | `BACKEND_SPEC.md` | `API_SPEC.md`, `DATA_SCHEMA.md`, `ML_GIS_CONTRACTS.md` | ml/ internals, gis/ internals, frontend/ |
| Feature engineering, model training, inference | `ML_SPEC.md` | `ML_GIS_CONTRACTS.md` §1 | backend/api/, frontend/, gis/ internals |
| Spatial/proximity/density/GeoJSON | `GIS_SPEC.md` | `ML_GIS_CONTRACTS.md` §2 | backend/api/, frontend/, ml/ internals |

If a task spans more than one row, stop and flag it as an
integration-layer question — that's P1's call, not something to resolve
by quietly editing across the boundary yourself.

## 3. The rule that overrides everything else

**Contracts win.** `API_SPEC.md`, `DATA_SCHEMA.md`, and `ML_GIS_CONTRACTS.md`
are fixed unless changed via a new entry in `ADRS.md`. If your task seems
to need a field, endpoint, or table column that doesn't exist in the
relevant contract file:
- Do not invent it.
- Do not silently rename an existing field to something more convenient.
- Flag the gap (in your output / PR description) and either wait for the
  contract to be updated, or implement against the contract as it stands
  and note the limitation explicitly.

If a contract file and the running code disagree, the contract is
correct and the code is buggy — fix the code, don't redefine the
contract to match a wrong implementation.

## 4. Status labels — use them honestly, everywhere

Every capability is one of:
- `[IMPLEMENTED]` — actually running in this repo right now.
- `[MVP TARGET]` — planned for this SIH build, not done yet. **Auth/JWT/RBAC
  is currently `[MVP TARGET]`** — do not describe it as working until it's
  actually wired end-to-end.
- `[FUTURE]` — national-scale/production concept, not part of this repo.
  Real LEA/bank/I4C integration, streaming ingestion, PostGIS, full MLOps,
  SHAP-based explainability all fall here unless an ADR says otherwise.

Never present a `[FUTURE]` item as if it exists — in code comments, PR
descriptions, docstrings, or anything a judge might read.

## 5. Two thresholds that are easy to conflate — don't

- The model's own **confidence floor** (`ML_SPEC.md`, default 0.35) decides
  whether a prediction is returned at all (`insufficient_confidence`).
- The backend's **alert threshold** (`ADRS.md` ADR-006, `risk_score >= 0.4
  AND confidence >= 0.5`) decides whether a *returned* prediction becomes
  an alert.

A prediction can clear the first and not the second. If your task touches
either one, use the exact numbers from the docs above — don't estimate or
carry over a number from memory.

## 6. Before you finish

- Re-read your role file's "What NOT to build here" section.
- Confirm every field name you used matches the relevant contract file
  exactly — no renamed keys, no added nesting, no dropped fields.
- If you touched a shared contract file, that's a signal you went out of
  scope. Revert and flag it instead, unless you are explicitly operating
  as P1/P5 on that specific file per `README.md`'s ownership table.
- If you're unsure whether something is `[MVP TARGET]` or `[FUTURE]`,
  check `README.md` and `ARCHITECTURE.md` §12 before guessing.
