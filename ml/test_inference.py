"""
CyberCast ML Layer — Inference Verification Test (Step 8A, P2)

Tests predict_single() from ml/inference.py using valid synthetic-style
feature values. Covers:

  1. Model loads successfully from ml/models/latest.pkl
  2. Exactly 9 features are passed in the correct order
  3. Prediction returns without error
  4. risk_score is a float in [0, 1]
  5. model_version is returned as a non-empty string
  6. No NaN or Inf values in or out
  7. High-signal candidate scores higher than low-signal candidate
  8. Invalid inputs are rejected correctly

Usage:
    py ml/test_inference.py
"""

import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.inference import predict_single

PASS = "PASS"
FAIL = "FAIL"


def check(label: str, condition: bool, detail: str = "") -> bool:
    status = PASS if condition else FAIL
    suffix = f"  ({detail})" if detail else ""
    print(f"  [{status}] {label}{suffix}")
    return condition


def run_tests() -> int:
    """Returns number of failed checks."""
    print("=" * 62)
    print("  CYBERCAST ML — INFERENCE VERIFICATION  (Step 8A)")
    print("=" * 62)
    failures = 0

    # ------------------------------------------------------------------
    # Test 1: HIGH-SIGNAL candidate (close ATM, high historical risk,
    #         high recent tx volume, high crime density)
    # ------------------------------------------------------------------
    print("\n[Test 1] High-signal candidate (expected high risk_score)")
    try:
        result_high = predict_single(
            hour_of_day=14,
            day_of_week=2,
            amount=45000.0,
            distance_from_crime=0.85,    # close to crime location
            atm_historical_risk=0.78,    # high historical risk
            txns_last_1h=12,             # high recent activity
            txns_last_6h=38,
            nearby_crime_density=7.2,    # high crime density nearby
            withdrawal_frequency=54.0,
        )
        rs_high = result_high["risk_score"]
        mv      = result_high["model_version"]

        failures += 0 if check("predict_single() returned without error", True) else 1
        failures += 0 if check("risk_score is a float", isinstance(rs_high, float),
                                f"got type {type(rs_high).__name__}") else 1
        failures += 0 if check("risk_score in [0, 1]", 0.0 <= rs_high <= 1.0,
                                f"got {rs_high:.6f}") else 1
        failures += 0 if check("risk_score is not NaN/Inf",
                                not math.isnan(rs_high) and not math.isinf(rs_high),
                                f"got {rs_high}") else 1
        failures += 0 if check("model_version is a non-empty string",
                                isinstance(mv, str) and len(mv) > 0,
                                f"got '{mv}'") else 1
        print(f"        risk_score    = {rs_high:.6f}")
        print(f"        model_version = {mv}")
    except Exception as exc:
        failures += 1
        check("predict_single() raised unexpected exception", False, str(exc))

    # ------------------------------------------------------------------
    # Test 2: LOW-SIGNAL candidate (far ATM, low historical risk,
    #         low recent activity, low crime density)
    # ------------------------------------------------------------------
    print("\n[Test 2] Low-signal candidate (expected low risk_score)")
    try:
        result_low = predict_single(
            hour_of_day=14,
            day_of_week=2,
            amount=45000.0,
            distance_from_crime=11.30,   # far from crime
            atm_historical_risk=0.15,    # low historical risk
            txns_last_1h=0,              # little recent activity
            txns_last_6h=4,
            nearby_crime_density=0.8,    # low crime density
            withdrawal_frequency=8.5,
        )
        rs_low = result_low["risk_score"]
        failures += 0 if check("risk_score is a float", isinstance(rs_low, float),
                                f"got type {type(rs_low).__name__}") else 1
        failures += 0 if check("risk_score in [0, 1]", 0.0 <= rs_low <= 1.0,
                                f"got {rs_low:.6f}") else 1
        print(f"        risk_score    = {rs_low:.6f}")

        # High-signal should score strictly higher than low-signal
        if "rs_high" in dir():
            failures += 0 if check(
                "High-signal score > Low-signal score",
                rs_high > rs_low,
                f"{rs_high:.4f} vs {rs_low:.4f}",
            ) else 1
    except Exception as exc:
        failures += 1
        check("predict_single() raised unexpected exception", False, str(exc))

    # ------------------------------------------------------------------
    # Test 3: Invalid input — NaN should be rejected
    # ------------------------------------------------------------------
    print("\n[Test 3] Invalid input: NaN in a feature (must raise ValueError)")
    try:
        predict_single(
            hour_of_day=float("nan"),
            day_of_week=2,
            amount=45000.0,
            distance_from_crime=0.85,
            atm_historical_risk=0.78,
            txns_last_1h=12,
            txns_last_6h=38,
            nearby_crime_density=7.2,
            withdrawal_frequency=54.0,
        )
        failures += 1
        check("ValueError raised for NaN input", False, "no exception was raised")
    except ValueError as e:
        failures += 0 if check("ValueError raised for NaN input", True, str(e)[:60]) else 1
    except Exception as exc:
        failures += 1
        check("ValueError raised for NaN input", False,
              f"unexpected exception type {type(exc).__name__}: {exc}")

    # ------------------------------------------------------------------
    # Test 4: Invalid input — Inf should be rejected
    # ------------------------------------------------------------------
    print("\n[Test 4] Invalid input: Inf in a feature (must raise ValueError)")
    try:
        predict_single(
            hour_of_day=14,
            day_of_week=2,
            amount=float("inf"),
            distance_from_crime=0.85,
            atm_historical_risk=0.78,
            txns_last_1h=12,
            txns_last_6h=38,
            nearby_crime_density=7.2,
            withdrawal_frequency=54.0,
        )
        failures += 1
        check("ValueError raised for Inf input", False, "no exception was raised")
    except ValueError as e:
        failures += 0 if check("ValueError raised for Inf input", True, str(e)[:60]) else 1
    except Exception as exc:
        failures += 1
        check("ValueError raised for Inf input", False,
              f"unexpected exception type {type(exc).__name__}: {exc}")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print()
    print("=" * 62)
    if failures == 0:
        print("  ALL CHECKS PASSED")
    else:
        print(f"  {failures} CHECK(S) FAILED")
    print("=" * 62)
    return failures


if __name__ == "__main__":
    n_failures = run_tests()
    sys.exit(0 if n_failures == 0 else 1)
