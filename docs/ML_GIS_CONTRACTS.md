# ML_GIS_CONTRACTS.md — Cross-team Interface Contracts
**Owners:** P2 (ML side) + P3 (GIS side), reviewed by P1. **P5 (backend) implements against these; P4 (frontend) never calls ML/GIS directly — only through the backend API in `API_SPEC.md`.**

This file exists so P2 and P3 can build against a fixed interface without waiting on each other or on the backend, and so the backend never needs to know which model or spatial library is behind the interface.

---

## 0. Semantics — `risk_score` vs `confidence`

Canonical definition lives in `ARCHITECTURE.md` §4 — read it before implementing either side of this contract. Summary: `risk_score` is the ranking key (likelihood this ATM is the withdrawal location); `confidence` is a separate certainty measure on that estimate. A high-risk/low-confidence result is a real, distinct case your code must be able to represent — never collapse the two into one number.

## 1. ML ↔ Backend Contract

**Principle:** the backend calls a `PredictionService`, which calls a `ModelInterface`. The backend must never know or care whether the model is Random Forest, XGBoost, or something else later. This lets P2 swap/retrain models without touching backend or API code.

### Input (backend → ML)

**Feature-generation ownership, made explicit (this was previously ambiguous — see `ARCHITECTURE.md` for context):**
- **Spatial features** (`distance_from_crime`, `nearby_crime_density`) — computed by GIS's `compute_spatial_features()` (`GIS_SPEC.md`), attached **per candidate ATM** by the backend before calling ML. These are never a single global object — each candidate has its own distance/density.
- **`atm_historical_risk`** — a stored, offline-updated value read straight from the `atms.historical_risk_score` column (`DATA_SCHEMA.md`); the backend attaches it per candidate. Not computed by GIS or ML at request time.
- **Temporal + behavioral features** (`hour_of_day`, `day_of_week`, `txns_last_1h`, `txns_last_6h`, `withdrawal_frequency`) — computed by the **ML module itself**, inside `predict()`, from the raw `crime.timestamp` and raw `recent_transactions` list below. The backend does **not** pre-aggregate these and pass them in — that would duplicate logic in two places and risk them drifting out of sync. Only raw transaction rows cross this boundary; aggregation is ML's job.

```json
{
  "crime": { "crime_id": "string", "crime_type": "string", "timestamp": "ISO8601", "location": {"lat":0.0,"lng":0.0}, "amount": 0.0 },
  "candidate_atms": [
    {
      "atm_id": "string",
      "location": {"lat":0.0,"lng":0.0},
      "atm_historical_risk": 0.0,
      "spatial_features": { "distance_from_crime": 0.0, "nearby_crime_density": 0.0 }
    }
  ],
  "recent_transactions": [ { "atm_id": "string", "timestamp": "ISO8601", "amount": 0.0 } ]
}
```

`recent_transactions` is the raw, unaggregated list (all candidate ATMs'
transactions in the relevant lookback window) — ML filters per `atm_id`
and computes `txns_last_1h`/`txns_last_6h`/`withdrawal_frequency` itself.

### Output (ML → backend)
```json
{
  "model_version": "string",
  "predictions": [
    {
      "atm_id": "string",
      "risk_score": 0.0,
      "confidence": 0.0,
      "predicted_window": { "start": "ISO8601", "end": "ISO8601" },
      "explanation": [ { "feature": "string", "value": 0.0, "contribution": "high|medium|low" } ]
    }
  ],
  "status": "ok | insufficient_confidence | insufficient_evidence"
}
```

**Rules:**
- P2 owns: feature generation, model loading, inference, ranking, confidence, model versioning, evaluation.
- P2 must not decide HTTP status codes, auth, or response envelope — that's backend's job. P2 returns the object above; backend wraps it into the `API_SPEC.md` response.
- If confidence is below the documented threshold, return `status: insufficient_confidence` and an empty or advisory `predictions` list — do not force a Top-K list into existence.
- Any change to this input/output shape must be updated here first, and flagged to P1 and P5.

## 2. GIS ↔ Backend Contract

**Principle:** P3 owns all spatial computation (distance, proximity, density, hotspot detection). The backend exposes P3's output as GeoJSON. **P4 (frontend) never computes spatial risk itself** — it only renders what it's given.

### GeoJSON FeatureCollection (returned by backend, computed by P3's spatial service)
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates": [longitude, latitude] },
      "properties": {
        "atm_id": "string",
        "risk_score": 0.0,
        "confidence": 0.0,
        "predicted_window": { "start": "ISO8601", "end": "ISO8601" },
        "risk_category": "low|medium|high",
        "explanation": ["string"]
      }
    }
  ]
}
```

**Data dependency (previously implicit — made explicit here):** the `SpatialInterface` never queries the database itself. The backend fetches the relevant `atms` and `crimes` rows and passes them as plain arguments into each interface method. See `GIS_SPEC.md` for the exact method signatures this implies — P3's module is a pure, stateless function library, not a service with its own DB access.

**Rules:**
- P3 owns: coordinates handling, distance calculations, proximity analysis, crime density, ATM proximity, spatial risk, hotspot detection, spatial feature generation, and producing the GeoJSON above.
- P4 owns: rendering this GeoJSON in React-Leaflet (markers, heatmap layers, popups). P4 must not independently calculate spatial risk or density.
- `risk_category` bucketing thresholds live in P3's spatial service, not hardcoded in the frontend.

## 3. Ownership Boundary Summary
- P2 → features + model + inference contract + evaluation. Stops at the JSON contract above.
- P3 → spatial computation + GeoJSON generation. Stops at the JSON contract above.
- P5 → wires both into FastAPI endpoints per `API_SPEC.md`, handles orchestration, persistence, auth.
- P4 → consumes `API_SPEC.md` responses (including the GeoJSON) only.

If P2 or P3 needs a new field, they propose it here (edit this file / flag P1), not invent it ad hoc inside their own module and hope backend adapts.
