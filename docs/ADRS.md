# ADRS.md — Architecture Decision Records
**Owner:** P1. New major decisions get appended here, never only discussed in chat.

---

### ADR-001
**Decision:** Use a modular monolith for the MVP, not microservices.
**Context:** Small student team, limited SIH timeline, need for easy debugging/demo.
**Chosen approach:** Single FastAPI application with clearly separated internal modules (API / domain / ML interface / spatial interface / data), single PostgreSQL database.
**Alternatives:** Microservices per layer (ingestion, prediction, geospatial, alert, identity).
**Why chosen:** Lower integration overhead, faster to build and demo, easier for a small team to debug end-to-end.
**MVP impact:** All modules deployed together; module boundaries enforced in code structure, not network boundaries.
**Future impact:** Clear module boundaries (see `BACKEND_SPEC.md` directory structure) make future extraction into services (ingestion/prediction/geospatial/alert/identity/reporting) possible without a full rewrite.

---

### ADR-002
**Decision:** Use PostgreSQL (no PostGIS) for the MVP.
**Context:** Need structured storage for crimes/ATMs/transactions/predictions/alerts; spatial needs for MVP are basic (distance/proximity, not complex spatial queries).
**Chosen approach:** Standard PostgreSQL with lat/lng columns; distance/proximity computed in the application layer (GeoPandas) rather than in the database.
**Alternatives:** PostGIS-enabled PostgreSQL.
**Why chosen:** Avoids extra setup/operational complexity for the MVP; application-layer spatial logic is sufficient at MVP data volumes.
**MVP impact:** GIS layer (`GIS_SPEC.md`) does distance/proximity math in Python.
**Future impact:** Re-evaluate PostGIS if spatial query volume/complexity grows at national scale (see `ARCHITECTURE.md` §12, Scalability — MVP vs Future).

---

### ADR-003
**Decision:** Synchronous, request-triggered prediction flow for the MVP (no event queue).
**Context:** Mode A (event-triggered) and Mode B (continuous monitoring) are both conceptually needed, but MVP timeline doesn't support real streaming infra.
**Chosen approach:** `POST /api/predictions/{crime_id}` runs the full pipeline synchronously; Mode B (continuous monitoring) is simulated with synthetic/mock data rather than a real event stream.
**Alternatives:** Kafka/message broker-based async pipeline.
**Why chosen:** Matches small-team/short-timeline constraints; still demonstrates the full intelligence pipeline end-to-end.
**MVP impact:** No message brokers, no async workers.
**Future impact:** Event/streaming infrastructure is the clear next step for real-time, high-volume national deployment (see `ARCHITECTURE.md` §12, Scalability — MVP vs Future).

---

### ADR-004
**Decision:** Predictions are Top-K ranked candidate locations, not a single predicted ATM.
**Context:** A single-ATM prediction claim is not honestly defensible given data/model uncertainty.
**Chosen approach:** Candidate ATM generation → feature scoring → ranking → Top-K output, each with risk score, confidence, predicted window, and explanation.
**Alternatives:** Single best-guess ATM prediction.
**Why chosen:** More honest, more useful to investigators (multiple leads), and more defensible under judge Q&A about false positives.
**MVP impact:** API, ML, and GIS contracts all built around a list of ranked predictions, not one value.
**Future impact:** K and horizon (1h/3h/6h/24h) can be tuned or made configurable per stakeholder at scale.

### ADR-005
**Decision:** MVP prediction horizon is fixed at **6 hours**.
**Context:** `ARCHITECTURE.md` §4 requires the horizon (1h/3h/6h/24h) to be explicitly chosen and documented, not left implicit. This was never actually decided in writing.
**Chosen approach:** `predicted_window.start = generated_at`, `predicted_window.end = generated_at + 6h`, applied uniformly to every prediction result in the MVP. No per-crime-type variation yet.
**Alternatives:** 1h (too narrow given sparse synthetic MVP data — poor recall); 24h (too diffuse to be "actionable," weak judge defensibility).
**Why chosen:** long enough to give investigators/banks a real response window, short enough that recency-based features (`txns_last_1h`, `txns_last_6h`, `withdrawal_frequency`) stay meaningful.
**MVP impact:** all `predicted_window` fields across `API_SPEC.md`, `ML_GIS_CONTRACTS.md`, and `DATA_SCHEMA.md` (`prediction_results` table) use this fixed 6h value.
**Future impact:** horizon becomes a configurable value per crime type/jurisdiction once there's enough historical data to tune it properly.

---

### ADR-006
**Decision:** An alert is generated for a `prediction_result` only when `risk_score >= 0.4 AND confidence >= 0.5`.
**Context:** `alert_generation.py` (`BACKEND_SPEC.md`) had no defined trigger rule. Without one, either every Top-K row becomes an alert (defeats the purpose of ranking) or the threshold gets invented ad hoc during implementation — exactly what contract-first is meant to prevent.
**Chosen approach:** severity mapping, reusing the same vocabulary as `GIS_SPEC.md`'s `risk_category` buckets:
| condition | severity |
|---|---|
| `risk_score >= 0.7` and `confidence >= 0.5` | `high` |
| `0.4 <= risk_score < 0.7` and `confidence >= 0.5` | `medium` |
| anything else | no alert created |
**Alternatives:** alert on every Top-K result (noisy, undermines the "risk-ranked intelligence" positioning from the North Star); alert on `risk_score` alone with no confidence floor (violates `ARCHITECTURE.md` §10's "never fabricate a high-risk prediction" principle — a high risk_score on thin data shouldn't carry the same weight as one backed by real signal).
**Why chosen:** one severity vocabulary system-wide (GIS map colors and alert severity now always agree), and the confidence floor keeps the alert engine from firing on guesses the model itself isn't sure about.
**Note — this is a distinct threshold from the model's own `insufficient_confidence` floor** (see `ML_SPEC.md`): a prediction can clear the model's floor and still be too weak to alert on. Two separate, both-documented thresholds, not one overloaded number.
**MVP impact:** `alert_generation.py` applies this rule to every `prediction_result` row after ranking; `DATA_SCHEMA.md`'s `alerts.severity` is populated from this mapping, never invented per-implementation.
**Future impact:** thresholds become tunable per crime-type/jurisdiction once there's enough data to calibrate against real outcomes.

<!-- Add new ADRs below this line, following the same template. -->

### ADR-XXX (template)
**Decision:**
**Context:**
**Chosen approach:**
**Alternatives:**
**Why chosen:**
**MVP impact:**
**Future impact:**
