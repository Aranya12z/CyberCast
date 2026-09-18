"""
app/interfaces/model_interface.py — ModelInterface ABC and MockModelInterface placeholder.

Reference: ML_GIS_CONTRACTS.md §1 (ML ↔ Backend Contract)
Architecture: ARCHITECTURE.md §3, §4, §10, §16
ML Spec: ML_SPEC.md §Feature set, §Confidence & the "don't fabricate" rule

# [MVP TARGET] — MockModelInterface is a clearly labeled temporary placeholder
# until P2's full model inference module is delivered.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List


class ModelInterface(ABC):
    """
    Abstract Base Class for ML models.
    The backend calls this interface without knowing the underlying implementation
    (Random Forest, XGBoost, etc.). Swappable per ARCHITECTURE.md §3 and ADR-001.
    """

    @abstractmethod
    def predict(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run inference on the given candidate ATMs and context.

        Input payload structure (ML_GIS_CONTRACTS.md §1):
        {
          "crime": {
            "crime_id": str,
            "crime_type": str,
            "timestamp": str (ISO 8601),
            "location": {"lat": float, "lng": float},
            "amount": float
          },
          "candidate_atms": [
            {
              "atm_id": str,
              "location": {"lat": float, "lng": float},
              "atm_historical_risk": float,
              "spatial_features": {
                "distance_from_crime": float,
                "nearby_crime_density": float
              }
            }
          ],
          "recent_transactions": [
            {
              "atm_id": str,
              "timestamp": str (ISO 8601),
              "amount": float
            }
          ]
        }

        Output response structure (ML_GIS_CONTRACTS.md §1):
        {
          "model_version": str,
          "predictions": [
            {
              "atm_id": str,
              "risk_score": float,
              "confidence": float,
              "predicted_window": {"start": str (ISO 8601), "end": str (ISO 8601)},
              "explanation": [
                {
                  "feature": str,
                  "value": float,
                  "contribution": "high" | "medium" | "low"
                }
              ]
            }
          ],
          "status": "ok" | "insufficient_confidence" | "insufficient_evidence"
        }
        """
        pass


class MockModelInterface(ModelInterface):
    """
    Deterministic mock implementation of ModelInterface for MVP testing & scaffolding.
    
    # [MVP TARGET] — TEMPORARY PLACEHOLDER
    # Used until P2 delivers the full ModelInterface.predict() implementation.
    # Scores deterministically across all 9 contract features (ML_SPEC.md §20):
    #   1. distance_from_crime
    #   2. nearby_crime_density
    #   3. atm_historical_risk
    #   4. hour_of_day
    #   5. day_of_week
    #   6. amount
    #   7. txns_last_1h
    #   8. txns_last_6h
    #   9. withdrawal_frequency
    #
    # Enforces confidence threshold 0.35 per ML_SPEC.md §50 ("don't fabricate").
    # Produces identical output shape to the real contract.
    """

    def __init__(
        self,
        model_version: str = "mock_rf_v1.0.0",
        top_k: int = 5,
        confidence_threshold: float = 0.35,
    ) -> None:
        self.model_version = model_version
        self.top_k = top_k
        self.confidence_threshold = confidence_threshold

    def predict(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Run deterministic prediction scoring over payload candidates."""
        crime = payload.get("crime") or {}
        candidate_atms = payload.get("candidate_atms") or []
        recent_txns = payload.get("recent_transactions") or []

        # If no candidates or missing crime data, return insufficient_evidence honestly
        if not candidate_atms or not crime:
            return {
                "model_version": self.model_version,
                "predictions": [],
                "status": "insufficient_evidence",
            }

        # Parse crime timestamp
        crime_ts_raw = crime.get("timestamp")
        try:
            if crime_ts_raw:
                # Handle 'Z' or ISO formats
                clean_ts = crime_ts_raw.replace("Z", "+00:00")
                crime_dt = datetime.fromisoformat(clean_ts)
            else:
                crime_dt = datetime.now(timezone.utc)
        except Exception:
            crime_dt = datetime.now(timezone.utc)

        # Compute crime-level temporal features (ML_SPEC.md §20)
        hour_of_day = crime_dt.hour
        day_of_week = crime_dt.weekday()
        amount = float(crime.get("amount", 0.0))

        # Build candidate predictions
        scored_candidates: List[Dict[str, Any]] = []

        for candidate in candidate_atms:
            atm_id = str(candidate.get("atm_id", ""))
            spatial = candidate.get("spatial_features") or {}
            dist_km = float(spatial.get("distance_from_crime", 5.0))
            density = float(spatial.get("nearby_crime_density", 0.0))
            hist_risk = float(candidate.get("atm_historical_risk", 0.0))

            # Compute transaction features for this ATM (ML_SPEC.md §34)
            atm_txns = [
                tx for tx in recent_txns if str(tx.get("atm_id", "")) == atm_id
            ]
            txns_1h = 0
            txns_6h = 0
            one_hr_delta = timedelta(hours=1)
            six_hr_delta = timedelta(hours=6)

            for tx in atm_txns:
                tx_ts_raw = tx.get("timestamp")
                if not tx_ts_raw:
                    continue
                try:
                    clean_tx_ts = str(tx_ts_raw).replace("Z", "+00:00")
                    tx_dt = datetime.fromisoformat(clean_tx_ts)
                    diff = abs(crime_dt - tx_dt)
                    if diff <= one_hr_delta:
                        txns_1h += 1
                    if diff <= six_hr_delta:
                        txns_6h += 1
                except Exception:
                    # Default counting if unparseable
                    txns_6h += 1

            withdrawal_freq = round(txns_6h / 6.0, 3)

            # Deterministic Risk Score (0.0 to 1.0)
            dist_factor = max(0.0, min(1.0, 1.0 - (dist_km / 10.0)))
            density_factor = min(1.0, density / 5.0)
            hist_factor = max(0.0, min(1.0, hist_risk))
            activity_factor = min(1.0, (txns_1h * 0.3) + (txns_6h * 0.05))
            time_factor = 0.8 if 8 <= hour_of_day <= 22 else 0.4

            raw_risk = (
                0.35 * dist_factor
                + 0.25 * hist_factor
                + 0.15 * density_factor
                + 0.15 * activity_factor
                + 0.10 * time_factor
            )
            risk_score = round(max(0.05, min(0.98, raw_risk)), 4)

            # Deterministic Confidence Score (0.0 to 1.0)
            # Higher confidence if close distance, high density, and recent activity
            base_conf = 0.50
            if dist_km <= 3.0:
                base_conf += 0.20
            elif dist_km <= 7.0:
                base_conf += 0.10
            elif dist_km > 15.0:
                base_conf -= 0.25

            if hist_risk > 0.0:
                base_conf += 0.10
            if density > 0.0:
                base_conf += 0.10
            if txns_6h > 0:
                base_conf += 0.05
            else:
                base_conf -= 0.10

            confidence = round(max(0.05, min(0.99, base_conf)), 4)

            # Explanation array (Feature contributions)
            explanations = []
            if dist_factor >= 0.6:
                explanations.append(
                    {"feature": "distance_from_crime", "value": round(dist_km, 2), "contribution": "high"}
                )
            elif dist_factor >= 0.3:
                explanations.append(
                    {"feature": "distance_from_crime", "value": round(dist_km, 2), "contribution": "medium"}
                )
            else:
                explanations.append(
                    {"feature": "distance_from_crime", "value": round(dist_km, 2), "contribution": "low"}
                )

            if hist_factor >= 0.5:
                explanations.append(
                    {"feature": "atm_historical_risk", "value": round(hist_risk, 3), "contribution": "high"}
                )
            elif hist_factor > 0.1:
                explanations.append(
                    {"feature": "atm_historical_risk", "value": round(hist_risk, 3), "contribution": "medium"}
                )

            if density_factor >= 0.4:
                explanations.append(
                    {"feature": "nearby_crime_density", "value": round(density, 2), "contribution": "medium"}
                )

            if txns_1h > 0:
                explanations.append(
                    {"feature": "txns_last_1h", "value": float(txns_1h), "contribution": "medium"}
                )

            if amount > 50000:
                explanations.append(
                    {"feature": "amount", "value": round(amount, 2), "contribution": "low"}
                )

            # Fixed 6-hour predicted window from crime time per ADR-005
            win_start = crime_dt.isoformat()
            win_end = (crime_dt + timedelta(hours=6)).isoformat()

            scored_candidates.append({
                "atm_id": atm_id,
                "risk_score": risk_score,
                "confidence": confidence,
                "predicted_window": {"start": win_start, "end": win_end},
                "explanation": explanations,
            })

        # Rank candidates by risk_score descending
        scored_candidates.sort(key=lambda x: x["risk_score"], reverse=True)
        top_predictions = scored_candidates[: self.top_k]

        # Check confidence threshold ("don't fabricate rule", ML_SPEC.md §50)
        max_conf = max(p["confidence"] for p in top_predictions) if top_predictions else 0.0
        if max_conf < self.confidence_threshold:
            return {
                "model_version": self.model_version,
                "predictions": [],
                "status": "insufficient_confidence",
            }

        return {
            "model_version": self.model_version,
            "predictions": top_predictions,
            "status": "ok",
        }
