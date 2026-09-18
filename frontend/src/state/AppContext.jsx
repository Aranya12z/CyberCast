import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient } from '../api/client';

const AppContext = createContext(null);

export const AppProvider = ({ children }) => {
  const [user, setUser] = useState({
    user_id: 'usr-sharma-901',
    name: 'Inspector Sharma',
    role: 'investigator', // 'investigator' | 'bank_analyst' | 'administrator'
    department: 'Cyber Crime Division, CID'
  });

  const [activeTab, setActiveTab] = useState('overview');
  const [selectedCrimeId, setSelectedCrimeId] = useState('crm-890214');
  const [isMockMode, setIsMockMode] = useState(apiClient.isMockMode());
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    apiClient.getAuthMe()
      .then(data => setUser(data))
      .catch(() => {
        // Fallback user if auth route unavailable
        setUser({
          user_id: 'usr-sharma-901',
          name: 'Inspector Sharma',
          role: 'investigator',
          department: 'Cyber Crime Division'
        });
      });
  }, [refreshTrigger]);

  const toggleMockMode = (enable) => {
    apiClient.setMockMode(enable);
    setIsMockMode(enable);
    setRefreshTrigger(prev => prev + 1);
  };

  const setRole = (newRole) => {
    setUser(prev => ({ ...prev, role: newRole }));
  };

  const refreshData = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <AppContext.Provider
      value={{
        user,
        setRole,
        activeTab,
        setActiveTab,
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
