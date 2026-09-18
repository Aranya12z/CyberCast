import React from 'react';
import { 
  Radar, 
  Shield, 
  ShieldAlert, 
  Building2, 
  Terminal, 
  ArrowRight, 
  CheckCircle2, 
  Sparkles,
  Lock,
  Layers
} from 'lucide-react';
import { useApp } from '../../state/AppContext';
import { ROLE_PERMISSIONS } from '../../config/rolePermissions';

export const LandingPage = () => {
  const { selectLoginRole } = useApp();

  const roleCards = [
    {
      key: 'investigator',
      config: ROLE_PERMISSIONS.investigator,
      badge: 'LAW ENFORCEMENT',
      badgeColor: 'border-blue-500/40 text-blue-400 bg-blue-950/40',
      icon: ShieldAlert,
      iconColor: 'text-blue-400 bg-blue-950/60 border-blue-500/30',
      accentHover: 'hover:border-blue-500/50 hover:shadow-blue-500/10',
      features: [
        'Spatial GIS Risk Map & withdrawal hotspots',
        'Top-K ATM predictions with 6-hr intervention horizon',
        'Actionable patrol dispatch & intervention alerts',
        'Case intelligence dossier & FIR telemetry'
      ],
      ctaText: 'Access Investigator Portal'
    },
    {
      key: 'bank_analyst',
      config: ROLE_PERMISSIONS.bank_analyst,
      badge: 'FINANCIAL INSTITUTIONS',
      badgeColor: 'border-emerald-500/40 text-emerald-400 bg-emerald-950/40',
      icon: Building2,
      iconColor: 'text-emerald-400 bg-emerald-950/60 border-emerald-500/30',
      accentHover: 'hover:border-emerald-500/50 hover:shadow-emerald-500/10',
      features: [
        'ATM cash-out vulnerability rankings',
        'Targeted ATM & card freeze alerts',
        'Cross-bank mule account cash-out telemetry',
        'High-risk withdrawal horizon monitoring'
      ],
      ctaText: 'Access Banking Portal'
    },
    {
      key: 'administrator',
      config: ROLE_PERMISSIONS.administrator,
      badge: 'OPERATIONS & TELEMETRY',
      badgeColor: 'border-amber-500/40 text-amber-400 bg-amber-950/40',
      icon: Terminal,
      iconColor: 'text-amber-400 bg-amber-950/60 border-amber-500/30',
      accentHover: 'hover:border-amber-500/50 hover:shadow-amber-500/10',
      features: [
        'ML prediction pipeline health & metrics',
        'System-wide alert escalation & audit trails',
        'Multi-agency role access governance',
        'Model versioning & telemetry monitoring'
      ],
      ctaText: 'Access Admin Console'
    }
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-indigo-600 selection:text-white">
      
      {/* Top Brand Header */}
      <header className="border-b border-slate-800/80 bg-slate-950/90 backdrop-blur px-8 py-4 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-slate-900 flex items-center justify-center border border-indigo-500/40 text-indigo-400 shadow-sm shadow-indigo-950">
              <Radar className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xl font-bold tracking-tight text-white font-mono">
                  CYBER<span className="text-indigo-400">CAST</span>
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-bold uppercase tracking-wider">
                  SIH 2026 PROTOTYPE
                </span>
              </div>
              <p className="text-[11px] text-slate-400 tracking-wide">
                Predictive Cybercrime Cash-out Early Intervention System
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 text-xs font-mono text-slate-400">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 border border-slate-800">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              PROTOTYPE ENVIRONMENT
            </span>
          </div>
        </div>
      </header>

      {/* Main Hero & Portals Section */}
      <main className="max-w-7xl mx-auto px-6 py-12 flex-1 flex flex-col justify-center w-full">
        
        {/* Hero Section */}
        <div className="text-center max-w-3xl mx-auto mb-12 space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-950/50 border border-indigo-500/30 text-indigo-300 text-xs font-mono font-medium">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            Role-Based Operational Access Architecture
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
            Stakeholder Intelligence Portals
          </h1>
          <p className="text-sm sm:text-base text-slate-400 leading-relaxed max-w-2xl mx-auto">
            Select your agency portal to access specialized early intervention dashboards, 
            spatial cash-out risk predictions, and threshold-triggered alert pipelines.
          </p>
        </div>

        {/* 3 Stakeholder Portals Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
          {roleCards.map(card => {
            const Icon = card.icon;
            return (
              <div
                key={card.key}
                className={`relative flex flex-col justify-between bg-slate-900/60 border border-slate-800 rounded-xl p-6 transition-all duration-200 shadow-lg ${card.accentHover} hover:-translate-y-1`}
              >
                <div>
                  {/* Top Badge & Icon */}
                  <div className="flex items-center justify-between mb-4">
                    <span className={`text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${card.badgeColor}`}>
                      {card.badge}
                    </span>
                    <div className={`p-2.5 rounded-lg border ${card.iconColor}`}>
                      <Icon className="w-5 h-5" />
                    </div>
                  </div>

                  {/* Title & Department */}
                  <h2 className="text-lg font-bold text-white mb-1">
                    {card.config.displayName}
                  </h2>
                  <div className="text-xs font-mono text-slate-400 mb-5">
                    {card.config.department}
                  </div>

                  {/* Key Capabilities */}
                  <div className="space-y-2.5 pt-4 border-t border-slate-800/80 mb-6">
                    <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
                      Authorized Capabilities:
                    </div>
                    {card.features.map((feat, idx) => (
                      <div key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                        <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0 mt-0.5" />
                        <span className="leading-snug">{feat}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Portal Access Button */}
                <button
                  onClick={() => selectLoginRole(card.key)}
                  className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-slate-800 hover:bg-indigo-600 text-white text-xs font-semibold tracking-wide border border-slate-700 hover:border-indigo-500 transition-all duration-150 shadow"
                >
                  <span>{card.ctaText}</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            );
          })}
        </div>

        {/* Demonstration Disclaimer Note */}
        <div className="mt-10 p-4 rounded-lg bg-slate-900/40 border border-slate-800/80 max-w-2xl mx-auto text-center space-y-1">
          <div className="flex items-center justify-center gap-2 text-xs font-mono font-semibold text-slate-300">
            <Lock className="w-3.5 h-3.5 text-indigo-400" />
            <span>SIH PROTOTYPE DEMONSTRATION NOTICE</span>
          </div>
          <p className="text-[11px] text-slate-400">
            Authentication is simulated client-side for academic and evaluation review. 
            Selecting a stakeholder launches pre-configured demonstration credentials adhering to the CyberCast RBAC matrix.
          </p>
        </div>

      </main>

      {/* Bottom Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950 py-4 px-8 text-center text-[11px] font-mono text-slate-400">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>CyberCast Research Prototype • Smart India Hackathon 2026</div>
          <div className="text-slate-400">Predictive Cybercrime Cash-out Early Intervention</div>
        </div>
      </footer>

    </div>
  );
};
