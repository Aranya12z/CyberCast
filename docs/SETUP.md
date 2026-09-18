# SETUP.md — Repo Layout & Local Dev Setup
**Owner:** shared, maintained by P1/P5.

## Suggested monorepo layout
```
sih-project/
  docs/
    README.md
    ARCHITECTURE.md
    INTEGRATION_SPEC.md
    API_SPEC.md
    DATA_SCHEMA.md
    ML_GIS_CONTRACTS.md
    BACKEND_SPEC.md
    FRONTEND_SPEC.md
    ML_SPEC.md
    GIS_SPEC.md
    ADRS.md
    SETUP.md
  backend/          # P1 + P5
    app/
    scripts/        # one-off admin scripts (seed_users.py, etc.)
    tests/
    requirements.txt
  ml/               # P2 — trained/loaded by backend, developed independently
    features/
    models/
    train.py
    evaluate.py
  gis/              # P3 — imported by backend, developed independently
    spatial/
  frontend/         # P4
    src/
    package.json
  data/
    synthetic/      # CSVs / mock data for MVP — no real personal data, per ARCHITECTURE.md §13 (Data Privacy)
```

## Environment variables (backend `.env`, never commit real secrets)
```
DATABASE_URL=postgresql://user:password@localhost:5432/cybercast_db
JWT_SECRET=changeme-replace-in-production
MODEL_PATH=./ml/models/latest.pkl
ENV=development
```
Copy `.env.example` to `.env` and fill in real secrets before running locally. The default `DATABASE_URL` matches `docker-compose.yml` exactly — no edit needed for local dev.

## Local run
```bash
# 1. Start the local Postgres database (requires Docker / Docker Desktop)
#    Data persists in a named volume across restarts.
#    Use 'docker compose down -v' for a clean-slate wipe.
docker compose up -d

# 2. Backend
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Copy env and run DB migrations
cp ../.env.example ../.env   # already has working defaults for local dev
alembic upgrade head

# 4. Seed placeholder users (one per role — idempotent, safe to re-run)
python scripts/seed_users.py
# Printed output shows the plaintext credentials for local testing.

# 5. Start the backend API server
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# ML (offline training, run separately, produces model file backend loads)
cd ml
python train.py
```

## Git workflow
- One branch per feature/module (e.g., `feature/prediction-endpoint`, `feature/gis-map`), branched off `integration` — not off `main` directly.
- PRs from feature branches merge into `integration` first. This is where cross-module contract mismatches (a field the frontend expects that the backend doesn't send, an ML output shape that drifted from `ML_GIS_CONTRACTS.md`) surface and get caught before they reach `main`.
- `integration` merges into `main` only at agreed milestones (e.g., after a working end-to-end demo slice runs cleanly), reviewed by P1.
- Contract file changes (`API_SPEC.md`, `DATA_SCHEMA.md`, `ML_GIS_CONTRACTS.md`) require an `ADRS.md` entry if they're structural (not just a typo fix), and P1 review regardless of which branch they land on.

## Testing
- Backend: `pytest` for domain logic; Postman collection (kept in `backend/postman/`) mirroring `API_SPEC.md` for contract-level checks.
- Frontend: component-level checks against mock fixtures in `frontend/src/api/mocks/` that match `API_SPEC.md` exactly.
- ML: offline evaluation scripts (`ml/evaluate.py`) producing metrics documented per `ML_SPEC.md`.
