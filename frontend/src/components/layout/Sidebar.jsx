import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  Map as MapIcon, 
  Target, 
  BellRing, 
  FileText, 
  ChevronRight
} from 'lucide-react';
import { useApp } from '../../state/AppContext';
import { apiClient } from '../../api/client';
import { isTabAllowed, getRoleConfig } from '../../config/rolePermissions';

export const Sidebar = () => {
  const { user, activeTab, setActiveTab, refreshTrigger } = useApp();
  const [activeAlertsCount, setActiveAlertsCount] = useState(0);

  useEffect(() => {
    apiClient.getAlerts('all')
      .then(alerts => {
        const unack = alerts.filter(a => a.status === 'new').length;
        setActiveAlertsCount(unack);
      })
      .catch(() => setActiveAlertsCount(0));
  }, [refreshTrigger]);

  // Ensure active tab is allowed for current role; fallback to default if not
  useEffect(() => {
    if (user?.role && !isTabAllowed(user.role, activeTab)) {
      const config = getRoleConfig(user.role);
      setActiveTab(config.defaultTab);
    }
  }, [user?.role, activeTab, setActiveTab]);

  const allNavItems = [
    {
      id: 'overview',
      label: 'Overview',
      desc: 'System summary & metrics',
      icon: LayoutDashboard,
    },
    {
      id: 'map',
      label: 'GIS Risk Map',
      desc: 'Geospatial cash-out hotspots',
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
      desc: 'Intervention dispatch queue',
      icon: BellRing,
      badge: activeAlertsCount > 0 ? activeAlertsCount : null
    },
    {
      id: 'intelligence',
      label: 'Intelligence Brief',
      desc: 'Case dossier & evidence',
      icon: FileText,
    }
  ];

  // Role-filtered navigation items strictly adhering to rolePermissions.js
  const visibleNavItems = allNavItems.filter(item => isTabAllowed(user?.role, item.id));

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-950 p-4 flex flex-col justify-between flex-shrink-0">
      <div className="space-y-5">
        
        {/* Navigation Category Label */}
        <div>
          <div className="text-xs font-semibold text-slate-400 px-3 mb-2">
            Modules
          </div>

          <nav className="space-y-1">
            {visibleNavItems.map(item => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;

              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-left transition ${
                    isActive
                      ? 'bg-slate-800 text-white font-medium'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/80'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`p-1.5 rounded-md ${isActive ? 'bg-indigo-600 text-white' : 'bg-slate-900 text-slate-400'}`}>
                      <Icon size={15} />
                    </div>
                    <div>
                      <div className="text-xs font-medium">{item.label}</div>
                      <div className="text-[11px] text-slate-500">{item.desc}</div>
                    </div>
                  </div>

                  {item.badge && (
                    <span className="px-1.5 py-0.2 text-[11px] font-medium rounded bg-red-600 text-white">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Analytical Parameters Info */}
        <div className="px-3 py-2.5 rounded-lg bg-slate-900/70 border border-slate-800/80 text-xs">
          <div className="font-medium text-slate-300 mb-0.5">Prediction Window</div>
          <p className="text-[11px] text-slate-400 leading-normal">
            Targets a fixed 6-hour future horizon for cash-out patrol intervention (ADR-005).
          </p>
        </div>

      </div>

      {/* Footer Navigation: Privacy Policy, Terms, and Project notice */}
      <div className="pt-3 border-t border-slate-800 text-xs space-y-2">
        <div className="flex flex-col space-y-0.5">
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
            <span>Terms & Conditions</span>
            <ChevronRight size={12} />
          </button>
        </div>

        <div className="text-[11px] text-slate-500 px-2 pt-1 border-t border-slate-900">
          <div>CyberCast Prototype v0.1.0</div>
          <div>SIH 2026 Evaluation</div>
        </div>
      </div>
    </aside>
  );
};


