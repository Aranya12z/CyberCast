# AGENTS.md — Entry Point for Every AI Coding Agent

**Read this file first, before opening any other project file or writing code.**

If you are a human teammate, `README.md` is your starting point instead.

This file exists specifically to make AI-agent behavior on this repository predictable, bounded, and consistent with the project's architecture and contracts.

---

## 1. Read Order — Always

Regardless of the task, follow this order:

1. **This file (`AGENTS.md`)**
2. `docs/INTEGRATION_SPEC.md` — contract-first rules, team boundaries, and AI-agent guardrails
3. `README.md` — project overview, project status categories, team ownership, and fixed MVP tech stack
4. `docs/ARCHITECTURE.md` — system architecture, layers, data flow, and implementation boundaries

Do not skip directly to a role-specific file.

The role-specific specifications assume that you already understand the boundaries defined by these four files.

### Important path rule

The root `README.md` describes the whole project.

All technical specifications and architecture documents are under `docs/`.

Do not create a second project README inside `docs/` unless P1 explicitly decides otherwise.

---

## 2. Route Yourself to the Correct Role File

After reading the four files above, identify the task and read the corresponding specification.

| Task                                                     | Role File                                                          | Shared Contracts to Read                                              | Never Edit                                                                     |
| -------------------------------------------------------- | ------------------------------------------------------------------ | --------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| React dashboard, GIS map UI, components, frontend state  | `docs/FRONTEND_SPEC.md`                                            | `docs/API_SPEC.md`, `docs/ML_GIS_CONTRACTS.md` §2                     | `backend/`, `ml/`, `gis/` internals; no client-side risk/distance calculations |
| FastAPI routes, orchestration, DB models, authentication | `docs/BACKEND_SPEC.md`                                             | `docs/API_SPEC.md`, `docs/DATA_SCHEMA.md`, `docs/ML_GIS_CONTRACTS.md` | `ml/` internals, `gis/` internals, frontend                                    |
| Feature engineering, model training, inference           | `docs/ML_SPEC.md`                                                  | `docs/ML_GIS_CONTRACTS.md` §1                                         | backend API, frontend, GIS internals                                           |
| Spatial/proximity/density/GeoJSON logic                  | `docs/GIS_SPEC.md`                                                 | `docs/ML_GIS_CONTRACTS.md` §2                                         | backend API, frontend, ML internals                                            |
| Cross-cutting/integration/architecture work              | `docs/ARCHITECTURE.md`, `docs/INTEGRATION_SPEC.md`, `docs/ADRS.md` | Relevant shared contracts                                             | Do not silently cross team boundaries                                          |

If a task spans more than one row, treat it as an **integration-layer question**.

Do not quietly edit multiple ownership areas simply because doing so appears convenient.

Flag the cross-boundary dependency and coordinate through P1.

---

## 3. Contracts Win

The following files are the project's shared contracts:

* `docs/API_SPEC.md`
* `docs/DATA_SCHEMA.md`
* `docs/ML_GIS_CONTRACTS.md`

These contracts are authoritative.

If implementation code disagrees with a contract, assume the implementation is wrong unless an explicit architecture decision has changed the contract.

### Never:

* invent a new API field because it is convenient
* silently rename an existing field
* invent an endpoint
* add a database column that is not part of the agreed schema
* change an ML input/output shape without coordination
* change the GeoJSON structure independently
* add undocumented nesting to a response
* silently remove a required field

### If the contract appears incomplete

Do not silently solve the ambiguity.

Instead:

1. identify the missing requirement
2. flag it as a contract/integration issue
3. coordinate with the owner
4. update the relevant contract only when authorized
5. record major architectural changes through `docs/ADRS.md` when appropriate

**Code must follow the agreed contract, not redefine it.**

---

## 4. Project Status Labels

Every capability described in documentation, code comments, PRs, demos, or implementation notes should be clearly treated as one of these:

### `[IMPLEMENTED]`

Actually working in the current repository.

It can be demonstrated or verified from the current code.

### `[MVP TARGET]`

Planned for the SIH preliminary/MVP build but not necessarily implemented yet.

Do not describe an MVP target as already working.

For example, authentication, JWT, and RBAC should only be described as implemented once they are actually wired end-to-end.

### `[FUTURE]`

A national-scale, production, or later-phase capability.

Examples include:

* real LEA integration
* real bank/FI integration
* real I4C integration
* production streaming ingestion
* PostGIS at scale
* full MLOps
* model registry and drift monitoring
* SHAP-based production explainability
* large-scale distributed infrastructure

Unless explicitly changed through an architecture decision, these are not MVP implementation requirements.

Never present a `[FUTURE]` capability as if it already exists.

---

## 5. MVP Scope Guardrails

This project is a **predictive intelligence layer**, not a replacement for the existing cybercrime complaint ecosystem.

Do not expand the MVP into unrelated systems.

### The MVP is focused on:

* ingesting cybercrime complaint/event information
* combining complaint, transaction, ATM, temporal, behavioral, and spatial signals
* generating candidate withdrawal locations
* ranking candidate locations
* assigning risk scores/confidence
* providing a predicted time window
* providing understandable prediction explanations
* displaying predictions through authorized dashboards
* generating actionable alerts based on agreed rules
* providing intelligence useful to LEA and financial institutions
* using synthetic/anonymized data for the prototype

### Do not build these unless explicitly authorized:

* a new public cybercrime complaint portal
* a generic public crime dashboard
* a generic ATM heatmap with no predictive layer
* an unrelated banking application
* a payment gateway
* a full financial transaction-processing system
* microservices
* Kafka/event-streaming infrastructure
* Kubernetes
* Redis
* Elasticsearch
* Spark
* Apache Sedona
* PostGIS
* GraphQL
* service mesh
* federated learning
* advanced MLOps

The MVP should remain a **modular monolith** unless `docs/ADRS.md` explicitly changes that decision.

---

## 6. Prediction Semantics

The system is intended to produce **ranked candidate withdrawal locations**, not claim that one exact ATM is guaranteed to be used.

A prediction should be treated as intelligence containing, where defined by the contracts:

* candidate ATM/location
* risk score
* confidence
* predicted time window
* explanation/reasons
* model version
* prediction status

Do not turn a probabilistic prediction into a statement of certainty.

The frontend must not independently reinterpret the model output.

The backend should consume the ML contract and expose the agreed API contract.

---

## 7. ML Boundary

ML code belongs to the ML layer and is owned primarily by P2.

AI agents working on ML must read:

* `docs/ML_SPEC.md`
* `docs/ML_GIS_CONTRACTS.md` §1
* relevant sections of `docs/API_SPEC.md` when understanding exposed outputs

### ML agents must not:

* create FastAPI routes
* modify frontend behavior
* implement GIS internals
* directly redesign the database schema
* invent API response structures

The ML implementation must expose behavior through the agreed ML interface/contract.

Model internals can change without changing the external contract, provided the contract remains satisfied.

---

## 8. GIS Boundary

GIS/spatial logic belongs to the GIS layer and is owned primarily by P3.

AI agents working on GIS must read:

* `docs/GIS_SPEC.md`
* `docs/ML_GIS_CONTRACTS.md` §2
* relevant sections of `docs/API_SPEC.md`

GIS responsibilities include things such as:

* coordinate handling
* distance/proximity calculations
* spatial candidate selection
* density calculations
* hotspot/spatial analysis
* GeoJSON generation

### GIS agents must not:

* implement frontend map components
* implement FastAPI routes
* modify ML model internals
* move spatial calculations into the frontend

The frontend displays spatial intelligence; it does not calculate the intelligence.

---

## 9. Backend Boundary

Backend engineering belongs primarily to P1/P5.

AI agents working on backend tasks must read:

* `docs/BACKEND_SPEC.md`
* `docs/API_SPEC.md`
* `docs/DATA_SCHEMA.md`
* `docs/ML_GIS_CONTRACTS.md`

The backend is responsible for:

* HTTP/API handling
* request validation
* authentication/authorization
* orchestration
* database access
* invoking ML through the ML interface
* invoking GIS through the spatial interface
* assembling contract-compliant responses
* alert decisioning/generation where specified
* audit logging where specified

### Backend agents must not:

* rewrite ML algorithms
* duplicate GIS calculations
* implement prediction logic in React
* silently modify shared contracts

Routers should remain thin.

Business workflow belongs in the appropriate backend/domain layer rather than being duplicated across endpoint handlers.

---

## 10. Frontend Boundary

Frontend work belongs primarily to P4.

AI agents working on frontend tasks must read:

* `docs/FRONTEND_SPEC.md`
* `docs/API_SPEC.md`
* `docs/ML_GIS_CONTRACTS.md` §2 when working with map/GeoJSON data

The frontend is responsible for:

* dashboards
* map visualization
* prediction visualization
* alerts UI
* filters
* tables/cards/charts
* loading/error/empty states
* role-aware presentation

### Frontend must not:

* calculate risk scores
* calculate crime/ATM distances
* implement prediction algorithms
* independently determine alert severity
* create backend-only business rules
* access ML internals directly

The backend is the source of truth for intelligence and authorization.

---

## 11. Feature Engineering Ownership

Feature engineering is intentionally divided by responsibility.

### P2 / ML

Owns:

* temporal features
* behavioral/transaction-derived features
* model-facing feature construction
* model training features
* model evaluation

### P3 / GIS

Owns:

* distance features
* proximity features
* spatial density
* hotspot/spatial features
* candidate location generation

### Backend / P1 + P5

Owns:

* orchestration
* retrieving the necessary data
* assembling the final model input according to `docs/ML_GIS_CONTRACTS.md`

Do not duplicate the same feature calculation in multiple layers.

---

## 12. Explainability Rules

Predictions must be explainable at the level actually supported by the implementation.

For the MVP, explanations should be based on the features/signals used by the model and the agreed contract.

Do not claim that the system provides advanced model explanations if only feature-based reasons or global feature importance are implemented.

SHAP or other advanced explainability methods are `[FUTURE]` unless explicitly adopted through `docs/ADRS.md`.

Explanations should help an investigator understand **why a location was ranked highly**, without presenting correlation as proof of criminal intent.

---

## 13. Confidence and Risk Scores

Do not assume that `risk_score` and `confidence` mean the same thing.

Use the definitions established in:

* `docs/ML_SPEC.md`
* `docs/ML_GIS_CONTRACTS.md`
* `docs/API_SPEC.md`

If those documents do not yet define a value's exact range or semantic meaning, **do not invent one in implementation**.

Similarly, do not copy threshold values from memory or from another project.

If a threshold is required but not defined, flag it as a contract/decision gap.

---

## 14. Alert Rules

A prediction and an alert are not automatically the same thing.

The system may:

1. generate/rank predictions
2. evaluate agreed alerting rules
3. create an alert only when the alert conditions are satisfied

Do not hard-code arbitrary alert thresholds.

Before implementing threshold-based alerting, verify the current rule in:

`docs/ADRS.md`

and the relevant ML/API specifications.

If the rule has not yet been formally decided, flag the issue instead of inventing a threshold.

---

## 15. Time Windows and Top-K

The system is intended to forecast **likely withdrawal locations within a defined future time window**.

The exact MVP horizon and Top-K configuration must follow the current architecture/contracts.

Do not independently choose values such as:

* 1 hour
* 3 hours
* 6 hours
* 24 hours
* Top-5
* Top-10

unless the current project documents explicitly define them.

If different documents disagree, stop and flag the inconsistency for P1.

Do not silently choose a value.

---

## 16. Authentication and Security

Security is part of the MVP architecture, but it should remain proportional to the hackathon scope.

Expected MVP concepts include:

* authentication
* JWT/session handling as specified
* role-based access control
* least privilege
* audit logging
* appropriate handling of sensitive transaction data
* secure configuration/secrets

Do not introduce enterprise security infrastructure unless explicitly approved.

Examples of out-of-scope MVP security infrastructure:

* full zero-trust architecture
* PKI infrastructure
* dedicated SOC
* service mesh security
* enterprise IAM platform
* production-grade secrets-management platform

Security claims must match what is actually implemented.

---

## 17. Data and Privacy

The MVP should use synthetic, anonymized, or otherwise safe development data.

Do not introduce real personal financial information into the repository.

Do not commit:

* real account numbers
* real customer identities
* passwords
* API keys
* JWT secrets
* private credentials
* sensitive transaction data

Use environment variables or appropriate secret handling for credentials.

If realistic data is required for testing, generate synthetic data that preserves the required structure without exposing real individuals.

---

## 18. AI-Agent Coding Rules

When using an AI coding agent:

### Before editing

1. Read this file.
2. Read `docs/INTEGRATION_SPEC.md`.
3. Read `README.md`.
4. Read `docs/ARCHITECTURE.md`.
5. Read the task-specific specification.
6. Read the relevant shared contracts.

### While editing

* Stay inside the task's ownership boundary.
* Reuse existing interfaces.
* Follow existing naming conventions.
* Do not create duplicate implementations.
* Do not add libraries without checking the fixed MVP stack.
* Do not modify unrelated files merely because they are nearby.
* Do not silently change contracts.
* Do not turn `[FUTURE]` capabilities into MVP requirements.
* Keep the implementation as simple as the MVP requires.

### Before finishing

* Run the relevant tests/checks.
* Verify imports and paths.
* Verify API field names against the contract.
* Verify database fields against `DATA_SCHEMA.md`.
* Verify ML inputs/outputs against `ML_GIS_CONTRACTS.md`.
* Verify GeoJSON against the GeoJSON contract.
* Check that no secrets or sensitive data were introduced.
* Check that no unrelated files were modified.
* Report any unresolved integration/contract issue instead of hiding it.

---

## 19. Cross-Team Changes

If implementation requires changes outside your assigned area:

**Do not silently make the change.**

Instead identify:

* what boundary is affected
* why the change is required
* which contract/spec is affected
* which owner should approve it

P1 owns architecture/integration decisions.

P1/P5 own the shared API/database contracts according to `README.md`.

P2/P3 own the ML/GIS contracts according to `README.md`.

Major architectural changes should be recorded in:

`docs/ADRS.md`

---

## 20. Git and Branching

The project follows:

```text
feature/* → integration → main
```

Expected feature branches include:

```text
feature/backend
feature/docs
feature/frontend
feature/gis
feature/ml
```

Do not develop directly on `main`.

Do not bypass `integration` for normal feature work.

Documentation changes should normally be made on:

```text
feature/docs
```

and then merged into:

```text
integration
```

before reaching `main`.

Keep commits focused and descriptive.

---

## 21. What Not to Assume

AI agents must not assume that something is implemented merely because it is documented.

The documentation describes a mixture of:

* `[IMPLEMENTED]`
* `[MVP TARGET]`
* `[FUTURE]`

Always verify the current repository state before claiming a feature works.

Similarly, do not assume that:

* a model is trained because a model file is mentioned
* authentication works because JWT is documented
* alerts are delivered because an alert API exists
* real-time monitoring exists because continuous monitoring is part of the architecture
* real LEA/bank integration exists because it is described as a future capability
* a prediction is accurate merely because a risk score is high

The demo must distinguish clearly between implemented prototype behavior and future production capabilities.

---

## 22. When Documents Conflict

Use this priority:

1. Explicit current architecture/contract decision approved by P1
2. Shared contracts
3. `docs/ADRS.md`
4. `docs/ARCHITECTURE.md`
5. Role-specific specifications
6. README/project overview
7. Existing implementation code
8. AI-agent assumptions

If two authoritative documents conflict, **do not guess**.

Report the conflict and ask P1 to resolve it.

Never silently choose whichever interpretation is easier to implement.

---

## 23. Final Principle

This repository is being built as a focused SIH prototype.

The goal is not to demonstrate how many technologies can be added.

The goal is to demonstrate a coherent chain:

```text
Cybercrime Event
      ↓
Relevant Signals
      ↓
Feature Engineering
      ↓
Candidate Withdrawal Locations
      ↓
ML Risk Scoring
      ↓
Top-K Ranking
      ↓
Time-Bounded Prediction
      ↓
Explainable Intelligence
      ↓
Authorized Dashboard / Alert
      ↓
Timely Intervention
```

Every implementation decision should strengthen that chain.

**Build only what is necessary, follow the contracts, respect ownership boundaries, and never present a future capability as an implemented one.**
