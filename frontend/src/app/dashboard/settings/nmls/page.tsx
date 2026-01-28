'use client';

import { useState } from 'react';
import { apiClient } from '@/lib/api/client';

interface NMLSVerification {
    nmls_id: string;
    status: 'verified' | 'pending' | 'failed' | 'expired';
    verified_at?: string;
    expires_at?: string;
    full_name?: string;
    licenses: {
        state: string;
        status: 'active' | 'inactive' | 'pending';
        expiry?: string;
    }[];
    error?: string;
}

export function NMLSVerificationPanel({ userId }: { userId: string }) {
    const [nmlsId, setNmlsId] = useState('');
    const [loading, setLoading] = useState(false);
    const [verification, setVerification] = useState<NMLSVerification | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleVerify = async () => {
        if (!nmlsId || nmlsId.length < 5) {
            setError('Please enter a valid NMLS ID');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const response = await apiClient.post('/api/v1/nmls/verify', {
                nmls_id: nmlsId,
                user_id: userId,
            });
            setVerification(response.data);
        } catch (err: unknown) {
            console.error('NMLS verification failed:', err);
            setError('Verification failed. Please check the NMLS ID and try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleAutoRefresh = async () => {
        if (!verification) return;

        setLoading(true);
        try {
            const response = await apiClient.post('/api/v1/nmls/refresh', {
                nmls_id: verification.nmls_id,
                user_id: userId,
            });
            setVerification(response.data);
        } catch (err) {
            console.error('NMLS refresh failed:', err);
            setError('Refresh failed. Please try again later.');
        } finally {
            setLoading(false);
        }
    };

    const statusColors = {
        verified: 'bg-green-100 text-green-800 border-green-500',
        pending: 'bg-yellow-100 text-yellow-800 border-yellow-500',
        failed: 'bg-red-100 text-red-800 border-red-500',
        expired: 'bg-orange-100 text-orange-800 border-orange-500',
    };

    const licenseStatusColors = {
        active: 'bg-green-100 text-green-700',
        inactive: 'bg-gray-100 text-gray-600',
        pending: 'bg-yellow-100 text-yellow-700',
    };

    return (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-4">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <span>🏛️</span> NMLS Verification
                </h2>
                <p className="text-blue-100 text-sm">
                    Verify your NMLS credentials for trust badges
                </p>
            </div>

            <div className="p-6 space-y-6">
                {/* Verification Form */}
                {!verification ? (
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                NMLS ID
                            </label>
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    value={nmlsId}
                                    onChange={(e) => setNmlsId(e.target.value.replace(/\D/g, ''))}
                                    placeholder="Enter your NMLS ID"
                                    className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    maxLength={12}
                                />
                                <button
                                    onClick={handleVerify}
                                    disabled={loading || !nmlsId}
                                    className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                                >
                                    {loading ? (
                                        <>
                                            <span className="animate-spin">⏳</span>
                                            Verifying...
                                        </>
                                    ) : (
                                        <>
                                            <span>✓</span>
                                            Verify
                                        </>
                                    )}
                                </button>
                            </div>
                            <p className="text-xs text-gray-500 mt-1">
                                Find your NMLS ID at{' '}
                                <a
                                    href="https://www.nmlsconsumeraccess.org"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-blue-600 hover:underline"
                                >
                                    nmlsconsumeraccess.org
                                </a>
                            </p>
                        </div>

                        {error && (
                            <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg">
                                {error}
                            </div>
                        )}
                    </div>
                ) : (
                    /* Verification Status */
                    <div className="space-y-4">
                        <div className={`border-l-4 ${statusColors[verification.status]} p-4 rounded-r-lg`}>
                            <div className="flex justify-between items-start">
                                <div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-xl">
                                            {verification.status === 'verified' ? '✅' :
                                                verification.status === 'pending' ? '⏳' :
                                                    verification.status === 'expired' ? '⚠️' : '❌'}
                                        </span>
                                        <span className="font-bold text-lg">
                                            NMLS #{verification.nmls_id}
                                        </span>
                                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${verification.status === 'verified' ? 'bg-green-200' :
                                                verification.status === 'pending' ? 'bg-yellow-200' :
                                                    'bg-red-200'
                                            }`}>
                                            {verification.status.toUpperCase()}
                                        </span>
                                    </div>
                                    {verification.full_name && (
                                        <p className="text-gray-700 mt-1">{verification.full_name}</p>
                                    )}
                                    {verification.verified_at && (
                                        <p className="text-sm text-gray-500 mt-1">
                                            Verified: {new Date(verification.verified_at).toLocaleDateString()}
                                        </p>
                                    )}
                                </div>
                                <button
                                    onClick={handleAutoRefresh}
                                    disabled={loading}
                                    className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                                >
                                    🔄 Refresh
                                </button>
                            </div>
                        </div>

                        {/* State Licenses */}
                        {verification.licenses && verification.licenses.length > 0 && (
                            <div>
                                <h3 className="font-semibold text-gray-700 mb-2">State Licenses</h3>
                                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                                    {verification.licenses.map((license, idx) => (
                                        <div
                                            key={idx}
                                            className={`px-3 py-2 rounded-lg ${licenseStatusColors[license.status]} flex items-center justify-between`}
                                        >
                                            <span className="font-medium">{license.state}</span>
                                            <span className="text-xs">
                                                {license.status === 'active' ? '✓' :
                                                    license.status === 'pending' ? '⏳' : '✗'}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Verification Badge Preview */}
                        <div className="bg-gray-50 rounded-lg p-4">
                            <h3 className="font-semibold text-gray-700 mb-2">Trust Badge Preview</h3>
                            <div className="flex items-center gap-3 bg-white border border-gray-200 rounded-lg p-3 w-fit">
                                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white text-lg">
                                    🏛️
                                </div>
                                <div>
                                    <div className="font-semibold text-gray-800">NMLS Verified</div>
                                    <div className="text-sm text-gray-500">#{verification.nmls_id}</div>
                                </div>
                                {verification.status === 'verified' && (
                                    <span className="bg-green-500 text-white text-xs px-2 py-1 rounded-full">
                                        ✓ Active
                                    </span>
                                )}
                            </div>
                            <p className="text-xs text-gray-500 mt-2">
                                This badge appears on your profile in the professional grid.
                            </p>
                        </div>

                        {/* Change NMLS */}
                        <button
                            onClick={() => {
                                setVerification(null);
                                setNmlsId('');
                            }}
                            className="text-sm text-blue-600 hover:underline"
                        >
                            Verify a different NMLS ID
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}

export default NMLSVerificationPanel;
