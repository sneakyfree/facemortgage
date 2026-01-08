/**
 * authStore tests.
 *
 * Note: With httpOnly cookie authentication, tokens are no longer stored in
 * localStorage or managed by the frontend. Only user info is stored in state.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import { useAuthStore } from './authStore';
import type { User } from '@/types';

// Mock apiClient
vi.mock('@/lib/api/client', () => ({
  apiClient: {
    post: vi.fn().mockResolvedValue({}),
  },
}));

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
  beforeEach(async () => {
    vi.clearAllMocks();
    mockLocalStorage.clear();

    // Reset store state
    const { result } = renderHook(() => useAuthStore());
    await act(async () => {
      await result.current.logout();
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
    it('sets user and authenticates (tokens handled by httpOnly cookies)', () => {
      const { result } = renderHook(() => useAuthStore());
      const mockUser = createMockUser();

      act(() => {
        result.current.login(mockUser);
      });

      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
    });

    it('stores user_id in localStorage', () => {
      const { result } = renderHook(() => useAuthStore());
      const mockUser = createMockUser({ id: 'login-user-789' });

      act(() => {
        result.current.login(mockUser);
      });

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('user_id', 'login-user-789');
    });

    it('sets loading to false', () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.setLoading(true);
      });

      act(() => {
        result.current.login(createMockUser());
      });

      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('logout', () => {
    it('clears user state', async () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.login(createMockUser());
      });

      expect(result.current.isAuthenticated).toBe(true);

      await act(async () => {
        await result.current.logout();
      });

      expect(result.current.user).toBe(null);
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('removes user_id from localStorage', async () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.login(createMockUser());
      });

      // Clear mock calls from login
      mockLocalStorage.removeItem.mockClear();

      await act(async () => {
        await result.current.logout();
      });

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('user_id');
    });

    it('calls logout endpoint to clear httpOnly cookies', async () => {
      const { apiClient } = await import('@/lib/api/client');
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.login(createMockUser());
      });

      await act(async () => {
        await result.current.logout();
      });

      expect(apiClient.post).toHaveBeenCalledWith('/auth/logout');
    });

    it('sets loading to false', async () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.setLoading(true);
      });

      await act(async () => {
        await result.current.logout();
      });

      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('persistence', () => {
    it('persists user and isAuthenticated', () => {
      const { result } = renderHook(() => useAuthStore());
      const mockUser = createMockUser();

      act(() => {
        result.current.login(mockUser);
      });

      // Check that persist middleware would save these fields
      // The partialize option specifies { user, isAuthenticated }
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
    });
  });

  describe('combined operations', () => {
    it('handles login then logout', async () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.login(createMockUser());
      });

      expect(result.current.isAuthenticated).toBe(true);

      await act(async () => {
        await result.current.logout();
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBe(null);
    });

    it('handles multiple logins', () => {
      const { result } = renderHook(() => useAuthStore());

      const user1 = createMockUser({ id: 'user-1', email: 'user1@test.com' });
      const user2 = createMockUser({ id: 'user-2', email: 'user2@test.com' });

      act(() => {
        result.current.login(user1);
      });

      expect(result.current.user?.email).toBe('user1@test.com');

      act(() => {
        result.current.login(user2);
      });

      expect(result.current.user?.email).toBe('user2@test.com');
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
