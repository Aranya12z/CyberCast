"""
CyberCast ML Layer - Offline Model Evaluation Script (P2)
Loads an already-trained model from ml/models/latest.pkl and evaluates it
against the synthetic dataset without retraining.

Reference: docs/ML_SPEC.md (offline metrics — precision@K, recall, calibration)
           docs/SETUP.md   (ml/evaluate.py runs offline evaluation)

Usage:
    py ml/evaluate.py
    py ml/evaluate.py --model ml/models/rf_v1_20260917.pkl
"""

import argparse
import pickle
import sys
from pathlib import Path
from typing import List

# Ensure CyberCast root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.features import prepare_training_data
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

DEFAULT_MODEL_PATH = PROJECT_ROOT / "ml" / "models" / "latest.pkl"
DEFAULT_DATASET_PATH = PROJECT_ROOT / "data" / "synthetic" / "synthetic_atm_withdrawals.csv"
# Must match the random_state used at training time for a reproducible split
EVAL_RANDOM_STATE = 42
EVAL_TEST_SIZE = 0.2


def precision_at_k(y_true: List[int], y_prob: List[float], k: int = 5) -> float:
    """
    Precision@K: fraction of actual withdrawal locations in the top-K
    candidates ranked by predicted probability.
    Relevant for the Top-K use case described in ARCHITECTURE.md §4.
    """
    paired = sorted(zip(y_prob, y_true), key=lambda x: x[0], reverse=True)
    top_k = [label for _, label in paired[:k]]
    return sum(top_k) / k if k > 0 else 0.0


def run_evaluation(
    model_path: Path = DEFAULT_MODEL_PATH,
    dataset_path: Path = DEFAULT_DATASET_PATH,
) -> None:
    print("=" * 62)
    print("  CYBERCAST ML - OFFLINE MODEL EVALUATION")
    print("=" * 62)
    print()

    # 1. Load model bundle
    print(f"[1] Loading model bundle from: {model_path}")
    if not model_path.exists():
        print(f"    ERROR: Model file not found at {model_path}")
        print("    Run ml/train.py first to produce a trained model.")
        sys.exit(1)

    with open(model_path, "rb") as f:
        bundle = pickle.load(f)

    print(f"    Model version  : {bundle.get('model_version', 'unknown')}")
    print(f"    Algorithm      : {bundle.get('algorithm', 'unknown')}")
    print(f"    Trained at     : {bundle.get('trained_at', 'unknown')}")
    print(f"    Feature count  : {len(bundle.get('feature_names', []))}")
    print(f"    Features       : {bundle.get('feature_names', [])}")
    model = bundle["model"]

    # 2. Load dataset and reproduce the same train/test split
    print(f"\n[2] Loading evaluation dataset from: {dataset_path}")
    X, y, feature_names = prepare_training_data(dataset_path)
    total = len(X)

    # Verify feature alignment between saved model and current data
    if bundle.get("feature_names") != feature_names:
        print("    WARNING: Feature names in saved model differ from current dataset.")

    _, X_test, _, y_test = train_test_split(
        X, y,
        test_size=EVAL_TEST_SIZE,
        random_state=EVAL_RANDOM_STATE,
        stratify=y,
    )
    n_test = len(X_test)
    print(f"    Total samples  : {total}")
    print(f"    Eval split     : {n_test} test samples  "
          f"(test_size={EVAL_TEST_SIZE}, random_state={EVAL_RANDOM_STATE})")

    # 3. Run predictions
    print("\n[3] Running predictions on test set...")
    y_pred = model.predict(X_test)
    y_prob_arr = model.predict_proba(X_test)[:, 1]
    y_prob = list(y_prob_arr)

    # 4. Compute and print all required metrics
    acc   = float(accuracy_score(y_test, y_pred))
    prec  = float(precision_score(y_test, y_pred, zero_division=0))
    rec   = float(recall_score(y_test, y_pred, zero_division=0))
    f1    = float(f1_score(y_test, y_pred, zero_division=0))
    roc   = float(roc_auc_score(y_test, y_prob_arr))
    pat5  = precision_at_k(y_test, y_prob, k=5)

    print("\n[4] Evaluation Results")
    print("-" * 62)
    print("  *** IMPORTANT: All metrics below apply to SYNTHETIC data. ***")
    print("  *** They do NOT reflect real-world model performance.     ***")
    print("-" * 62)
    print(f"\n    {'ACCURACY':<22}: {acc:.4f}")
    print(f"    {'PRECISION':<22}: {prec:.4f}")
    print(f"    {'RECALL':<22}: {rec:.4f}")
    print(f"    {'F1_SCORE':<22}: {f1:.4f}")
    print(f"    {'ROC_AUC':<22}: {roc:.4f}")
    print(f"    {'PRECISION@5 (Top-K)':<22}: {pat5:.4f}")

    # Full per-class classification report
    print("\n    --- Per-class Classification Report ---")
    report = classification_report(
        y_test,
        y_pred,
        target_names=["non-withdrawal (0)", "withdrawal (1)"],
        zero_division=0,
    )
    for line in report.splitlines():
        print(f"    {line}")

    # Feature importances
    print("\n    --- Feature Importances (global, from trained Random Forest) ---")
    importance_pairs = sorted(
        zip(feature_names, model.feature_importances_),
        key=lambda x: x[1],
        reverse=True,
    )
    for feat, imp in importance_pairs:
        bar = "#" * int(imp * 40)
        print(f"    {feat:<25}: {imp:.4f}  {bar}")

    print()
    print("=" * 62)
    print("  EVALUATION COMPLETE")
    print("=" * 62)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CyberCast offline ML evaluation")
    parser.add_argument(
        "--model",
        type=str,
        default=str(DEFAULT_MODEL_PATH),
        help="Path to a saved model .pkl bundle (default: ml/models/latest.pkl)",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=str(DEFAULT_DATASET_PATH),
        help="Path to evaluation CSV dataset",
    )
    args = parser.parse_args()
    run_evaluation(
        model_path=Path(args.model),
        dataset_path=Path(args.dataset),
    )
