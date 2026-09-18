/**
 * Central API Client for CyberCast Dashboard
 * Conforms strictly to docs/API_SPEC.md
 */

import mockSummary from './mocks/dashboardSummary.json';
import mockCrimes from './mocks/crimes.json';
import mockPredictions from './mocks/predictions.json';
import mockAlerts from './mocks/alerts.json';
import mockIntelligence from './mocks/intelligence.json';
import mockGeoJSON from './mocks/atmsGeoJSON.json';

const API_BASE = import.meta.env?.VITE_API_BASE_URL || '/api';

// In-memory mock alerts state to support live acknowledgement in demo
let localAlerts = [...mockAlerts];

export const apiClient = {
  /**
   * Check if mock mode is forced via localStorage or environment
   */
  isMockMode() {
    const stored = localStorage.getItem('cybercast_mock_mode');
    if (stored !== null) return stored === 'true';
    return true; // Default to mock until backend is verified live
  },

  setMockMode(enable) {
    localStorage.setItem('cybercast_mock_mode', enable ? 'true' : 'false');
  },

  /**
   * User auth details
   * GET /api/auth/me
   */
  async getAuthMe() {
    if (this.isMockMode()) {
      return {
        user_id: "usr-sharma-901",
        name: "Inspector Sharma",
        role: "investigator", // "investigator" | "bank_analyst" | "administrator"
        department: "Cyber Crime Division, CID"
      };
    }
    const res = await fetch(`${API_BASE}/auth/me`);
    if (!res.ok) throw new Error(`Auth check failed: ${res.status}`);
    return res.json();
  },

  /**
   * Dashboard Summary
   * GET /api/dashboard/summary
   */
  async getDashboardSummary() {
    if (this.isMockMode()) {
      // Calculate dynamic active alert count from local state
      const activeCount = localAlerts.filter(a => a.status === 'new').length;
      return {
        ...mockSummary,
        active_alerts: activeCount
      };
    }
    const res = await fetch(`${API_BASE}/dashboard/summary`);
    if (!res.ok) throw new Error(`Dashboard summary failed: ${res.status}`);
    return res.json();
  },

  /**
   * List Crimes
   * GET /api/crimes
   */
  async getCrimes() {
    if (this.isMockMode()) {
      return mockCrimes;
    }
    const res = await fetch(`${API_BASE}/crimes`);
    if (!res.ok) throw new Error(`Fetch crimes failed: ${res.status}`);
    return res.json();
  },

  /**
   * Get Crime by ID
   * GET /api/crimes/{crime_id}
   */
  async getCrimeById(crimeId) {
    if (this.isMockMode()) {
      const match = mockCrimes.find(c => c.crime_id === crimeId);
      if (!match) throw new Error(`Crime not found: ${crimeId}`);
      return match;
    }
    const res = await fetch(`${API_BASE}/crimes/${crimeId}`);
    if (!res.ok) throw new Error(`Fetch crime ${crimeId} failed: ${res.status}`);
    return res.json();
  },

  /**
   * Get predictions for a crime
   * GET /api/predictions/{crime_id}
   */
  async getPredictions(crimeId) {
    if (this.isMockMode()) {
      const result = mockPredictions[crimeId] || {
        crime_id: crimeId,
        generated_at: new Date().toISOString(),
        model_version: "rf_v1_20260917",
        predictions: [],
        status: "insufficient_evidence"
      };
      return result;
    }
    const res = await fetch(`${API_BASE}/predictions/${crimeId}`);
    if (!res.ok) throw new Error(`Fetch predictions failed: ${res.status}`);
    return res.json();
  },

  /**
   * Trigger synchronous prediction pipeline (Mode A)
   * POST /api/predictions/{crime_id}
   */
  async triggerPrediction(crimeId) {
    if (this.isMockMode()) {
      // Simulate pipeline execution latency
      await new Promise(r => setTimeout(r, 600));
      return this.getPredictions(crimeId);
    }
    const res = await fetch(`${API_BASE}/predictions/${crimeId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!res.ok) throw new Error(`Trigger prediction failed: ${res.status}`);
    return res.json();
  },

  /**
   * List Alerts
   * GET /api/alerts
   */
  async getAlerts(filterSeverity = null) {
    if (this.isMockMode()) {
      if (!filterSeverity || filterSeverity === 'all') {
        return [...localAlerts];
      }
      return localAlerts.filter(a => a.severity === filterSeverity);
    }
    const url = filterSeverity && filterSeverity !== 'all'
      ? `${API_BASE}/alerts?severity=${filterSeverity}`
      : `${API_BASE}/alerts`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Fetch alerts failed: ${res.status}`);
    return res.json();
  },

  /**
   * Acknowledge an Alert
   * POST /api/alerts/{alert_id}/acknowledge
   */
  async acknowledgeAlert(alertId) {
    if (this.isMockMode()) {
      const target = localAlerts.find(a => a.alert_id === alertId);
      if (target) {
        target.status = 'acknowledged';
      }
      return { success: true, alert_id: alertId, status: 'acknowledged' };
    }
    const res = await fetch(`${API_BASE}/alerts/${alertId}/acknowledge`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error(`Acknowledge alert failed: ${res.status}`);
    return res.json();
  },

  /**
   * Intelligence Report
   * GET /api/intelligence/{crime_id}
   */
  async getIntelligence(crimeId) {
    if (this.isMockMode()) {
      const dossier = mockIntelligence[crimeId];
      if (dossier) return dossier;
      // Synthesize fallback for missing entry
      const crime = mockCrimes.find(c => c.crime_id === crimeId) || {
        crime_id: crimeId,
        crime_type: "Cyber Financial Fraud",
        timestamp: new Date().toISOString(),
        location: { lat: 12.9716, lng: 77.5946 },
        amount: 50000
      };
      return {
        crime_id: crimeId,
        crime,
        latest_prediction: {
          generated_at: new Date().toISOString(),
          model_version: "rf_v1_20260917",
          status: "insufficient_evidence",
          top_result: null
        },
        evidence: [],
        related_alerts: [],
        summary: `No high-confidence candidate ATM patterns detected for incident ${crimeId}.`
      };
    }
    const res = await fetch(`${API_BASE}/intelligence/${crimeId}`);
    if (!res.ok) throw new Error(`Fetch intelligence failed: ${res.status}`);
    return res.json();
  },

  /**
   * GeoJSON FeatureCollection for Map
   * Conforms strictly to ML_GIS_CONTRACTS.md §2
   */
  async getAtmsGeoJSON() {
    if (this.isMockMode()) {
      return mockGeoJSON;
    }
    const res = await fetch(`${API_BASE}/atms?format=geojson`);
    if (!res.ok) throw new Error(`Fetch GeoJSON failed: ${res.status}`);
    return res.json();
  }
};
