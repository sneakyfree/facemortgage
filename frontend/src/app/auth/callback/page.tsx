'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api/client';
import { authApi } from '@/lib/api/endpoints';
import { useAuthStore } from '@/stores/authStore';

function OAuthCallbackContent() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const { login } = useAuthStore();
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const handleCallback = async () => {
            const code = searchParams.get('code');
            const state = searchParams.get('state');
            const errorParam = searchParams.get('error');

            if (errorParam) {
                setError(`OAuth error: ${errorParam}`);
                setIsLoading(false);
                return;
            }

            if (!code) {
                setError('No authorization code received');
                setIsLoading(false);
                return;
            }

            try {
                // Exchange code for tokens
                await apiClient.post('/oauth/google', {
                    code,
                    redirect_uri: `${window.location.origin}/auth/callback`,
                    user_type: 'borrower', // Default for new users
                });

                // Fetch user profile
                const user = await authApi.getMe();
                login(user);

                // Redirect based on user type
                if (user.user_type === 'borrower') {
                    router.push('/');
                } else {
                    router.push('/dashboard');
                }
            } catch (err: unknown) {
                console.error('OAuth callback error:', err);
                if (err && typeof err === 'object' && 'response' in err) {
                    const axiosError = err as { response?: { data?: { detail?: string } } };
                    setError(axiosError.response?.data?.detail || 'Authentication failed');
                } else {
                    setError('Authentication failed. Please try again.');
                }
                setIsLoading(false);
            }
        };

        handleCallback();
    }, [searchParams, router, login]);

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Completing sign in...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4">
                <div className="max-w-md w-full space-y-8 text-center">
                    <div className="rounded-full bg-red-100 p-3 mx-auto w-16 h-16 flex items-center justify-center">
                        <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </div>
                    <h2 className="text-2xl font-bold text-gray-900">Sign In Failed</h2>
                    <p className="text-gray-600">{error}</p>
                    <a
                        href="/auth/login"
                        className="inline-block w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                    >
                        Back to Login
                    </a>
                </div>
            </div>
        );
    }

    return null;
}

function LoadingFallback() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
            <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">Loading...</p>
            </div>
        </div>
    );
}

export default function OAuthCallbackPage() {
    return (
        <Suspense fallback={<LoadingFallback />}>
            <OAuthCallbackContent />
        </Suspense>
    );
}
