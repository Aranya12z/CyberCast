import React from 'react';
import { Shield, Radar, UserCheck, Database, RefreshCw } from 'lucide-react';
import { useApp } from '../../state/AppContext';

export const Navbar = () => {
  const { user, setRole, isMockMode, toggleMockMode, refreshData } = useApp();

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-slate-950 px-6 py-3">
      <div className="flex items-center justify-between">
        
        {/* Left: Brand Identity */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-slate-900 flex items-center justify-center border border-indigo-500/40 text-indigo-400">
            <Radar className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold tracking-tight text-white font-mono">
                CYBER<span className="text-indigo-400">CAST</span>
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-bold uppercase tracking-wider">
                SIH PROTOTYPE
              </span>
            </div>
            <p className="text-[11px] text-slate-400 tracking-wide">
              Predictive Cybercrime Cash-out Early Intervention System
            </p>
          </div>
        </div>

        {/* Right: Operational Controls & Role Switcher */}
        <div className="flex items-center gap-4">
          
          {/* Refresh Data Button */}
          <button
            onClick={refreshData}
            title="Refresh Intelligence Data"
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition"
          >
            <RefreshCw size={15} />
          </button>

          {/* Mode Badge & Toggle */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs">
            <Database size={14} className={isMockMode ? "text-amber-400" : "text-emerald-400"} />
            <span className="text-slate-400 font-mono text-[11px]">DATA SOURCE:</span>
            <button
              onClick={() => toggleMockMode(!isMockMode)}
              className={`font-mono font-semibold px-2 py-0.5 rounded text-[11px] border transition ${
                isMockMode
                  ? "bg-slate-800 text-amber-300 border-amber-800/80"
                  : "bg-slate-800 text-emerald-300 border-emerald-800/80"
              }`}
              title="Click to toggle between Mock Fixtures and Live Backend"
            >
              {isMockMode ? "MOCK FIXTURES" : "LIVE FASTAPI"}
            </button>
          </div>

          {/* Role-Based Access Control Switcher */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800">
            <UserCheck size={14} className="text-indigo-400" />
            <span className="text-slate-400 text-xs font-mono">ROLE:</span>
            <select
              value={user.role}
              onChange={(e) => setRole(e.target.value)}
              className="bg-transparent text-xs font-mono font-semibold text-indigo-300 focus:outline-none cursor-pointer"
            >
              <option value="investigator" className="bg-slate-900 text-slate-100">Investigator (LEA)</option>
              <option value="bank_analyst" className="bg-slate-900 text-slate-100">Bank / FI Analyst</option>
              <option value="administrator" className="bg-slate-900 text-slate-100">Administrator</option>
            </select>
          </div>

          {/* Active Operator Badge */}
          <div className="hidden lg:flex items-center gap-2.5 pl-2 border-l border-slate-800">
            <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-mono font-bold text-slate-300">
              {user.name.split(' ').map(n => n[0]).join('')}
            </div>
            <div className="text-left">
              <div className="text-xs font-medium text-slate-200">{user.name}</div>
              <div className="text-[10px] text-slate-400 font-mono">{user.department || "Cyber Crime Cell"}</div>
            </div>
          </div>

        </div>

      </div>
    </header>
  );
};
