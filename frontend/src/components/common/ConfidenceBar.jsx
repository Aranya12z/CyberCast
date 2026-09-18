import React from 'react';

/**
 * ConfidenceBar component
 * Renders model certainty [0, 1] as distinct from risk likelihood
 * Marks the ADR-006 alert threshold floor (0.50)
 */
export const ConfidenceBar = ({ confidence = 0, showLabel = true }) => {
  const percentage = Math.round(Math.min(Math.max(confidence, 0), 1) * 100);
  
  // Color scale based on certainty
  let barColor = 'bg-slate-500';
  if (confidence >= 0.75) barColor = 'bg-emerald-500';
  else if (confidence >= 0.5) barColor = 'bg-indigo-500';
  else if (confidence >= 0.35) barColor = 'bg-amber-500';
  else barColor = 'bg-red-500';

  return (
    <div className="w-full">
      {showLabel && (
        <div className="flex justify-between items-center text-xs mb-1 font-mono">
          <span className="text-slate-400">Certainty:</span>
          <span className="font-semibold text-slate-200">{percentage}%</span>
        </div>
      )}
      <div className="relative w-full h-2 bg-slate-950 rounded-sm overflow-hidden border border-slate-700/60">
        <div
          className={`h-full transition-all duration-300 ${barColor}`}
          style={{ width: `${percentage}%` }}
        />
        {/* Subtle marker at 50% ADR-006 alert floor */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-white/40"
          style={{ left: '50%' }}
          title="ADR-006 Alert Trigger Floor (50%)"
        />
      </div>
    </div>
  );
};
