# ARCHITECTURE.md — Master System Architecture
**Owner:** P1 (You). **Role:** Architecture + integration authority. You are the only person/agent allowed to change this file.
**Audience:** You, and any AI agent asked to reason about or review the whole system. Other team members should treat this as read-only context, not an implementation task list for their own module.

---

## 1. North Star
> An intelligence layer that helps existing cybercrime and financial systems act **before the next withdrawal happens.**

Never let the system read as: another complaint portal, another crime dashboard, "just an ML model," or an ATM heatmap. Every architectural artifact should visibly connect: **complaint/event → features → prediction → ranked locations → risk/confidence/explanation → GIS + alert → stakeholder action.**

## 2. Full Data Flow (canonical)
```
Historical data + New complaint/event + ATM/location data + Transaction/activity data
        ↓
Data preprocessing
        ↓
Feature engineering (distance_from_crime, hour_of_day, day_of_week, amount,
  ATM historical risk, txns_last_1h, txns_last_6h, nearby_crime_density,
  withdrawal_frequency, temporal/geospatial behavioural features)
        ↓
Prediction engine
        ↓
Candidate ATM/location generation
        ↓
Risk scoring → Ranking → Top-K likely withdrawal locations
        ↓
Prediction record (risk score, confidence, predicted window, explanation)
        ↓
GIS dashboard        +        Alert engine
        ↓                            ↓
Investigators          LEA / bank / FI notification
```

## 3. Layered Architecture

| Layer | Tech | Responsibility | Owner |
|---|---|---|---|
| L1 Presentation | React + Leaflet + Recharts | Dashboard, GIS map, risk cards, alerts, filters — **no prediction logic** | P4 |
| L2 API/Application | FastAPI | Auth, routing, validation, orchestration — coordinates domain services, not a god-file | P1/P5 |
| L3 Domain/Intelligence | Python (backend) | Complaint processing, transaction analysis, risk scoring, hotspot orchestration, alert generation | P1/P5 |
| L4 ML/Predictive | scikit-learn (RF/XGBoost) | Feature generation, inference, ranking, confidence, model swap-ability | P2 |
| L5 Geospatial | GeoPandas/GeoJSON | Distance, proximity, density, hotspot detection, GeoJSON generation | P3 |
| L6 Data | PostgreSQL | Structured storage: crimes, atms, transactions, predictions, alerts, users, audit_logs | P1/P5 |

**Hard rule:** L4 (ML) is only ever called through a `Model Interface`, never hard-coded into API routes. L5 (spatial) is only ever called through the spatial service — P4 (frontend) must never compute spatial risk itself; it only renders what P3/backend already computed.

## 4. Prediction Model (Top-K, not single-ATM)
Do NOT architect around "predicts one exact ATM." Architecture is:
**Candidate locations → scoring → ranking → Top-K predictions.**

Each prediction object must contain, at minimum: `atm_id`, `risk_score`, `confidence`, `predicted_window`, `explanation`. MVP horizon is fixed at **6 hours** — see `ADRS.md` ADR-005. The system produces **risk-ranked intelligence**, never a "guaranteed withdrawal" claim.

**Semantics — `risk_score` vs `confidence` (do not conflate these):**
- `risk_score` [0,1] — the model's estimated likelihood that this candidate ATM is the actual withdrawal location within `predicted_window`. This is the ranking key for Top-K.
- `confidence` [0,1] — the model's certainty *in that risk_score estimate itself*, driven by how much relevant historical/transaction signal supported the calculation for this specific candidate. A prediction can be high `risk_score` but low `confidence` (a strong pattern match on thin data) — such a result must never be presented or acted on with the same weight as a high-risk/high-confidence one.
- Two distinct, both-documented thresholds use these values: the model's own floor for whether to return a prediction *at all* (`ML_SPEC.md`, `status: insufficient_confidence`), and the backend's separate floor for whether a returned prediction becomes an *alert* (`ADRS.md` ADR-006). Do not merge these into one number.

## 5. Two Operating Modes
- **Mode A — Event Triggered:** new complaint → historical pattern retrieval → nearby ATM identification → feature calc → scoring → Top-K → risk/confidence/explanation → alert if threshold met.
- **Mode B — Continuous Monitoring:** transaction stream → anomaly/risk analysis → behavioural pattern eval → candidate cash-out event → scoring → alert/intelligence. **MVP may simulate this with synthetic/mock data rather than real streaming infrastructure.**

## 6. Synchronous MVP (no event bus yet)
```
POST /api/predictions/{crime_id}
  1. retrieve complaint
  2. retrieve relevant ATM data
  3. retrieve relevant historical/transaction data
  4. generate features
  5. run model
  6. rank candidate ATMs
  7. save predictions
  8. return Top-K results
```
Event queues / streaming / async workers / message brokers are **FUTURE**, not MVP. Do not introduce them without an ADR proving a concrete MVP-blocking problem.

## 7. Modular Monolith Decision
**MVP = modular monolith**, not microservices. Reasons: small team, limited time, easier debugging/deployment/demo, lower integration overhead. Modules must still have clean boundaries (L2–L6 above) so future extraction into services (ingestion / prediction / geospatial / alert / identity / reporting) remains possible without a rewrite.

## 8. Security & Auditability (supporting layer, not the centerpiece)
- AuthN, RBAC (roles: investigator/LEA, bank/FI analyst, administrator), encryption in transit, audit logs, least-privilege access.
- Audit log entries: `event_id, user, action, timestamp, resource, metadata`. The architecture must be able to answer: **"Who did what, when, and to which intelligence record?"**
- Required audit events (canonical action names used in code): `login`, `logout`, `prediction_generated`, `prediction_viewed`, `alert_generated`, `alert_acknowledged`, `intelligence_viewed`, `data_modification`, `administrative_action`. Note: the intelligence event is named `intelligence_viewed` (not "intelligence report created") because the report is assembled on-the-fly from existing data at GET time — there is no separate creation step.
- Explicitly out of scope for MVP: SOC infrastructure, zero-trust enterprise architecture, complex PKI, military-grade systems, advanced pentest infra. These are FUTURE only.

## 9. Explainability
Every prediction carries feature-based reasons (e.g., high historical ATM risk, proximity to crime, unusual recent activity, high nearby crime density, temporal similarity, abnormal withdrawal frequency). SHAP/advanced explainability = FUTURE, not MVP. Never invent explanation mechanisms that aren't actually implemented.

## 10. Failure & Edge-Case Handling (must be designed for, not bolted on)
Missing coordinates, no nearby ATM, insufficient historical data, no transaction activity, duplicate complaint, invalid transaction data, model unavailable, low-confidence prediction, prediction outside horizon, DB failure, notification failure, malformed requests. **Principle:** if confidence is too low, return `insufficient_confidence` / `insufficient_evidence` — never manufacture a high-risk prediction to look impressive.

## 11. Observability (MVP scope)
Application logs, API error logs, prediction generation logs, alert generation logs, audit logs. Centralized logging/metrics/tracing/model monitoring = FUTURE.

## 12. Scalability — MVP vs Future (never blur these)

**MVP:** synthetic/mock data → PostgreSQL → FastAPI → embedded/in-process ML inference → React dashboard.

**Future/National scale:** multiple real data sources → secure ingestion layer → event/stream processing → scalable analytics → dedicated ML inference service → geospatial service → centralized/federated intelligence → alert/notification infrastructure → stakeholder integrations (I4C, banks, LEAs). Concerns to name explicitly as future-only: millions of transactions, real-time processing, multi-jurisdiction, model retraining/versioning, data governance, high availability.

## 13. Data Privacy
Minimize personal data, use synthetic/anonymized data for MVP, RBAC, encrypted comms, controlled DB access, auditability, retention policy. **Never use real personal financial information in the MVP.**

## 14. Documentation Set to Maintain
`README.md`, `ARCHITECTURE.md` (this file), `INTEGRATION_SPEC.md`, `DATA_SCHEMA.md`, `API_SPEC.md`, `ML_SPEC.md`, `GIS_SPEC.md`, `BACKEND_SPEC.md`, `FRONTEND_SPEC.md`, `ML_GIS_CONTRACTS.md`, `ADRS.md`, `SETUP.md`. Architecture decisions live in `ADRS.md`, not only in chat history.

## 15. Architecture Review Checklist (run before approving any change)
- **Functionality:** does every deliverable have an architectural home? Does the full vertical slice work end-to-end?
- **Integration:** are interfaces/API contracts explicit? Can frontend/ML/GIS/backend be built independently against the contracts?
- **Data:** is the flow clear? Are ownership/schemas clear? Are sensitive fields controlled?
- **ML:** is inference isolated behind an interface? Are models swappable? Are predictions ranked with correct confidence semantics?
- **GIS:** is spatial logic separated from map UI? Is the GeoJSON/API output defined?
- **Security:** authN, authZ, auditability, encryption all accounted for?
- **Reliability:** are missing-data/failure paths handled?
- **Scalability:** can MVP evolve without a rewrite?
- **SIH feasibility:** can a small team actually build and demo this?
- **Judge defensibility:** can every claim be explained honestly (see `INTEGRATION_SPEC.md` §5, Judge-Defensibility Checklist)?

## 16. Anti-overengineering Rule
Before adopting any new technology, ask: **"What concrete problem does this solve that the current architecture cannot?"** No strong answer → reject it. Optimize for *credible, demonstrable, defensible* over *technologically impressive*.

## 17. Team Ownership (do not cross these lines without going through P1)
- **P1 (you):** overall architecture + integration; must understand every component enough to integrate them.
- **P2:** ML — feature pipeline, model, inference contract, evaluation.
- **P3:** GIS — spatial data, geospatial processing, distance/proximity, hotspots, GeoJSON generation.
- **P4:** Frontend — React structure, components, dashboard, map UI, API consumption only.
- **P5:** Backend engineering — FastAPI, endpoints, configuration, integration, technical testing.
- **P6:** Domain/product — requirements, operational workflow, domain validation, actionability, limitations, real-world scenarios. **Does not own technical architecture.**
