'use client';

import Link from 'next/link';
import { useAuthStore } from '@/stores/authStore';
import Button from '@/components/ui/Button';

export default function Header() {
  const { user, isAuthenticated, logout } = useAuthStore();

  return (
    <>
      {/* Skip to content link for keyboard users */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
      >
        Skip to main content
      </a>
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-2">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-700 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-xl">FM</span>
              </div>
              <span className="text-xl font-bold text-gray-900">FaceMortgage</span>
            </Link>

            {/* Navigation */}
            <nav className="hidden md:flex items-center gap-6">
              <Link href="/" className="text-gray-600 hover:text-gray-900 font-medium">
                Find Professionals
              </Link>
              <Link href="/how-it-works" className="text-gray-600 hover:text-gray-900 font-medium">
                How It Works
              </Link>
              <Link href="/for-professionals" className="text-gray-600 hover:text-gray-900 font-medium">
                For Professionals
              </Link>
            </nav>

            {/* Auth Buttons */}
            <div className="flex items-center gap-4">
              {isAuthenticated && user ? (
                <>
                  <span className="text-gray-600">
                    Hello, <span className="font-medium">{user.first_name}</span>
                  </span>
                  {user.user_type !== 'borrower' && (
                    <Link href="/dashboard">
                      <Button variant="outline" size="sm">
                        Dashboard
                      </Button>
                    </Link>
                  )}
                  <Button variant="ghost" size="sm" onClick={logout}>
                    Logout
                  </Button>
                </>
              ) : (
                <>
                  <Link href="/auth/login">
                    <Button variant="ghost" size="sm">
                      Log In
                    </Button>
                  </Link>
                  <Link href="/auth/register">
                    <Button size="sm">Sign Up</Button>
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </header>
    </>
  );
}
