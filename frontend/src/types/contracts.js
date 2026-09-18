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
