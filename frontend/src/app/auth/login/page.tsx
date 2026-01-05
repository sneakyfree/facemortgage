'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { apiClient } from '@/lib/api/client';
import { authApi } from '@/lib/api/endpoints';
import { useAuthStore } from '@/stores/authStore';
import type { TokenPair } from '@/types';

// Quick login test accounts
const QUICK_LOGIN_ACCOUNTS = [
  {
    label: 'Super Admin',
    email: 'superadmin@facemortgage.com',
    password: 'superadmin123',
    color: 'bg-purple-600 hover:bg-purple-700',
  },
  {
    label: 'Admin',
    email: 'admin@facemortgage.com',
    password: 'admin123',
    color: 'bg-blue-600 hover:bg-blue-700',
  },
  {
    label: 'User',
    email: 'user@facemortgage.com',
    password: 'user123',
    color: 'bg-green-600 hover:bg-green-700',
  },
  {
    label: 'Sales Rep',
    email: 'sales@facemortgage.com',
    password: 'sales123',
    color: 'bg-orange-600 hover:bg-orange-700',
  },
];

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuthStore();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleQuickLogin = (account: typeof QUICK_LOGIN_ACCOUNTS[0]) => {
    setEmail(account.email);
    setPassword(account.password);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      // Login to get tokens
      const tokenResponse = await apiClient.post<TokenPair>('/auth/login', {
        email,
        password,
      });

      const { access_token, refresh_token } = tokenResponse.data;

      // Store tokens temporarily
      localStorage.setItem('access_token', access_token);
      if (refresh_token) {
        localStorage.setItem('refresh_token', refresh_token);
      }

      // Fetch user profile
      const user = await authApi.getMe();

      // Update auth store
      login(user, access_token, refresh_token);

      // Redirect based on user type
      if (user.user_type === 'borrower') {
        router.push('/');
      } else {
        router.push('/dashboard');
      }
    } catch (err: unknown) {
      console.error('Login error:', err);
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } };
        setError(axiosError.response?.data?.detail || 'Invalid email or password');
      } else {
        setError('An error occurred. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Or{' '}
            <Link
              href="/auth/register"
              className="font-medium text-blue-600 hover:text-blue-500"
            >
              create a new account
            </Link>
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="flex">
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">{error}</h3>
                </div>
              </div>
            </div>
          )}

          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="email" className="sr-only">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Email address"
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Password"
              />
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <input
                id="remember-me"
                name="remember-me"
                type="checkbox"
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900">
                Remember me
              </label>
            </div>

            <div className="text-sm">
              <Link
                href="/auth/forgot-password"
                className="font-medium text-blue-600 hover:text-blue-500"
              >
                Forgot your password?
              </Link>
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <span className="flex items-center">
                  <svg
                    className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Signing in...
                </span>
              ) : (
                'Sign in'
              )}
            </button>
          </div>
        </form>

        {/* Quick Login Buttons */}
        <div className="mt-8 border-t pt-6">
          <p className="text-center text-sm text-gray-500 mb-4">
            Quick Login (Development Only)
          </p>
          <div className="grid grid-cols-2 gap-3">
            {QUICK_LOGIN_ACCOUNTS.map((account) => (
              <button
                key={account.email}
                type="button"
                onClick={() => handleQuickLogin(account)}
                className={`${account.color} text-white text-sm font-medium py-2 px-4 rounded-md transition-colors`}
              >
                {account.label}
              </button>
            ))}
          </div>
          <p className="text-center text-xs text-gray-400 mt-3">
            Click a button to fill credentials, then click &quot;Sign in&quot;
          </p>
        </div>
      </div>
    </div>
  );
}
