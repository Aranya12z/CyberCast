/**
 * Data Schema Constants & Contract Definitions
 * Strictly mirrors docs/API_SPEC.md and docs/ML_GIS_CONTRACTS.md
 */

/**
 * Valid roles per docs/DATA_SCHEMA.md #users
 * @readonly
 * @enum {string}
 */
export const UserRoles = {
  INVESTIGATOR: 'investigator',
  BANK_ANALYST: 'bank_analyst',
  ADMINISTRATOR: 'administrator',
};

/**
 * Prediction run status values per docs/API_SPEC.md §80
 * @readonly
 * @enum {string}
 */
export const PredictionStatus = {
  OK: 'ok',
  INSUFFICIENT_CONFIDENCE: 'insufficient_confidence',
  INSUFFICIENT_EVIDENCE: 'insufficient_evidence',
};

/**
 * Alert severity levels per docs/ADRS.md ADR-006
 * @readonly
 * @enum {string}
 */
export const AlertSeverity = {
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low',
};

/**
 * ADR-006 Alert Trigger Evaluation Rule:
 * High: risk_score >= 0.7 AND confidence >= 0.5
 * Medium: 0.4 <= risk_score < 0.7 AND confidence >= 0.5
 * 
 * Note: Alert generation is owned by backend domain layer (alert_generation.py);
 * this helper is strictly for UI badge rendering verification.
 */
export const getSeverityFromScores = (riskScore, confidence) => {
  if (confidence < 0.5) return null;
  if (riskScore >= 0.7) return AlertSeverity.HIGH;
  if (riskScore >= 0.4) return AlertSeverity.MEDIUM;
  return null;
};

/**
 * Prediction candidate item shape per docs/API_SPEC.md §/api/predictions/*
 *
 * Approved contract enrichment (P1-approved, 2026-09-18):
 * `bank` and `area` are optional fields sourced from atms.bank / atms.area.
 * The backend is responsible for populating them via ATM registry join (P5 task).
 * Frontend must not compute or fabricate these values.
 *
 * @typedef {Object} PredictionCandidate
 * @property {string}  atm_id           - ATM identifier
 * @property {string}  [bank]           - Institution name (optional)
 * @property {string}  [area]           - Human-readable locality (optional)
 * @property {number}  risk_score       - Risk likelihood score (0.0–1.0)
 * @property {number}  confidence       - Model certainty score (0.0–1.0)
 * @property {{start: string, end: string}} predicted_window - ISO8601 UTC window (ADR-005: fixed 6h)
 * @property {Array<{feature: string, value: number, contribution: string}>} explanation
 */

/**
 * Alert item shape per docs/API_SPEC.md §/api/alerts/*
 *
 * Approved contract enrichment (P1-approved, 2026-09-18):
 * `bank` and `area` are optional fields sourced from atms.bank / atms.area.
 *
 * @typedef {Object} AlertItem
 * @property {string}  alert_id         - Alert identifier
 * @property {string}  crime_id         - Associated crime/complaint identifier
 * @property {string}  atm_id           - ATM identifier
 * @property {string}  [bank]           - Institution name (optional)
 * @property {string}  [area]           - Human-readable locality (optional)
 * @property {string}  severity         - 'low' | 'medium' | 'high' (ADR-006)
 * @property {string}  created_at       - ISO8601 UTC timestamp
 * @property {string}  status           - 'new' | 'acknowledged' | 'resolved'
 * @property {string}  channel          - 'dashboard' | 'mock_sms' | 'mock_email'
 */

/**
 * Intelligence top_result sub-object per docs/API_SPEC.md §/api/intelligence/*
 *
 * Approved contract enrichment (P1-approved, 2026-09-18):
 * `bank` and `area` are optional fields sourced from atms.bank / atms.area.
 *
 * @typedef {Object} IntelligenceTopResult
 * @property {string}  atm_id           - ATM identifier
 * @property {string}  [bank]           - Institution name (optional)
 * @property {string}  [area]           - Human-readable locality (optional)
 * @property {number}  risk_score       - Risk likelihood score
 * @property {number}  confidence       - Model certainty score
 * @property {{start: string, end: string}} predicted_window - ISO8601 UTC window
 */

/**
 * GeoJSON Feature properties per docs/ML_GIS_CONTRACTS.md §2
 *
 * Approved contract enrichment (P1/P3-approved, 2026-09-18):
 * `bank` and `area` are optional ATM registry pass-through fields.
 * They are populated by the backend after GIS spatial computation —
 * NOT computed by the GIS spatial service (P3).
 *
 * @typedef {Object} GeoJSONFeatureProperties
 * @property {string}  atm_id           - ATM identifier
 * @property {string}  [bank]           - Institution name (optional, backend pass-through)
 * @property {string}  [area]           - Human-readable locality (optional, backend pass-through)
 * @property {number}  risk_score       - Risk likelihood score
 * @property {number}  confidence       - Model certainty score
 * @property {{start: string, end: string}} predicted_window - ISO8601 UTC window
 * @property {string}  risk_category    - 'low' | 'medium' | 'high' (bucketed by P3 spatial service)
 * @property {string[]} explanation     - Human-readable contributing factors
 */

