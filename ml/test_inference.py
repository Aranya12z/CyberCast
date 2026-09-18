"""
CyberCast ML Layer — Inference Verification Test (Steps 8A + 8B + 9A + 9B + 10, P2)

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

Also tests rank_candidates() (Step 8B ranking only):

  1. Results are ordered by risk_score descending
  2. K limits the number of returned rows
  3. Fewer candidates than K returns every real candidate (no padding)
  4. An empty candidate list returns an empty list

Also tests build_candidate_features() (live 9-feature construction):

  1. hour_of_day / day_of_week from crime.timestamp
  2. 1-hour and 6-hour transaction counts
  3. ATM id filtering
  4. spatial / historical fields copied, not recomputed
  5. missing or invalid required values rejected

Also tests ModelInterface.predict() (end-to-end contract pipeline):

  1. Valid payload with multiple ATMs returns ranked predictions
  2. Predictions ranked highest risk first
  3. model_version and status returned correctly
  4. K respected when set via constructor
  5. Empty candidate_atms handled safely
  6. All previous tests continue to pass

Also tests confidence handling (Step 10):

  1. confidence returned and in [0, 1] for predict_single()
  2. confidence included in rank_candidates() and ModelInterface output
  3. High-confidence payload returns status "ok"
  4. Low confidence_floor triggers "insufficient_confidence"
  5. Predictions are empty when confidence is insufficient

Usage:
    py ml/test_inference.py
"""

import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.inference import (
    DEFAULT_CONFIDENCE_FLOOR,
    ModelInterface,
    build_candidate_features,
    predict_single,
    rank_candidates,
)

# Shared feature templates for ranking tests (same 9 fields as predict_single).
_BASE_FEATURES = {
    "hour_of_day": 14,
    "day_of_week": 2,
    "amount": 45000.0,
}

HIGH_SIGNAL = {
    "atm_id": "atm-high",
    **_BASE_FEATURES,
    "distance_from_crime": 0.85,
    "atm_historical_risk": 0.78,
    "txns_last_1h": 12,
    "txns_last_6h": 38,
    "nearby_crime_density": 7.2,
    "withdrawal_frequency": 54.0,
}

MID_SIGNAL = {
    "atm_id": "atm-mid",
    **_BASE_FEATURES,
    "distance_from_crime": 1.20,
    "atm_historical_risk": 0.65,
    "txns_last_1h": 9,
    "txns_last_6h": 28,
    "nearby_crime_density": 5.5,
    "withdrawal_frequency": 40.0,
}

LOW_SIGNAL = {
    "atm_id": "atm-low",
    **_BASE_FEATURES,
    "distance_from_crime": 11.30,
    "atm_historical_risk": 0.15,
    "txns_last_1h": 0,
    "txns_last_6h": 4,
    "nearby_crime_density": 0.8,
    "withdrawal_frequency": 8.5,
}

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
    print("  CYBERCAST ML — INFERENCE VERIFICATION  (8A+8B+9A+9B+10)")
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
        # Step 10: confidence checks
        conf_high = result_high["confidence"]
        failures += 0 if check("confidence is returned",
                                "confidence" in result_high) else 1
        failures += 0 if check("confidence is a float in [0, 1]",
                                isinstance(conf_high, float)
                                and 0.0 <= conf_high <= 1.0,
                                f"got {conf_high}") else 1
        failures += 0 if check("confidence >= 0.5 (binary max-prob)",
                                conf_high >= 0.5, f"got {conf_high:.6f}") else 1
        print(f"        risk_score    = {rs_high:.6f}")
        print(f"        confidence    = {conf_high:.6f}")
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
    # Test 5: rank_candidates — descending risk_score order
    # ------------------------------------------------------------------
    print("\n[Test 5] rank_candidates: descending risk_score order")
    try:
        three = [LOW_SIGNAL, HIGH_SIGNAL, MID_SIGNAL]
        ranked = rank_candidates(three, k=3)
        scores = [row["risk_score"] for row in ranked]
        ids = [row["atm_id"] for row in ranked]
        descending = all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))
        min_score = min(scores)
        failures += 0 if check("returned 3 scored candidates", len(ranked) == 3,
                                f"got {len(ranked)}") else 1
        failures += 0 if check("each row has atm_id, risk_score, and confidence",
                                all("atm_id" in row and "risk_score" in row
                                    and "confidence" in row for row in ranked)) else 1
        failures += 0 if check("risk_score is descending (ties allowed)",
                                descending, f"scores={scores}") else 1
        failures += 0 if check("highest-risk atm_id is first",
                                ids[0] == "atm-high", f"order={ids}") else 1
        failures += 0 if check("last row has the lowest risk_score",
                                ranked[-1]["risk_score"] == min_score,
                                f"last={ranked[-1]}") else 1
        print(f"        order = {ids}")
        print(f"        scores = {[round(s, 6) for s in scores]}")
    except Exception as exc:
        failures += 1
        check("rank_candidates() ranking test", False, str(exc))

    # ------------------------------------------------------------------
    # Test 6: K limits the number of results
    # ------------------------------------------------------------------
    print("\n[Test 6] rank_candidates: K limits result count")
    try:
        three = [LOW_SIGNAL, HIGH_SIGNAL, MID_SIGNAL]
        ranked_all = rank_candidates(three, k=3)
        ranked_k2 = rank_candidates(three, k=2)
        failures += 0 if check("K=2 returns exactly 2 candidates",
                                len(ranked_k2) == 2, f"got {len(ranked_k2)}") else 1
        failures += 0 if check("K=2 is the first two of the full ranking",
                                ranked_k2 == ranked_all[:2],
                                f"got {[row['atm_id'] for row in ranked_k2]}") else 1
        failures += 0 if check("K=2 is shorter than the uncut ranking",
                                len(ranked_k2) < len(ranked_all)) else 1
    except Exception as exc:
        failures += 1
        check("rank_candidates() K-limit test", False, str(exc))

    # ------------------------------------------------------------------
    # Test 7: fewer candidates than K — no fake padding
    # ------------------------------------------------------------------
    print("\n[Test 7] rank_candidates: fewer candidates than K (no padding)")
    try:
        ranked_short = rank_candidates(
            [LOW_SIGNAL, HIGH_SIGNAL],
            k=4,
        )
        ids_short = [row["atm_id"] for row in ranked_short]
        failures += 0 if check("returns 2 real candidates, not 4",
                                len(ranked_short) == 2, f"got {len(ranked_short)}") else 1
        failures += 0 if check("preserves both real atm_id values",
                                set(ids_short) == {"atm-high", "atm-low"},
                                f"got {ids_short}") else 1
        failures += 0 if check("still ranked descending",
                                ids_short == ["atm-high", "atm-low"],
                                f"got {ids_short}") else 1
    except Exception as exc:
        failures += 1
        check("rank_candidates() short-list test", False, str(exc))

    # ------------------------------------------------------------------
    # Test 8: empty candidate list
    # ------------------------------------------------------------------
    print("\n[Test 8] rank_candidates: empty candidate list")
    try:
        ranked_empty = rank_candidates([], k=3)
        failures += 0 if check("empty input returns a list",
                                isinstance(ranked_empty, list)) else 1
        failures += 0 if check("empty input returns zero rows",
                                len(ranked_empty) == 0,
                                f"got {ranked_empty}") else 1
    except Exception as exc:
        failures += 1
        check("rank_candidates() empty-list test", False, str(exc))

    # ------------------------------------------------------------------
    # Test 9+: build_candidate_features (live contract feature-building)
    # 2026-09-16T14:30:00Z is a Wednesday → weekday() == 2, hour == 14.
    # ------------------------------------------------------------------
    print("\n[Test 9] build_candidate_features: hour/day, spatial, historical")
    crime = {
        "crime_id": "c1",
        "crime_type": "upi_fraud",
        "timestamp": "2026-09-16T14:30:00Z",
        "location": {"lat": 12.97, "lng": 77.59},
        "amount": 45000.0,
    }
    candidate = {
        "atm_id": "atm-a",
        "location": {"lat": 12.98, "lng": 77.60},
        "atm_historical_risk": 0.78,
        "spatial_features": {
            "distance_from_crime": 0.85,
            "nearby_crime_density": 7.2,
        },
    }
    recent_txns = [
        {"atm_id": "atm-a", "timestamp": "2026-09-16T14:00:00Z", "amount": 1000.0},
        {"atm_id": "atm-a", "timestamp": "2026-09-16T13:45:00Z", "amount": 2000.0},
        {"atm_id": "atm-a", "timestamp": "2026-09-16T10:00:00Z", "amount": 3000.0},
        {"atm_id": "atm-a", "timestamp": "2026-09-16T07:00:00Z", "amount": 4000.0},
        {"atm_id": "atm-b", "timestamp": "2026-09-16T14:10:00Z", "amount": 5000.0},
        {"atm_id": "atm-a", "timestamp": "2026-09-16T14:40:00Z", "amount": 6000.0},
        {"atm_id": "atm-a", "timestamp": "2026-09-16T14:30:00+05:30", "amount": 7000.0},
    ]
    try:
        feats = build_candidate_features(crime, candidate, recent_txns)
        failures += 0 if check("hour_of_day extracted from timestamp",
                                feats["hour_of_day"] == 14.0,
                                f"got {feats['hour_of_day']}") else 1
        failures += 0 if check("day_of_week extracted from timestamp (Wed=2)",
                                feats["day_of_week"] == 2.0,
                                f"got {feats['day_of_week']}") else 1
        failures += 0 if check("amount copied from crime.amount",
                                feats["amount"] == 45000.0) else 1
        failures += 0 if check("distance_from_crime copied from spatial_features",
                                feats["distance_from_crime"] == 0.85) else 1
        failures += 0 if check("nearby_crime_density copied from spatial_features",
                                feats["nearby_crime_density"] == 7.2) else 1
        failures += 0 if check("atm_historical_risk copied from candidate",
                                feats["atm_historical_risk"] == 0.78) else 1
        failures += 0 if check("atm_id preserved", feats["atm_id"] == "atm-a") else 1
    except Exception as exc:
        failures += 1
        check("build_candidate_features() spatial/temporal test", False, str(exc))

    print("\n[Test 10] build_candidate_features: 1h/6h counts and ATM filter")
    try:
        feats = build_candidate_features(crime, candidate, recent_txns)
        # 1h window [13:30Z, 14:30Z]: 14:00Z, 13:45Z  (not 10:00, 07:00, future 14:40,
        # not atm-b, not 14:30+05:30 which is 09:00Z)
        failures += 0 if check("txns_last_1h counts only this ATM in prior 1h",
                                feats["txns_last_1h"] == 2.0,
                                f"got {feats['txns_last_1h']}") else 1
        # 6h window [08:30Z, 14:30Z]: 14:00, 13:45, 10:00  (not 07:00, future, atm-b,
        # not 09:00Z from +05:30 offset? 14:30+05:30 = 09:00Z which IS inside 6h)
        # Recalculate: 14:30+05:30 = 09:00 UTC, window start 08:30 UTC → INCLUDED in 6h.
        # So 6h count = 14:00, 13:45, 10:00, 09:00Z(offset) = 4. Not atm-b, not 07:00, not 14:40.
        failures += 0 if check("txns_last_6h counts this ATM in prior 6h",
                                feats["txns_last_6h"] == 4.0,
                                f"got {feats['txns_last_6h']}") else 1
        failures += 0 if check("withdrawal_frequency matches 6h count (documented assumption)",
                                feats["withdrawal_frequency"] == feats["txns_last_6h"]) else 1
        failures += 0 if check("other ATM transactions are excluded",
                                feats["txns_last_1h"] == 2.0) else 1
    except Exception as exc:
        failures += 1
        check("build_candidate_features() txn-count test", False, str(exc))

    print("\n[Test 11] build_candidate_features: timezone-aware timestamp hour")
    try:
        ist_crime = dict(crime)
        ist_crime["timestamp"] = "2026-09-16T14:30:00+05:30"
        feats_ist = build_candidate_features(ist_crime, candidate, [])
        failures += 0 if check("hour uses the timestamp clock (14), not converted UTC",
                                feats_ist["hour_of_day"] == 14.0,
                                f"got {feats_ist['hour_of_day']}") else 1
        failures += 0 if check("empty recent_transactions yields zero counts",
                                feats_ist["txns_last_1h"] == 0.0
                                and feats_ist["txns_last_6h"] == 0.0) else 1
    except Exception as exc:
        failures += 1
        check("build_candidate_features() timezone hour test", False, str(exc))

    print("\n[Test 12] build_candidate_features: missing/invalid values rejected")
    try:
        build_candidate_features({"timestamp": "2026-09-16T14:30:00Z"}, candidate, [])
        failures += 1
        check("KeyError for missing crime.amount", False, "no exception")
    except KeyError:
        failures += 0 if check("KeyError for missing crime.amount", True) else 1
    except Exception as exc:
        failures += 1
        check("KeyError for missing crime.amount", False, str(exc))

    try:
        bad_ts = dict(crime)
        bad_ts["timestamp"] = "not-a-timestamp"
        build_candidate_features(bad_ts, candidate, [])
        failures += 1
        check("ValueError for invalid crime.timestamp", False, "no exception")
    except ValueError:
        failures += 0 if check("ValueError for invalid crime.timestamp", True) else 1
    except Exception as exc:
        failures += 1
        check("ValueError for invalid crime.timestamp", False, str(exc))

    try:
        bad_spatial = {
            "atm_id": "atm-a",
            "atm_historical_risk": 0.5,
            "spatial_features": {
                "distance_from_crime": float("nan"),
                "nearby_crime_density": 1.0,
            },
        }
        build_candidate_features(crime, bad_spatial, [])
        failures += 1
        check("ValueError for NaN spatial feature", False, "no exception")
    except ValueError:
        failures += 0 if check("ValueError for NaN spatial feature", True) else 1
    except Exception as exc:
        failures += 1
        check("ValueError for NaN spatial feature", False, str(exc))

    try:
        missing_spatial = {
            "atm_id": "atm-a",
            "atm_historical_risk": 0.5,
        }
        build_candidate_features(crime, missing_spatial, [])
        failures += 1
        check("KeyError for missing spatial_features", False, "no exception")
    except KeyError:
        failures += 0 if check("KeyError for missing spatial_features", True) else 1
    except Exception as exc:
        failures += 1
        check("KeyError for missing spatial_features", False, str(exc))

    # ==================================================================
    # Step 9B: ModelInterface.predict() — end-to-end contract pipeline
    # ==================================================================
    print("\n[Test 13] ModelInterface.predict(): valid multi-ATM contract payload")
    contract_payload = {
        "crime": {
            "crime_id": "c1",
            "crime_type": "upi_fraud",
            "timestamp": "2026-09-16T14:30:00Z",
            "location": {"lat": 12.97, "lng": 77.59},
            "amount": 45000.0,
        },
        "candidate_atms": [
            {
                "atm_id": "atm-close",
                "location": {"lat": 12.98, "lng": 77.60},
                "atm_historical_risk": 0.78,
                "spatial_features": {
                    "distance_from_crime": 0.85,
                    "nearby_crime_density": 7.2,
                },
            },
            {
                "atm_id": "atm-mid",
                "location": {"lat": 13.00, "lng": 77.62},
                "atm_historical_risk": 0.50,
                "spatial_features": {
                    "distance_from_crime": 3.5,
                    "nearby_crime_density": 3.0,
                },
            },
            {
                "atm_id": "atm-far",
                "location": {"lat": 13.10, "lng": 77.70},
                "atm_historical_risk": 0.10,
                "spatial_features": {
                    "distance_from_crime": 12.0,
                    "nearby_crime_density": 0.5,
                },
            },
        ],
        "recent_transactions": [
            {"atm_id": "atm-close", "timestamp": "2026-09-16T14:00:00Z", "amount": 1000},
            {"atm_id": "atm-close", "timestamp": "2026-09-16T13:45:00Z", "amount": 2000},
            {"atm_id": "atm-mid",   "timestamp": "2026-09-16T14:10:00Z", "amount": 500},
        ],
    }
    try:
        mi = ModelInterface()  # no K → return all candidates
        result = mi.predict(contract_payload)
        preds = result["predictions"]
        failures += 0 if check("returns a dict", isinstance(result, dict)) else 1
        failures += 0 if check("status is 'ok'", result.get("status") == "ok",
                                f"got {result.get('status')}") else 1
        failures += 0 if check("model_version is a non-empty string",
                                isinstance(result.get("model_version"), str)
                                and len(result["model_version"]) > 0,
                                f"got {result.get('model_version')!r}") else 1
        failures += 0 if check("predictions is a list",
                                isinstance(preds, list)) else 1
        failures += 0 if check("returned 3 predictions (one per ATM)",
                                len(preds) == 3, f"got {len(preds)}") else 1
        failures += 0 if check("each prediction has atm_id, risk_score, confidence",
                                all("atm_id" in p and "risk_score" in p
                                    and "confidence" in p for p in preds)) else 1
        # Verify scores are valid floats in [0, 1]
        all_valid = all(
            isinstance(p["risk_score"], float)
            and 0.0 <= p["risk_score"] <= 1.0
            for p in preds
        )
        failures += 0 if check("all risk_scores are floats in [0, 1]", all_valid) else 1
        print(f"        predictions = {[(p['atm_id'], round(p['risk_score'], 6)) for p in preds]}")
    except Exception as exc:
        failures += 1
        check("ModelInterface.predict() valid payload", False, str(exc))

    # ------------------------------------------------------------------
    # Test 14: predictions ranked descending by risk_score
    # ------------------------------------------------------------------
    print("\n[Test 14] ModelInterface.predict(): ranked highest risk first")
    try:
        mi = ModelInterface()
        result = mi.predict(contract_payload)
        preds = result["predictions"]
        scores = [p["risk_score"] for p in preds]
        descending = all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))
        failures += 0 if check("predictions sorted by risk_score descending",
                                descending, f"scores={[round(s, 6) for s in scores]}") else 1
        # The closest ATM with highest historical risk should rank first
        failures += 0 if check("closest, highest-risk ATM is first",
                                preds[0]["atm_id"] == "atm-close",
                                f"got {preds[0]['atm_id']}") else 1
    except Exception as exc:
        failures += 1
        check("ModelInterface.predict() ranking order", False, str(exc))

    # ------------------------------------------------------------------
    # Test 15: model_version matches the trained model bundle
    # ------------------------------------------------------------------
    print("\n[Test 15] ModelInterface.predict(): model_version returned")
    try:
        mi = ModelInterface()
        result = mi.predict(contract_payload)
        mv = result["model_version"]
        # Cross-check with a direct predict_single() call
        direct = predict_single(
            hour_of_day=14, day_of_week=2, amount=45000.0,
            distance_from_crime=0.85, atm_historical_risk=0.78,
            txns_last_1h=0, txns_last_6h=0,
            nearby_crime_density=7.2, withdrawal_frequency=0,
        )
        failures += 0 if check("model_version matches predict_single()",
                                mv == direct["model_version"],
                                f"interface={mv!r}, direct={direct['model_version']!r}") else 1
    except Exception as exc:
        failures += 1
        check("ModelInterface.predict() model_version", False, str(exc))

    # ------------------------------------------------------------------
    # Test 16: K respected when set via constructor
    # ------------------------------------------------------------------
    print("\n[Test 16] ModelInterface(k=2): K limits predictions")
    try:
        mi_k2 = ModelInterface(k=2)
        result_k2 = mi_k2.predict(contract_payload)
        preds_k2 = result_k2["predictions"]
        failures += 0 if check("K=2 returns exactly 2 predictions",
                                len(preds_k2) == 2, f"got {len(preds_k2)}") else 1
        # Should still be ranked descending
        if len(preds_k2) >= 2:
            failures += 0 if check("K=2 predictions still ranked descending",
                                    preds_k2[0]["risk_score"] >= preds_k2[1]["risk_score"]) else 1
        # K=1 returns exactly 1
        mi_k1 = ModelInterface(k=1)
        result_k1 = mi_k1.predict(contract_payload)
        failures += 0 if check("K=1 returns exactly 1 prediction",
                                len(result_k1["predictions"]) == 1,
                                f"got {len(result_k1['predictions'])}") else 1
    except Exception as exc:
        failures += 1
        check("ModelInterface K-limit test", False, str(exc))

    # ------------------------------------------------------------------
    # Test 17: empty candidate_atms handled safely
    # ------------------------------------------------------------------
    print("\n[Test 17] ModelInterface.predict(): empty candidate_atms")
    try:
        mi = ModelInterface()
        empty_payload = {
            "crime": contract_payload["crime"],
            "candidate_atms": [],
            "recent_transactions": [],
        }
        result_empty = mi.predict(empty_payload)
        failures += 0 if check("status is 'ok'",
                                result_empty["status"] == "ok") else 1
        failures += 0 if check("predictions is an empty list",
                                result_empty["predictions"] == [],
                                f"got {result_empty['predictions']}") else 1
        failures += 0 if check("model_version still returned",
                                isinstance(result_empty["model_version"], str)
                                and len(result_empty["model_version"]) > 0) else 1
    except Exception as exc:
        failures += 1
        check("ModelInterface.predict() empty candidates", False, str(exc))

    # ------------------------------------------------------------------
    # Test 18: missing candidate_atms key defaults to empty
    # ------------------------------------------------------------------
    print("\n[Test 18] ModelInterface.predict(): missing candidate_atms key")
    try:
        mi = ModelInterface()
        minimal_payload = {"crime": contract_payload["crime"]}
        result_min = mi.predict(minimal_payload)
        failures += 0 if check("status is 'ok'",
                                result_min["status"] == "ok") else 1
        failures += 0 if check("predictions is an empty list",
                                result_min["predictions"] == []) else 1
    except Exception as exc:
        failures += 1
        check("ModelInterface.predict() missing key", False, str(exc))

    # ==================================================================
    # Step 10: Confidence handling
    # ==================================================================
    print("\n[Test 19] predict_single(): confidence is separate from risk_score")
    try:
        # High-signal: risk_score should be high, confidence should be high
        r_high = predict_single(
            hour_of_day=14, day_of_week=2, amount=45000.0,
            distance_from_crime=0.85, atm_historical_risk=0.78,
            txns_last_1h=12, txns_last_6h=38,
            nearby_crime_density=7.2, withdrawal_frequency=54.0,
        )
        # Low-signal: risk_score should be low, confidence should be high
        # (model is confident it is NOT the withdrawal location)
        r_low = predict_single(
            hour_of_day=14, day_of_week=2, amount=45000.0,
            distance_from_crime=11.30, atm_historical_risk=0.15,
            txns_last_1h=0, txns_last_6h=4,
            nearby_crime_density=0.8, withdrawal_frequency=8.5,
        )
        failures += 0 if check("high-signal risk_score > low-signal risk_score",
                                r_high["risk_score"] > r_low["risk_score"],
                                f"{r_high['risk_score']:.4f} vs {r_low['risk_score']:.4f}") else 1
        failures += 0 if check("confidence and risk_score are different keys",
                                "confidence" in r_high and "risk_score" in r_high
                                and r_high["confidence"] != r_high.get("__none__")) else 1
        failures += 0 if check("high-signal confidence >= 0.5",
                                r_high["confidence"] >= 0.5) else 1
        failures += 0 if check("low-signal confidence >= 0.5",
                                r_low["confidence"] >= 0.5,
                                f"got {r_low['confidence']:.6f}") else 1
        print(f"        high: risk={r_high['risk_score']:.4f}, conf={r_high['confidence']:.4f}")
        print(f"        low:  risk={r_low['risk_score']:.4f}, conf={r_low['confidence']:.4f}")
    except Exception as exc:
        failures += 1
        check("predict_single() confidence test", False, str(exc))

    print("\n[Test 20] ModelInterface: high-confidence payload returns status 'ok'")
    try:
        mi = ModelInterface()  # default confidence_floor=0.35
        result = mi.predict(contract_payload)
        failures += 0 if check("status is 'ok'", result["status"] == "ok",
                                f"got {result['status']}") else 1
        failures += 0 if check("predictions are non-empty",
                                len(result["predictions"]) > 0) else 1
        # All predictions should have confidence
        for p in result["predictions"]:
            failures += 0 if check(
                f"  {p['atm_id']}: confidence in [0,1]",
                isinstance(p["confidence"], float) and 0.0 <= p["confidence"] <= 1.0,
                f"got {p.get('confidence')}",
            ) else 1
    except Exception as exc:
        failures += 1
        check("ModelInterface high-confidence test", False, str(exc))

    print("\n[Test 21] ModelInterface: insufficient_confidence via high confidence_floor")
    try:
        # Set confidence_floor unrealistically high (1.1) so it always triggers.
        # This is deterministic and does not depend on model behavior.
        mi_strict = ModelInterface(confidence_floor=1.1)
        result_strict = mi_strict.predict(contract_payload)
        failures += 0 if check("status is 'insufficient_confidence'",
                                result_strict["status"] == "insufficient_confidence",
                                f"got {result_strict['status']}") else 1
        failures += 0 if check("predictions list is empty",
                                result_strict["predictions"] == [],
                                f"got {len(result_strict['predictions'])} predictions") else 1
        failures += 0 if check("model_version still returned",
                                isinstance(result_strict["model_version"], str)
                                and len(result_strict["model_version"]) > 0) else 1
    except Exception as exc:
        failures += 1
        check("ModelInterface insufficient_confidence test", False, str(exc))

    print("\n[Test 22] ModelInterface: confidence_floor=0.0 never triggers insufficient")
    try:
        mi_zero = ModelInterface(confidence_floor=0.0)
        result_zero = mi_zero.predict(contract_payload)
        failures += 0 if check("status is 'ok' with floor=0.0",
                                result_zero["status"] == "ok") else 1
        failures += 0 if check("predictions returned with floor=0.0",
                                len(result_zero["predictions"]) > 0) else 1
    except Exception as exc:
        failures += 1
        check("ModelInterface confidence_floor=0 test", False, str(exc))

    print("\n[Test 23] DEFAULT_CONFIDENCE_FLOOR is 0.35")
    failures += 0 if check("DEFAULT_CONFIDENCE_FLOOR == 0.35",
                            DEFAULT_CONFIDENCE_FLOOR == 0.35,
                            f"got {DEFAULT_CONFIDENCE_FLOOR}") else 1

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
