import React, { useEffect } from 'react';
import { AppProvider, useApp } from './state/AppContext';
import { isTabAllowed, getRoleConfig } from './config/rolePermissions';
import { LandingPage } from './pages/auth/LandingPage';
import { LoginPage } from './pages/auth/LoginPage';
import { Navbar } from './components/layout/Navbar';
import { Sidebar } from './components/layout/Sidebar';
import { Footer } from './components/layout/Footer';
import { Overview } from './pages/Overview';
import { GISMap } from './pages/GISMap';
import { Predictions } from './pages/Predictions';
import { Alerts } from './pages/Alerts';
import { Intelligence } from './pages/Intelligence';
import { PrivacyPolicy } from './pages/PrivacyPolicy';
import { TermsAndConditions } from './pages/TermsAndConditions';

const MainLayout = () => {
  const { activeTab, setActiveTab, user } = useApp();

  // Guard against activeTab not permitted for the authenticated role
  useEffect(() => {
    if (user?.role && !isTabAllowed(user.role, activeTab)) {
      const config = getRoleConfig(user.role);
      setActiveTab(config.defaultTab);
    }
  }, [user?.role, activeTab, setActiveTab]);

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

          {/* Global Footer */}
          <Footer />
        </main>
      </div>
    </div>
  );
};

const AppContent = () => {
  const { currentScreen, isAuthenticated } = useApp();

  if (currentScreen === 'login') {
    return <LoginPage />;
  }

  if (currentScreen === 'dashboard' && isAuthenticated) {
    return <MainLayout />;
  }

  // Default: LandingPage (also returns unauthenticated users to landing screen)
  return <LandingPage />;
};

export function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}

export default App;

