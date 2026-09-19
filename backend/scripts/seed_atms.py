"""
backend/scripts/seed_atms.py — Seed representative ATM network for local dev.

Usage (from backend/):
    python scripts/seed_atms.py

Seeds 20 realistic ATMs clustered around Punjab (31.1–31.4 N, 75.5–75.9 E)
with varied historical risk scores (0.15 to 0.92) across major banking networks.

IMPORTANT:
  - These are PLACEHOLDER coordinates and risk profiles for local development ONLY.
  - Never use these in staging, production, or any real deployment.
  - No real operational telemetry or credentials are stored here (ARCHITECTURE.md §13).

Idempotent: running this script twice does NOT create duplicate ATMs.
If an ATM with the same bank and area already exists, the script skips that row
and prints a "skipped (already exists)" message.

Architecture references:
  DATA_SCHEMA.md §atms (fields: atm_id, latitude, longitude, bank, area, historical_risk_score)
  ML_GIS_CONTRACTS.md §1, §2
  BACKEND_SPEC.md §Data Seeding
"""
from __future__ import annotations

import os
import sys
import uuid

# Allow running from repo root OR from backend/
_script_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_script_dir)          # backend/
_repo_root   = os.path.dirname(_backend_dir)          # repo root
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# Set .env path explicitly so pydantic-settings finds it when the script
# is run from either backend/ or the repo root.
_env_path = os.path.join(_repo_root, ".env")
if not os.path.exists(_env_path):
    _env_path = os.path.join(_backend_dir, ".env")

os.environ.setdefault("ENV_FILE_PATH", _env_path)

from app.core.config import get_settings  # noqa: E402
from app.core.db import Base, SessionLocal, engine  # noqa: E402
from app.models import atm as _atm_module  # noqa: E402,F401  — ensures ATM is registered
from app.models.atm import ATM  # noqa: E402


# ---------------------------------------------------------------------------
# Seed ATMs dataset (Punjab region: Jalandhar / Phagwara / Ludhiana / Kapurthala)
# Coordinates: ~31.1 - 31.4 N, ~75.5 - 75.9 E
# ---------------------------------------------------------------------------
SEED_ATMS = [
    {
        "bank": "State Bank of India",
        "area": "Model Town, Jalandhar",
        "latitude": 31.3090,
        "longitude": 75.5792,
        "historical_risk_score": 0.88,
    },
    {
        "bank": "HDFC Bank",
        "area": "Civil Lines, Jalandhar",
        "latitude": 31.3260,
        "longitude": 75.5762,
        "historical_risk_score": 0.74,
    },
    {
        "bank": "Punjab National Bank",
        "area": "GT Road, Phagwara",
        "latitude": 31.2240,
        "longitude": 75.7708,
        "historical_risk_score": 0.92,
    },
    {
        "bank": "ICICI Bank",
        "area": "Rama Mandi, Jalandhar",
        "latitude": 31.3055,
        "longitude": 75.6184,
        "historical_risk_score": 0.65,
    },
    {
        "bank": "Axis Bank",
        "area": "Sarabha Nagar, Ludhiana",
        "latitude": 30.8872,
        "longitude": 75.8164,
        "historical_risk_score": 0.81,
    },
    {
        "bank": "Bank of Baroda",
        "area": "BMC Chowk, Jalandhar",
        "latitude": 31.3195,
        "longitude": 75.5841,
        "historical_risk_score": 0.53,
    },
    {
        "bank": "Canara Bank",
        "area": "Mall Road, Kapurthala",
        "latitude": 31.3802,
        "longitude": 75.3815,
        "historical_risk_score": 0.42,
    },
    {
        "bank": "Kotak Mahindra Bank",
        "area": "Urban Estate Phase II, Jalandhar",
        "latitude": 31.2874,
        "longitude": 75.6021,
        "historical_risk_score": 0.79,
    },
    {
        "bank": "Punjab National Bank",
        "area": "Nakodar Chowk, Jalandhar",
        "latitude": 31.3168,
        "longitude": 75.5670,
        "historical_risk_score": 0.61,
    },
    {
        "bank": "State Bank of India",
        "area": "Ferozepur Road, Ludhiana",
        "latitude": 30.8994,
        "longitude": 75.8236,
        "historical_risk_score": 0.70,
    },
    {
        "bank": "HDFC Bank",
        "area": "Satnampura, Phagwara",
        "latitude": 31.2185,
        "longitude": 75.7620,
        "historical_risk_score": 0.58,
    },
    {
        "bank": "IndusInd Bank",
        "area": "Jyoti Chowk, Jalandhar",
        "latitude": 31.3285,
        "longitude": 75.5721,
        "historical_risk_score": 0.49,
    },
    {
        "bank": "Union Bank of India",
        "area": "Clock Tower, Ludhiana",
        "latitude": 30.9125,
        "longitude": 75.8540,
        "historical_risk_score": 0.85,
    },
    {
        "bank": "State Bank of India",
        "area": "Sultanpur Lodhi Road, Kapurthala",
        "latitude": 31.3740,
        "longitude": 75.3900,
        "historical_risk_score": 0.33,
    },
    {
        "bank": "ICICI Bank",
        "area": "Law Gate, Phagwara",
        "latitude": 31.2482,
        "longitude": 75.7042,
        "historical_risk_score": 0.91,
    },
    {
        "bank": "Axis Bank",
        "area": "Cantt Railway Station Road, Jalandhar",
        "latitude": 31.2820,
        "longitude": 75.6295,
        "historical_risk_score": 0.46,
    },
    {
        "bank": "Punjab & Sind Bank",
        "area": "Basti Nau, Jalandhar",
        "latitude": 31.3210,
        "longitude": 75.5490,
        "historical_risk_score": 0.28,
    },
    {
        "bank": "HDFC Bank",
        "area": "Ghumar Mandi, Ludhiana",
        "latitude": 30.9020,
        "longitude": 75.8340,
        "historical_risk_score": 0.67,
    },
    {
        "bank": "Bank of India",
        "area": "Adampur Doaba, Jalandhar",
        "latitude": 31.4280,
        "longitude": 75.7205,
        "historical_risk_score": 0.22,
    },
    {
        "bank": "State Bank of India",
        "area": "Goraya Market, Jalandhar Highway",
        "latitude": 31.1305,
        "longitude": 75.7720,
        "historical_risk_score": 0.15,
    },
]


def seed():
    """
    Create the seed ATMs if they do not already exist.
    Prints ATM location summaries to stdout.
    """
    settings = get_settings()
    print(f"\n[seed_atms] Connecting to: {settings.DATABASE_URL!r}")

    # Create tables if they don't exist yet (safe for SQLite tests; on Postgres,
    # alembic upgrade head should have been run first).
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    print()
    print("=" * 70)
    print("  CyberCast — ATM Network Seed (LOCAL DEV ONLY)")
    print("  Populates representative ATM nodes in Punjab cluster.")
    print("=" * 70)

    try:
        created = 0
        skipped = 0

        for spec in SEED_ATMS:
            existing = (
                db.query(ATM)
                .filter(ATM.bank == spec["bank"], ATM.area == spec["area"])
                .first()
            )
            if existing:
                print(f"  [SKIP]    bank={spec['bank']:24s}  area={spec['area']:32s} (already exists)")
                skipped += 1
                continue

            atm = ATM(
                atm_id=uuid.uuid4(),
                bank=spec["bank"],
                area=spec["area"],
                latitude=spec["latitude"],
                longitude=spec["longitude"],
                historical_risk_score=spec["historical_risk_score"],
            )
            db.add(atm)
            db.flush()

            print(
                f"  [CREATED] bank={spec['bank']:24s}  "
                f"area={spec['area']:32s}  "
                f"lat/lng=({spec['latitude']:.4f}, {spec['longitude']:.4f})  "
                f"risk={spec['historical_risk_score']:.2f}"
            )
            created += 1

        db.commit()

    except Exception as exc:
        db.rollback()
        print(f"\n[seed_atms] ERROR: {exc}", file=sys.stderr)
        raise
    finally:
        db.close()

    print()
    print(f"  Done: {created} created, {skipped} skipped.")
    print("=" * 70)
    print()


if __name__ == "__main__":
    seed()
