/**
 * Centralized Role Permissions and Configuration for CyberCast Frontend
 * Defines prototype stakeholder roles, allowed modules, default tabs, and display metadata.
 */

export const ROLE_PERMISSIONS = {
  investigator: {
    role: 'investigator',
    displayName: 'Cyber Crime Investigator',
    department: 'Cyber Crime Division, CID',
    defaultTab: 'map',
    allowedTabs: [
      'overview',
      'map',
      'predictions',
      'alerts',
      'intelligence',
      'privacy',
      'terms'
    ]
  },
  bank_analyst: {
    role: 'bank_analyst',
    displayName: 'Bank / Financial Institution',
    department: 'Fraud Monitoring & Operations',
    defaultTab: 'predictions',
    allowedTabs: [
      'overview',
      'map',
      'predictions',
      'alerts',
      'privacy',
      'terms'
    ]
  },
  administrator: {
    role: 'administrator',
    displayName: 'System Administrator',
    department: 'CyberCast Operations Command',
    defaultTab: 'overview',
    allowedTabs: [
      'overview',
      'map',
      'predictions',
      'alerts',
      'intelligence',
      'privacy',
      'terms'
    ]
  }
};

/**
 * Helper to get role configuration safely, defaulting to investigator if invalid or undefined
 * @param {string} role
 */
export const getRoleConfig = (role) => {
  return ROLE_PERMISSIONS[role] || ROLE_PERMISSIONS.investigator;
};

/**
 * Check if a tab is allowed for a given role
 * @param {string} role
 * @param {string} tabId
 * @returns {boolean}
 */
export const isTabAllowed = (role, tabId) => {
  const config = getRoleConfig(role);
  return config.allowedTabs.includes(tabId);
};
