"""
CyberCast ML Layer — Basic Inference Module (P2)
Step 8A: single-candidate ATM risk scoring.

Loads the trained RandomForest model bundle from ml/models/latest.pkl
and returns a risk_score for ONE candidate ATM given its 9 feature values.

What is NOT implemented here (deferred to later steps):
  - Top-K ranking across multiple candidates
  - confidence threshold / insufficient_confidence check
  - predicted_window
  - feature-based explanation / contribution labels
  - full ML_GIS_CONTRACTS.md output envelope
  - backend / FastAPI integration

Reference: docs/ML_SPEC.md, docs/ML_GIS_CONTRACTS.md §1
"""

import math
import pickle
import sys
from pathlib import Path
from typing import Dict

# Ensure project root is on sys.path regardless of how this module is invoked
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.features import FEATURE_NAMES

DEFAULT_MODEL_PATH: Path = PROJECT_ROOT / "ml" / "models" / "latest.pkl"

# Module-level cache so the model is only loaded once per process
_model_bundle: Dict = {}


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
                      This is the ranking key for future Top-K logic.
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
    prob = model.predict_proba([feature_vector])[0][1]
    risk_score = float(prob)

    return {
        "risk_score":    risk_score,
        "model_version": model_version,
    }
