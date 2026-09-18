import React from 'react';

/**
 * RiskBadge component
 * Follows ADR-006 and GIS_SPEC.md thresholds:
 * risk_score >= 0.7 -> high (red)
 * 0.4 <= risk_score < 0.7 -> medium (amber)
 * risk_score < 0.4 -> low (blue)
 */
export const RiskBadge = ({ score, category }) => {
  let cat = category;
  if (!cat && typeof score === 'number') {
    if (score >= 0.7) cat = 'high';
    else if (score >= 0.4) cat = 'medium';
    else cat = 'low';
  }

  const styles = {
    high: 'bg-red-950/80 text-red-400 border-red-800/60 ring-red-500/20',
    medium: 'bg-amber-950/80 text-amber-400 border-amber-800/60 ring-amber-500/20',
    low: 'bg-blue-950/80 text-blue-400 border-blue-800/60 ring-blue-500/20'
  };

  const labels = {
    high: 'HIGH RISK',
    medium: 'MED RISK',
    low: 'LOW RISK'
  };

  const activeStyle = styles[cat] || styles.low;
  const label = labels[cat] || 'LOW';

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold font-mono tracking-wider rounded-md border ${activeStyle} ring-1`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cat === 'high' ? 'bg-red-400 animate-pulse' : cat === 'medium' ? 'bg-amber-400' : 'bg-blue-400'}`} />
      {typeof score === 'number' ? `${(score * 100).toFixed(0)}% • ` : ''}{label}
    </span>
  );
};
