import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@/types';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  setUser: (user: User | null) => void;
  setLoading: (loading: boolean) => void;
  login: (user: User, accessToken: string, refreshToken?: string) => void;
  setTokens: (accessToken: string, refreshToken?: string) => void;
  logout: () => void;
  getAccessToken: () => string | null;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: true,

      setUser: (user) => {
        // Also update user_id in localStorage when user is set (e.g., on rehydration)
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

      login: (user, accessToken, refreshToken) => {
        if (typeof window !== 'undefined') {
          localStorage.setItem('access_token', accessToken);
          if (user.id) {
            localStorage.setItem('user_id', user.id);
          }
          if (refreshToken) {
            localStorage.setItem('refresh_token', refreshToken);
          }
        }
        set({
          user,
          isAuthenticated: true,
          isLoading: false,
        });
      },

      setTokens: (accessToken, refreshToken) => {
        if (typeof window !== 'undefined') {
          localStorage.setItem('access_token', accessToken);
          if (refreshToken) {
            localStorage.setItem('refresh_token', refreshToken);
          }
        }
      },

      logout: () => {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user_id');
        }
        set({
          user: null,
          isAuthenticated: false,
          isLoading: false,
        });
      },

      getAccessToken: () => {
        if (typeof window !== 'undefined') {
          return localStorage.getItem('access_token');
        }
        return null;
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);
