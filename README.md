# Predictive Cybercrime Withdrawal Intelligence System — Project Docs

## Problem Statement
Development of a Predictive Analytics Framework for Cybercrime Complaints to Forecast Likely Cash Withdrawal Locations in Advance, Enabling Generation of Actionable Intelligence for Timely and Proactive Cybercrime Intervention.

## One-line North Star
> A predictive intelligence layer that helps existing cybercrime and financial systems act **before the next withdrawal happens.**

This is **not** a cybercrime complaint portal, not a generic crime dashboard, not "just an ML model," and not an ATM heatmap. It is a layer that turns complaints + transaction/location signals into **ranked, explained, time-boxed intelligence**.

---

## How to use this doc set

This project is split into **role-scoped specs**. Each file is written so that a human teammate *or* an AI coding agent (Claude Code, Cursor, etc.) working on that slice has everything it needs — and nothing it needs to guess at — without wandering into another owner's territory.

**Golden rule for every agent/teammate:** if a proposed change conflicts with `API_SPEC.md`, `DATA_SCHEMA.md`, or `ML_GIS_CONTRACTS.md`, **the contract wins**. Propose a contract change explicitly (via an ADR) rather than silently diverging.

| File | Owner | Purpose |
|---|---|---|
| `ARCHITECTURE.md` | P1 (you) | Master architecture, layers, data flow, north star, review checklist |
| `BACKEND_SPEC.md` | P1 + P5 (you) | FastAPI application layer, domain/orchestration layer, endpoint implementation |
| `FRONTEND_SPEC.md` | P4 | React dashboard, GIS map UI, components, state |
| `ML_SPEC.md` | P2 | Feature engineering, model, inference contract, evaluation |
| `GIS_SPEC.md` | P3 | Spatial analytics, proximity/hotspot logic, GeoJSON generation |
| `API_SPEC.md` | Shared (P1 owns, all read) | Every REST endpoint, request/response schema |
| `DATA_SCHEMA.md` | Shared (P1/P5 own, all read) | PostgreSQL schema, entity relationships |
| `ML_GIS_CONTRACTS.md` | Shared (P2/P3 own, P5 reads) | ML input/output contract, GeoJSON feature contract |
| `INTEGRATION_SPEC.md` | P1 | Cross-cutting rules: contract-first process, team boundaries, AI-agent guardrails |
| `ADRS.md` | P1 | Architecture Decision Records for major choices |
| `SETUP.md` | Shared | Repo layout, local dev setup, environment variables |
| `AGENTS.md` | P1 | **Read this first if you're an AI coding agent.** Entry-point hierarchy that routes you to your role file and the shared contracts you need. |

## Team → File Map

- **P1 (You) — Architecture + Integration:** `ARCHITECTURE.md`, `INTEGRATION_SPEC.md`, `ADRS.md`, and co-owns `API_SPEC.md` / `DATA_SCHEMA.md`.
- **P2 — ML:** `ML_SPEC.md` (+ reads `ML_GIS_CONTRACTS.md`, `API_SPEC.md`).
- **P3 — GIS:** `GIS_SPEC.md` (+ reads `ML_GIS_CONTRACTS.md`, `API_SPEC.md`).
- **P4 — Frontend:** `FRONTEND_SPEC.md` (+ reads `API_SPEC.md` only — never touches backend/ML/GIS code).
- **P5 — Backend Engineering:** `BACKEND_SPEC.md` (+ reads/enforces `API_SPEC.md`, `DATA_SCHEMA.md`, `ML_GIS_CONTRACTS.md`).
- **P6 — Domain/Product:** reads `ARCHITECTURE.md` §9 (Explainability) and `INTEGRATION_SPEC.md` §5 (Judge-Defensibility Checklist) — validates real-world plausibility, does not own technical architecture.

## Categories to never blur (used throughout every doc)
- **IMPLEMENTED** — what the current prototype actually does today.
- **MVP TARGET** — what we intend to finish for SIH.
- **FUTURE / NATIONAL SCALE** — what would be needed for production at scale. Never presented as already built.

## MVP Tech Stack (fixed — do not add technologies without an ADR)
- **Frontend:** React, Tailwind CSS, React-Leaflet/Leaflet, Recharts
- **Backend:** FastAPI, Python
- **Database:** PostgreSQL (single instance, no microservices, no PostGIS unless an ADR justifies it)
- **ML:** scikit-learn, Random Forest and/or XGBoost
- **Geospatial:** GeoJSON, GeoPandas (basic use only)
- **Integration/Testing:** REST, Postman, pytest, Git/GitHub

No Kubernetes, Kafka, Redis, Elasticsearch, Spark, Apache Sedona, PostGIS, microservices, GraphQL, service mesh, federated learning, or advanced MLOps in the MVP unless an ADR in `ADRS.md` explicitly justifies it.
