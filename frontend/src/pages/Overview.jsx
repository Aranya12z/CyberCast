import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  Target, 
  Activity, 
  CheckCircle2, 
  ArrowRight, 
  Clock, 
  AlertTriangle,
  Play,
  FileCheck,
  Info
} from 'lucide-react';
import { StatCard } from '../components/common/StatCard';
import { useApp } from '../state/AppContext';
import { apiClient } from '../api/client';

export const Overview = () => {
  const { setActiveTab, setSelectedCrimeId, refreshTrigger } = useApp();
  const [summary, setSummary] = useState(null);
  const [crimes, setCrimes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isTriggering, setIsTriggering] = useState(false);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      apiClient.getDashboardSummary(),
      apiClient.getCrimes()
    ])
      .then(([summaryData, crimesData]) => {
        setSummary(summaryData);
        setCrimes(crimesData);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load overview data:", err);
        setLoading(false);
      });
  }, [refreshTrigger]);

  const handleInspectCrime = (crimeId) => {
    setSelectedCrimeId(crimeId);
    setActiveTab('predictions');
  };

  const handleTriggerPrediction = async (crimeId) => {
    setIsTriggering(true);
    try {
      await apiClient.triggerPrediction(crimeId);
      setSelectedCrimeId(crimeId);
      setActiveTab('predictions');
    } finally {
      setIsTriggering(false);
    }
  };

  if (loading || !summary) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <div className="flex items-center gap-3 text-indigo-400 font-mono text-sm">
          <Activity size={18} />
          <span>Loading dashboard summary...</span>
        </div>
      </div>
    );
  }

  const { active_alerts, high_risk_predictions, prediction_stats, recent_activity } = summary;

  return (
    <div className="space-y-6">
      
      {/* Top Banner: Project Overview */}
      <div className="p-5 sm:p-6 rounded-xl bg-slate-900 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-medium text-slate-400 mb-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>Operational Prototype Active</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Cybercrime Cash-Out Prediction & Early Intervention
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
            Analyzes cybercrime complaints, transaction velocity, and spatial signals to identify likely ATM cash-out points for proactive patrol and account intervention.
          </p>
        </div>

        <div className="flex items-center gap-3 flex-shrink-0">
          <button
            onClick={() => setActiveTab('map')}
            className="px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition flex items-center gap-2 shadow-sm"
          >
            <span>Open GIS Map</span>
            <ArrowRight size={14} />
          </button>
        </div>
      </div>

      {/* Demonstration Dataset Notice */}
      <div className="px-4 py-2.5 rounded-lg bg-slate-900/60 border border-slate-800 flex items-center gap-2.5 text-xs text-slate-400">
        <Info size={15} className="text-indigo-400 flex-shrink-0" />
        <span>
          <strong className="text-slate-300 font-medium">Demonstration Environment:</strong> Displayed incidents, predictions, and transaction velocities represent synthetic evaluation data for the Smart India Hackathon prototype.
        </span>
      </div>

      {/* KPI Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Alerts"
          value={active_alerts}
          subtext="Requiring patrol or bank intervention"
          icon={ShieldAlert}
          alertLevel={active_alerts > 0 ? 'high' : 'none'}
        />
        <StatCard
          title="High-Risk Candidates"
          value={high_risk_predictions}
          subtext="ATMs with &ge; 70% withdrawal likelihood"
          icon={Target}
          alertLevel="high"
        />
        <StatCard
          title="Predictions Run"
          value={prediction_stats?.total_predictions_run || 0}
          subtext="Synchronous complaint evaluations"
          icon={Activity}
          alertLevel="info"
        />
        <StatCard
          title="Average Certainty"
          value={`${Math.round((prediction_stats?.avg_confidence || 0) * 100)}%`}
          subtext="Overall model confidence score"
          icon={CheckCircle2}
          alertLevel="none"
        />
      </div>

      {/* Two Columns: Active Complaints & Recent Intelligence Stream */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left 2 Cols: Ingested Incidents Ready for Intervention */}
        <div className="lg:col-span-2 p-5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h2 className="text-sm font-semibold text-white">
                Active Complaints Feed
              </h2>
              <p className="text-[11px] text-slate-400">
                Reported complaints evaluated for candidate ATM withdrawal locations
              </p>
            </div>
            <span className="text-xs text-slate-400">
              {crimes.length} incidents logged
            </span>
          </div>

          <div className="space-y-2.5">
            {crimes.map(c => (
              <div
                key={c.crime_id}
                className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 transition flex flex-col sm:flex-row sm:items-center justify-between gap-3"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-semibold text-indigo-400">{c.crime_id}</span>
                    <span className="text-xs font-medium text-slate-200">{c.crime_type}</span>
                  </div>
                  <div className="flex items-center gap-2.5 text-[11px] text-slate-400 mt-1 font-mono">
                    <span>Loss: ₹{c.amount?.toLocaleString('en-IN')}</span>
                    <span className="text-slate-600">•</span>
                    <span>Coord: {c.location.lat}, {c.location.lng}</span>
                    <span className="text-slate-600">•</span>
                    <span>{new Date(c.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} UTC</span>
                  </div>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  <button
                    onClick={() => handleInspectCrime(c.crime_id)}
                    className="px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition"
                  >
                    View Top-K
                  </button>
                  <button
                    onClick={() => handleTriggerPrediction(c.crime_id)}
                    disabled={isTriggering}
                    className="px-3 py-1.5 rounded-md bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition flex items-center gap-1.5 shadow-sm"
                  >
                    <Play size={12} />
                    <span>Run Model</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right 1 Col: Recent Operational Activity */}
        <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-4">
          <div className="border-b border-slate-800 pb-3">
            <h2 className="text-sm font-semibold text-white">
              Recent System Activity
            </h2>
            <p className="text-[11px] text-slate-400">
              Activity log stream from predictive pipeline
            </p>
          </div>

          <div className="space-y-3">
            {(recent_activity || []).map((act, i) => {
              const isAlert = act.type === 'alert_created';
              const isAck = act.type === 'alert_acknowledged';

              return (
                <div key={i} className="flex gap-3 text-xs">
                  <div className="mt-1">
                    {isAlert ? (
                      <span className="flex h-2 w-2 rounded-full bg-red-400" />
                    ) : isAck ? (
                      <span className="flex h-2 w-2 rounded-full bg-emerald-400" />
                    ) : (
                      <span className="flex h-2 w-2 rounded-full bg-indigo-400" />
                    )}
                  </div>
                  <div className="space-y-0.5 flex-1">
                    <p className="text-slate-200 leading-snug font-medium">
                      {act.summary}
                    </p>
                    <div className="flex items-center gap-2 text-[10px] font-mono text-slate-400">
                      <span className="text-indigo-400 font-semibold">{act.crime_id}</span>
                      <span>•</span>
                      <span>{new Date(act.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

      </div>

    </div>
  );
};

