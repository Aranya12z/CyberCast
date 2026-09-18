# CyberCast — Frontend & Intelligence Dashboard (P4)

This directory contains the **L1 Presentation Layer** for the **CyberCast Predictive Intelligence System** (Smart India Hackathon 2026).

---

## 1. Role Ownership & Boundaries (P4)

**Owner:** P4 — Frontend / Dashboard  
**Component:** `frontend/`  
**Governing Specs:** `docs/FRONTEND_SPEC.md`, `docs/API_SPEC.md`, `docs/ML_GIS_CONTRACTS.md` §2, `docs/ADRS.md`

### Hard Rules:
- **No Client-Side Computation:** The dashboard strictly visualizes intelligence provided by the backend API and ML/GIS modules. Risk likelihood, spatial distances, candidate ranking, and alert thresholds are **never** calculated client-side.
- **Contract Fidelity:** Field names, data types, and nesting match `docs/API_SPEC.md` and `docs/ML_GIS_CONTRACTS.md` §2 exactly.
- **Honest AI Reporting:** When model certainty falls below threshold (0.35), the UI honestly reports `status: "insufficient_confidence"` per `ARCHITECTURE.md` §10 without fabricating results.

---

## 2. Tech Stack

- **Framework:** React 18 (Vite)
- **Styling:** Tailwind CSS (Dark Command Tactical Theme)
- **GIS Map:** Leaflet & React-Leaflet with CartoDB Dark Matter tiles
- **Charts:** Recharts (Risk Likelihood vs Model Certainty)
- **Icons:** Lucide React

---

## 3. Directory Structure

```
frontend/
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── index.html
├── .env.example
├── public/
│   └── shield.svg
└── src/
    ├── main.jsx
    ├── App.jsx
    ├── index.css
    ├── api/
    │   ├── client.js                   # Unified API client with Mock/Live toggle
    │   └── mocks/                      # Strict contract fixtures
    │       ├── dashboardSummary.json   # /api/dashboard/summary
    │       ├── crimes.json             # /api/crimes
    │       ├── atmsGeoJSON.json        # ML_GIS_CONTRACTS.md §2 FeatureCollection
    │       ├── predictions.json        # /api/predictions/{crime_id} + edge cases
    │       ├── alerts.json             # /api/alerts
    │       └── intelligence.json       # /api/intelligence/{crime_id}
    ├── state/
    │   └── AppContext.jsx              # Role switcher, active incident state, data refresh
    ├── components/
    │   ├── layout/                     # Navbar, Sidebar, Role Switcher
    │   ├── common/                     # RiskBadge (ADR-006), ConfidenceBar, StatCard, StatusBanner
    │   ├── map/                        # LeafletMap, MapLegend
    │   ├── predictions/                # TopKTable (ADR-004/005), ExplanationList
    │   ├── alerts/                     # AlertCard, Alert Filters
    │   └── charts/                     # RiskDistributionChart (Recharts)
    └── pages/
        ├── Overview.jsx                # /overview: KPI stats, incident ingestion, audit log
        ├── GISMap.jsx                  # /map: Geospatial ATM hotspots & candidate inspector
        ├── Predictions.jsx             # /predictions: Top-K ranking & feature explanations
        ├── Alerts.jsx                  # /alerts: Severity triage & acknowledge workflow
        └── Intelligence.jsx            # /intelligence: Full incident dossier & briefing
```

---

## 4. Running the Dashboard Locally

### Prerequisites
- Node.js (v18+) and npm

### Installation
```bash
cd frontend
npm install
```

### Run Dev Server
```bash
npm run dev
```
The application will launch at `http://localhost:3000`.

### Production Build
```bash
npm run build
```

---

## 5. Architectural Decisions Implemented

1. **Top-K Ranked Locations (ADR-004):** The UI presents candidates ranked by `risk_score` descending rather than claiming certainty on a single ATM.
2. **Fixed 6-Hour Prediction Window (ADR-005):** Forecast windows are displayed uniformly as 6 hours from inference timestamp.
3. **Alert Thresholds & Severity Mapping (ADR-006):**
   - High Severity: `risk_score >= 0.7` AND `confidence >= 0.5`
   - Medium Severity: `0.4 <= risk_score < 0.7` AND `confidence >= 0.5`
4. **Non-Fabrication Policy:** Handled via `StatusBanner.jsx` when `status: "insufficient_confidence"` or `"insufficient_evidence"`.
5. **Dual Operating Modes:**
   - Mode A (Event-Triggered): Interactive "Run Model" trigger simulating synchronous complaint prediction pipeline.
   - Mode B (Continuous): Monitored through live alerts queue.
