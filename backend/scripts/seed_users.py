"""
backend/scripts/seed_users.py — Seed one placeholder user per role for local dev.

Usage (from backend/):
    python scripts/seed_users.py

Creates exactly three users:
  - investigator   / investigator@cybercast.local  / CyberCast@Inv2026
  - bank_analyst   / analyst@cybercast.local       / CyberCast@Anl2026
  - administrator  / admin@cybercast.local         / CyberCast@Adm2026

IMPORTANT:
  - These are PLACEHOLDER credentials for local development ONLY.
  - Never use these in staging, production, or any real deployment.
  - No real personal information is stored here (ARCHITECTURE.md §13).

Idempotent: running this script twice does NOT create duplicate users.
If a user with the same name already exists the script skips that row
and prints a "skipped (already exists)" message.

Why username-as-name? The auth router identifies users by User.name
(the login field), matching the current LoginRequest schema. If the
auth schema is updated to an email field, update this script to match.

Architecture references:
  DATA_SCHEMA.md §users (roles: investigator / bank_analyst / administrator)
  ARCHITECTURE.md §8 (RBAC — least-privilege access)
  BACKEND_SPEC.md §Auth & RBAC
"""
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
from app.core.security import hash_password  # noqa: E402  — reuse existing impl
from app.models import user as _user_module  # noqa: E402,F401  — ensures User is registered
from app.models.user import User  # noqa: E402


# ---------------------------------------------------------------------------
# Placeholder credentials
# Format: (name/login, role, email_label, plaintext_password)
# ---------------------------------------------------------------------------
SEED_USERS = [
    {
        "name":     "investigator",
        "role":     "investigator",
        "email":    "investigator@cybercast.local",
        "password": "CyberCast@Inv2026",
    },
    {
        "name":     "bank_analyst",
        "role":     "bank_analyst",
        "email":    "analyst@cybercast.local",
        "password": "CyberCast@Anl2026",
    },
    {
        "name":     "administrator",
        "role":     "administrator",
        "email":    "admin@cybercast.local",
        "password": "CyberCast@Adm2026",
    },
]


def seed():
    """
    Create the three seed users if they do not already exist.
    Prints credentials to stdout on creation so developers can log in immediately.
    """
    settings = get_settings()
    print(f"\n[seed_users] Connecting to: {settings.DATABASE_URL!r}")

    # Create tables if they don't exist yet (safe for SQLite tests; on Postgres,
    # alembic upgrade head should have been run first).
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    print()
    print("=" * 60)
    print("  CyberCast — Placeholder User Seed (LOCAL DEV ONLY)")
    print("  These credentials must NOT be used in production.")
    print("=" * 60)

    try:
        created = 0
        skipped = 0

        for spec in SEED_USERS:
            existing = db.query(User).filter(User.name == spec["name"]).first()
            if existing:
                print(f"  [SKIP]    role={spec['role']:15s}  user '{spec['name']}' already exists")
                skipped += 1
                continue

            user = User(
                user_id=uuid.uuid4(),
                name=spec["name"],
                role=spec["role"],
                password_hash=hash_password(spec["password"]),
            )
            db.add(user)
            db.flush()

            print(f"  [CREATED] role={spec['role']:15s}  "
                  f"login={spec['name']!r:20s}  "
                  f"email={spec['email']!r:35s}  "
                  f"password={spec['password']!r}")
            created += 1

        db.commit()

    except Exception as exc:
        db.rollback()
        print(f"\n[seed_users] ERROR: {exc}", file=sys.stderr)
        raise
    finally:
        db.close()

    print()
    print(f"  Done: {created} created, {skipped} skipped.")
    print("=" * 60)
    print()


if __name__ == "__main__":
    seed()
