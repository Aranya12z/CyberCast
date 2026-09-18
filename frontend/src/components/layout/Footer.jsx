import React from 'react';
import { Radar, Shield } from 'lucide-react';
import { useApp } from '../../state/AppContext';

/* ─────────────────────────────────────────────────────────
   FooterLink — styled navigation button using setActiveTab()
   Used for all internal page navigation inside the footer.
───────────────────────────────────────────────────────── */
const FooterLink = ({ tabId, children }) => {
  const { setActiveTab } = useApp();
  return (
    <button
      onClick={() => setActiveTab(tabId)}
      className="block text-left text-[12px] text-slate-400 hover:text-slate-200 transition-colors duration-150 py-0.5"
    >
      {children}
    </button>
  );
};

/* ─────────────────────────────────────────────────────────
   FooterColumnHeading — consistent column label
───────────────────────────────────────────────────────── */
const FooterColumnHeading = ({ children }) => (
  <div className="text-[10px] font-bold font-mono tracking-widest text-slate-400 uppercase mb-4">
    {children}
  </div>
);

/* ─────────────────────────────────────────────────────────
   Footer — global application footer
   Rendered once inside MainLayout (App.jsx), below all page
   content, within the main scroll container.
───────────────────────────────────────────────────────── */
export const Footer = () => {
  const { setActiveTab } = useApp();

  return (
    <footer className="mt-16 border-t border-slate-800 bg-slate-950">

      {/* ── Top grid section ── */}
      <div className="max-w-7xl mx-auto px-6 py-10">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-10">

          {/* ── Column 1: Brand ── */}
          <div className="space-y-4 sm:col-span-2 lg:col-span-1">
            {/* Brand mark — mirrors Navbar identity */}
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-slate-900 border border-indigo-500/30 flex items-center justify-center text-indigo-400 flex-shrink-0">
                <Radar className="w-4 h-4" />
              </div>
              <span className="text-base font-bold tracking-tight text-white font-mono">
                CYBER<span className="text-indigo-400">CAST</span>
              </span>
            </div>

            {/* Tagline */}
            <p className="text-[11px] text-slate-400 leading-relaxed max-w-xs">
              Predictive Cybercrime Cash-out Early Intervention System
            </p>

            {/* Factual description */}
            <p className="text-[11px] text-slate-500 leading-relaxed max-w-xs">
              Academic and hackathon prototype for predictive cybercrime intelligence and proactive intervention.
            </p>

            {/* Project badge */}
            <div className="inline-flex items-center gap-1.5 px-2 py-1 rounded bg-slate-900 border border-slate-800 text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
              <Shield className="w-3 h-3 text-indigo-400" />
              SIH Prototype
            </div>
          </div>

          {/* ── Column 2: Intelligence modules ── */}
          <div>
            <FooterColumnHeading>Intelligence</FooterColumnHeading>
            <nav className="space-y-2">
              <FooterLink tabId="overview">Overview</FooterLink>
              <FooterLink tabId="map">GIS Risk Map</FooterLink>
              <FooterLink tabId="predictions">Top-K Predictions</FooterLink>
              <FooterLink tabId="alerts">Actionable Alerts</FooterLink>
              <FooterLink tabId="intelligence">Intelligence Brief</FooterLink>
            </nav>
          </div>

          {/* ── Column 3: Legal / project pages ── */}
          <div>
            <FooterColumnHeading>Project</FooterColumnHeading>
            <nav className="space-y-2">
              <FooterLink tabId="privacy">Privacy Policy</FooterLink>
              <FooterLink tabId="terms">Terms and Conditions</FooterLink>
            </nav>
          </div>

          {/* ── Column 4: Project information ── */}
          <div>
            <FooterColumnHeading>Project Information</FooterColumnHeading>
            <ul className="space-y-2">
              <li className="text-[12px] text-slate-400">Smart India Hackathon 2026</li>
              <li className="text-[12px] text-slate-400">CyberCast Research Prototype</li>
              <li className="text-[12px] text-slate-400">Prototype / Demonstration Environment</li>
            </ul>
          </div>

        </div>
      </div>

      {/* ── Bottom bar ── */}
      <div className="border-t border-slate-800/80">
        <div className="max-w-7xl mx-auto px-6 py-4 flex flex-col sm:flex-row items-center justify-between gap-3">

          {/* Identity */}
          <div className="flex items-center gap-2 text-[11px] font-mono text-slate-500">
            <span>CyberCast Research Prototype</span>
            <span className="text-slate-700">•</span>
            <span>Smart India Hackathon 2026</span>
          </div>

          {/* Legal links */}
          <div className="flex items-center gap-4 text-[11px] font-mono">
            <button
              onClick={() => setActiveTab('privacy')}
              className="text-slate-500 hover:text-slate-300 transition-colors duration-150"
            >
              Privacy Policy
            </button>
            <span className="text-slate-700">•</span>
            <button
              onClick={() => setActiveTab('terms')}
              className="text-slate-500 hover:text-slate-300 transition-colors duration-150"
            >
              Terms and Conditions
            </button>
          </div>

        </div>
      </div>

    </footer>
  );
};
