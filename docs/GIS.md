# GIS_SPEC.md — Geospatial / Spatial Analytics Layer Implementation Guide

**Owner:** P3. **Scope:** L5 (Geospatial) layer only.
**Contract you must honor, not redefine:** `ML_GIS_CONTRACTS.md` §2 (GIS ↔ Backend Contract).
**Do not touch:** FastAPI routes, database models, model training/inference code (P2's job), React/map UI code (P4's job — you compute, they render).

---

## Tech

GeoJSON, GeoPandas (basic use only). No PostGIS, no Apache Sedona, no dedicated spatial database unless an ADR in `ADRS.md` justifies it.

## What you own

- Coordinate handling
- Distance calculations (crime ↔ ATM, ATM ↔ ATM)
- Proximity analysis (which ATMs are "nearby" a crime, by what radius)
- Crime density computation (`nearby_crime_density` feature consumed by ML — see `ML_GIS_CONTRACTS.md`)
- ATM proximity ranking (candidate ATM shortlist generation, which feeds ML's `candidate_atms` input)
- Spatial risk bucketing (`risk_category`: low/medium/high thresholds)
- Hotspot detection (clustering of historical crime/withdrawal points)
- GeoJSON FeatureCollection generation for the map

## Interface you must implement

**Data dependency — your module is stateless, it never touches the database.**
The backend fetches `atms` and recent `crimes` rows itself and passes them
in as plain arguments. This was previously implicit and caused confusion
about whether GIS code queries Postgres directly — it does not.

```python
class SpatialInterface(ABC):
    def get_candidate_atms(self, crime_location: dict, radius_km: float, atms: list[dict]) -> list[dict]:
        """atms = full ATM list, fetched by the backend from the `atms` table.
        Returns the subset within radius_km as [{atm_id, location}] — feeds
        ML's candidate_atms input (before atm_historical_risk/spatial_features
        are attached — see ML_GIS_CONTRACTS.md §1)."""

    def compute_spatial_features(self, crime_location: dict, atm_location: dict,
                                  historical_crimes: list[dict]) -> dict:
        """historical_crimes = recent crimes fetched by the backend from the
        `crimes` table (for density calc). Returns
        {distance_from_crime, nearby_crime_density} for one ATM. Called once
        per candidate ATM; the backend attaches the result into that
        candidate's `spatial_features` before calling ML."""

    def to_geojson(self, predictions: list[dict]) -> dict:
        """Takes backend-merged prediction results (already including
        risk_score/confidence/predicted_window/explanation + atm location)
        and returns the FeatureCollection shape defined in
        ML_GIS_CONTRACTS.md §2 exactly, including predicted_window (not a
        single predicted_time) in each feature's properties."""
```

The backend calls these three methods; it does not reimplement distance math or clustering itself.

## Candidate ATM generation flow

```
Crime location
  ↓
Radius/proximity search over atms table (via backend query, or a bbox param you define)
  ↓
Candidate ATM list → passed to ML as candidate_atms (see ML_GIS_CONTRACTS.md §1)
```

Keep the radius/threshold value documented here once chosen (e.g., "5km default search radius") so P2 and P1 know why a candidate list has the size it does.

## GeoJSON contract — do not diverge

Reproduce exactly the shape in `ML_GIS_CONTRACTS.md` §2. If you need an extra `properties` field (e.g., a new visualization need from P4), add it to that shared file first, then implement — don't ship a differently-shaped FeatureCollection that only your code understands.

## Risk category thresholds

Define and document your `risk_score → low/medium/high` bucketing here once agreed with P2 (since `risk_score` originates from the ML layer, but the _bucketing_ for map display is a GIS/presentation concern):

```
risk_score >= 0.7   → high
0.4 <= risk_score < 0.7 → medium
risk_score < 0.4    → low
```

(Placeholder — update once tuned against real model output distribution.)

## What NOT to build here

No model training/inference (that's `ML_SPEC.md`), no FastAPI endpoints, no React map components — you produce data structures (candidate lists, feature dicts, GeoJSON); P4 renders them, P5 wires them into endpoints.
