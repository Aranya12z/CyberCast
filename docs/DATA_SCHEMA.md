# DATA_SCHEMA.md — PostgreSQL Schema
**Owner:** P1 + P5. **All other roles: READ ONLY** — ML (P2) and GIS (P3) consume data via the backend/API, not by writing their own direct DB access layer, unless explicitly agreed with P1/P5.

One PostgreSQL database for MVP. No micro-databases, no premature normalization, no PostGIS unless an ADR justifies it.

## Core Tables

### `crimes`
| column | type | notes |
|---|---|---|
| crime_id | UUID/PK | |
| crime_type | text | |
| timestamp | timestamptz | |
| latitude | double precision | |
| longitude | double precision | |
| amount | numeric | |

### `atms`
| column | type | notes |
|---|---|---|
| atm_id | UUID/PK | |
| latitude | double precision | |
| longitude | double precision | |
| bank | text | |
| area | text | |
| historical_risk_score | numeric | rolling risk score, updated offline (not by request-time inference); this is the `atm_historical_risk` value the backend attaches to each candidate before calling ML — see `ML_GIS_CONTRACTS.md` §1 |

### `transactions`
| column | type | notes |
|---|---|---|
| transaction_id | UUID/PK | |
| atm_id | UUID/FK → atms | |
| timestamp | timestamptz | |
| amount | numeric | |
| account_id | text | synthetic/anonymized for MVP |

### `predictions`
| column | type | notes |
|---|---|---|
| prediction_id | UUID/PK | one row per prediction *run* |
| crime_id | UUID/FK → crimes | |
| generated_at | timestamptz | |
| model_version | text | see `model_metadata` |
| status | text | ok / insufficient_confidence / insufficient_evidence |

### `prediction_results`
| column | type | notes |
|---|---|---|
| result_id | UUID/PK | |
| prediction_id | UUID/FK → predictions | |
| atm_id | UUID/FK → atms | |
| risk_score | numeric | |
| confidence | numeric | |
| predicted_window_start | timestamptz | |
| predicted_window_end | timestamptz | |

### `prediction_features`
| column | type | notes |
|---|---|---|
| feature_id | UUID/PK | |
| result_id | UUID/FK → prediction_results | **not** `predictions` — a prediction *run* produces multiple Top-K ATM results, and the explanation (feature contributions) is per candidate ATM, not per run. Fixed from an earlier draft that pointed this at `predictions.prediction_id`, which would have mixed every candidate's features into one bucket. |
| feature_name | text | e.g. distance_from_crime |
| feature_value | numeric | |
| contribution | text | high/medium/low, feeds explanation |

### `alerts`
| column | type | notes |
|---|---|---|
| alert_id | UUID/PK | |
| prediction_id | UUID/FK → predictions | |
| atm_id | UUID/FK → atms | |
| severity | text | low/medium/high |
| created_at | timestamptz | |
| status | text | new/acknowledged/resolved |
| channel | text | dashboard/mock_sms/mock_email |

### `users`
| column | type | notes |
|---|---|---|
| user_id | UUID/PK | |
| name | text | |
| role | text | investigator / bank_analyst / administrator — single enum-like text column |
| password_hash | text | bcrypt hash; never store or log plaintext |

Note: there is deliberately **no separate `roles` table** for MVP — three
fixed roles don't justify a many-to-many join table. If role permissions
need to vary per-user beyond the fixed three, that's a `[FUTURE]` schema
change requiring an ADR, not a silent addition.

### `audit_logs`
| column | type | notes |
|---|---|---|
| event_id | UUID/PK | |
| user_id | UUID/FK → users | |
| action | text | e.g. prediction_generated, alert_acknowledged |
| timestamp | timestamptz | |
| resource | text | e.g. crime_id / prediction_id affected |
| metadata | jsonb | |

### `model_metadata`
| column | type | notes |
|---|---|---|
| model_version | text/PK | |
| trained_at | timestamptz | |
| algorithm | text | random_forest / xgboost |
| eval_metrics | jsonb | |

## Key Relationships
```
Crime (1) ──< Prediction (run) (1) ──< Prediction Result (many, Top-K rows)
Prediction Result (1) ──< Prediction Feature (many)
Prediction Result (1) ──< Alert (0..1, if threshold met)
ATM (1) ──< Transaction (many)
ATM (1) ──< Prediction Result (many, across different runs)
```

## Rules
- Do not add tables for things that are `[FUTURE]` (e.g., no multi-tenant/jurisdiction tables in MVP).
- Any schema change goes through P1/P5 and gets reflected here before code is merged — this is the source of truth, not the ORM models.
