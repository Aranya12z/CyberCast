import React from 'react';
import { AppProvider, useApp } from './state/AppContext';
import { Navbar } from './components/layout/Navbar';
import { Sidebar } from './components/layout/Sidebar';
import { Overview } from './pages/Overview';
import { GISMap } from './pages/GISMap';
import { Predictions } from './pages/Predictions';
import { Alerts } from './pages/Alerts';
import { Intelligence } from './pages/Intelligence';
import { PrivacyPolicy } from './pages/PrivacyPolicy';
import { TermsAndConditions } from './pages/TermsAndConditions';

const MainLayout = () => {
  const { activeTab, setActiveTab } = useApp();

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 selection:bg-indigo-600 selection:text-white">
      {/* Top Tactical Command Header */}
      <Navbar />

      <div className="flex-1 flex overflow-hidden">
        {/* Left Tactical Navigation Sidebar */}
        <Sidebar />

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto p-6 bg-slate-950 flex flex-col justify-between">
          <div className="max-w-7xl w-full mx-auto flex-1">
            {activeTab === 'overview' && <Overview />}
            {activeTab === 'map' && <GISMap />}
            {activeTab === 'predictions' && <Predictions />}
            {activeTab === 'alerts' && <Alerts />}
            {activeTab === 'intelligence' && <Intelligence />}
            {activeTab === 'privacy' && <PrivacyPolicy />}
            {activeTab === 'terms' && <TermsAndConditions />}
          </div>

          {/* Bottom Footer with Compliance and Disclaimers */}
          <footer className="mt-12 pt-4 border-t border-slate-800/80 text-xs text-slate-400 max-w-7xl w-full mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-[11px] font-mono text-slate-400">
              <span>CyberCast Research Prototype</span>
              <span>•</span>
              <span>Smart India Hackathon (SIH 2026)</span>
            </div>

            <div className="flex items-center gap-4 text-xs font-mono">
              <button
                onClick={() => setActiveTab('privacy')}
                className="hover:text-slate-300 transition"
              >
                Privacy Policy
              </button>
              <span>•</span>
              <button
                onClick={() => setActiveTab('terms')}
                className="hover:text-slate-300 transition"
              >
                Terms and Conditions
              </button>
            </div>
          </footer>
        </main>
      </div>
    </div>
  );
};

export function App() {
  return (
    <AppProvider>
      <MainLayout />
    </AppProvider>
  );
}

export default App;
