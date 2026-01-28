'use client';

import { useState, useEffect } from 'react';

export function CookieConsent() {
    const [show, setShow] = useState(false);
    const [showPreferences, setShowPreferences] = useState(false);
    const [preferences, setPreferences] = useState({
        necessary: true, // Always true, can't be disabled
        analytics: true,
        marketing: false,
    });

    useEffect(() => {
        // Check if user has already consented
        const consent = localStorage.getItem('cookie_consent');
        if (!consent) {
            // Show banner after a short delay for better UX
            setTimeout(() => setShow(true), 1000);
        }
    }, []);

    const handleAcceptAll = () => {
        const allPrefs = { necessary: true, analytics: true, marketing: true };
        localStorage.setItem('cookie_consent', JSON.stringify(allPrefs));
        localStorage.setItem('cookie_consent_date', new Date().toISOString());
        setShow(false);
    };

    const handleRejectNonEssential = () => {
        const minPrefs = { necessary: true, analytics: false, marketing: false };
        localStorage.setItem('cookie_consent', JSON.stringify(minPrefs));
        localStorage.setItem('cookie_consent_date', new Date().toISOString());
        setShow(false);
    };

    const handleSavePreferences = () => {
        localStorage.setItem('cookie_consent', JSON.stringify(preferences));
        localStorage.setItem('cookie_consent_date', new Date().toISOString());
        setShowPreferences(false);
        setShow(false);
    };

    if (!show) return null;

    return (
        <>
            {/* Cookie banner */}
            <div
                role="dialog"
                aria-modal="true"
                aria-labelledby="cookie-consent-title"
                className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-gray-200 shadow-2xl p-6 md:p-8"
            >
                <div className="max-w-6xl mx-auto">
                    <div className="flex flex-col md:flex-row md:items-center gap-4 md:gap-8">
                        <div className="flex-1">
                            <h2 id="cookie-consent-title" className="text-lg font-semibold text-gray-900 mb-2">
                                🍪 We use cookies
                            </h2>
                            <p className="text-sm text-gray-600">
                                We use cookies to improve your experience, analyze site traffic, and personalize content.
                                By clicking "Accept All", you consent to our use of cookies. Read our{' '}
                                <a href="/privacy" className="text-blue-600 hover:underline">Privacy Policy</a>{' '}
                                for more information.
                            </p>
                        </div>
                        <div className="flex flex-col sm:flex-row gap-3">
                            <button
                                onClick={() => setShowPreferences(true)}
                                className="px-5 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:ring-2 focus:ring-blue-500"
                            >
                                Customize
                            </button>
                            <button
                                onClick={handleRejectNonEssential}
                                className="px-5 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:ring-2 focus:ring-blue-500"
                            >
                                Reject Non-Essential
                            </button>
                            <button
                                onClick={handleAcceptAll}
                                className="px-5 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500"
                            >
                                Accept All
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Preferences modal */}
            {showPreferences && (
                <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-2xl max-w-lg w-full p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-4">Cookie Preferences</h2>
                        <p className="text-sm text-gray-600 mb-6">
                            Manage your cookie preferences below. Required cookies cannot be disabled.
                        </p>

                        <div className="space-y-4 mb-6">
                            {/* Necessary cookies */}
                            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                                <div>
                                    <p className="font-medium text-gray-900">Necessary Cookies</p>
                                    <p className="text-sm text-gray-500">Required for the website to function</p>
                                </div>
                                <input
                                    type="checkbox"
                                    checked={true}
                                    disabled
                                    className="w-5 h-5 rounded"
                                    aria-label="Necessary cookies (required)"
                                />
                            </div>

                            {/* Analytics cookies */}
                            <div className="flex items-center justify-between p-4 border rounded-lg">
                                <div>
                                    <p className="font-medium text-gray-900">Analytics Cookies</p>
                                    <p className="text-sm text-gray-500">Help us understand how you use our site</p>
                                </div>
                                <input
                                    type="checkbox"
                                    checked={preferences.analytics}
                                    onChange={(e) => setPreferences({ ...preferences, analytics: e.target.checked })}
                                    className="w-5 h-5 rounded text-blue-600"
                                    aria-label="Analytics cookies"
                                />
                            </div>

                            {/* Marketing cookies */}
                            <div className="flex items-center justify-between p-4 border rounded-lg">
                                <div>
                                    <p className="font-medium text-gray-900">Marketing Cookies</p>
                                    <p className="text-sm text-gray-500">Used to personalize ads and content</p>
                                </div>
                                <input
                                    type="checkbox"
                                    checked={preferences.marketing}
                                    onChange={(e) => setPreferences({ ...preferences, marketing: e.target.checked })}
                                    className="w-5 h-5 rounded text-blue-600"
                                    aria-label="Marketing cookies"
                                />
                            </div>
                        </div>

                        <div className="flex gap-3">
                            <button
                                onClick={() => setShowPreferences(false)}
                                className="flex-1 px-4 py-2.5 text-sm font-medium text-gray-700 border rounded-lg hover:bg-gray-50"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleSavePreferences}
                                className="flex-1 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
                            >
                                Save Preferences
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
