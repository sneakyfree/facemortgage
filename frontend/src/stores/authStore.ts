import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@/types';
import { apiClient } from '@/lib/api/client';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  setUser: (user: User | null) => void;
  setLoading: (loading: boolean) => void;
  login: (user: User) => void;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: true,

      setUser: (user) => {
        // Store user_id for WebSocket connections (non-sensitive)
        if (typeof window !== 'undefined') {
          if (user?.id) {
            localStorage.setItem('user_id', user.id);
          } else {
            localStorage.removeItem('user_id');
          }
        }
        set({
          user,
          isAuthenticated: !!user,
          isLoading: false,
        });
      },

      setLoading: (isLoading) => set({ isLoading }),

      login: (user) => {
        // Tokens are stored in httpOnly cookies by the server
        // We only store user info in state
        if (typeof window !== 'undefined' && user.id) {
          localStorage.setItem('user_id', user.id);
        }
        set({
          user,
          isAuthenticated: true,
          isLoading: false,
        });
      },

      logout: async () => {
        try {
          // Call logout endpoint to clear httpOnly cookies on the server
          await apiClient.post('/auth/logout');
        } catch {
          // Ignore errors - cookies might already be expired
        }

        if (typeof window !== 'undefined') {
          localStorage.removeItem('user_id');
        }
        set({
          user: null,
          isAuthenticated: false,
          isLoading: false,
        });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);
