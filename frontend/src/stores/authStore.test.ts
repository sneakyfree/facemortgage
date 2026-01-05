/**
 * authStore tests.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { act, renderHook } from '@testing-library/react';
import { useAuthStore } from './authStore';
import type { User } from '@/types';

// Mock localStorage
const mockLocalStorage = {
  store: {} as Record<string, string>,
  getItem: vi.fn((key: string) => mockLocalStorage.store[key] || null),
  setItem: vi.fn((key: string, value: string) => {
    mockLocalStorage.store[key] = value;
  }),
  removeItem: vi.fn((key: string) => {
    delete mockLocalStorage.store[key];
  }),
  clear: vi.fn(() => {
    mockLocalStorage.store = {};
  }),
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
  writable: true,
});

// Helper to create mock user
function createMockUser(overrides: Partial<User> = {}): User {
  return {
    id: 'user-123',
    email: 'test@example.com',
    first_name: 'Test',
    last_name: 'User',
    user_type: 'borrower',
    email_verified: false,
    phone_verified: false,
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('authStore', () => {
  // Reset store and localStorage before each test
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocalStorage.clear();

    // Reset store state
    const { result } = renderHook(() => useAuthStore());
    act(() => {
      result.current.logout();
    });
  });

  describe('initial state', () => {
    it('has null user initially', () => {
      const { result } = renderHook(() => useAuthStore());

      expect(result.current.user).toBe(null);
    });

    it('is not authenticated initially', () => {
      const { result } = renderHook(() => useAuthStore());

      expect(result.current.isAuthenticated).toBe(false);
    });

    it('is not loading after logout', () => {
      const { result } = renderHook(() => useAuthStore());

      // After logout in beforeEach, isLoading should be false
      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('setUser', () => {
    it('sets user and authenticates', () => {
      const { result } = renderHook(() => useAuthStore());
      const mockUser = createMockUser();

      act(() => {
        result.current.setUser(mockUser);
      });

      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
    });

    it('stores user_id in localStorage', () => {
      const { result } = renderHook(() => useAuthStore());
      const mockUser = createMockUser({ id: 'user-456' });

      act(() => {
        result.current.setUser(mockUser);
      });

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('user_id', 'user-456');
    });

    it('removes user_id from localStorage when user is null', () => {
      const { result } = renderHook(() => useAuthStore());

      // First set a user
      act(() => {
        result.current.setUser(createMockUser());
      });

      // Then clear
      act(() => {
        result.current.setUser(null);
      });

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('user_id');
    });

    it('clears authentication when user is null', () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.setUser(createMockUser());
      });

      expect(result.current.isAuthenticated).toBe(true);

      act(() => {
        result.current.setUser(null);
      });

      expect(result.current.isAuthenticated).toBe(false);
    });

    it('sets loading to false', () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.setLoading(true);
      });

      act(() => {
        result.current.setUser(createMockUser());
      });

      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('setLoading', () => {
    it('sets loading to true', () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.setLoading(true);
      });

      expect(result.current.isLoading).toBe(true);
    });

    it('sets loading to false', () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.setLoading(true);
      });

      act(() => {
        result.current.setLoading(false);
      });

      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('login', () => {
    it('sets user and stores tokens', () => {
      const { result } = renderHook(() => useAuthStore());
      const mockUser = createMockUser();

      act(() => {
        result.current.login(mockUser, 'access-token-123', 'refresh-token-456');
      });

      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('access_token', 'access-token-123');
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('refresh_token', 'refresh-token-456');
    });

    it('stores user_id in localStorage', () => {
      const { result } = renderHook(() => useAuthStore());
      const mockUser = createMockUser({ id: 'login-user-789' });

      act(() => {
        result.current.login(mockUser, 'token');
      });

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('user_id', 'login-user-789');
    });

    it('works without refresh token', () => {
      const { result } = renderHook(() => useAuthStore());
      const mockUser = createMockUser();

      act(() => {
        result.current.login(mockUser, 'access-only-token');
      });

      expect(result.current.isAuthenticated).toBe(true);
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('access_token', 'access-only-token');
      // refresh_token should not be set if not provided
      expect(mockLocalStorage.setItem).not.toHaveBeenCalledWith('refresh_token', expect.anything());
    });

    it('sets loading to false', () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.setLoading(true);
      });

      act(() => {
        result.current.login(createMockUser(), 'token');
      });

      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('setTokens', () => {
    it('stores both tokens', () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.setTokens('new-access-token', 'new-refresh-token');
      });

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('access_token', 'new-access-token');
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('refresh_token', 'new-refresh-token');
    });

    it('stores only access token when refresh is not provided', () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.setTokens('access-only');
      });

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('access_token', 'access-only');
    });

    it('does not change user state', () => {
      const { result } = renderHook(() => useAuthStore());
      const mockUser = createMockUser();

      act(() => {
        result.current.setUser(mockUser);
      });

      act(() => {
        result.current.setTokens('new-token');
      });

      // User should remain unchanged
      expect(result.current.user).toEqual(mockUser);
    });
  });

  describe('logout', () => {
    it('clears user state', () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.login(createMockUser(), 'token', 'refresh');
      });

      expect(result.current.isAuthenticated).toBe(true);

      act(() => {
        result.current.logout();
      });

      expect(result.current.user).toBe(null);
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('removes tokens from localStorage', () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.login(createMockUser(), 'token', 'refresh');
      });

      // Clear mock calls from login
      mockLocalStorage.removeItem.mockClear();

      act(() => {
        result.current.logout();
      });

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('access_token');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('refresh_token');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('user_id');
    });

    it('sets loading to false', () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.setLoading(true);
        result.current.logout();
      });

      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('getAccessToken', () => {
    it('returns access token from localStorage', () => {
      const { result } = renderHook(() => useAuthStore());

      mockLocalStorage.store['access_token'] = 'stored-access-token';

      const token = result.current.getAccessToken();

      expect(token).toBe('stored-access-token');
      expect(mockLocalStorage.getItem).toHaveBeenCalledWith('access_token');
    });

    it('returns null when no token exists', () => {
      const { result } = renderHook(() => useAuthStore());

      mockLocalStorage.store = {};

      const token = result.current.getAccessToken();

      expect(token).toBe(null);
    });
  });

  describe('persistence', () => {
    it('persists user and isAuthenticated', () => {
      const { result } = renderHook(() => useAuthStore());
      const mockUser = createMockUser();

      act(() => {
        result.current.login(mockUser, 'token');
      });

      // Check that persist middleware would save these fields
      // The partialize option specifies { user, isAuthenticated }
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
    });
  });

  describe('combined operations', () => {
    it('handles login then logout', () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.login(createMockUser(), 'token', 'refresh');
      });

      expect(result.current.isAuthenticated).toBe(true);

      act(() => {
        result.current.logout();
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBe(null);
    });

    it('handles multiple logins', () => {
      const { result } = renderHook(() => useAuthStore());

      const user1 = createMockUser({ id: 'user-1', email: 'user1@test.com' });
      const user2 = createMockUser({ id: 'user-2', email: 'user2@test.com' });

      act(() => {
        result.current.login(user1, 'token-1');
      });

      expect(result.current.user?.email).toBe('user1@test.com');

      act(() => {
        result.current.login(user2, 'token-2');
      });

      expect(result.current.user?.email).toBe('user2@test.com');
    });

    it('handles token refresh', () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.login(createMockUser(), 'old-token', 'old-refresh');
      });

      act(() => {
        result.current.setTokens('new-token', 'new-refresh');
      });

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('access_token', 'new-token');
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('refresh_token', 'new-refresh');
      // User should still be logged in
      expect(result.current.isAuthenticated).toBe(true);
    });
  });

  describe('user types', () => {
    it('handles borrower user type', () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.setUser(createMockUser({ user_type: 'borrower' }));
      });

      expect(result.current.user?.user_type).toBe('borrower');
    });

    it('handles loan_officer user type', () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.setUser(
          createMockUser({
            user_type: 'loan_officer',
            professional_profile: { id: 'pro-123' },
          })
        );
      });

      expect(result.current.user?.user_type).toBe('loan_officer');
    });

    it('handles realtor user type', () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.setUser(createMockUser({ user_type: 'realtor' }));
      });

      expect(result.current.user?.user_type).toBe('realtor');
    });
  });
});
