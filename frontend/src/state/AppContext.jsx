import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { ROLE_PERMISSIONS, getRoleConfig } from '../config/rolePermissions';

const AppContext = createContext(null);

const SESSION_STORAGE_KEY = 'cybercast_session_auth';

// Prototype mock profiles for instant, zero-backend role simulation
export const PROTOTYPE_PROFILES = {
  investigator: {
    user_id: 'usr-sharma-901',
    name: 'Inspector Sharma',
    role: 'investigator',
    department: 'Cyber Crime Division, CID'
  },
  bank_analyst: {
    user_id: 'usr-priya-902',
    name: 'Priya Nair',
    role: 'bank_analyst',
    department: 'Fraud Monitoring & Operations',
    bank_name: 'National Banking Fraud Monitoring Cell'
  },
  administrator: {
    user_id: 'usr-admin-903',
    name: 'System Admin',
    role: 'administrator',
    department: 'CyberCast Operations Command'
  }
};

const getStoredSession = () => {
  try {
    const raw = sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (!raw) return null;
    const session = JSON.parse(raw);
    if (session && session.isAuthenticated && session.user && ROLE_PERMISSIONS[session.user.role]) {
      return session;
    }
  } catch (err) {
    console.warn('Unable to parse stored session:', err);
  }
  return null;
};

export const AppProvider = ({ children }) => {
  const initialSession = getStoredSession();

  // Authentication & Screen state
  const [isAuthenticated, setIsAuthenticated] = useState(Boolean(initialSession?.isAuthenticated));
  const [currentScreen, setCurrentScreen] = useState(initialSession ? 'dashboard' : 'landing');
  const [selectedLoginRole, setSelectedLoginRole] = useState(null);

  // User state (restores from session or defaults to Inspector Sharma for existing prototype dashboard)
  const [user, setUser] = useState(
    initialSession?.user || PROTOTYPE_PROFILES.investigator
  );

  // Active navigation tab
  const [activeTab, setActiveTab] = useState(
    initialSession?.activeTab || (initialSession?.user?.role ? getRoleConfig(initialSession.user.role).defaultTab : 'overview')
  );

  // Existing crime selection & mock mode state
  const [selectedCrimeId, setSelectedCrimeId] = useState('crm-890214');
  const [isMockMode, setIsMockMode] = useState(apiClient.isMockMode());
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Listen for auth expiration events from apiClient
  useEffect(() => {
    const handleAuthExpired = () => {
      setIsAuthenticated(false);
      setSelectedLoginRole(null);
      setCurrentScreen('landing');
      setUser(PROTOTYPE_PROFILES.investigator);
      setActiveTab('overview');
    };

    window.addEventListener('cybercast_auth_expired', handleAuthExpired);
    return () => {
      window.removeEventListener('cybercast_auth_expired', handleAuthExpired);
    };
  }, []);

  // Optional sync with backend auth if mock mode is disabled
  useEffect(() => {
    if (!apiClient.isMockMode() && isAuthenticated && apiClient.getToken()) {
      apiClient.getAuthMe()
        .then(data => {
          if (data && data.role) {
            setUser(prev => ({
              ...prev,
              user_id: data.user_id,
              name: data.name,
              role: data.role,
              department: data.role === 'investigator'
                ? 'Cyber Crime Division, CID'
                : data.role === 'bank_analyst'
                ? 'Fraud Monitoring & Operations'
                : 'CyberCast Operations Command'
            }));
          }
        })
        .catch(() => {
          // Handled by 401 interceptor in apiClient
        });
    }
  }, [refreshTrigger, isAuthenticated]);

  /**
   * Select a role to navigate to its login screen
   * @param {string} role
   */
  const selectLoginRole = (role) => {
    if (ROLE_PERMISSIONS[role]) {
      setSelectedLoginRole(role);
      setCurrentScreen('login');
    } else {
      console.warn(`Invalid role selected: ${role}`);
    }
  };

  /**
   * Login action: sets authenticated role profile and persists session
   * @param {string} role
   * @param {object} customProfile
   */
  const loginAsRole = (role, customProfile = null) => {
    const targetRole = ROLE_PERMISSIONS[role] ? role : 'investigator';
    const baseProfile = PROTOTYPE_PROFILES[targetRole] || PROTOTYPE_PROFILES.investigator;
    const profile = customProfile ? { ...baseProfile, ...customProfile, role: targetRole } : baseProfile;
    const roleConfig = getRoleConfig(targetRole);

    setUser(profile);
    setIsAuthenticated(true);
    setCurrentScreen('dashboard');
    setSelectedLoginRole(null);
    setActiveTab(roleConfig.defaultTab);

    try {
      sessionStorage.setItem(
        SESSION_STORAGE_KEY,
        JSON.stringify({
          isAuthenticated: true,
          user: profile,
          activeTab: roleConfig.defaultTab
        })
      );
    } catch (err) {
      console.warn('Failed to save session to sessionStorage:', err);
    }
  };

  /**
   * Logout action: clears token, session, and returns to landing portal
   */
  const logout = () => {
    apiClient.logout();
    setIsAuthenticated(false);
    setSelectedLoginRole(null);
    setCurrentScreen('landing');
    setUser(PROTOTYPE_PROFILES.investigator);
    setActiveTab('overview');

    try {
      sessionStorage.removeItem(SESSION_STORAGE_KEY);
    } catch (err) {
      console.warn('Failed to clear session storage:', err);
    }
  };

  /**
   * Wrapper for tab change to persist tab across browser refreshes
   */
  const handleSetActiveTab = (tab) => {
    setActiveTab(tab);
    try {
      const raw = sessionStorage.getItem(SESSION_STORAGE_KEY);
      if (raw) {
        const session = JSON.parse(raw);
        if (session && session.isAuthenticated) {
          session.activeTab = tab;
          sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
        }
      }
    } catch (err) {
      // Ignore sessionStorage write error
    }
  };

  /**
   * Kept temporarily for backward compatibility with Navbar role switcher
   */
  const setRole = (newRole) => {
    if (PROTOTYPE_PROFILES[newRole]) {
      const newProfile = PROTOTYPE_PROFILES[newRole];
      setUser(newProfile);
      const roleConfig = getRoleConfig(newRole);
      if (!roleConfig.allowedTabs.includes(activeTab)) {
        handleSetActiveTab(roleConfig.defaultTab);
      }
      if (isAuthenticated) {
        try {
          sessionStorage.setItem(
            SESSION_STORAGE_KEY,
            JSON.stringify({
              isAuthenticated: true,
              user: newProfile,
              activeTab: roleConfig.defaultTab
            })
          );
        } catch (e) {}
      }
    } else {
      setUser(prev => ({ ...prev, role: newRole }));
    }
  };

  const toggleMockMode = (enable) => {
    apiClient.setMockMode(enable);
    setIsMockMode(enable);
    setRefreshTrigger(prev => prev + 1);
  };

  const refreshData = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <AppContext.Provider
      value={{
        // Authentication & Screen state
        currentScreen,
        setCurrentScreen,
        isAuthenticated,
        selectedLoginRole,
        selectLoginRole,
        loginAsRole,
        logout,

        // User & Role state (backward compatible)
        user,
        setRole,

        // Tab navigation
        activeTab,
        setActiveTab: handleSetActiveTab,

        // Operational & Mock state
        selectedCrimeId,
        setSelectedCrimeId,
        isMockMode,
        toggleMockMode,
        refreshTrigger,
        refreshData
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

