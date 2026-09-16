# Predictive Analytics Framework for Cybercrime Cash-Withdrawal Forecasting

**Smart India Hackathon 2026**

A predictive intelligence layer that sits over the existing cybercrime and
financial ecosystem to forecast likely cash-withdrawal locations after a
cybercrime complaint — enabling investigators and financial institutions
to act **before** a withdrawal happens, not just after.

> This is not a complaint portal, not a generic crime dashboard, and not
> "just an ML model." It's the intelligence layer that turns a complaint
> into ranked, explained, time-windowed, actionable predictions.

---

## Problem statement

Development of a Predictive Analytics Framework for Cybercrime Complaints
to Forecast Likely Cash Withdrawal Locations in Advance, Enabling
Generation of Actionable Intelligence for Timely and Proactive Cybercrime
Intervention.

We are **not** rebuilding NCRP. This system consumes complaint,
transaction, ATM, and geospatial data and produces risk-ranked
intelligence for existing stakeholders to act on.

## How it works, conceptually

```
Cybercrime complaint + historical patterns + transaction behaviour
+ ATM/location data + temporal & geospatial context
        |
Data processing → Feature engineering → Predictive analytics
        |
Ranked, risk-scored, confidence-scored candidate withdrawal locations
        |
GIS visualization + explanation + alerts to investigators / banks / LEAs
```

## System architecture

```
React dashboard  (presentation)
      |
FastAPI backend  (auth, routing, orchestration)
      |
Domain / intelligence layer
      |-- ML layer            (feature gen, inference, ranking)
      |-- Geospatial layer    (proximity, hotspots, GeoJSON)
      |-- Alert layer         (thresholds, notifications)
      |
PostgreSQL  (single database)
```

MVP is a **modular monolith** — one deployable FastAPI app with strict
internal module boundaries, chosen deliberately over microservices for a
small team on a hackathon timeline. Full rationale in
[`ARCHITECTURE.md`](./ARCHITECTURE.md).

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React, Tailwind CSS, React-Leaflet, Recharts |
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| ML | scikit-learn, Random Forest / XGBoost |
| Geospatial | GeoJSON, GeoPandas |
| Testing / integration | Postman, pytest, GitHub |

Deliberately **excluded** from the MVP (documented, not forgotten):
Kubernetes, Kafka, Redis, Elasticsearch, Spark, PostGIS, microservices,
GraphQL, service meshes, federated learning, full MLOps. See
`ARCHITECTURE.md` for what moves from "future" to "MVP" and why.

## Repository structure

```
frontend/         React dashboard
backend/
  routes/          FastAPI endpoints
  models/          SQLAlchemy models
  schemas/         Pydantic request/response models
  auth/            JWT auth + RBAC
  domain/          geospatial + alert + orchestration logic
  ml/              feature pipeline + model + inference
  db/              session + Alembic migrations
  tests/
docs/              all specs and guides — see below
```

## Documentation

Every architectural decision, contract, and scope boundary is written
down — nothing lives only in chat or in someone's head. Read the relevant
doc **before** writing code in that area.

| Document | What it defines |
|---|---|
| `ARCHITECTURE.md` | System overview, ADRs, layer boundaries |
| `DATA_SCHEMA.md` | PostgreSQL tables and relationships |
| `API_SPEC.md` | REST endpoint contract (request/response shapes) |
| `ML_SPEC.md` | ML ↔ backend interface contract |
| `GIS_SPEC.md` | Geospatial ↔ frontend interface (GeoJSON) |
| `FRONTEND_SPEC.md` | React app structure, pages, state |
| `ALERT_SPEC.md` | Alert thresholds, severity, notification rules |
| `SECURITY_SPEC.md` | Auth, RBAC permission matrix, audit events |
| `FRONTEND_AGENT.md` | Scope for the frontend AI coding agent |
| `ML_AGENT.md` | Scope for the ML AI coding agent |
| `INTEGRATION_AGENT.md` | Scope for the geospatial/alert/orchestration AI agent |
| `BACKEND_GUIDE.md` | Backend implementation guide |

**Contracts win.** If an implementation conflicts with a spec, the spec
wins unless the team deliberately changes it via a new ADR in
`ARCHITECTURE.md` — never a silent edit.

## Key architectural decisions (full detail in `ARCHITECTURE.md`)

- **Prediction horizon: 6 hours** from complaint intake.
- **Synchronous MVP** — no event streaming; `POST /api/predictions/{crime_id}`
  runs the full pipeline in one request.
- **Modular monolith**, not microservices, for MVP.
- **Single PostgreSQL**, no PostGIS yet — GeoJSON + GeoPandas is enough
  at MVP scale.
- **Top-K ranked candidates**, never a single "the" predicted ATM — the
  system produces risk-ranked intelligence, not a guarantee.
- **Never fabricate a high-confidence prediction** when evidence is
  weak — the system returns an explicit "insufficient confidence"
  response instead.

## What's implemented vs. planned

- **Implemented**: see current repo state / latest demo — kept honest,
  not aspirational.
- **MVP target**: everything specified in the docs above.
- **Future / national scale**: event/stream ingestion, PostGIS, model
  versioning + drift monitoring, real LEA/bank/I4C integrations,
  multi-jurisdiction data governance. Explicitly out of scope for this
  build — never presented as already working.

All data used in this project is **synthetic**. No real personal or
financial information is used at any stage.

## Team

| Role | Owns |
|---|---|
| Architecture & backend | System design, FastAPI, auth/RBAC, DB, deployment |
| Frontend | React dashboard, GIS map UI |
| ML | Feature pipeline, model, prediction service |
| Integration | Geospatial functions, alert engine, orchestration layer |
| Domain / product | Requirements validation, real-world scenario review |

## Getting started

```bash
# backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# frontend
cd frontend
npm install
npm run dev
```

(Full environment setup, seed data, and migration steps to be added to
`SETUP.md` as the implementation lands.)

## License

TBD.
