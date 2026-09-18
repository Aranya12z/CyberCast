import React from 'react';
import { RiskBadge } from '../common/RiskBadge';
import { ConfidenceBar } from '../common/ConfidenceBar';
import { Clock, ChevronRight, MapPin, Building } from 'lucide-react';

export const TopKTable = ({ 
  predictions = [], 
  selectedAtmId, 
  onSelectCandidate = () => {} 
}) => {
  if (!predictions || predictions.length === 0) {
    return (
      <div className="p-8 text-center rounded-xl bg-slate-900 border border-slate-800">
        <p className="text-sm text-slate-400 font-mono">No candidate locations ranked for this query.</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/80 shadow-md">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-900 text-[11px] font-mono uppercase tracking-wider text-slate-400">
              <th className="py-3 px-4 w-12 text-center">RANK</th>
              <th className="py-3 px-4">CANDIDATE ATM</th>
              <th className="py-3 px-4">ESTIMATED RISK</th>
              <th className="py-3 px-4 w-44">MODEL CERTAINTY</th>
              <th className="py-3 px-4">6-HR PREDICTED WINDOW</th>
              <th className="py-3 px-4 text-right">ACTION</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-xs">
            {predictions.map((item, index) => {
              const isSelected = selectedAtmId === item.atm_id;
              const rank = index + 1;

              const windowStart = item.predicted_window?.start 
                ? new Date(item.predicted_window.start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                : 'N/A';
              const windowEnd = item.predicted_window?.end 
                ? new Date(item.predicted_window.end).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                : 'N/A';

              return (
                <tr
                  key={item.atm_id}
                  onClick={() => onSelectCandidate(item)}
                  className={`cursor-pointer transition-colors ${
                    isSelected 
                      ? 'bg-slate-800/80' 
                      : 'hover:bg-slate-850'
                  }`}
                >
                  {/* Rank */}
                  <td className="py-4 px-4 text-center">
                    <span className={`inline-flex items-center justify-center w-6 h-6 rounded-md font-mono text-xs font-bold ${
                      rank === 1 
                        ? 'bg-red-600 text-white' 
                        : rank === 2 
                        ? 'bg-amber-600 text-white' 
                        : 'bg-slate-800 text-slate-300'
                    }`}>
                      {rank}
                    </span>
                  </td>

                  {/* Candidate ATM */}
                  <td className="py-4 px-4">
                    <div className="font-semibold text-slate-100 flex items-center gap-1.5">
                      <Building size={14} className="text-slate-400" />
                      <span>{item.bank || item.atm_id}</span>
                    </div>
                    <div className="text-[11px] text-slate-400 flex items-center gap-1 mt-0.5 font-mono">
                      <MapPin size={12} className="text-slate-500" />
                      <span>{item.area || 'Bangalore'} • <span className="text-slate-400">{item.atm_id}</span></span>
                    </div>
                  </td>

                  {/* Risk Score */}
                  <td className="py-4 px-4">
                    <RiskBadge score={item.risk_score} />
                  </td>

                  {/* Confidence Bar */}
                  <td className="py-4 px-4">
                    <ConfidenceBar confidence={item.confidence} />
                  </td>

                  {/* Predicted Window */}
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-1.5 font-mono text-[11px] text-slate-300">
                      <Clock size={13} className="text-indigo-400" />
                      <span>{windowStart} to {windowEnd}</span>
                    </div>
                    <span className="text-[10px] text-slate-500 block mt-0.5">Fixed 6-hour window (ADR-005)</span>
                  </td>

                  {/* Action */}
                  <td className="py-4 px-4 text-right">
                    <button
                      className={`px-3 py-1.5 rounded-md text-xs font-medium inline-flex items-center gap-1 border transition ${
                        isSelected
                          ? 'bg-indigo-600 text-white border-indigo-500'
                          : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700'
                      }`}
                    >
                      <span>Explain</span>
                      <ChevronRight size={14} />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
