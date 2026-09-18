"""
CyberCast ML Layer — Basic Inference Module (P2)
Step 8A: single-candidate ATM risk scoring.
Step 8B (ranking only): score multiple prepared candidates and return Top-K.
Step 9A: build_candidate_features() — live 9-feature construction from contract payload.
Step 9B: ModelInterface.predict() — end-to-end contract-in → ranked-predictions-out.
Step 10: confidence handling — per-candidate confidence + overall confidence floor.
Step 12: explanation — feature-based reasons with high/medium/low contribution labels.

Loads the trained RandomForest model bundle from ml/models/latest.pkl
and returns a risk_score for ONE candidate ATM given its 9 feature values.
rank_candidates() reuses predict_single() and sorts by risk_score.
build_candidate_features() prepares those 9 values from a contract payload row.

confidence semantics (ARCHITECTURE.md §4, ML_SPEC.md §risk_score vs confidence):
  risk_score  = P(positive class) — model likelihood, the ranking key.
  confidence  = 0.5 * atm_historical_risk + 0.5 * min(1.0, txns_last_6h / 10)
                Measures certainty based on supporting data signal (historical
                risk profile + recent transaction volume). Normalized to [0, 1].
  These are separate outputs: a high risk_score with low confidence is a valid
  and distinct case (e.g. strong pattern match on thin data).

Overall confidence aggregation:
  max_confidence = max of per-candidate confidences across the returned Top-K.
  If max_confidence < confidence_floor (default 0.35), returns
  status="insufficient_confidence" with predictions=[].
  Rationale: if at least one Top-K candidate has sufficient data support, the
  run is meaningful; requiring the *average* to clear the floor wrongly penalises
  runs that include distant/inactive fallback candidates alongside a strong match.

explanation semantics (ML_SPEC.md §Explainability, ML_GIS_CONTRACTS.md §1):
  Top 3 features ranked by the model's global feature_importances_, descending.
  For each candidate, attaches actual candidate feature value and contribution:
    - importance >= 0.18         -> "high"
    - 0.10 <= importance < 0.18  -> "medium"
    - importance < 0.10          -> "low"

predicted_window semantics (ADRS.md ADR-005, ML_GIS_CONTRACTS.md §1):
  Fixed 6-hour prediction window from the crime timestamp:
    start: crime timestamp (ISO8601)
    end:   crime timestamp + 6 hours (ISO8601)
  Preserves timezone offset if timezone-aware.

What is NOT implemented here (deferred to later steps):
  - backend / FastAPI integration

Reference: docs/ML_SPEC.md, docs/ML_GIS_CONTRACTS.md §1, docs/ARCHITECTURE.md §4, §9, docs/ADRS.md ADR-005
"""

import math
import pickle
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is on sys.path regardless of how this module is invoked
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.features import FEATURE_NAMES

DEFAULT_MODEL_PATH: Path = PROJECT_ROOT / "ml" / "models" / "latest.pkl"

# Module-level cache for the loaded model bundle so we only read disk once
_model_bundle: Dict[str, Any] = {}


def get_feature_contribution_label(importance: float) -> str:
    """
    Map feature importance to contribution label per Step 12 spec:
      - importance >= 0.18        -> "high"
      - 0.10 <= importance < 0.18 -> "medium"
      - importance < 0.10         -> "low"
    """
    if importance >= 0.18:
        return "high"
    elif importance >= 0.10:
        return "medium"
    else:
        return "low"


def build_explanation(
    feature_values: Dict[str, Any],
    model: Any,
    feature_names: List[str],
    top_n: int = 3,
) -> List[Dict[str, Any]]:
    """
    Build Top-N feature-based explanation items for a candidate ATM.

    1. Uses the trained Random Forest model's feature_importances_.
    2. Ranks the 9 features by global feature importance, descending.
    3. Selects the Top-N features (default 3).
    4. For each selected feature, extracts the candidate ATM's actual feature value.
    5. Assigns contribution label:
       - importance >= 0.18         -> "high"
       - 0.10 <= importance < 0.18  -> "medium"
       - importance < 0.10          -> "low"
    """
    importances = getattr(model, "feature_importances_", None)
    if importances is None:
        return []

    ranked_features = sorted(
        zip(feature_names, importances),
        key=lambda pair: float(pair[1]),
        reverse=True,
    )

    explanation = []
    for feat_name, imp in ranked_features[:top_n]:
        val = float(feature_values.get(feat_name, 0.0))
        label = get_feature_contribution_label(float(imp))
        explanation.append({
            "feature": feat_name,
            "value": val,
            "contribution": label,
        })

    return explanation


def _load_bundle(model_path: Path = DEFAULT_MODEL_PATH) -> Dict:
    """
    Load the model bundle from disk into the module-level cache.
    Raises FileNotFoundError if the model file is missing.
    """
    global _model_bundle
    path_key = str(model_path)

    if path_key not in _model_bundle:
        if not model_path.exists():
            raise FileNotFoundError(
                f"Trained model not found at: {model_path}\n"
                "Run ml/train.py first to produce the model file."
            )
        with open(model_path, "rb") as f:
            _model_bundle[path_key] = pickle.load(f)

    return _model_bundle[path_key]


def predict_single(
    hour_of_day: float,
    day_of_week: float,
    amount: float,
    distance_from_crime: float,
    atm_historical_risk: float,
    txns_last_1h: float,
    txns_last_6h: float,
    nearby_crime_density: float,
    withdrawal_frequency: float,
    model_path: Path = DEFAULT_MODEL_PATH,
) -> Dict:
    """
    Compute a risk_score for ONE candidate ATM using the trained RF model.

    Parameters
    ----------
    All 9 feature values (floats), in the order defined by FEATURE_NAMES:
        hour_of_day, day_of_week, amount, distance_from_crime,
        atm_historical_risk, txns_last_1h, txns_last_6h,
        nearby_crime_density, withdrawal_frequency

    Returns
    -------
    dict with keys:
        risk_score    (float in [0, 1]) — model's estimated probability
                      that this candidate ATM is the withdrawal location.
                      This is the ranking key for Top-K logic.
        confidence    (float in [0, 1]) — signal support / data density score:
                      0.5 * atm_historical_risk + 0.5 * min(1.0, txns_last_6h / 10).
                      Measures how much relevant historical and transactional
                      evidence backs the estimate for this specific candidate.
        model_version (str)             — version identifier of the loaded model.
    """
    bundle = _load_bundle(model_path)
    model = bundle["model"]
    model_version: str = bundle["model_version"]
    saved_features = bundle["feature_names"]

    # Build the feature vector in the exact order stored in the model bundle
    # (matches FEATURE_NAMES from prepare_features.py)
    raw_values = {
        "hour_of_day":          hour_of_day,
        "day_of_week":          day_of_week,
        "amount":               amount,
        "distance_from_crime":  distance_from_crime,
        "atm_historical_risk":  atm_historical_risk,
        "txns_last_1h":         txns_last_1h,
        "txns_last_6h":         txns_last_6h,
        "nearby_crime_density": nearby_crime_density,
        "withdrawal_frequency": withdrawal_frequency,
    }

    # Construct vector in saved feature order (guard against future reordering)
    feature_vector = []
    for feat in saved_features:
        if feat not in raw_values:
            raise KeyError(
                f"Feature '{feat}' required by model but not supplied to predict_single()."
            )
        val = float(raw_values[feat])
        if math.isnan(val) or math.isinf(val):
            raise ValueError(
                f"Feature '{feat}' contains an invalid value: {val}. "
                "NaN and Inf are not permitted."
            )
        feature_vector.append(val)

    if len(feature_vector) != 9:
        raise ValueError(
            f"Expected exactly 9 features; got {len(feature_vector)}."
        )

    # Probability for the positive class (index 1 = withdrawal location)
    risk_score = float(model.predict_proba([feature_vector])[0][1])

    # Confidence per ARCHITECTURE.md §4 & ML_SPEC.md (Signal Support / Data Density):
    # confidence = 0.5 * atm_historical_risk + 0.5 * min(1.0, txns_last_6h / 10)
    # Both components are bounded in [0, 1], guaranteeing confidence in [0, 1].
    hist_signal = max(0.0, min(1.0, float(atm_historical_risk)))
    txn_signal = max(0.0, min(1.0, float(txns_last_6h) / 10.0))
    confidence = float(round(0.5 * hist_signal + 0.5 * txn_signal, 6))

    # Step 12: Feature-based explanation (ML_SPEC.md §Explainability)
    explanation = build_explanation(raw_values, model, saved_features, top_n=3)

    return {
        "risk_score":    risk_score,
        "confidence":    confidence,
        "explanation":   explanation,
        "model_version": model_version,
    }


def rank_candidates(
    candidates: List[Dict],
    k: int,
    model_path: Path = DEFAULT_MODEL_PATH,
) -> List[Dict]:
    """
    Score multiple ATM candidates and return at most K, ranked by risk_score.

    Each candidate must already contain atm_id plus the same 9 feature fields
    accepted by predict_single(). K is a caller-supplied limit, not a
    project-wide default — the contracts do not define a fixed K.

    Returns a list of {"atm_id", "risk_score", "confidence", "explanation"} dicts,
    highest risk first.
    Never invents extra rows if there are fewer than K real candidates.
    An empty input list yields an empty result.
    """
    if not candidates or k <= 0:
        return []

    scored: List[Dict] = []

    for candidate in candidates:
        if "atm_id" not in candidate:
            raise KeyError("Each candidate must include 'atm_id'.")

        feature_kwargs = {}
        for feat in FEATURE_NAMES:
            if feat not in candidate:
                raise KeyError(
                    f"Candidate '{candidate.get('atm_id')}' is missing "
                    f"required feature '{feat}'."
                )
            feature_kwargs[feat] = candidate[feat]

        result = predict_single(model_path=model_path, **feature_kwargs)
        scored.append({
            "atm_id": candidate["atm_id"],
            "risk_score": result["risk_score"],
            "confidence": result["confidence"],
            "explanation": result["explanation"],
        })

    scored.sort(key=lambda row: row["risk_score"], reverse=True)
    return scored[:k]


def _parse_iso8601(value: Any, field_name: str) -> datetime:
    """Parse an ISO8601 timestamp, including values with Z or an offset."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"'{field_name}' must be a non-empty ISO8601 timestamp.")

    text = value.strip()
    if text.endswith("Z") or text.endswith("z"):
        text = text[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as err:
        raise ValueError(
            f"'{field_name}' is not a valid ISO8601 timestamp: {value}"
        ) from err

    return parsed


def build_predicted_window(crime_timestamp: Any, window_hours: int = 6) -> Dict[str, str]:
    """
    Construct the predicted_window dict per ML_GIS_CONTRACTS.md §1 & ADR-005.

    Parameters
    ----------
    crime_timestamp : str
        ISO8601 timestamp string from the crime payload.
    window_hours : int
        Duration of the prediction horizon (fixed at 6 hours for MVP per ADR-005).

    Returns
    -------
    dict with keys:
        start : ISO8601 string matching the crime timestamp.
        end   : ISO8601 string for crime timestamp + window_hours,
                preserving timezone offset when timezone-aware.
    """
    start_dt = _parse_iso8601(crime_timestamp, "crime.timestamp")
    end_dt = start_dt + timedelta(hours=window_hours)

    ts_str = str(crime_timestamp).strip() if crime_timestamp is not None else ""
    if ts_str.endswith("Z") or ts_str.endswith("z"):
        start_out = ts_str
        end_out = end_dt.isoformat().replace("+00:00", "Z")
    else:
        start_out = ts_str if ts_str else start_dt.isoformat()
        end_out = end_dt.isoformat()

    return {
        "start": start_out,
        "end": end_out,
    }


def _as_utc(value: datetime) -> datetime:
    """Compare instants in UTC. Naive timestamps are treated as UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _finite_float(value: Any, field_name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as err:
        raise ValueError(
            f"'{field_name}' must be numeric; got {value!r}."
        ) from err

    if math.isnan(number) or math.isinf(number):
        raise ValueError(
            f"'{field_name}' contains an invalid value: {number}. "
            "NaN and Inf are not permitted."
        )
    return number


def _count_recent_txns(
    atm_id: str,
    crime_ts: datetime,
    recent_transactions: List[Dict],
    window: timedelta,
) -> float:
    """Count this ATM's transactions in (crime_ts - window) .. crime_ts inclusive."""
    window_start = crime_ts - window
    count = 0
    for txn in recent_transactions:
        if not isinstance(txn, dict):
            raise ValueError("Each recent transaction must be an object.")
        if txn.get("atm_id") != atm_id:
            continue
        if "timestamp" not in txn:
            raise KeyError(
                f"Transaction for ATM '{atm_id}' is missing 'timestamp'."
            )
        txn_ts = _as_utc(_parse_iso8601(txn["timestamp"], "recent_transactions.timestamp"))
        if window_start <= txn_ts <= crime_ts:
            count += 1
    return float(count)


def build_candidate_features(
    crime: Dict,
    candidate_atm: Dict,
    recent_transactions: Optional[List[Dict]] = None,
) -> Dict:
    """
    Convert ONE contract candidate ATM into the 9-feature dict used by
    predict_single() / rank_candidates().

    Spatial fields and atm_historical_risk are consumed as provided.
    Temporal and transaction-count features are derived here.

    Implementation assumption: docs do not define withdrawal_frequency.
    This helper sets it equal to txns_last_6h (the 6-hour transaction count
    for this ATM). Do not treat that as a separately designed formula.
    """
    if not isinstance(crime, dict):
        raise ValueError("'crime' must be an object.")
    if not isinstance(candidate_atm, dict):
        raise ValueError("'candidate_atm' must be an object.")

    for field in ("timestamp", "amount"):
        if field not in crime:
            raise KeyError(f"crime is missing required field '{field}'.")

    if "atm_id" not in candidate_atm:
        raise KeyError("candidate_atm is missing required field 'atm_id'.")
    if "atm_historical_risk" not in candidate_atm:
        raise KeyError("candidate_atm is missing required field 'atm_historical_risk'.")
    if "spatial_features" not in candidate_atm:
        raise KeyError("candidate_atm is missing required field 'spatial_features'.")

    spatial = candidate_atm["spatial_features"]
    if not isinstance(spatial, dict):
        raise ValueError("candidate_atm.spatial_features must be an object.")
    for field in ("distance_from_crime", "nearby_crime_density"):
        if field not in spatial:
            raise KeyError(
                f"candidate_atm.spatial_features is missing required field '{field}'."
            )

    if recent_transactions is None:
        txns: List[Dict] = []
    elif not isinstance(recent_transactions, list):
        raise ValueError("'recent_transactions' must be a list.")
    else:
        txns = recent_transactions

    crime_wall = _parse_iso8601(crime["timestamp"], "crime.timestamp")
    crime_ts = _as_utc(crime_wall)
    atm_id = candidate_atm["atm_id"]

    txns_last_1h = _count_recent_txns(atm_id, crime_ts, txns, timedelta(hours=1))
    txns_last_6h = _count_recent_txns(atm_id, crime_ts, txns, timedelta(hours=6))

    features = {
        "atm_id": atm_id,
        "hour_of_day": float(crime_wall.hour),
        "day_of_week": float(crime_wall.weekday()),
        "amount": _finite_float(crime["amount"], "crime.amount"),
        "distance_from_crime": _finite_float(
            spatial["distance_from_crime"],
            "spatial_features.distance_from_crime",
        ),
        "atm_historical_risk": _finite_float(
            candidate_atm["atm_historical_risk"],
            "candidate_atm.atm_historical_risk",
        ),
        "txns_last_1h": txns_last_1h,
        "txns_last_6h": txns_last_6h,
        "nearby_crime_density": _finite_float(
            spatial["nearby_crime_density"],
            "spatial_features.nearby_crime_density",
        ),
        # Assumption (docs unspecified): withdrawal_frequency uses the
        # same transaction count as txns_last_6h. Not a separate formula.
        "withdrawal_frequency": txns_last_6h,
    }

    for feat in FEATURE_NAMES:
        _finite_float(features[feat], feat)

    return features


# Default overall confidence floor per ML_SPEC.md §Confidence
DEFAULT_CONFIDENCE_FLOOR: float = 0.35


class ModelInterface:
    """
    Steps 9B + 10 — End-to-end prediction interface for the CyberCast contract.

    Accepts the same payload shape produced by the backend:
        {
            "crime":                { ... },
            "candidate_atms":       [ ... ],
            "recent_transactions":  [ ... ]   (optional)
        }

    Returns:
        {
            "model_version": "<version>",
            "predictions":   [ {"atm_id", "risk_score", "confidence", "predicted_window", "explanation"}, ... ],
            "status":        "ok" | "insufficient_confidence"
        }

    Parameters
    ----------
    k : int or None
        Max predictions returned.  None → return all candidates.
    confidence_floor : float
        If the mean per-candidate confidence falls below this value, return
        status="insufficient_confidence" with an empty predictions list.
        Default 0.35 per ML_SPEC.md.
    """

    def __init__(
        self,
        k: Optional[int] = None,
        confidence_floor: float = DEFAULT_CONFIDENCE_FLOOR,
        model_path: Path = DEFAULT_MODEL_PATH,
    ) -> None:
        self._k = k
        self._confidence_floor = confidence_floor
        self._model_path = model_path

    def predict(self, payload: dict) -> dict:
        """
        Run the full inference pipeline on a contract payload.

        1. Validate inputs.
        2. Build 9-feature dicts for every candidate ATM.
        3. Score and rank via rank_candidates().
        4. Apply overall confidence floor.
        5. Return the contract-shaped output envelope.
        """
        if not isinstance(payload, dict):
            raise ValueError("payload must be a dict.")

        crime = payload.get("crime")
        if not isinstance(crime, dict):
            raise ValueError("payload must contain a 'crime' dict.")

        candidate_atms = payload.get("candidate_atms")
        if candidate_atms is None:
            candidate_atms = []
        if not isinstance(candidate_atms, list):
            raise ValueError("'candidate_atms' must be a list.")

        recent_transactions = payload.get("recent_transactions")
        if recent_transactions is None:
            recent_transactions = []
        if not isinstance(recent_transactions, list):
            raise ValueError("'recent_transactions' must be a list.")

        # Determine effective K
        effective_k = self._k if self._k is not None else len(candidate_atms)

        # Empty candidates → insufficient_evidence (ML_SPEC.md §Confidence)
        # No candidate ATMs means there is genuinely no evidence to score;
        # returning "ok" with an empty list would misrepresent a data-gap as a
        # clean successful run.
        if not candidate_atms or effective_k <= 0:
            bundle = _load_bundle(self._model_path)
            return {
                "model_version": bundle["model_version"],
                "predictions": [],
                "status": "insufficient_evidence",
            }

        # Build feature dicts for every candidate
        prepared: List[Dict] = []
        for atm in candidate_atms:
            features = build_candidate_features(
                crime, atm, recent_transactions,
            )
            prepared.append(features)

        # Score and rank
        ranked = rank_candidates(prepared, k=effective_k, model_path=self._model_path)

        # Retrieve model_version from the (already-cached) bundle
        bundle = _load_bundle(self._model_path)
        model_version = bundle["model_version"]

        # ----- Step 10: overall confidence floor -----
        # Use the MAX per-candidate confidence across the returned Top-K.
        # If even the best-supported ranked candidate falls below the floor,
        # the run lacks sufficient data signal and we decline to return
        # predictions (status="insufficient_confidence").
        # This allows a single high-confidence candidate to keep the run valid
        # even when other candidates have thin data support.
        if ranked:
            max_confidence = max(r["confidence"] for r in ranked)
        else:
            max_confidence = 0.0

        if max_confidence < self._confidence_floor:
            return {
                "model_version": model_version,
                "predictions": [],
                "status": "insufficient_confidence",
            }

        # Build 6-hour predicted window from crime timestamp (ADR-005)
        predicted_window = build_predicted_window(crime.get("timestamp"), window_hours=6)

        predictions: List[Dict[str, Any]] = []
        for r in ranked:
            predictions.append({
                "atm_id": r["atm_id"],
                "risk_score": r["risk_score"],
                "confidence": r["confidence"],
                "predicted_window": predicted_window,
                "explanation": r["explanation"],
            })

        return {
            "model_version": model_version,
            "predictions": predictions,
            "status": "ok",
        }

