import React, { useState, useEffect } from 'react';
import { LeafletMap } from '../components/map/LeafletMap';
import { MapLegend } from '../components/map/MapLegend';
import { RiskBadge } from '../components/common/RiskBadge';
import { ConfidenceBar } from '../components/common/ConfidenceBar';
import { useApp } from '../state/AppContext';
import { apiClient } from '../api/client';
import { 
  MapPin, 
  Building, 
  Clock, 
  AlertTriangle, 
  Filter, 
  ShieldCheck, 
  Layers,
  ArrowRight
} from 'lucide-react';

export const GISMap = () => {
  const { selectedCrimeId, setSelectedCrimeId, setActiveTab, refreshTrigger } = useApp();
  const [geoJsonData, setGeoJsonData] = useState(null);
  const [crimes, setCrimes] = useState([]);
  const [activeCrime, setActiveCrime] = useState(null);
  const [filterCategory, setFilterCategory] = useState('all'); // 'all' | 'high' | 'medium' | 'low'
  const [selectedAtmId, setSelectedAtmId] = useState('atm-hdfc-8821');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      apiClient.getAtmsGeoJSON(),
      apiClient.getCrimes()
    ])
      .then(([geoJson, crimesList]) => {
        setGeoJsonData(geoJson);
        setCrimes(crimesList);
        const match = crimesList.find(c => c.crime_id === selectedCrimeId) || crimesList[0];
        setActiveCrime(match);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load GIS data:", err);
        setLoading(false);
      });
  }, [selectedCrimeId, refreshTrigger]);

  const handleCrimeChange = (crimeId) => {
    setSelectedCrimeId(crimeId);
    const match = crimes.find(c => c.crime_id === crimeId);
    if (match) setActiveCrime(match);
  };

  // Find properties of currently selected ATM
  const selectedAtmFeature = geoJsonData?.features?.find(
    f => f.properties?.atm_id === selectedAtmId
  );
  const selectedAtm = selectedAtmFeature?.properties || null;

  return (
    <div className="space-y-4 h-[calc(100vh-6rem)] flex flex-col">
      
      {/* Top Controls: Incident Context & Risk Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl bg-slate-900 border border-slate-800 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-slate-800 text-indigo-400 border border-slate-700">
            <Layers size={18} />
          </div>
          <div>
            <div className="text-xs font-bold text-white font-mono uppercase tracking-wide">
              Geospatial Cash-out Intelligence Map
            </div>
            <div className="text-[11px] text-slate-400">
              Rendering GeoJSON FeatureCollection directly from spatial interface
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          
          {/* Incident Selector */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-xs">
            <span className="text-slate-400 font-mono text-[11px]">CASE:</span>
            <select
              value={selectedCrimeId}
              onChange={(e) => handleCrimeChange(e.target.value)}
              className="bg-transparent text-xs font-mono font-semibold text-indigo-300 focus:outline-none cursor-pointer"
            >
              {crimes.map(c => (
                <option key={c.crime_id} value={c.crime_id} className="bg-slate-900 text-slate-100">
                  {c.crime_id}: {c.crime_type.split('/')[0]}
                </option>
              ))}
            </select>
          </div>

          {/* Risk Level Filter Buttons */}
          <div className="flex items-center gap-1 p-1 rounded-lg bg-slate-800/80 border border-slate-700 text-xs font-mono">
            <button
              onClick={() => setFilterCategory('all')}
              className={`px-2.5 py-1 rounded-md transition ${
                filterCategory === 'all'
                  ? 'bg-indigo-600 text-white font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              All ATMs
            </button>
            <button
              onClick={() => setFilterCategory('high')}
              className={`px-2.5 py-1 rounded-md transition ${
                filterCategory === 'high'
                  ? 'bg-red-600 text-white font-semibold'
                  : 'text-slate-400 hover:text-red-400'
              }`}
            >
              High Risk
            </button>
            <button
              onClick={() => setFilterCategory('medium')}
              className={`px-2.5 py-1 rounded-md transition ${
                filterCategory === 'medium'
                  ? 'bg-amber-600 text-white font-semibold'
                  : 'text-slate-400 hover:text-amber-400'
              }`}
            >
              Medium
            </button>
            <button
              onClick={() => setFilterCategory('low')}
              className={`px-2.5 py-1 rounded-md transition ${
                filterCategory === 'low'
                  ? 'bg-blue-600 text-white font-semibold'
                  : 'text-slate-400 hover:text-blue-400'
              }`}
            >
              Low
            </button>
          </div>

        </div>
      </div>

      {/* Main Map & Candidate Detail Panel Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 flex-1 min-h-0">
        
        {/* Left 3 Cols: Leaflet Map */}
        <div className="lg:col-span-3 relative h-full rounded-xl overflow-hidden border border-slate-800">
          <LeafletMap
            geoJsonData={geoJsonData}
            crimeLocation={activeCrime?.location ? { ...activeCrime.location, crime_type: activeCrime.crime_type, amount: activeCrime.amount } : null}
            filterCategory={filterCategory}
            selectedAtmId={selectedAtmId}
            onSelectAtm={(id) => setSelectedAtmId(id)}
          />

          {/* Floating Legend Overlay in Top Right */}
          <div className="absolute top-4 right-4 z-[400] max-w-xs">
            <MapLegend />
          </div>
        </div>

        {/* Right 1 Col: Selected ATM Candidate Inspector */}
        <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col justify-between overflow-y-auto">
          {selectedAtm ? (
            <div className="space-y-4">
              <div className="border-b border-slate-800 pb-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-slate-400 uppercase">
                    {selectedAtm.atm_id}
                  </span>
                  <RiskBadge category={selectedAtm.risk_category} score={selectedAtm.risk_score} />
                </div>
                <h3 className="text-base font-bold text-white mt-1">
                  {selectedAtm.bank || 'Selected ATM'}
                </h3>
                <p className="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
                  <MapPin size={13} className="text-slate-500" />
                  <span>{selectedAtm.area || 'Bangalore'}</span>
                </p>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 gap-2 bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs">
                <div>
                  <div className="text-[10px] font-mono text-slate-400 uppercase">RISK SCORE</div>
                  <div className="text-lg font-bold font-mono text-red-400">
                    {(selectedAtm.risk_score * 100).toFixed(1)}%
                  </div>
                </div>
                <div>
                  <div className="text-[10px] font-mono text-slate-400 uppercase">CERTAINTY</div>
                  <div className="text-lg font-bold font-mono text-indigo-400">
                    {(selectedAtm.confidence * 100).toFixed(1)}%
                  </div>
                </div>
              </div>

              <div>
                <ConfidenceBar confidence={selectedAtm.confidence} />
              </div>

              {/* 6h Window */}
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs">
                <div className="text-[10px] font-mono text-slate-400 uppercase mb-1 flex items-center gap-1">
                  <Clock size={12} className="text-indigo-400" />
                  <span>PREDICTED TIME WINDOW (ADR-005):</span>
                </div>
                <div className="font-mono font-semibold text-slate-200">
                  {new Date(selectedAtm.predicted_window?.start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  {' to '}
                  {new Date(selectedAtm.predicted_window?.end).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">6 Hours from model run</div>
              </div>

              {/* Explanation Signals */}
              <div className="space-y-2">
                <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                  IDENTIFIED SPATIAL / TEMPORAL SIGNALS
                </div>
                <ul className="space-y-1.5 text-xs">
                  {(selectedAtm.explanation || []).map((exp, i) => (
                    <li key={i} className="p-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-300 leading-snug">
                      • {exp}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-slate-500 font-mono text-xs">
              Click an ATM marker on the map to inspect candidate intelligence.
            </div>
          )}

          {/* Bottom Action to jump to Predictions Table */}
          <div className="pt-4 border-t border-slate-800 mt-4">
            <button
              onClick={() => setActiveTab('predictions')}
              className="w-full py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold flex items-center justify-center gap-2 transition"
            >
              <span>View Full Ranked Top-K Table</span>
              <ArrowRight size={14} />
            </button>
          </div>

        </div>

      </div>

    </div>
  );
};
