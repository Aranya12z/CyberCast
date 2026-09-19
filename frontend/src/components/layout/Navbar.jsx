import React from 'react';
import { Radar, UserCheck, Database, RefreshCw, LogOut } from 'lucide-react';
import { useApp } from '../../state/AppContext';
import { getRoleConfig } from '../../config/rolePermissions';

export const Navbar = () => {
  const { user, isMockMode, toggleMockMode, refreshData, logout } = useApp();
  const roleConfig = getRoleConfig(user?.role);

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-slate-950 px-6 py-2.5">
      <div className="flex items-center justify-between">
        
        {/* Brand Identity */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center border border-indigo-500/30 text-indigo-400">
            <Radar className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold tracking-tight text-white font-mono">
                CYBER<span className="text-indigo-400">CAST</span>
              </span>
              <span className="text-[11px] px-2 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-800 font-medium">
                SIH 2026 Prototype
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Predictive Cybercrime Cash-out Early Intervention System
            </p>
          </div>
        </div>

        {/* Operational Controls, Locked Role Indicator, and Sign Out */}
        <div className="flex items-center gap-2.5 sm:gap-3">
          
          {/* Refresh Data Button */}
          <button
            onClick={refreshData}
            title="Refresh Intelligence Data"
            className="p-1.5 rounded-md bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition"
          >
            <RefreshCw size={14} />
          </button>

          {/* Data Source Toggle */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-xs">
            <Database size={13} className={isMockMode ? "text-amber-400" : "text-emerald-400"} />
            <span className="text-slate-400 text-xs hidden md:inline">Source:</span>
            <button
              onClick={() => toggleMockMode(!isMockMode)}
              className={`font-medium px-2 py-0.5 rounded text-xs transition ${
                isMockMode
                  ? "bg-slate-800 text-amber-300 border border-amber-800/60"
                  : "bg-slate-800 text-emerald-300 border border-emerald-800/60"
              }`}
              title="Toggle between mock test data and live FastAPI backend"
            >
              {isMockMode ? "Mock Data" : "Live API"}
            </button>
          </div>

          {/* Non-Editable Locked Role Indicator */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-xs">
            <UserCheck size={14} className="text-indigo-400" />
            <span className="text-slate-400 hidden sm:inline">Role:</span>
            <span className="font-semibold text-slate-200">
              {roleConfig.displayName}
            </span>
          </div>

          {/* Active Operator Badge */}
          <div className="hidden lg:flex items-center gap-2 pl-2 border-l border-slate-800">
            <div className="w-7 h-7 rounded-md bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-semibold text-slate-300">
              {user?.name ? user.name.split(' ').map(n => n[0]).join('') : 'CC'}
            </div>
            <div className="text-left">
              <div className="text-xs font-medium text-slate-200">{user?.name || 'Operator'}</div>
              <div className="text-[11px] text-slate-400">{user?.department || "Cyber Crime Division"}</div>
            </div>
          </div>

          {/* Sign Out Button */}
          <button
            onClick={logout}
            title="Sign out of current prototype session"
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-slate-400 hover:text-red-300 hover:bg-slate-800 hover:border-red-900/60 transition text-xs font-medium"
          >
            <LogOut size={13} />
            <span className="hidden sm:inline">Sign Out</span>
          </button>

        </div>

      </div>
    </header>
  );
};


