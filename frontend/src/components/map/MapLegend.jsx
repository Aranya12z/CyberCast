import React from 'react';
import { Target, AlertCircle, Shield } from 'lucide-react';

export const MapLegend = () => {
  return (
    <div className="p-3.5 rounded-lg bg-slate-900/95 border border-slate-700/80 shadow-lg space-y-2 text-xs">
      <div className="font-mono text-[11px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-700/60 pb-1.5 flex items-center gap-1.5">
        <Target size={13} className="text-indigo-400" />
        <span>GIS INTEL LEGEND</span>
      </div>

      <div className="space-y-1.5 font-mono text-[11px]">
        {/* Crime Epicenter */}
        <div className="flex items-center gap-2">
          <div className="w-3.5 h-3.5 rounded-sm bg-indigo-600 border border-white" />
          <span className="text-slate-300 font-sans font-medium">Reported Crime Origin</span>
        </div>

        {/* High Risk ATM */}
        <div className="flex items-center gap-2">
          <div className="w-3.5 h-3.5 rounded-sm bg-red-500 border border-white" />
          <span className="text-red-300 font-sans font-medium">High Risk ATM (&ge; 70%)</span>
        </div>

        {/* Medium Risk ATM */}
        <div className="flex items-center gap-2">
          <div className="w-3.5 h-3.5 rounded-sm bg-amber-500 border border-white" />
          <span className="text-amber-300 font-sans font-medium">Medium Risk ATM (40 to 69%)</span>
        </div>

        {/* Low Risk ATM */}
        <div className="flex items-center gap-2">
          <div className="w-3.5 h-3.5 rounded-sm bg-blue-500 border border-white" />
          <span className="text-blue-300 font-sans font-medium">Low Risk ATM (&lt; 40%)</span>
        </div>

        {/* Radius */}
        <div className="flex items-center gap-2 pt-1 border-t border-slate-800">
          <div className="w-3.5 h-3.5 rounded-sm border border-dashed border-indigo-400" />
          <span className="text-slate-400 font-sans text-[10px]">Candidate Proximity Radius</span>
        </div>
      </div>
    </div>
  );
};
