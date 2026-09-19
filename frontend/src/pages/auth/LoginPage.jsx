import React, { useState } from 'react';
import { 
  Radar, 
  ArrowLeft, 
  ShieldAlert, 
  Building2, 
  Terminal, 
  KeyRound, 
  UserCheck, 
  LogIn, 
  Info,
  Compass,
  Check
} from 'lucide-react';
import { useApp, PROTOTYPE_PROFILES } from '../../state/AppContext';
import { getRoleConfig } from '../../config/rolePermissions';

export const LoginPage = () => {
  const { selectedLoginRole, setCurrentScreen, loginAsRole } = useApp();

  // Fallback to investigator if accessed without explicit selection
  const roleKey = selectedLoginRole || 'investigator';
  const roleConfig = getRoleConfig(roleKey);
  const prototypeProfile = PROTOTYPE_PROFILES[roleKey] || PROTOTYPE_PROFILES.investigator;

  // Form mock state for interactive feel during demonstration
  const [operatorId, setOperatorId] = useState(prototypeProfile.user_id);
  const [pinCode, setPinCode] = useState('••••••••');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Role visual accents and domain-tailored labels
  const roleVisuals = {
    investigator: {
      badge: 'LAW ENFORCEMENT ACCESS',
      badgeColor: 'border-blue-500/40 text-blue-400 bg-blue-950/40',
      icon: ShieldAlert,
      iconColor: 'text-blue-400 bg-blue-950/60 border-blue-500/30',
      cardBorder: 'border-slate-800 hover:border-blue-500/30',
      idLabel: 'Officer Badge / CID Identifier',
      pinLabel: 'Authorization Access PIN',
      destinationHint: 'GIS Risk Map (6-Hr Horizon)',
      submitLabel: `Authenticate Session — ${prototypeProfile.name} (CID)`,
      submittingLabel: 'Authorizing Law Enforcement Session...',
      buttonBg: 'bg-blue-600 hover:bg-blue-500 text-white',
      focusRing: 'focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500'
    },
    bank_analyst: {
      badge: 'FINANCIAL INSTITUTION ACCESS',
      badgeColor: 'border-emerald-500/40 text-emerald-400 bg-emerald-950/40',
      icon: Building2,
      iconColor: 'text-emerald-400 bg-emerald-950/60 border-emerald-500/30',
      cardBorder: 'border-slate-800 hover:border-emerald-500/30',
      idLabel: 'Analyst Identifier / Employee ID',
      pinLabel: 'Fraud Operations Access PIN',
      destinationHint: 'Top-K Predictions (ATM Cash-out)',
      submitLabel: `Authenticate Session — ${prototypeProfile.name} (Banking)`,
      submittingLabel: 'Authorizing Financial Institution Session...',
      buttonBg: 'bg-emerald-600 hover:bg-emerald-500 text-white',
      focusRing: 'focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500'
    },
    administrator: {
      badge: 'OPERATIONS & TELEMETRY ACCESS',
      badgeColor: 'border-amber-500/40 text-amber-400 bg-amber-950/40',
      icon: Terminal,
      iconColor: 'text-amber-400 bg-amber-950/60 border-amber-500/30',
      cardBorder: 'border-slate-800 hover:border-amber-500/30',
      idLabel: 'System Administrator Identifier',
      pinLabel: 'Console Key / PIN',
      destinationHint: 'System Overview & Telemetry',
      submitLabel: `Authenticate Session — ${prototypeProfile.name} (Ops)`,
      submittingLabel: 'Authorizing Administrator Session...',
      buttonBg: 'bg-amber-600 hover:bg-amber-500 text-white',
      focusRing: 'focus:ring-2 focus:ring-amber-500/40 focus:border-amber-500'
    }
  };

  const visual = roleVisuals[roleKey] || roleVisuals.investigator;
  const RoleIcon = visual.icon;

  const handleDemoSignIn = (e) => {
    if (e) e.preventDefault();
    setIsSubmitting(true);
    // Simulate brief validation feedback for demonstration
    setTimeout(() => {
      loginAsRole(roleKey);
    }, 250);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-indigo-600 selection:text-white">
      
      {/* Top Header with Back Action */}
      <header className="border-b border-slate-800/80 bg-slate-950/90 backdrop-blur px-8 py-3.5 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          
          <button
            onClick={() => setCurrentScreen('landing')}
            className="flex items-center gap-2 text-xs font-mono text-slate-400 hover:text-white transition-colors duration-150 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>BACK TO PORTALS</span>
          </button>

          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center border border-indigo-500/40 text-indigo-400">
              <Radar className="w-4 h-4" />
            </div>
            <span className="text-base font-bold tracking-tight text-white font-mono">
              CYBER<span className="text-indigo-400">CAST</span>
            </span>
          </div>

          <div className="text-[10px] font-mono px-2.5 py-1 rounded bg-slate-900 text-slate-400 border border-slate-800 font-bold uppercase tracking-wider">
            SIH EVALUATION
          </div>

        </div>
      </header>

      {/* Main Login Card */}
      <main className="max-w-lg mx-auto px-6 py-8 flex-1 flex flex-col justify-center w-full">
        
        <div className={`bg-slate-900/70 border ${visual.cardBorder} rounded-2xl p-7 sm:p-8 shadow-2xl transition-colors duration-200 space-y-5`}>
          
          {/* Header Role Identity */}
          <div className="space-y-2.5 text-center">
            
            <div className="inline-flex items-center justify-center mb-0.5">
              <div className={`p-3 rounded-xl border ${visual.iconColor} shadow-md`}>
                <RoleIcon className="w-6 h-6" />
              </div>
            </div>

            <div className="flex justify-center">
              <span className={`text-[10px] font-mono font-bold uppercase tracking-wider px-2.5 py-0.5 rounded border ${visual.badgeColor}`}>
                {visual.badge}
              </span>
            </div>

            <h1 className="text-2xl font-bold text-white tracking-tight">
              {roleConfig.displayName}
            </h1>

            <p className="text-xs font-mono text-slate-400">
              {roleConfig.department}
            </p>

          </div>

          {/* Pre-Configured Operator Card */}
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2.5">
            <div className="flex items-center justify-between text-[11px] font-mono">
              <span className="text-slate-400 uppercase tracking-wider">OPERATOR PROFILE:</span>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-900 text-indigo-300 font-semibold border border-indigo-500/20 text-[10px]">
                <Check className="w-3 h-3 text-indigo-400" />
                VERIFIED DEMO ID
              </span>
            </div>

            <div className="flex items-center gap-3 pt-0.5">
              <div className="w-9 h-9 rounded-lg bg-indigo-950/60 border border-indigo-500/30 flex items-center justify-center text-indigo-300 font-mono font-bold text-xs">
                {prototypeProfile.name.split(' ').map(n => n[0]).join('')}
              </div>
              <div className="text-left">
                <div className="text-xs font-semibold text-white">
                  {prototypeProfile.name}
                </div>
                <div className="text-[11px] font-mono text-slate-400">
                  ID: {prototypeProfile.user_id} {prototypeProfile.bank_name ? `• ${prototypeProfile.bank_name}` : ''}
                </div>
              </div>
            </div>
          </div>

          {/* Simulated Login Form */}
          <form onSubmit={handleDemoSignIn} className="space-y-4">
            
            {/* Operator Identifier Input */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label htmlFor="operator-id-input" className="text-xs font-mono text-slate-300 uppercase tracking-wide">
                  {visual.idLabel}
                </label>
                <span className="text-[10px] font-mono text-indigo-400 bg-indigo-950/40 border border-indigo-500/20 px-1.5 py-0.2 rounded">
                  AUTO-FILLED FOR DEMO
                </span>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <UserCheck className="w-4 h-4" />
                </div>
                <input
                  id="operator-id-input"
                  type="text"
                  autoComplete="off"
                  value={operatorId}
                  onChange={(e) => setOperatorId(e.target.value)}
                  className={`w-full pl-9 pr-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-slate-100 placeholder-slate-500 ${visual.focusRing} focus:outline-none transition-all duration-150`}
                  placeholder="Officer / Analyst Identifier"
                />
              </div>
            </div>

            {/* Access Token Input */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label htmlFor="operator-pin-input" className="text-xs font-mono text-slate-300 uppercase tracking-wide">
                  {visual.pinLabel}
                </label>
                <span className="text-[10px] font-mono text-slate-400 bg-slate-950 border border-slate-800 px-1.5 py-0.2 rounded">
                  AUTHORIZED KEY
                </span>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <KeyRound className="w-4 h-4" />
                </div>
                <input
                  id="operator-pin-input"
                  type="password"
                  autoComplete="off"
                  value={pinCode}
                  onChange={(e) => setPinCode(e.target.value)}
                  className={`w-full pl-9 pr-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-slate-100 placeholder-slate-500 ${visual.focusRing} focus:outline-none transition-all duration-150`}
                  placeholder="Security Access Key"
                />
              </div>
            </div>

            {/* Target Routing Hint */}
            <div className="flex items-center justify-between px-3 py-2 rounded-lg bg-slate-950/70 border border-slate-800 text-[11px] font-mono">
              <div className="flex items-center gap-1.5 text-slate-400">
                <Compass className="w-3.5 h-3.5 text-indigo-400" />
                <span>DEFAULT TARGET:</span>
              </div>
              <span className="font-semibold text-indigo-300">
                {visual.destinationHint}
              </span>
            </div>

            {/* Primary Sign In Button */}
            <button
              type="submit"
              disabled={isSubmitting}
              className={`w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg font-semibold text-xs tracking-wide transition-all duration-150 shadow-md ${visual.buttonBg} ${isSubmitting ? 'opacity-70 cursor-wait' : ''} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900`}
            >
              <LogIn className="w-4 h-4" />
              <span>
                {isSubmitting ? visual.submittingLabel : visual.submitLabel}
              </span>
            </button>

          </form>

          {/* Truthful Prototype Demonstration Notice */}
          <div className="p-3 rounded-lg bg-slate-950/40 border border-slate-800/80 flex items-start gap-2.5 text-[11px] text-slate-400 leading-relaxed">
            <Info className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-slate-300">SIH Evaluation Mode: </span>
              Prototype demonstration of role-based access control. Authenticating loads the verified stakeholder profile, initializes session persistence, and isolates navigation according to the CyberCast RBAC matrix.
            </div>
          </div>

        </div>

      </main>

      {/* Bottom Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950 py-3.5 px-8 text-center text-[11px] font-mono text-slate-400">
        <div>CyberCast Prototype • Academic & Hackathon Evaluation</div>
      </footer>

    </div>
  );
};

