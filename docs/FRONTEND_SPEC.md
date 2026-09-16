# FRONTEND_SPEC.md — React Dashboard Implementation Guide
**Owner:** P4. **Scope:** L1 (Presentation) layer only.
**Contract you must honor, not redefine:** `API_SPEC.md` — including the GeoJSON shape in `ML_GIS_CONTRACTS.md` §2.
**Do not touch:** backend code, ML code, spatial computation code. You render data; you never compute risk, distance, density, or predictions client-side. If a number or geometry isn't in the API response, ask for it to be added to `API_SPEC.md` — don't calculate it yourself.

---

## Tech
React, Tailwind CSS, React-Leaflet/Leaflet, Recharts.

## You can start immediately, without waiting on backend
Build a mock API client that returns fixtures matching `API_SPEC.md` exactly (same field names, same nesting). Swap the mock for real `fetch`/axios calls once backend endpoints are live — no component code should need to change if the mock fixtures were accurate.

## Directory structure (suggested)
```
frontend/
  src/
    pages/
      Overview.jsx
      GISMap.jsx
      Predictions.jsx
      Alerts.jsx
      Intelligence.jsx
    components/
      map/            # ATM markers, heatmap layer, risk-zone overlay
      predictions/     # risk/confidence cards, explanation list
      alerts/          # alert list, severity badge, acknowledge button
      charts/          # Recharts wrappers
      common/          # buttons, filters, tables
    api/
      client.js        # single place all API calls go through
      mocks/           # fixture JSON matching API_SPEC.md
    state/              # React context or lightweight store
    types/              # JSDoc/TS types mirroring API_SPEC.md schemas
```

## Pages & required content

### Overview
Total active alerts, high-risk prediction count, prediction statistics, recent activity feed. Pulls from `/api/dashboard/summary`.

### GIS
Heatmap, ATM markers, risk zones, predicted locations, filters. Renders the GeoJSON FeatureCollection from `ML_GIS_CONTRACTS.md` §2 directly — color/size markers by `risk_category`/`risk_score` from the `properties` object; do not recompute these.

### Predictions
Crime/case ID, predicted locations list, risk score, confidence, predicted window, explanation — sourced from `/api/predictions/{crime_id}`.

### Alerts
Severity, location, time, status, acknowledge action — sourced from `/api/alerts`, posts to `/api/alerts/{alert_id}/acknowledge`.

### Intelligence
Case information, prediction evidence, relevant patterns, generated summary — sourced from `/api/intelligence/{crime_id}`, which now has a concrete response shape in `API_SPEC.md` (`crime`, `latest_prediction`, `evidence[]`, `related_alerts[]`, `summary`). Render `evidence` the same way you render a prediction's `explanation` array — don't build a second explanation-rendering component for this page.

## Role-aware UI
The `/api/auth/me` role (`investigator` / `bank_analyst` / `administrator`) determines which panels/actions are visible. Keep this as a simple capability check, not duplicated business logic — the backend is the source of truth for what a role *can do*; the frontend just hides/shows accordingly.

## Explanation rendering
Each prediction's `explanation` array (`feature`, `value`, `contribution`) should render as a short human-readable reason list (e.g., "High historical ATM risk", "Close proximity to reported crime") — map `contribution: high/medium/low` to visual weight, don't invent new categories.

## What NOT to build here
No client-side risk scoring, no client-side distance/proximity math, no direct ML or spatial library calls, no direct DB access. If the dashboard needs a derived value, it must come from the API.
