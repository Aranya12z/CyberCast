"""
CyberCast ML Layer - Random Forest Model Training Script (P2)
Trains a RandomForestClassifier using the 9 contract-specified features.
Reference: docs/ML_SPEC.md, docs/ML_GIS_CONTRACTS.md, docs/SETUP.md
"""

import datetime
import pickle
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Ensure CyberCast root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.features import FEATURE_NAMES, TARGET_NAME, prepare_training_data
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

MODEL_VERSION = "rf_v1_20260917"
DEFAULT_DATASET_PATH = PROJECT_ROOT / "data" / "synthetic" / "synthetic_atm_withdrawals.csv"
MODELS_DIR = PROJECT_ROOT / "ml" / "models"
PRIMARY_MODEL_FILE = MODELS_DIR / "latest.pkl"
VERSIONED_MODEL_FILE = MODELS_DIR / f"{MODEL_VERSION}.pkl"


def precision_at_k(y_true: List[int], y_prob: List[float], k: int = 5) -> float:
    """
    Precision@K: of the top-K candidates ranked by predicted probability,
    how many are actual withdrawal locations?
    Relevant for the Top-K ranking use case per ML_SPEC.md and ARCHITECTURE.md §4.
    """
    paired = sorted(zip(y_prob, y_true), key=lambda x: x[0], reverse=True)
    top_k = [label for _, label in paired[:k]]
    return sum(top_k) / k if k > 0 else 0.0


def train_and_evaluate(
    dataset_path: Path = DEFAULT_DATASET_PATH,
    random_state: int = 42,
    test_size: float = 0.2,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Loads features, trains a RandomForestClassifier, evaluates metrics,
    and serializes the trained model bundle to ml/models/.
    """
    print("=" * 62)
    print(f"  CYBERCAST ML MODEL TRAINING  (Version: {MODEL_VERSION})")
    print("=" * 62)

    # 1. Load X and y using existing feature preparation module
    print(f"\n[1] Loading dataset from: {dataset_path}")
    X, y, feature_names = prepare_training_data(dataset_path)
    total_samples = len(X)
    print(f"    Loaded {total_samples} samples with {len(feature_names)} features.")

    # 2. Split dataset into train and test sets
    print(f"\n[2] Splitting dataset (test_size={test_size}, random_state={random_state}, stratify=y)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )
    n_train = len(X_train)
    n_test = len(X_test)
    print(f"    Training samples : {n_train} ({n_train / total_samples * 100:.0f}%)")
    print(f"    Testing samples  : {n_test}  ({n_test / total_samples * 100:.0f}%)")

    # 3. Instantiate and train RandomForestClassifier
    print("\n[3] Training RandomForestClassifier...")
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=5,
        min_samples_split=2,
        min_samples_leaf=1,
        random_state=random_state,
    )
    rf_model.fit(X_train, y_train)
    print("    Training completed.")

    # 4. Evaluate on test set
    print("\n[4] Evaluation on hold-out test set")
    print("-" * 62)
    print("  NOTE: ALL metrics below apply to SYNTHETIC data only.")
    print("  They do NOT represent real-world performance.")
    print("  This prototype uses artificially generated data for the MVP.")
    print("-" * 62)

    y_pred = rf_model.predict(X_test)
    y_prob_arr = rf_model.predict_proba(X_test)[:, 1]
    y_prob = list(y_prob_arr)

    acc       = float(accuracy_score(y_test, y_pred))
    prec      = float(precision_score(y_test, y_pred, zero_division=0))
    rec       = float(recall_score(y_test, y_pred, zero_division=0))
    f1        = float(f1_score(y_test, y_pred, zero_division=0))
    roc       = float(roc_auc_score(y_test, y_prob_arr))
    pat5      = precision_at_k(y_test, y_prob, k=5)

    metrics = {
        "accuracy":       acc,
        "precision":      prec,
        "recall":         rec,
        "f1_score":       f1,
        "roc_auc":        roc,
        "precision_at_5": pat5,
    }

    print(f"\n    {'ACCURACY':<18}: {acc:.4f}")
    print(f"    {'PRECISION':<18}: {prec:.4f}")
    print(f"    {'RECALL':<18}: {rec:.4f}")
    print(f"    {'F1_SCORE':<18}: {f1:.4f}")
    print(f"    {'ROC_AUC':<18}: {roc:.4f}")
    print(f"    {'PRECISION@5 (Top-K)':<18}: {pat5:.4f}")

    # Full per-class classification report (classification_report was previously imported but not printed)
    print("\n    --- Per-class Classification Report ---")
    report = classification_report(
        y_test,
        y_pred,
        target_names=["non-withdrawal (0)", "withdrawal (1)"],
        zero_division=0,
    )
    for line in report.splitlines():
        print(f"    {line}")

    # 5. Feature importances — global explainability context (ML_SPEC.md §Explainability)
    print("\n    --- Feature Importances (global, from trained Random Forest) ---")
    importance_pairs = sorted(
        zip(feature_names, rf_model.feature_importances_),
        key=lambda x: x[1],
        reverse=True,
    )
    for feat, imp in importance_pairs:
        bar = "#" * int(imp * 40)
        print(f"    {feat:<25}: {imp:.4f}  {bar}")

    # 6. Build model artifact bundle
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    artifact = {
        "model": rf_model,
        "model_version": MODEL_VERSION,
        "algorithm": "random_forest",
        "feature_names": feature_names,
        "target_name": TARGET_NAME,
        "eval_metrics": metrics,
        "eval_note": (
            "Metrics evaluated on SYNTHETIC data only. "
            "Do not claim real-world performance."
        ),
        "trained_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "train_samples": n_train,
        "test_samples": n_test,
        "random_state": random_state,
    }

    # 7. Save model to ml/models/
    print("\n[5] Saving model artifacts...")
    for target_path in (PRIMARY_MODEL_FILE, VERSIONED_MODEL_FILE):
        with open(target_path, "wb") as f:
            pickle.dump(artifact, f, protocol=pickle.HIGHEST_PROTOCOL)
        print(f"    Saved: {target_path}")

    # 8. Reload verification
    print("\n[6] Verifying saved model reload...")
    with open(PRIMARY_MODEL_FILE, "rb") as f:
        loaded_bundle = pickle.load(f)

    assert loaded_bundle["model_version"] == MODEL_VERSION, "Version mismatch on reload"
    assert loaded_bundle["feature_names"] == feature_names, "Feature names mismatch on reload"
    assert "eval_note" in loaded_bundle, "eval_note missing in reloaded bundle"
    sample_pred = loaded_bundle["model"].predict([X_test[0]])
    print(f"    Reload: SUCCESS (sample prediction = {sample_pred[0]})")

    print("\n" + "=" * 62)
    print("  TRAINING PROCESS FINISHED SUCCESSFULLY")
    print("=" * 62)

    summary = {
        "n_train": n_train,
        "n_test": n_test,
        "model": "RandomForestClassifier",
        "model_file": str(PRIMARY_MODEL_FILE),
        "versioned_file": str(VERSIONED_MODEL_FILE),
        "metrics": metrics,
    }
    return artifact, summary


if __name__ == "__main__":
    train_and_evaluate()
