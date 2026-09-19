/**
 * Central API Client for CyberCast Dashboard
 * Conforms strictly to docs/API_SPEC.md and docs/BACKEND_SPEC.md
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
    return import.meta.env?.VITE_USE_MOCK === 'true';
  },

  setMockMode(enable) {
    localStorage.setItem('cybercast_mock_mode', enable ? 'true' : 'false');
  },

  /**
   * Token and auth state management
   */
  getToken() {
    return localStorage.getItem('cybercast_token');
  },

  setToken(token) {
    if (token) {
      localStorage.setItem('cybercast_token', token);
    } else {
      localStorage.removeItem('cybercast_token');
    }
  },

  clearAuth() {
    localStorage.removeItem('cybercast_token');
    localStorage.removeItem('cybercast_user_role');
    try {
      sessionStorage.removeItem('cybercast_session_auth');
    } catch (_) {}
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('cybercast_auth_expired'));
    }
  },

  /**
   * Central HTTP request helper attaching Authorization: Bearer <token>
   */
  async request(path, options = {}) {
    const url = path.startsWith('http') ? path : `${API_BASE}${path.startsWith('/') ? '' : '/'}${path}`;
    const headers = {
      ...(options.headers || {})
    };

    const token = this.getToken();
    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(options.body);
    }

    const res = await fetch(url, {
      ...options,
      headers
    });

    if (res.status === 401 && !path.includes('/auth/login')) {
      this.clearAuth();
      const error = new Error('Authentication expired. Please log in again.');
      error.status = 401;
      throw error;
    }

    if (!res.ok) {
      let errorDetail = `Request failed: ${res.status}`;
      try {
        const errorJson = await res.json();
        if (errorJson?.error?.message) {
          errorDetail = errorJson.error.message;
        } else if (errorJson?.detail) {
          errorDetail = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
        }
      } catch (_) {}
      const error = new Error(errorDetail);
      error.status = res.status;
      throw error;
    }

    if (res.status === 204) return null;
    return res.json();
  },

  /**
   * User authentication
   * POST /api/auth/login
   */
  async login(username, password) {
    if (this.isMockMode()) {
      return {
        access_token: 'mock-jwt-token',
        token_type: 'bearer',
        role: 'investigator'
      };
    }
    const data = await this.request('/auth/login', {
      method: 'POST',
      body: { username, password }
    });
    if (data?.access_token) {
      this.setToken(data.access_token);
      if (data.role) {
        localStorage.setItem('cybercast_user_role', data.role);
      }
    }
    return data;
  },

  /**
   * Invalidate session
   * POST /api/auth/logout
   */
  async logout() {
    if (!this.isMockMode()) {
      try {
        await this.request('/auth/logout', { method: 'POST' });
      } catch (err) {
        console.warn('Backend logout call failed:', err);
      }
    }
    this.clearAuth();
  },

  /**
   * User auth profile
   * GET /api/auth/me
   */
  async getAuthMe() {
    if (this.isMockMode()) {
      return {
        user_id: 'usr-sharma-901',
        name: 'Inspector Sharma',
        role: 'investigator',
        department: 'Cyber Crime Division, CID'
      };
    }
    return this.request('/auth/me');
  },

  /**
   * Dashboard Summary
   * GET /api/dashboard/summary
   */
  async getDashboardSummary() {
    if (this.isMockMode()) {
      const activeCount = localAlerts.filter(a => a.status === 'new').length;
      return {
        ...mockSummary,
        active_alerts: activeCount
      };
    }
    return this.request('/dashboard/summary');
  },

  /**
   * List Crimes
   * GET /api/crimes
   */
  async getCrimes() {
    if (this.isMockMode()) {
      return mockCrimes;
    }
    return this.request('/crimes');
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
    return this.request(`/crimes/${crimeId}`);
  },

  /**
   * Ingest new crime complaint
   * POST /api/crimes
   */
  async createCrime(payload) {
    if (this.isMockMode()) {
      const newCrime = {
        crime_id: `crm-${Date.now().toString().slice(-6)}`,
        ...payload
      };
      mockCrimes.unshift(newCrime);
      return newCrime;
    }
    return this.request('/crimes', {
      method: 'POST',
      body: payload
    });
  },

  /**
   * Get predictions for a crime
   * GET /api/predictions/{crime_id}
   */
  async getPredictions(crimeId) {
    if (this.isMockMode()) {
      return mockPredictions[crimeId] || {
        crime_id: crimeId,
        generated_at: new Date().toISOString(),
        model_version: 'rf_v1_20260917',
        predictions: [],
        status: 'insufficient_evidence'
      };
    }
    return this.request(`/predictions/${crimeId}`);
  },

  /**
   * Trigger synchronous prediction pipeline (Mode A)
   * POST /api/predictions/{crime_id}
   */
  async triggerPrediction(crimeId) {
    if (this.isMockMode()) {
      await new Promise(r => setTimeout(r, 600));
      return this.getPredictions(crimeId);
    }
    return this.request(`/predictions/${crimeId}`, {
      method: 'POST'
    });
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
    const query = filterSeverity && filterSeverity !== 'all'
      ? `/alerts?severity=${filterSeverity}`
      : '/alerts';
    return this.request(query);
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
    return this.request(`/alerts/${alertId}/acknowledge`, {
      method: 'POST'
    });
  },

  /**
   * Intelligence Report
   * GET /api/intelligence/{crime_id}
   */
  async getIntelligence(crimeId) {
    if (this.isMockMode()) {
      const dossier = mockIntelligence[crimeId];
      if (dossier) return dossier;
      const crime = mockCrimes.find(c => c.crime_id === crimeId) || {
        crime_id: crimeId,
        crime_type: 'Cyber Financial Fraud',
        timestamp: new Date().toISOString(),
        location: { lat: 12.9716, lng: 77.5946 },
        amount: 50000
      };
      return {
        crime_id: crimeId,
        crime,
        latest_prediction: {
          generated_at: new Date().toISOString(),
          model_version: 'rf_v1_20260917',
          status: 'insufficient_evidence',
          top_result: null
        },
        evidence: [],
        related_alerts: [],
        summary: `No high-confidence candidate ATM patterns detected for incident ${crimeId}.`
      };
    }
    return this.request(`/intelligence/${crimeId}`);
  },

  /**
   * GeoJSON FeatureCollection for Map
   * Conforms strictly to ML_GIS_CONTRACTS.md §2
   */
  async getAtmsGeoJSON() {
    if (this.isMockMode()) {
      return mockGeoJSON;
    }
    return this.request('/atms?format=geojson');
  }
};
