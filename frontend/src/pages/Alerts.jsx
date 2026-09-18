import React, { useState, useEffect } from 'react';
import { AlertCard } from '../components/alerts/AlertCard';
import { useApp } from '../state/AppContext';
import { apiClient } from '../api/client';
import { Bell, Filter, CheckCircle2, ShieldAlert, AlertTriangle } from 'lucide-react';

export const Alerts = () => {
  const { refreshTrigger, refreshData } = useApp();
  const [alerts, setAlerts] = useState([]);
  const [severityFilter, setSeverityFilter] = useState('all'); // 'all' | 'high' | 'medium' | 'low'
  const [statusFilter, setStatusFilter] = useState('all'); // 'all' | 'new' | 'acknowledged'
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    apiClient.getAlerts(severityFilter)
      .then(data => {
        setAlerts(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load alerts:", err);
        setLoading(false);
      });
  }, [severityFilter, refreshTrigger]);

  const handleAcknowledge = async (alertId) => {
    try {
      await apiClient.acknowledgeAlert(alertId);
      // Update local state immediately
      setAlerts(prev => prev.map(a => 
        a.alert_id === alertId ? { ...a, status: 'acknowledged' } : a
      ));
      refreshData();
    } catch (err) {
      console.error("Failed to acknowledge alert:", err);
    }
  };

  const filteredAlerts = alerts.filter(a => {
    if (statusFilter === 'all') return true;
    return a.status === statusFilter;
  });

  const unacknowledgedCount = alerts.filter(a => a.status === 'new').length;

  return (
    <div className="space-y-6">
      
      {/* Header & ADR-006 Policy Info */}
      <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-md bg-red-950 text-red-300 text-[11px] font-mono font-bold border border-red-800">
              ALERT INTERVENTION QUEUE
            </span>
            <span className="text-xs font-mono text-slate-400">
              Trigger Rule: <strong className="text-slate-200">ADR-006</strong> (Risk &ge; 0.4 and Confidence &ge; 0.5)
            </span>
          </div>

          <h1 className="text-xl font-bold text-white tracking-tight mt-1.5 flex items-center gap-2.5">
            <span>Actionable Law Enforcement Alerts</span>
            {unacknowledgedCount > 0 && (
              <span className="px-2 py-0.5 rounded-md bg-red-600 text-white text-xs font-mono font-bold">
                {unacknowledgedCount} PENDING
              </span>
            )}
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Alerts are automatically triggered when candidate predictions meet agreed risk likelihood and model certainty floors.
          </p>
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-3">
          
          {/* Status Filter */}
          <div className="flex items-center gap-1 p-1 rounded-lg bg-slate-800 border border-slate-700 text-xs font-mono">
            <button
              onClick={() => setStatusFilter('all')}
              className={`px-2.5 py-1 rounded-md transition ${statusFilter === 'all' ? 'bg-indigo-600 text-white font-semibold' : 'text-slate-400 hover:text-slate-200'}`}
            >
              All Status
            </button>
            <button
              onClick={() => setStatusFilter('new')}
              className={`px-2.5 py-1 rounded-md transition ${statusFilter === 'new' ? 'bg-red-600 text-white font-semibold' : 'text-slate-400 hover:text-red-400'}`}
            >
              Pending ({unacknowledgedCount})
            </button>
            <button
              onClick={() => setStatusFilter('acknowledged')}
              className={`px-2.5 py-1 rounded-md transition ${statusFilter === 'acknowledged' ? 'bg-slate-700 text-white font-semibold' : 'text-slate-400 hover:text-slate-200'}`}
            >
              Acknowledged
            </button>
          </div>

          {/* Severity Filter */}
          <div className="flex items-center gap-1 p-1 rounded-lg bg-slate-800 border border-slate-700 text-xs font-mono">
            <button
              onClick={() => setSeverityFilter('all')}
              className={`px-2.5 py-1 rounded-md transition ${severityFilter === 'all' ? 'bg-indigo-600 text-white font-semibold' : 'text-slate-400 hover:text-slate-200'}`}
            >
              All Severity
            </button>
            <button
              onClick={() => setSeverityFilter('high')}
              className={`px-2.5 py-1 rounded-md transition ${severityFilter === 'high' ? 'bg-red-600 text-white font-semibold' : 'text-slate-400 hover:text-red-400'}`}
            >
              High
            </button>
            <button
              onClick={() => setSeverityFilter('medium')}
              className={`px-2.5 py-1 rounded-md transition ${severityFilter === 'medium' ? 'bg-amber-600 text-white font-semibold' : 'text-slate-400 hover:text-amber-400'}`}
            >
              Medium
            </button>
          </div>

        </div>
      </div>

      {/* Alerts List */}
      {loading ? (
        <div className="p-12 text-center font-mono text-sm text-indigo-400">
          Loading alerts from queue...
        </div>
      ) : filteredAlerts.length > 0 ? (
        <div className="space-y-3">
          {filteredAlerts.map(alert => (
            <AlertCard
              key={alert.alert_id}
              alert={alert}
              onAcknowledge={handleAcknowledge}
            />
          ))}
        </div>
      ) : (
        <div className="p-12 text-center rounded-xl bg-slate-900/40 border border-slate-800 text-slate-400 text-xs font-mono">
          No alerts matching selected filters.
        </div>
      )}

      {/* ADR-006 Technical Specification Note */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-400 space-y-1">
        <div className="font-mono text-[11px] font-bold text-slate-300 uppercase flex items-center gap-1.5">
          <ShieldAlert size={14} className="text-indigo-400" />
          <span>Decision Rules (ADR-006)</span>
        </div>
        <p className="leading-relaxed">
          Severity is deterministically mapped from candidate prediction metrics: High Severity (risk &ge; 0.7 and confidence &ge; 0.5) and Medium Severity (0.4 &le; risk &lt; 0.7 and confidence &ge; 0.5).
        </p>
      </div>

    </div>
  );
};
