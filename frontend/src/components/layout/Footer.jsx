import React from 'react';
import { Radar } from 'lucide-react';
import { useApp } from '../../state/AppContext';
import { isTabAllowed } from '../../config/rolePermissions';

/* ─────────────────────────────────────────────────────────
   FooterLink — styled navigation button using setActiveTab()
───────────────────────────────────────────────────────── */
const FooterLink = ({ tabId, children }) => {
  const { setActiveTab } = useApp();
  return (
    <button
      onClick={() => setActiveTab(tabId)}
      className="block text-left text-xs text-slate-400 hover:text-slate-200 transition-colors duration-150 py-0.5"
    >
      {children}
    </button>
  );
};

/* ─────────────────────────────────────────────────────────
   FooterColumnHeading — standard clean column label
───────────────────────────────────────────────────────── */
const FooterColumnHeading = ({ children }) => (
  <div className="text-xs font-semibold text-slate-300 mb-3">
    {children}
  </div>
);

export const Footer = () => {
  const { user, setActiveTab } = useApp();

  return (
    <footer className="mt-14 border-t border-slate-800 bg-slate-950">

      {/* Grid section */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">

          {/* Column 1: Brand */}
          <div className="space-y-3 sm:col-span-2 lg:col-span-1">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-slate-900 border border-indigo-500/30 flex items-center justify-center text-indigo-400 flex-shrink-0">
                <Radar className="w-3.5 h-3.5" />
              </div>
              <span className="text-base font-bold tracking-tight text-white font-mono">
                CYBER<span className="text-indigo-400">CAST</span>
              </span>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed max-w-xs">
              Predictive Cybercrime Cash-out Early Intervention System
            </p>

            <p className="text-[11px] text-slate-500 leading-relaxed max-w-xs">
              Student engineering prototype for predictive cybercrime intelligence and early intervention.
            </p>
          </div>

          {/* Column 2: Navigation modules (Role-aware) */}
          <div>
            <FooterColumnHeading>Modules</FooterColumnHeading>
            <nav className="space-y-1.5">
              {isTabAllowed(user?.role, 'overview') && <FooterLink tabId="overview">Overview</FooterLink>}
              {isTabAllowed(user?.role, 'map') && <FooterLink tabId="map">GIS Risk Map</FooterLink>}
              {isTabAllowed(user?.role, 'predictions') && <FooterLink tabId="predictions">Top-K Predictions</FooterLink>}
              {isTabAllowed(user?.role, 'alerts') && <FooterLink tabId="alerts">Actionable Alerts</FooterLink>}
              {isTabAllowed(user?.role, 'intelligence') && <FooterLink tabId="intelligence">Intelligence Brief</FooterLink>}
            </nav>
          </div>

          {/* Column 3: Legal & project pages */}
          <div>
            <FooterColumnHeading>Project</FooterColumnHeading>
            <nav className="space-y-1.5">
              <FooterLink tabId="privacy">Privacy Policy</FooterLink>
              <FooterLink tabId="terms">Terms & Conditions</FooterLink>
            </nav>
          </div>

          {/* Column 4: Project information */}
          <div>
            <FooterColumnHeading>About CyberCast</FooterColumnHeading>
            <ul className="space-y-1.5 text-xs text-slate-400">
              <li>Smart India Hackathon 2026</li>
              <li>Academic Research Prototype</li>
              <li>Simulated Evaluation Environment</li>
            </ul>
          </div>

        </div>
      </div>

      {/* Bottom bar */}
      <div className="border-t border-slate-800/80">
        <div className="max-w-7xl mx-auto px-6 py-3.5 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-500">
          <div>
            CyberCast Prototype • Smart India Hackathon 2026
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setActiveTab('privacy')}
              className="hover:text-slate-300 transition-colors duration-150"
            >
              Privacy Policy
            </button>
            <span>•</span>
            <button
              onClick={() => setActiveTab('terms')}
              className="hover:text-slate-300 transition-colors duration-150"
            >
              Terms & Conditions
            </button>
          </div>
        </div>
      </div>

    </footer>
  );
};

