import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Development-only logger that suppresses logs in production.
 * Use this instead of console.log/warn/error for debug messages.
 */
const isDev = process.env.NODE_ENV === 'development';

export const logger = {
  log: (...args: unknown[]) => {
    if (isDev) console.log(...args);
  },
  warn: (...args: unknown[]) => {
    if (isDev) console.warn(...args);
  },
  error: (...args: unknown[]) => {
    // Errors are always logged for debugging production issues
    console.error(...args);
  },
  debug: (...args: unknown[]) => {
    if (isDev) console.log('[DEBUG]', ...args);
  },
};

export function formatRating(rating: number): string {
  return rating.toFixed(1);
}

export function formatPickupTime(seconds?: number): string {
  if (!seconds) return 'N/A';
  if (seconds < 60) return `${Math.round(seconds)}s`;
  return `${Math.round(seconds / 60)}m`;
}

export function getUserTypeLabel(userType: string): string {
  const labels: Record<string, string> = {
    loan_officer: 'Loan Officer',
    realtor: 'Realtor',
    title_rep: 'Title Rep',
    attorney: 'Attorney',
    borrower: 'Borrower',
  };
  return labels[userType] || userType;
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    online_available: 'bg-green-500',
    online_busy: 'bg-yellow-500',
    in_call: 'bg-red-500',
    away: 'bg-gray-400',
    offline: 'bg-gray-300',
  };
  return colors[status] || 'bg-gray-300';
}

export function getInitials(firstName: string, lastName: string): string {
  return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();
}

/**
 * Get or create an anonymous session ID for unauthenticated users.
 * Used for tracking anonymous callers.
 */
export function getAnonymousSessionId(): string {
  if (typeof window === 'undefined') return '';

  const key = 'fm_anonymous_session';
  let sessionId = sessionStorage.getItem(key);

  if (!sessionId) {
    sessionId = `${Date.now()}-${crypto.randomUUID()}`;
    sessionStorage.setItem(key, sessionId);
  }

  return sessionId;
}

/**
 * Generate a simple device fingerprint from browser info.
 * Used for fraud prevention on anonymous calls.
 */
export function getDeviceFingerprint(): string {
  if (typeof window === 'undefined') return '';

  const data = [
    navigator.userAgent,
    navigator.language,
    screen.width,
    screen.height,
    new Date().getTimezoneOffset(),
  ].join('|');

  return btoa(data).slice(0, 64);
}
