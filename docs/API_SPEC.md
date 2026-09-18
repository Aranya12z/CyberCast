# API_SPEC.md — REST API Contract
**Owner:** P1 (architecture) + P5 (implementation). **All other roles: READ ONLY.**
**Rule:** If your implementation needs a field this doc doesn't have, **propose an addition here first** (via P1) — do not silently invent response shapes. Frontend (P4) should be able to build entirely against mock JSON that matches this file, in parallel with backend/ML/GIS work.

Status tags used below: `[IMPLEMENTED]` `[MVP TARGET]` `[FUTURE]`. Default assume `[MVP TARGET]` unless marked otherwise.

---

## Conventions
- Base path: `/api`
- Auth: Bearer JWT in `Authorization` header (see Auth group)
- All timestamps: ISO 8601 UTC
- All coordinates: `{ "lat": float, "lng": float }` (WGS84)
- Errors: `{ "error": { "code": "string", "message": "string", "details": {} } }` with appropriate HTTP status

## Endpoint Groups

### `/api/auth/*` `[MVP TARGET]`
- `POST /api/auth/login` → `{ access_token, token_type, role }`
- `POST /api/auth/logout`
- `GET /api/auth/me` → `{ user_id, name, role }`

Not yet implemented — see `BACKEND_SPEC.md` Auth & RBAC section. Do not
describe this as working in a demo until it actually is.

### `/api/crimes/*`
- `GET /api/crimes` — list/filter complaints
- `GET /api/crimes/{crime_id}` → crime detail
- `POST /api/crimes` — create/ingest a complaint (MVP: manual or CSV-seeded)

Crime object:
```json
{
  "crime_id": "string",
  "crime_type": "string",
  "timestamp": "ISO8601",
  "location": { "lat": 0.0, "lng": 0.0 },
  "amount": 0.0
}
```

### `/api/atms/*`
- `GET /api/atms` — list ATMs (optional bbox/radius filter)
- `GET /api/atms/{atm_id}`

ATM object:
```json
{ "atm_id": "string", "location": { "lat": 0.0, "lng": 0.0 }, "bank": "string", "area": "string" }
```

### `/api/transactions/*`
- `GET /api/transactions` — filter by atm_id / account_id / time range (MVP: synthetic data)

Transaction object:
```json
{ "transaction_id": "string", "atm_id": "string", "timestamp": "ISO8601", "amount": 0.0, "account_id": "string" }
```

### `/api/predictions/*` — **the core contract**
- `POST /api/predictions/{crime_id}` — trigger prediction generation (Mode A, synchronous MVP flow per `ARCHITECTURE.md` §6)
- `GET /api/predictions/{crime_id}` — retrieve most recent prediction run for a crime

Response:
```json
{
  "crime_id": "string",
  "generated_at": "ISO8601",
  "model_version": "string",
  "predictions": [
    {
      "atm_id": "string",
      "bank": "string",
      "area": "string",
      "location": { "lat": 0.0, "lng": 0.0 },
      "risk_score": 0.0,
      "confidence": 0.0,
      "predicted_window": { "start": "ISO8601", "end": "ISO8601" },
      "explanation": [
        { "feature": "distance_from_crime", "value": 0.0, "contribution": "high|medium|low" }
      ]
    }
  ],
  "status": "ok | insufficient_confidence | insufficient_evidence"
}
```
**Rule (from `ARCHITECTURE.md` §10):** if the model cannot produce a confident prediction, `status` must reflect that honestly — never fabricate a high-risk result to fill the response.

`risk_score` vs `confidence` semantics: see `ARCHITECTURE.md` §4 — they are independent values, not two names for one number. `predicted_window` is fixed at 6 hours from `generated_at` for MVP (`ADRS.md` ADR-005).

### `/api/alerts/*`
- `GET /api/alerts` — list, filterable by severity/status
- `POST /api/alerts/{alert_id}/acknowledge`

Alerts are generated per `ADRS.md` ADR-006 (`risk_score >= 0.4 AND confidence >= 0.5`, with severity mapped from those same thresholds) — this endpoint group only lists/acknowledges what `alert_generation.py` already created; it doesn't recompute severity.

Alert object:
```json
{
  "alert_id": "string",
  "crime_id": "string",
  "atm_id": "string",
  "severity": "low|medium|high",
  "created_at": "ISO8601",
  "status": "new|acknowledged|resolved",
  "channel": "dashboard|mock_sms|mock_email"
}
```

### `/api/dashboard/*`
- `GET /api/dashboard/summary`

```json
{
  "active_alerts": 0,
  "high_risk_predictions": 0,
  "prediction_stats": {
    "total_predictions_run": 0,
    "avg_confidence": 0.0,
    "insufficient_evidence_rate": 0.0
  },
  "recent_activity": [
    {
      "type": "prediction_generated | alert_created | alert_acknowledged",
      "timestamp": "ISO8601",
      "crime_id": "string",
      "summary": "string"
    }
  ]
}
```
All four `prediction_stats` and `recent_activity` fields are simple
aggregate queries over `predictions`/`prediction_results`/`alerts` — no
new business logic belongs in this endpoint (`BACKEND_SPEC.md`).

### `/api/intelligence/*`
- `GET /api/intelligence/{crime_id}`

```json
{
  "crime_id": "string",
  "crime": { "...": "the crime object, per the /api/crimes shape above" },
  "latest_prediction": {
    "generated_at": "ISO8601",
    "model_version": "string",
    "status": "ok | insufficient_confidence | insufficient_evidence",
    "top_result": {
      "atm_id": "string", "risk_score": 0.0, "confidence": 0.0,
      "predicted_window": { "start": "ISO8601", "end": "ISO8601" }
    }
  },
  "evidence": [
    { "feature": "distance_from_crime", "value": 0.0, "contribution": "high|medium|low" }
  ],
  "related_alerts": [
    { "alert_id": "string", "severity": "low|medium|high", "status": "new|acknowledged|resolved" }
  ],
  "summary": "string — short human-readable text, MVP: template-generated from the fields above, not model-generated free text unless an ADR says otherwise"
}
```
`evidence` is the winning candidate's `prediction_features` rows
(`DATA_SCHEMA.md`), reused as-is — this endpoint assembles existing data,
it doesn't generate new explanation content (`intelligence_generation.py`,
`BACKEND_SPEC.md`).

## GeoJSON Response (used by `/api/predictions` map variant and `/api/atms?format=geojson`)
See `ML_GIS_CONTRACTS.md` §GIS↔Backend Contract for the authoritative FeatureCollection shape. Do not redefine it here — this file only points to it to avoid drift.

## What is NOT in MVP (`[FUTURE]`)
- Real LEA/bank/I4C system integration endpoints
- Streaming/webhook ingestion endpoints
- Multi-tenant/jurisdiction routing

## Change process
Any change to a request/response shape = edit this file first, note it in `ADRS.md` if it's a significant structural change, then implement. Frontend, ML, and GIS agents should treat a mismatch between this file and running code as a **bug to report**, not something to silently work around by inventing their own shape.
