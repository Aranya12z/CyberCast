"""
CyberCast ML Layer - Feature Preparation Module (P2)
Extracts and prepares the 9 contract-specified ML features for training and inference.
Reference: docs/ML_SPEC.md & docs/ML_GIS_CONTRACTS.md
"""

import csv
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

# Exact 9 contract-required ML features
FEATURE_NAMES: List[str] = [
    "hour_of_day",
    "day_of_week",
    "amount",
    "distance_from_crime",
    "atm_historical_risk",
    "txns_last_1h",
    "txns_last_6h",
    "nearby_crime_density",
    "withdrawal_frequency",
]

# Binary classification target label
TARGET_NAME: str = "is_withdrawal_location"


def extract_feature_vector(row: Dict[str, Any]) -> List[float]:
    """
    Extract the 9 numerical features from a single dictionary record.
    Ensures strict validation against NaN and infinity.
    """
    vector: List[float] = []
    for feature in FEATURE_NAMES:
        if feature not in row:
            raise KeyError(f"Missing required feature '{feature}' in record: {row}")
        
        raw_val = row[feature]
        try:
            val = float(raw_val)
        except (ValueError, TypeError) as err:
            raise ValueError(f"Invalid numeric value '{raw_val}' for feature '{feature}': {err}")

        if math.isnan(val) or math.isinf(val):
            raise ValueError(f"Feature '{feature}' contains NaN or Inf: {val}")

        vector.append(val)
    return vector


def load_dataset(csv_path: Union[str, Path]) -> List[Dict[str, str]]:
    """
    Read CSV dataset into a list of row dictionaries.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file does not exist at: {path}")

    with open(path, mode="r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise ValueError(f"Dataset at {path} is empty.")

    return rows


def prepare_training_data(
    csv_path: Union[str, Path] = "data/synthetic/synthetic_atm_withdrawals.csv",
) -> Tuple[List[List[float]], List[int], List[str]]:
    """
    Loads the dataset, selects only the 9 specified ML features,
    and separates features (X) from the target (y).

    Returns:
        X: 2D list of shape (N, 9) suitable for scikit-learn
        y: 1D list of shape (N,) containing binary target values (0 or 1)
        feature_names: List of the 9 feature column names
    """
    rows = load_dataset(csv_path)

    X: List[List[float]] = []
    y: List[int] = []

    for idx, row in enumerate(rows):
        # Extract features
        features = extract_feature_vector(row)
        X.append(features)

        # Extract target
        if TARGET_NAME not in row:
            raise KeyError(f"Target column '{TARGET_NAME}' missing at row {idx}")

        raw_target = row[TARGET_NAME]
        try:
            target_val = int(raw_target)
        except (ValueError, TypeError) as err:
            raise ValueError(f"Invalid target '{raw_target}' at row {idx}: {err}")

        if target_val not in (0, 1):
            raise ValueError(f"Target must be binary 0 or 1, got '{target_val}' at row {idx}")

        y.append(target_val)

    return X, y, FEATURE_NAMES.copy()
