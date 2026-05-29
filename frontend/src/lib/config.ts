/**
 * Frontend configuration
 *
 * Centralizes all environment-based configuration.
 * In production, ensure NEXT_PUBLIC_API_URL and NEXT_PUBLIC_WS_URL are set.
 */

function getEnvVar(name: string, fallback: string): string {
  if (typeof window !== 'undefined') {
    // Client-side: use window.__ENV__ if available (for runtime config)
    const windowEnv = (window as unknown as { __ENV__?: Record<string, string> }).__ENV__;
    if (windowEnv?.[name]) {
      return windowEnv[name];
    }
  }

  // Use Next.js public env vars
  const value = process.env[name];
  if (value) {
    return value;
  }

  // Development fallback only
  if (process.env.NODE_ENV !== 'production') {
    return fallback;
  }

  // In production, warn if using fallback
  console.warn(`Environment variable ${name} is not set, using fallback: ${fallback}`);
  return fallback;
}

// Derive WebSocket URL from API URL if not explicitly set
function deriveWsUrl(apiUrl: string): string {
  try {
    const url = new URL(apiUrl);
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    return url.origin;
  } catch {
    // Fallback for relative URLs or invalid URLs
    return apiUrl.replace(/^http/, 'ws');
  }
}

// API Configuration
export const API_BASE_URL = getEnvVar(
  'NEXT_PUBLIC_API_URL',
  'http://localhost:8000'
);

// WebSocket Configuration
export const WS_BASE_URL = getEnvVar(
  'NEXT_PUBLIC_WS_URL',
  deriveWsUrl(API_BASE_URL)
);

// API Version prefix
export const API_V1_PREFIX = '/api/v1';

// Full API URL with version
export const API_URL = `${API_BASE_URL}${API_V1_PREFIX}`;

// Environment
export const isDevelopment = process.env.NODE_ENV === 'development';
export const isProduction = process.env.NODE_ENV === 'production';
export const isTest = process.env.NODE_ENV === 'test';

// Feature flags (can be extended)
export const config = {
  api: {
    baseUrl: API_BASE_URL,
    url: API_URL,
    timeout: 30000,
  },
  ws: {
    baseUrl: WS_BASE_URL,
    reconnectAttempts: 5,
    reconnectDelay: 1000,
    heartbeatInterval: 10000,
  },
  // Add other config sections as needed
} as const;

export default config;
