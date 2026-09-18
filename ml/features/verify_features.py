"""
Verification test for CyberCast ML feature engineering module.
"""

import math
import sys
from pathlib import Path

# Add project root to sys.path so ml package can be imported directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.features import FEATURE_NAMES, TARGET_NAME, prepare_training_data


def run_verification():
    print("--- CYBERCAST ML FEATURE VERIFICATION ---")

    # 1. Module import
    print("1. Module import: SUCCESS")

    # 2. Dataset loading
    dataset_path = PROJECT_ROOT / "data" / "synthetic" / "synthetic_atm_withdrawals.csv"
    X, y, feature_names = prepare_training_data(dataset_path)
    print(f"2. Dataset loaded: SUCCESS ({len(X)} rows loaded from {dataset_path.name})")

    # 3. X feature count
    n_features = len(X[0]) if X else 0
    all_rows_have_9 = all(len(row) == 9 for row in X)
    print(f"3. X feature count: {n_features} (All rows have exactly 9 features: {all_rows_have_9})")
    assert n_features == 9, f"Expected 9 features, got {n_features}"
    assert all_rows_have_9, "Some rows do not contain 9 features"

    # 4. Feature names check
    expected_features = [
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
    print(f"4. Feature names match: {feature_names == expected_features}")
    print(f"   Feature list: {feature_names}")
    assert feature_names == expected_features, "Feature names do not match specification"

    # 5. y binary target check
    unique_targets = set(y)
    is_binary = unique_targets.issubset({0, 1})
    print(f"5. y target values: {unique_targets} (Binary 0/1: {is_binary})")
    print(f"   Target counts -> 1s: {y.count(1)}, 0s: {y.count(0)}")
    assert is_binary, f"Target values are not binary: {unique_targets}"

    # 6. Length alignment
    same_len = len(X) == len(y)
    print(f"6. Row count alignment: len(X)={len(X)}, len(y)={len(y)} (Matches: {same_len})")
    assert same_len, "X and y row counts do not match"

    # 7. No NaN or infinite values
    has_nan_inf = any(
        math.isnan(val) or math.isinf(val)
        for row in X
        for val in row
    )
    print(f"7. NaN / Infinite values in X: {has_nan_inf} (Clean: {not has_nan_inf})")
    assert not has_nan_inf, "Found NaN or Infinite values in features"

    print("------------------------------------------")
    print("ALL 7 VERIFICATION CHECKS PASSED.")


if __name__ == "__main__":
    run_verification()
