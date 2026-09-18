import React from 'react';
import { Bell, CheckCircle2, ShieldAlert, Clock, MapPin } from 'lucide-react';
import { RiskBadge } from '../common/RiskBadge';

export const AlertCard = ({ alert, onAcknowledge = () => {} }) => {
  const isNew = alert.status === 'new';

  const severityStyles = {
    high: 'border-red-900/70 bg-slate-900/90',
    medium: 'border-amber-900/70 bg-slate-900/90',
    low: 'border-slate-800 bg-slate-900/80'
  };

  const channelBadges = {
    dashboard: 'bg-slate-800 text-slate-300 border-slate-700',
    mock_sms: 'bg-slate-800 text-slate-300 border-slate-700',
    mock_email: 'bg-slate-800 text-slate-300 border-slate-700'
  };

  const createdFormatted = alert.created_at
    ? new Date(alert.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })
    : 'Recent';

  return (
    <div className={`p-5 rounded-xl border transition-colors ${severityStyles[alert.severity] || 'border-slate-800 bg-slate-900/80'}`}>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className={`p-2 rounded-lg ${isNew ? 'bg-red-950 text-red-400 border border-red-800' : 'bg-slate-800 text-slate-400 border border-slate-700'}`}>
            <Bell size={16} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-slate-200">{alert.alert_id}</span>
              <RiskBadge category={alert.severity} />
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded-md border uppercase ${channelBadges[alert.channel] || 'bg-slate-800 text-slate-300 border-slate-700'}`}>
                {alert.channel?.replace('_', ' ')}
              </span>
            </div>
            <div className="text-xs text-slate-400 mt-0.5">
              Associated Incident: <span className="font-mono text-indigo-400 font-semibold">{alert.crime_id}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isNew ? (
            <button
              onClick={() => onAcknowledge(alert.alert_id)}
              className="px-3.5 py-1.5 rounded-md bg-red-600 hover:bg-red-500 text-white text-xs font-semibold shadow-sm transition flex items-center gap-1.5"
            >
              <CheckCircle2 size={14} />
              <span>Acknowledge Intervention</span>
            </button>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md bg-slate-800 text-emerald-400 text-xs font-mono font-medium border border-slate-700">
              <CheckCircle2 size={14} />
              <span>ACKNOWLEDGED</span>
            </span>
          )}
        </div>
      </div>

      <div className="pt-3 grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
        <div className="flex items-center gap-1.5 text-slate-300">
          <MapPin size={14} className="text-slate-500" />
          <span>ATM Target: <strong className="text-white">{alert.bank || alert.atm_id}</strong> {alert.area ? `(${alert.area})` : ''}</span>
        </div>
        <div className="flex items-center gap-1.5 text-slate-400 sm:justify-end font-mono text-[11px]">
          <Clock size={13} className="text-slate-500" />
          <span>Generated: {createdFormatted}</span>
        </div>
      </div>
    </div>
  );
};
