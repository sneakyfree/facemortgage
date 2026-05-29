import axios from 'axios';
import { API_BASE_URL, API_V1_PREFIX, config } from '@/lib/config';

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}${API_V1_PREFIX}`,
  timeout: config.api.timeout,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Enable httpOnly cookie handling
});

// Helper to extract CSRF token from cookies
function getCsrfToken(): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie
    .split('; ')
    .find((row) => row.startsWith('csrf_token='));
  return match ? match.split('=')[1] : null;
}

// Request interceptor to add CSRF token to state-changing requests
apiClient.interceptors.request.use((requestConfig) => {
  const method = requestConfig.method?.toUpperCase();

  // Add CSRF token for state-changing methods
  if (method && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      requestConfig.headers['X-CSRF-Token'] = csrfToken;
    }
  }

  return requestConfig;
});

// Response interceptor for error handling and automatic token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and not already retrying, try to refresh token via cookie
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Refresh endpoint reads refresh_token from httpOnly cookie automatically
        const refreshCsrf = getCsrfToken();
        await axios.post(
          `${API_BASE_URL}${API_V1_PREFIX}/auth/refresh`,
          {},
          {
            withCredentials: true,
            headers: refreshCsrf ? { 'X-CSRF-Token': refreshCsrf } : {},
          }
        );

        // Retry original request - new access_token cookie is set automatically
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        // Clear any client-side state
        if (typeof window !== 'undefined') {
          localStorage.removeItem('user_id');
          window.location.href = '/auth/login';
        }
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
