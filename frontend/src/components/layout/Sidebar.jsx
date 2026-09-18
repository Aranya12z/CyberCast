import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  Map as MapIcon, 
  Target, 
  BellRing, 
  FileText, 
  ShieldAlert,
  Shield,
  FileCheck,
  ChevronRight
} from 'lucide-react';
import { useApp } from '../../state/AppContext';
import { apiClient } from '../../api/client';

export const Sidebar = () => {
  const { activeTab, setActiveTab, refreshTrigger } = useApp();
  const [activeAlertsCount, setActiveAlertsCount] = useState(0);

  useEffect(() => {
    apiClient.getAlerts('all')
      .then(alerts => {
        const unack = alerts.filter(a => a.status === 'new').length;
        setActiveAlertsCount(unack);
      })
      .catch(() => setActiveAlertsCount(0));
  }, [refreshTrigger]);

  const navItems = [
    {
      id: 'overview',
      label: 'Overview',
      desc: 'System summary and metrics',
      icon: LayoutDashboard,
    },
    {
      id: 'map',
      label: 'GIS Risk Map',
      desc: 'Geospatial withdrawal hotspots',
      icon: MapIcon,
    },
    {
      id: 'predictions',
      label: 'Top-K Predictions',
      desc: 'Ranked candidate ATMs',
      icon: Target,
    },
    {
      id: 'alerts',
      label: 'Actionable Alerts',
      desc: 'Threshold-triggered interventions',
      icon: BellRing,
      badge: activeAlertsCount > 0 ? activeAlertsCount : null
    },
    {
      id: 'intelligence',
      label: 'Intelligence Brief',
      desc: 'Case dossier and evidence',
      icon: FileText,
    }
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-950 p-4 flex flex-col justify-between flex-shrink-0">
      <div className="space-y-6">
        
        {/* Navigation Category Label */}
        <div>
          <div className="text-[10px] font-bold font-mono tracking-widest text-slate-400 uppercase px-3 mb-2">
            INTELLIGENCE MODULES
          </div>

          <nav className="space-y-1">
            {navItems.map(item => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;

              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-left transition ${
                    isActive
                      ? 'bg-slate-800 text-white border border-slate-700 font-medium'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`p-1.5 rounded-md ${isActive ? 'bg-indigo-600 text-white' : 'bg-slate-900 text-slate-400 border border-slate-800'}`}>
                      <Icon size={16} />
                    </div>
                    <div>
                      <div className="text-xs font-semibold">{item.label}</div>
                      <div className="text-[10px] text-slate-400">{item.desc}</div>
                    </div>
                  </div>

                  {item.badge && (
                    <span className="px-1.5 py-0.5 text-[11px] font-mono font-bold rounded-md bg-red-600 text-white">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tactical Status Box */}
        <div className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 text-xs">
          <div className="flex items-center gap-2 text-indigo-400 font-mono font-semibold text-[11px] mb-1">
            <ShieldAlert size={14} />
            <span>INTERVENTION HORIZON</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Predictions target a fixed 6-hour future withdrawal horizon (ADR-005) for early patrol dispatch.
          </p>
        </div>

      </div>

      {/* Footer Navigation: Privacy Policy, Terms, and Prototype notice */}
      <div className="pt-4 border-t border-slate-800 text-xs space-y-2">
        <div className="flex flex-col space-y-1">
          <button
            onClick={() => setActiveTab('privacy')}
            className={`text-left text-[11px] px-2 py-1 rounded transition flex items-center justify-between ${
              activeTab === 'privacy' ? 'text-indigo-400 bg-slate-900 font-medium' : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            <span>Privacy Policy</span>
            <ChevronRight size={12} />
          </button>
          <button
            onClick={() => setActiveTab('terms')}
            className={`text-left text-[11px] px-2 py-1 rounded transition flex items-center justify-between ${
              activeTab === 'terms' ? 'text-indigo-400 bg-slate-900 font-medium' : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            <span>Terms and Conditions</span>
            <ChevronRight size={12} />
          </button>
        </div>

        <div className="text-[10px] font-mono text-slate-400 px-2 pt-1 border-t border-slate-900">
          <div>CyberCast Prototype v0.1.0</div>
          <div className="text-slate-400">SIH 2026 Evaluation</div>
        </div>
      </div>
    </aside>
  );
};
