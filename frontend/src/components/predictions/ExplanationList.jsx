import React from 'react';
import { ArrowUpRight, CheckCircle2, TrendingUp, MapPin, Clock, Activity, BarChart2 } from 'lucide-react';

export const ExplanationList = ({ explanation = [] }) => {
  if (!explanation || explanation.length === 0) {
    return (
      <div className="text-xs text-slate-500 italic py-1">
        No specific feature explanations recorded for this candidate.
      </div>
    );
  }

  // Feature labels mapper
  const featureMeta = {
    distance_from_crime: {
      label: 'Proximity to Crime Epicenter',
      unit: 'km',
      icon: MapPin,
      format: (val) => `${val} km distance`
    },
    nearby_crime_density: {
      label: 'Nearby Incident Density',
      unit: 'incidents/km²',
      icon: TrendingUp,
      format: (val) => `${val} complaints/km²`
    },
    atm_historical_risk: {
      label: 'Historical ATM Risk Baseline',
      unit: '',
      icon: BarChart2,
      format: (val) => `${(val * 100).toFixed(0)}% historical rating`
    },
    txns_last_1h: {
      label: '1-Hour Transaction Spike',
      unit: 'txns',
      icon: Activity,
      format: (val) => `${val} txns recorded`
    },
    txns_last_6h: {
      label: '6-Hour Velocity Volume',
      unit: 'txns',
      icon: Clock,
      format: (val) => `${val} recent txns`
    },
    withdrawal_frequency: {
      label: 'Withdrawal Frequency Anomaly',
      unit: 'x',
      icon: TrendingUp,
      format: (val) => `${val}x above baseline`
    },
    hour_of_day: {
      label: 'Diurnal Withdrawal Pattern Match',
      unit: 'h',
      icon: Clock,
      format: (val) => `Hour ${val}:00 correlation`
    }
  };

  const contributionStyles = {
    high: {
      badge: 'bg-red-950/80 text-red-300 border-red-800/60 ring-red-500/20',
      label: 'HIGH IMPACT',
      bar: 'bg-red-500'
    },
    medium: {
      badge: 'bg-amber-950/80 text-amber-300 border-amber-800/60 ring-amber-500/20',
      label: 'MED IMPACT',
      bar: 'bg-amber-500'
    },
    low: {
      badge: 'bg-slate-800 text-slate-400 border-slate-700 ring-slate-600/20',
      label: 'LOW IMPACT',
      bar: 'bg-slate-500'
    }
  };

  return (
    <div className="space-y-2.5">
      {explanation.map((item, idx) => {
        const meta = featureMeta[item.feature] || {
          label: item.feature.replace(/_/g, ' '),
          format: (v) => `${v}`
        };
        const style = contributionStyles[item.contribution] || contributionStyles.low;
        const Icon = meta.icon || ArrowUpRight;

        return (
          <div
            key={idx}
            className="flex items-center justify-between p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition"
          >
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 rounded-md bg-slate-800 text-slate-300">
                <Icon size={14} />
              </div>
              <div>
                <div className="text-xs font-medium text-slate-200">{meta.label}</div>
                <div className="text-[11px] font-mono text-slate-400">{meta.format(item.value)}</div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded border ${style.badge}`}>
                {style.label}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
};
