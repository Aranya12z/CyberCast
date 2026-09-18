import React, { useState, useEffect } from 'react';
import { TopKTable } from '../components/predictions/TopKTable';
import { ExplanationList } from '../components/predictions/ExplanationList';
import { RiskDistributionChart } from '../components/charts/RiskDistributionChart';
import { StatusBanner } from '../components/common/StatusBanner';
import { RiskBadge } from '../components/common/RiskBadge';
import { ConfidenceBar } from '../components/common/ConfidenceBar';
import { useApp } from '../state/AppContext';
import { apiClient } from '../api/client';
import { 
  Target, 
  Play, 
  RotateCcw, 
  Layers, 
  AlertCircle, 
  Clock, 
  FileText,
  MapPin,
  Building,
  CheckCircle2,
  Info
} from 'lucide-react';

export const Predictions = () => {
  const { selectedCrimeId, setSelectedCrimeId, setActiveTab, refreshTrigger } = useApp();
  const [crimes, setCrimes] = useState([]);
  const [currentCrime, setCurrentCrime] = useState(null);
  const [predictionRun, setPredictionRun] = useState(null);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isTriggering, setIsTriggering] = useState(false);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      apiClient.getCrimes(),
      apiClient.getPredictions(selectedCrimeId)
    ])
      .then(([crimesList, predData]) => {
        setCrimes(crimesList);
        const crime = crimesList.find(c => c.crime_id === selectedCrimeId) || crimesList[0];
        setCurrentCrime(crime);
        setPredictionRun(predData);

        if (predData?.predictions?.length > 0) {
          setSelectedCandidate(predData.predictions[0]);
        } else {
          setSelectedCandidate(null);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load predictions:", err);
        setLoading(false);
      });
  }, [selectedCrimeId, refreshTrigger]);

  const handleSelectCrime = (crimeId) => {
    setSelectedCrimeId(crimeId);
  };

  const handleRerunPrediction = async () => {
    setIsTriggering(true);
    try {
      const updated = await apiClient.triggerPrediction(selectedCrimeId);
      setPredictionRun(updated);
      if (updated?.predictions?.length > 0) {
        setSelectedCandidate(updated.predictions[0]);
      }
    } finally {
      setIsTriggering(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center font-mono text-sm text-indigo-400">
        Retrieving ML Top-K Candidate Rankings...
      </div>
    );
  }

  const predictionsList = predictionRun?.predictions || [];
  const status = predictionRun?.status || 'ok';

  return (
    <div className="space-y-6">
      
      {/* Header: Crime Context & Actions */}
      <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-md bg-slate-800 text-slate-300 text-[11px] font-mono font-bold border border-slate-700">
              MODE A: EVENT-TRIGGERED INFERENCE
            </span>
            <span className="text-xs font-mono text-slate-400">
              Model: <strong className="text-slate-200">{predictionRun?.model_version || 'rf_v1_20260917'}</strong>
            </span>
          </div>

          <div className="flex items-baseline gap-3 mt-1.5">
            <h1 className="text-xl font-bold text-white font-mono">
              {currentCrime?.crime_id}
            </h1>
            <span className="text-sm font-semibold text-slate-300">
              {currentCrime?.crime_type}
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-slate-400 mt-1">
            <span>Reported Loss: <strong className="text-slate-200">₹{currentCrime?.amount?.toLocaleString('en-IN')}</strong></span>
            <span>•</span>
            <span>Epicenter: {currentCrime?.location?.lat}, {currentCrime?.location?.lng}</span>
            <span>•</span>
            <span>Timestamp: {new Date(currentCrime?.timestamp).toLocaleString()}</span>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3 flex-shrink-0">
          
          {/* Crime Switcher */}
          <div className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-xs">
            <span className="text-slate-400 font-mono text-[11px]">SWITCH CASE:</span>
            <select
              value={selectedCrimeId}
              onChange={(e) => handleSelectCrime(e.target.value)}
              className="bg-transparent text-xs font-mono font-semibold text-indigo-300 focus:outline-none cursor-pointer"
            >
              {crimes.map(c => (
                <option key={c.crime_id} value={c.crime_id} className="bg-slate-900 text-slate-100">
                  {c.crime_id} ({c.crime_type.split(' ')[0]})
                </option>
              ))}
            </select>
          </div>

          {/* Re-trigger Prediction Button */}
          <button
            onClick={handleRerunPrediction}
            disabled={isTriggering}
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold shadow-sm transition flex items-center gap-1.5"
          >
            <Play size={14} />
            <span>{isTriggering ? 'Executing Model...' : 'Re-run Inference'}</span>
          </button>

          {/* View Intelligence Dossier Button */}
          <button
            onClick={() => setActiveTab('intelligence')}
            className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition flex items-center gap-1.5"
          >
            <FileText size={14} />
            <span>View Dossier</span>
          </button>

        </div>
      </div>

      {/* Honest Status Handling for Edge Cases */}
      <StatusBanner status={status} />

      {/* Top-K Candidates Table and Distribution Chart */}
      {status === 'ok' && predictionsList.length > 0 ? (
        <div className="space-y-6">
          
          {/* Main Top-K Ranked Table */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-white font-mono uppercase tracking-wide">
                  Top-K Ranked Withdrawal Locations (ADR-004)
                </h2>
                <p className="text-[11px] text-slate-400">
                  Ranked by risk likelihood with a fixed 6-hour forecast window (ADR-005)
                </p>
              </div>
              <span className="text-xs font-mono px-2.5 py-1 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                Top {predictionsList.length} Candidates
              </span>
            </div>

            <TopKTable
              predictions={predictionsList}
              selectedAtmId={selectedCandidate?.atm_id}
              onSelectCandidate={(c) => setSelectedCandidate(c)}
            />
          </div>

          {/* Split Section: Detailed Candidate Explanation & Comparison */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Candidate Feature Explanation Box */}
            <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-4">
              <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
                <div>
                  <div className="text-[10px] font-mono text-slate-400 uppercase">
                    CANDIDATE EXPLANATION DRILLDOWN
                  </div>
                  <h3 className="text-base font-bold text-white mt-0.5">
                    {selectedCandidate?.bank || 'Candidate ATM'}: {selectedCandidate?.atm_id}
                  </h3>
                </div>
                {selectedCandidate && (
                  <RiskBadge score={selectedCandidate.risk_score} />
                )}
              </div>

              {selectedCandidate ? (
                <div className="space-y-4">
                  <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 grid grid-cols-2 gap-3 text-xs font-mono">
                    <div>
                      <span className="text-slate-400 text-[10px]">RISK LIKELIHOOD</span>
                      <div className="text-lg font-bold text-red-400">
                        {(selectedCandidate.risk_score * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px]">MODEL CERTAINTY</span>
                      <div className="text-lg font-bold text-indigo-400">
                        {(selectedCandidate.confidence * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>

                  <div>
                    <div className="text-xs font-bold text-slate-300 uppercase font-mono mb-2">
                      Feature Signals Contributing to Prediction:
                    </div>
                    <ExplanationList explanation={selectedCandidate.explanation} />
                  </div>
                </div>
              ) : (
                <div className="text-xs text-slate-500 italic py-6 text-center">
                  Select a candidate row above to inspect explanation features.
                </div>
              )}
            </div>

            {/* Candidate Comparison Chart */}
            <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
              <div className="border-b border-slate-800 pb-3">
                <h3 className="text-sm font-bold text-white font-mono uppercase tracking-wide">
                  Risk Likelihood vs Model Certainty
                </h3>
                <p className="text-[11px] text-slate-400">
                  Visualizing independent risk and confidence values per system architecture
                </p>
              </div>

              <RiskDistributionChart predictions={predictionsList} />
            </div>

          </div>

        </div>
      ) : (
        status === 'ok' && (
          <div className="p-12 text-center rounded-xl bg-slate-900/40 border border-slate-800 text-slate-400 text-xs font-mono">
            No candidates generated for this query.
          </div>
        )
      )}

    </div>
  );
};
