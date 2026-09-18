import React from 'react';
import { AlertTriangle, Info, CheckCircle2 } from 'lucide-react';

export const StatusBanner = ({ status = 'ok', message }) => {
  if (status === 'ok') return null;

  const configs = {
    insufficient_confidence: {
      title: 'Insufficient Model Confidence',
      desc: message || 'Candidate ATM patterns were identified, but overall confidence fell below the operational safety floor (0.35). Predictions are suppressed to prevent false positive interventions.',
      styles: 'bg-amber-950/40 border-amber-800/80 text-amber-300 ring-1 ring-amber-500/20',
      icon: AlertTriangle
    },
    insufficient_evidence: {
      title: 'Insufficient Historical Evidence',
      desc: message || 'Complaint signals (transaction timestamps, geographic proximity, or account velocity) are insufficient to build a reliable predictive feature vector. Further intelligence gathering required.',
      styles: 'bg-slate-900/80 border-slate-700/80 text-slate-300 ring-1 ring-slate-600/30',
      icon: Info
    }
  };

  const current = configs[status] || {
    title: 'Advisory Status: ' + status,
    desc: message || 'System operating in non-standard state.',
    styles: 'bg-slate-900 border-slate-700 text-slate-300',
    icon: Info
  };

  const Icon = current.icon;

  return (
    <div className={`p-4 rounded-xl border ${current.styles} flex items-start gap-3 my-4`}>
      <Icon className="w-5 h-5 flex-shrink-0 mt-0.5" />
      <div>
        <h4 className="text-sm font-semibold tracking-wide uppercase font-mono">{current.title}</h4>
        <p className="text-xs mt-1 leading-relaxed opacity-90">{current.desc}</p>
        <p className="text-[11px] mt-2 font-mono text-slate-400">
          * Protocol: Model adherence to ARCHITECTURE.md §10 (Non-fabrication of intelligence).
        </p>
      </div>
    </div>
  );
};
