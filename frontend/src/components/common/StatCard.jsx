import React from 'react';

export const StatCard = ({ title, value, subtext, icon: Icon, badge, alertLevel = 'none' }) => {
  const borderStyles = {
    none: 'border-slate-800 bg-slate-900/80 hover:border-slate-700',
    high: 'border-slate-800 bg-slate-900/90 hover:border-red-800/80',
    medium: 'border-slate-800 bg-slate-900/90 hover:border-amber-800/80',
    info: 'border-slate-800 bg-slate-900/90 hover:border-indigo-800/80'
  };

  return (
    <div className={`p-5 rounded-xl border ${borderStyles[alertLevel] || borderStyles.none} transition-colors`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
          {title}
        </span>
        {Icon && (
          <div className="p-2 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
            <Icon size={16} />
          </div>
        )}
      </div>
      
      <div className="flex items-baseline gap-2">
        <span className="text-3xl font-bold font-mono tracking-tight text-white">
          {value}
        </span>
        {badge && (
          <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
            {badge}
          </span>
        )}
      </div>

      {subtext && (
        <p className="mt-2 text-xs text-slate-400 flex items-center gap-1.5">
          {subtext}
        </p>
      )}
    </div>
  );
};
