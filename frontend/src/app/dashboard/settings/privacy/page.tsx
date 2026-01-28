'use client';

import { useState } from 'react';
import { apiClient } from '@/lib/api/client';

export default function PrivacySettingsPage() {
    const [exporting, setExporting] = useState(false);
    const [exportRequested, setExportRequested] = useState(false);
    const [deleting, setDeleting] = useState(false);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [deleteConfirmText, setDeleteConfirmText] = useState('');

    const handleExportData = async () => {
        setExporting(true);
        try {
            const { data } = await apiClient.post('/users/me/gdpr-export');
            setExportRequested(true);
            // If immediate download is available
            if (data.download_url) {
                window.open(data.download_url, '_blank');
            }
        } catch (err) {
            alert('Failed to request data export. Please try again.');
        } finally {
            setExporting(false);
        }
    };

    const handleDeleteAccount = async () => {
        if (deleteConfirmText !== 'DELETE') {
            alert('Please type DELETE to confirm');
            return;
        }

        setDeleting(true);
        try {
            await apiClient.delete('/users/me');
            // Redirect to goodbye page
            window.location.href = '/goodbye';
        } catch (err) {
            alert('Failed to delete account. Please contact support.');
        } finally {
            setDeleting(false);
        }
    };

    return (
        <div className="p-6 max-w-2xl mx-auto">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900">Privacy & Data</h1>
                <p className="mt-1 text-gray-600">Manage your personal data and privacy settings</p>
            </div>

            {/* Data Export */}
            <section className="bg-white rounded-xl border p-6 mb-6">
                <div className="flex items-start gap-4">
                    <div className="p-3 bg-blue-100 rounded-lg">
                        <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                    </div>
                    <div className="flex-1">
                        <h2 className="text-lg font-semibold text-gray-900">Download Your Data</h2>
                        <p className="text-sm text-gray-600 mt-1 mb-4">
                            Request a copy of all your personal data in a machine-readable format (JSON).
                            This includes your profile, leads, calls, reviews, and activity history.
                        </p>

                        {exportRequested ? (
                            <div className="flex items-center gap-2 text-green-600">
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                                <span className="font-medium">Export requested! Check your email for the download link.</span>
                            </div>
                        ) : (
                            <button
                                onClick={handleExportData}
                                disabled={exporting}
                                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                            >
                                {exporting ? 'Requesting...' : 'Request Data Export'}
                            </button>
                        )}
                    </div>
                </div>
            </section>

            {/* Cookie Preferences */}
            <section className="bg-white rounded-xl border p-6 mb-6">
                <div className="flex items-start gap-4">
                    <div className="p-3 bg-gray-100 rounded-lg">
                        <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                        </svg>
                    </div>
                    <div className="flex-1">
                        <h2 className="text-lg font-semibold text-gray-900">Cookie Preferences</h2>
                        <p className="text-sm text-gray-600 mt-1 mb-4">
                            Manage which cookies you allow. Required cookies cannot be disabled.
                        </p>
                        <button
                            onClick={() => {
                                localStorage.removeItem('cookie_consent');
                                window.location.reload();
                            }}
                            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                        >
                            Manage Cookie Preferences
                        </button>
                    </div>
                </div>
            </section>

            {/* Third-Party Sharing */}
            <section className="bg-white rounded-xl border p-6 mb-6">
                <div className="flex items-start gap-4">
                    <div className="p-3 bg-gray-100 rounded-lg">
                        <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                        </svg>
                    </div>
                    <div className="flex-1">
                        <h2 className="text-lg font-semibold text-gray-900">Data Sharing</h2>
                        <p className="text-sm text-gray-600 mt-1">
                            We do not sell your personal data. Data is only shared with service providers
                            necessary to operate the platform.{' '}
                            <a href="/privacy" className="text-blue-600 hover:underline">
                                Read our Privacy Policy
                            </a>
                        </p>
                    </div>
                </div>
            </section>

            {/* Account Deletion */}
            <section className="bg-white rounded-xl border border-red-200 p-6">
                <div className="flex items-start gap-4">
                    <div className="p-3 bg-red-100 rounded-lg">
                        <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                    </div>
                    <div className="flex-1">
                        <h2 className="text-lg font-semibold text-red-900">Delete Account</h2>
                        <p className="text-sm text-gray-600 mt-1 mb-4">
                            Permanently delete your account and all associated data. This action cannot be undone.
                        </p>

                        {showDeleteConfirm ? (
                            <div className="space-y-4">
                                <div className="p-4 bg-red-50 rounded-lg">
                                    <p className="text-sm text-red-800 font-medium mb-2">
                                        Are you absolutely sure? This will:
                                    </p>
                                    <ul className="text-sm text-red-700 list-disc list-inside space-y-1">
                                        <li>Delete your profile and all personal information</li>
                                        <li>Cancel any active subscriptions</li>
                                        <li>Remove all your leads and call history</li>
                                        <li>Delete all reviews you've received</li>
                                    </ul>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Type DELETE to confirm
                                    </label>
                                    <input
                                        type="text"
                                        value={deleteConfirmText}
                                        onChange={(e) => setDeleteConfirmText(e.target.value)}
                                        className="w-full px-4 py-2 border border-red-300 rounded-lg focus:ring-red-500 focus:border-red-500"
                                        placeholder="DELETE"
                                    />
                                </div>
                                <div className="flex gap-3">
                                    <button
                                        onClick={() => { setShowDeleteConfirm(false); setDeleteConfirmText(''); }}
                                        className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        onClick={handleDeleteAccount}
                                        disabled={deleting || deleteConfirmText !== 'DELETE'}
                                        className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                                    >
                                        {deleting ? 'Deleting...' : 'Delete My Account'}
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <button
                                onClick={() => setShowDeleteConfirm(true)}
                                className="px-4 py-2 text-red-600 border border-red-300 rounded-lg hover:bg-red-50"
                            >
                                Delete My Account
                            </button>
                        )}
                    </div>
                </div>
            </section>
        </div>
    );
}
