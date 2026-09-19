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
  Check,
  AlertCircle
} from 'lucide-react';
import { useApp, PROTOTYPE_PROFILES } from '../../state/AppContext';
import { getRoleConfig } from '../../config/rolePermissions';
import { apiClient } from '../../api/client';

export const LoginPage = () => {
  const { selectedLoginRole, setCurrentScreen, loginAsRole } = useApp();

  // Fallback to investigator if accessed without explicit selection
  const roleKey = selectedLoginRole || 'investigator';
  const roleConfig = getRoleConfig(roleKey);
  const prototypeProfile = PROTOTYPE_PROFILES[roleKey] || PROTOTYPE_PROFILES.investigator;

  // Form state matching backend LoginRequest schema (username / password)
  const [username, setUsername] = useState(roleKey);
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // Role visual accents and domain-tailored labels
  const roleVisuals = {
    investigator: {
      badge: 'LAW ENFORCEMENT ACCESS',
      badgeColor: 'border-blue-500/40 text-blue-400 bg-blue-950/40',
      icon: ShieldAlert,
      iconColor: 'text-blue-400 bg-blue-950/60 border-blue-500/30',
      cardBorder: 'border-slate-800 hover:border-blue-500/30',
      idLabel: 'Officer Username / CID Identifier',
      pinLabel: 'Password',
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
      idLabel: 'Analyst Username / Employee ID',
      pinLabel: 'Password',
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
      idLabel: 'System Administrator Username',
      pinLabel: 'Password',
      destinationHint: 'System Overview & Telemetry',
      submitLabel: `Authenticate Session — ${prototypeProfile.name} (Ops)`,
      submittingLabel: 'Authorizing Administrator Session...',
      buttonBg: 'bg-amber-600 hover:bg-amber-500 text-white',
      focusRing: 'focus:ring-2 focus:ring-amber-500/40 focus:border-amber-500'
    }
  };

  const visual = roleVisuals[roleKey] || roleVisuals.investigator;
  const RoleIcon = visual.icon;

  const handleSignIn = async (e) => {
    if (e) e.preventDefault();
    if (!username.trim() || !password) {
      setErrorMessage('Please enter both username and password.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage('');

    try {
      // Real login call to backend POST /api/auth/login
      const tokenData = await apiClient.login(username.trim(), password);
      
      // Fetch authenticated user profile from GET /api/auth/me
      let userProfile = null;
      try {
        const me = await apiClient.getAuthMe();
        userProfile = {
          user_id: me.user_id,
          name: me.name,
          role: me.role,
          department: me.role === 'investigator'
            ? 'Cyber Crime Division, CID'
            : me.role === 'bank_analyst'
            ? 'Fraud Monitoring & Operations'
            : 'CyberCast Operations Command'
        };
      } catch (_) {
        userProfile = {
          user_id: `usr-${tokenData.role}`,
          name: username,
          role: tokenData.role
        };
      }

      // Drive session strictly from server-returned role
      loginAsRole(tokenData.role, userProfile);
    } catch (err) {
      if (err.status === 401 || err.message?.includes('401') || err.message?.includes('Incorrect')) {
        setErrorMessage('Incorrect username or password. Please verify credentials.');
      } else {
        setErrorMessage(err.message || 'Authentication service unreachable. Please check network connection.');
      }
    } finally {
      setIsSubmitting(false);
    }
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
                VERIFIED ACCESS
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
                  Role: {roleKey} {prototypeProfile.bank_name ? `• ${prototypeProfile.bank_name}` : ''}
                </div>
              </div>
            </div>
          </div>

          {/* Error Message Display */}
          {errorMessage && (
            <div className="p-3 rounded-lg bg-rose-950/50 border border-rose-500/40 flex items-center gap-2.5 text-xs text-rose-300">
              <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Real Login Form */}
          <form onSubmit={handleSignIn} className="space-y-4">
            
            {/* Username Input */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label htmlFor="username-input" className="text-xs font-mono text-slate-300 uppercase tracking-wide">
                  {visual.idLabel}
                </label>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <UserCheck className="w-4 h-4" />
                </div>
                <input
                  id="username-input"
                  type="text"
                  autoComplete="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className={`w-full pl-9 pr-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-slate-100 placeholder-slate-500 ${visual.focusRing} focus:outline-none transition-all duration-150`}
                  placeholder="Enter username"
                  required
                />
              </div>
            </div>

            {/* Password Input */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label htmlFor="password-input" className="text-xs font-mono text-slate-300 uppercase tracking-wide">
                  {visual.pinLabel}
                </label>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <KeyRound className="w-4 h-4" />
                </div>
                <input
                  id="password-input"
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={`w-full pl-9 pr-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-slate-100 placeholder-slate-500 ${visual.focusRing} focus:outline-none transition-all duration-150`}
                  placeholder="Enter password"
                  required
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
              <span className="font-semibold text-slate-300">RBAC Enforcement: </span>
              Authentication issues a secure JWT token from the backend. The server-validated role isolates capabilities, panel routing, and write operations across the CyberCast platform.
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
