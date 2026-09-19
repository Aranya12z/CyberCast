# ML_SPEC.md — Predictive Analytics Layer Implementation Guide
**Owner:** P2. **Scope:** L4 (ML/Predictive Analytics) layer only.
**Contract you must honor, not redefine:** `ML_GIS_CONTRACTS.md` §1 (ML ↔ Backend Contract).
**Do not touch:** FastAPI routes, database models, spatial/GeoJSON code, React code. You receive an input JSON, return an output JSON — everything else is someone else's layer.

---

## Tech
scikit-learn, Random Forest and/or XGBoost. No deep learning, no AutoML platforms, no MLOps stack for MVP — those are FUTURE per `ARCHITECTURE.md` §16 (Anti-overengineering Rule) and this file's own "Model lifecycle" section below, unless an ADR justifies otherwise.

## What you own
- Feature generation (from the raw fields the backend gives you)
- Model loading (offline-trained, saved locally, loaded by the backend/inference module)
- Inference / prediction scoring
- Ranking candidates into Top-K
- Confidence/probability calibration
- Model versioning — **MVP scope:** a manually incremented string identifier set at training time (e.g. `rf_v1_20260917`), stored alongside its eval metrics in `model_metadata` (`DATA_SCHEMA.md`). This is not a model registry: no automatic tracking, no rollback tooling, no drift detection. Those are `[FUTURE]` per `ARCHITECTURE.md` §16 and §12.
- Evaluation outputs (offline metrics — precision@K, recall, calibration — documented, not exposed live in MVP)

## Feature set (baseline — extend via this file, not silently in code)
| feature | description |
|---|---|
| distance_from_crime | distance between candidate ATM and reported crime location |
| hour_of_day / day_of_week | temporal context of the complaint |
| amount | transaction/complaint amount |
| atm_historical_risk | prior risk score of the ATM based on history |
| txns_last_1h / txns_last_6h | recent transaction volume at candidate ATM |
| nearby_crime_density | crime density around the ATM (computed by GIS layer — you consume it, don't recompute it) |
| withdrawal_frequency | historical withdrawal pattern feature |

**Note (feature ownership, now explicit — see `ML_GIS_CONTRACTS.md` §1):**
- `distance_from_crime` and `nearby_crime_density` arrive pre-computed, per candidate ATM, in `candidate_atms[].spatial_features` — P3's output via the backend. Do not recompute these.
- `atm_historical_risk` arrives pre-attached per candidate in `candidate_atms[].atm_historical_risk` — a stored DB value the backend attaches. Not computed by you or by GIS at request time.
- `hour_of_day`, `day_of_week`, `txns_last_1h`, `txns_last_6h`, and `withdrawal_frequency` are **yours to compute** from the raw `crime.timestamp` and raw `recent_transactions` list. No pre-aggregated version of these is passed in — aggregating from the raw list is explicitly your job, so it only happens in one place.

## Interface you must implement
```python
class ModelInterface(ABC):
    def predict(self, payload: dict) -> dict:
        """
        payload matches ML_GIS_CONTRACTS.md §1 Input exactly.
        returns dict matching ML_GIS_CONTRACTS.md §1 Output exactly.
        """
```
The backend only ever calls `.predict(payload)`. It does not know or care if this is Random Forest or XGBoost underneath — that's the whole point of the interface (`ARCHITECTURE.md` §3, §12).

## risk_score vs confidence — read this before implementing scoring
Full semantics live in `ARCHITECTURE.md` §4 (canonical) and `ML_GIS_CONTRACTS.md` §0. In short: `risk_score` ranks candidates; `confidence` measures how much you trust that ranking for this specific candidate. They are independent outputs, not two names for the same number — your model must be able to produce a high `risk_score` with a low `confidence` when the pattern is strong but the supporting data is thin.

## Confidence & the "don't fabricate" rule
Top-K default: 5 candidates.
This is the intended MVP default for the number of ATM candidates returned/ranked by the ML prediction layer, while the ModelInterface may accept a configurable k value.

**MVP default threshold: if the run's overall confidence falls below 0.35, return:**
```json
{ "status": "insufficient_confidence", "predictions": [] }
```
Never pad out a Top-K list to look complete. Judges will ask about false positives (`INTEGRATION_SPEC.md` §5, Judge-Defensibility Checklist) — an honest "insufficient evidence" path is a feature, not a gap.

**This is a different, lower-stakes threshold than alert generation.** A prediction with `confidence` between 0.35 and 0.5 clears this floor (so it's returned and shown to the investigator) but will *not* trigger an alert — that's a separate, backend-side rule (`ADRS.md` ADR-006, `risk_score >= 0.4 AND confidence >= 0.5`). Don't merge the two thresholds or assume one implies the other.

## Explainability (MVP scope)
Feature-based explanations only — for each Top-K prediction, return the top contributing features with a `high/medium/low` contribution label (e.g., derived from feature importances or simple rule-based bucketing). **Do not claim SHAP or advanced explainability unless actually implemented** — that's `FUTURE` per `ARCHITECTURE.md` §9 (Explainability).

## Model lifecycle (MVP scope only)
```
Data → training (offline, notebook/script) → evaluation → save model file → 
backend loads model file → inference via ModelInterface → (future: monitoring/retraining)
```
Full MLOps (drift monitoring, auto-retraining, model registry service) = FUTURE. For MVP: train offline, save locally, load in-process.

## What NOT to build here
No FastAPI routes, no database writes, no GeoJSON generation, no frontend code, no message queues/streaming. Your deliverable is a Python module exposing `ModelInterface.predict()` plus your offline training/evaluation scripts.
