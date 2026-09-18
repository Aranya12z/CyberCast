import React, { useState, useEffect } from 'react';
import { useApp } from '../state/AppContext';
import { apiClient } from '../api/client';
import { ExplanationList } from '../components/predictions/ExplanationList';
import { RiskBadge } from '../components/common/RiskBadge';
import { ConfidenceBar } from '../components/common/ConfidenceBar';
import { 
  FileText, 
  Printer, 
  MapPin, 
  Clock, 
  ShieldCheck, 
  AlertTriangle, 
  Building,
  CheckCircle2,
  Share2
} from 'lucide-react';

export const Intelligence = () => {
  const { selectedCrimeId, setSelectedCrimeId, refreshTrigger } = useApp();
  const [dossier, setDossier] = useState(null);
  const [crimes, setCrimes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      apiClient.getIntelligence(selectedCrimeId),
      apiClient.getCrimes()
    ])
      .then(([intel, crimesList]) => {
        setDossier(intel);
        setCrimes(crimesList);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load intelligence dossier:", err);
        setLoading(false);
      });
  }, [selectedCrimeId, refreshTrigger]);

  if (loading || !dossier) {
    return (
      <div className="p-12 text-center font-mono text-sm text-indigo-400">
        Compiling Intelligence Dossier...
      </div>
    );
  }

  const { crime, latest_prediction, evidence, related_alerts, summary } = dossier;
  const topResult = latest_prediction?.top_result;

  const windowStart = topResult?.predicted_window?.start
    ? new Date(topResult.predicted_window.start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : 'N/A';
  const windowEnd = topResult?.predicted_window?.end
    ? new Date(topResult.predicted_window.end).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : 'N/A';

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      
      {/* Top Dossier Header & Printable Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-xl bg-slate-900 border border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-md bg-slate-800 text-slate-300 text-[11px] font-mono font-bold border border-slate-700">
              INTELLIGENCE BRIEFING DOSSIER
            </span>
            <span className="text-xs font-mono text-slate-400">
              Prepared for Investigative and Analytical Review
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white font-mono mt-1">
            CASE REF: {dossier.crime_id}
          </h1>
        </div>

        <div className="flex items-center gap-3">
          {/* Case Switcher */}
          <div className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-xs">
            <span className="text-slate-400 font-mono text-[11px]">CASE:</span>
            <select
              value={selectedCrimeId}
              onChange={(e) => setSelectedCrimeId(e.target.value)}
              className="bg-transparent text-xs font-mono font-semibold text-indigo-300 focus:outline-none cursor-pointer"
            >
              {crimes.map(c => (
                <option key={c.crime_id} value={c.crime_id} className="bg-slate-900 text-slate-100">
                  {c.crime_id}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => window.print()}
            className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition flex items-center gap-1.5"
          >
            <Printer size={14} />
            <span>Print Dossier</span>
          </button>
        </div>
      </div>

      {/* Narrative Executive Summary Box */}
      <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
        <div className="flex items-center gap-2 text-indigo-400 font-mono text-xs font-bold uppercase tracking-wider">
          <FileText size={15} />
          <span>Operational Intelligence Narrative</span>
        </div>
        <p className="text-sm text-slate-200 leading-relaxed font-sans">
          {summary}
        </p>
      </div>

      {/* Grid: Incident Metadata + Top Prediction Target */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Crime Incident Facts */}
        <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-4">
          <div className="border-b border-slate-800 pb-3">
            <h2 className="text-xs font-mono font-bold text-slate-400 uppercase">
              REPORTED INCIDENT FACTS
            </h2>
            <div className="text-base font-bold text-white mt-1">
              {crime?.crime_type}
            </div>
          </div>

          <div className="space-y-2.5 text-xs font-mono">
            <div className="flex justify-between py-1.5 border-b border-slate-800/60">
              <span className="text-slate-400">Reported Loss Amount:</span>
              <span className="font-bold text-white">₹{crime?.amount?.toLocaleString('en-IN')}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-800/60">
              <span className="text-slate-400">Complaint Timestamp:</span>
              <span className="text-slate-200">{new Date(crime?.timestamp).toLocaleString()}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-800/60">
              <span className="text-slate-400">Incident Location Coordinates:</span>
              <span className="text-slate-200">Lat {crime?.location?.lat}, Lng {crime?.location?.lng}</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-slate-400">District / Area:</span>
              <span className="text-slate-200">Bangalore Urban Cyber Jurisdiction</span>
            </div>
          </div>
        </div>

        {/* Forecasted Primary Target ATM */}
        <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-4">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div>
              <h2 className="text-xs font-mono font-bold text-slate-400 uppercase">
                PRIMARY PREDICTED CASH-OUT TARGET
              </h2>
              <div className="text-base font-bold text-white mt-1">
                {topResult ? (topResult.bank || topResult.atm_id) : 'No Confident Candidate'}
              </div>
            </div>
            {topResult && (
              <RiskBadge score={topResult.risk_score} />
            )}
          </div>

          {topResult ? (
            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-2 bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono">
                <div>
                  <span className="text-[10px] text-slate-400 uppercase">PREDICTED RISK</span>
                  <div className="text-lg font-bold text-red-400">
                    {(topResult.risk_score * 100).toFixed(1)}%
                  </div>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase">MODEL CONFIDENCE</span>
                  <div className="text-lg font-bold text-indigo-400">
                    {(topResult.confidence * 100).toFixed(1)}%
                  </div>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
                <div className="text-[10px] font-mono text-slate-400 uppercase flex items-center gap-1">
                  <Clock size={12} className="text-indigo-400" />
                  <span>ACTIONABLE INTERVENTION WINDOW (ADR-005):</span>
                </div>
                <div className="font-mono text-xs font-bold text-slate-200">
                  {windowStart} to {windowEnd} UTC
                </div>
              </div>

              <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
                <Building size={13} className="text-slate-500" />
                <span>Target Area: <strong className="text-slate-200">{topResult.area || 'Bangalore'}</strong></span>
              </div>
            </div>
          ) : (
            <div className="py-6 text-center text-xs text-slate-500 font-mono">
              Insufficient confidence to designate a primary target.
            </div>
          )}
        </div>

      </div>

      {/* Evidentiary Features (Model Signals) */}
      <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-4">
        <div className="border-b border-slate-800 pb-3">
          <h2 className="text-xs font-mono font-bold text-slate-400 uppercase">
            CORROBORATING PREDICTIVE SIGNALS AND EVIDENCE
          </h2>
          <p className="text-[11px] text-slate-400">
            Feature contributions evaluated across spatial, temporal, and transaction velocity vectors
          </p>
        </div>

        <ExplanationList explanation={evidence} />
      </div>

      {/* Related Alerts & Dispatches */}
      {related_alerts && related_alerts.length > 0 && (
        <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
          <div className="border-b border-slate-800 pb-2">
            <h2 className="text-xs font-mono font-bold text-slate-400 uppercase">
              ASSOCIATED LAW ENFORCEMENT ALERTS
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {related_alerts.map((al, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between text-xs">
                <div>
                  <span className="font-mono font-bold text-slate-200">{al.alert_id}</span>
                  <div className="text-[11px] text-slate-400 capitalize">Status: {al.status}</div>
                </div>
                <RiskBadge category={al.severity} />
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
};
