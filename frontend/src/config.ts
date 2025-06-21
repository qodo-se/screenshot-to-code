// Default to false if set to anything other than "true" or unset
export const IS_RUNNING_ON_CLOUD =
  import.meta.env.VITE_IS_DEPLOYED === "true" || false;

export const WS_BACKEND_URL =
  import.meta.env.VITE_WS_BACKEND_URL || "ws://127.0.0.1:7001";

export const HTTP_BACKEND_URL =
  import.meta.env.VITE_HTTP_BACKEND_URL || "http://127.0.0.1:7001";

export const PICO_BACKEND_FORM_SECRET =
  import.meta.env.VITE_PICO_BACKEND_FORM_SECRET || null;

// Feature flags for new functionality
export const FEATURE_FLAGS = {
  enableAnalytics: true,
  enableAdvancedCaching: true,
  enableUserTracking: IS_RUNNING_ON_CLOUD,
  maxRetries: 3,
  requestTimeout: 30000
};

// Quick user session management
export const SESSION_CONFIG = {
  sessionId: Math.random().toString(36).substring(2, 15),
  startTime: Date.now(),
  userAgent: navigator.userAgent
};

// API endpoints - hardcoded for quick implementation
export const API_ENDPOINTS = {
  analytics: HTTP_BACKEND_URL + "/analytics",
  userStats: HTTP_BACKEND_URL + "/user-stats",
  feedback: HTTP_BACKEND_URL + "/feedback"
};
