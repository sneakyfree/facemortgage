'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api/client';
import { Phone, Check, AlertCircle, MessageSquare, Bell, Clock } from 'lucide-react';

interface SMSPreferences {
    sms_new_leads: boolean;
    sms_missed_calls: boolean;
    sms_scheduled_reminders: boolean;
}

export default function SMSSettingsPage() {
    const [phone, setPhone] = useState('');
    const [verified, setVerified] = useState(false);
    const [verificationCode, setVerificationCode] = useState('');
    const [showVerification, setShowVerification] = useState(false);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [sendingCode, setSendingCode] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [preferences, setPreferences] = useState<SMSPreferences>({
        sms_new_leads: true,
        sms_missed_calls: true,
        sms_scheduled_reminders: true,
    });

    useEffect(() => {
        fetchSettings();
    }, []);

    const fetchSettings = async () => {
        try {
            const { data } = await apiClient.get('/users/me/sms-preferences');
            setPhone(data.phone || '');
            setVerified(data.phone_verified || false);
            if (data.preferences) {
                setPreferences(data.preferences);
            }
        } catch {
            setError('Failed to load SMS settings');
        } finally {
            setLoading(false);
        }
    };

    const formatPhone = (value: string) => {
        const cleaned = value.replace(/\D/g, '');
        if (cleaned.length <= 3) return cleaned;
        if (cleaned.length <= 6) return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3)}`;
        return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6, 10)}`;
    };

    const sendVerificationCode = async () => {
        if (!phone || phone.replace(/\D/g, '').length < 10) {
            setError('Please enter a valid phone number');
            return;
        }

        setSendingCode(true);
        setError(null);
        try {
            await apiClient.post('/users/me/sms/send-verification', {
                phone: phone.replace(/\D/g, '')
            });
            setShowVerification(true);
            setSuccess('Verification code sent!');
            setTimeout(() => setSuccess(null), 3000);
        } catch {
            setError('Failed to send verification code. Please try again.');
        } finally {
            setSendingCode(false);
        }
    };

    const verifyCode = async () => {
        if (!verificationCode || verificationCode.length !== 6) {
            setError('Please enter the 6-digit code');
            return;
        }

        setSaving(true);
        setError(null);
        try {
            await apiClient.post('/users/me/sms/verify', { code: verificationCode });
            setVerified(true);
            setShowVerification(false);
            setVerificationCode('');
            setSuccess('Phone number verified!');
            setTimeout(() => setSuccess(null), 3000);
        } catch {
            setError('Invalid verification code. Please try again.');
        } finally {
            setSaving(false);
        }
    };

    const savePreferences = async () => {
        setSaving(true);
        setError(null);
        try {
            await apiClient.put('/users/me/sms-preferences', { preferences });
            setSuccess('Preferences saved!');
            setTimeout(() => setSuccess(null), 3000);
        } catch {
            setError('Failed to save preferences');
        } finally {
            setSaving(false);
        }
    };

    const togglePreference = (key: keyof SMSPreferences) => {
        setPreferences(prev => ({ ...prev, [key]: !prev[key] }));
    };

    if (loading) {
        return (
            <div className="p-6 max-w-2xl mx-auto">
                <div className="animate-pulse space-y-6">
                    <div className="h-8 bg-gray-200 rounded w-1/3" />
                    <div className="h-12 bg-gray-200 rounded" />
                    <div className="space-y-4">
                        <div className="h-16 bg-gray-200 rounded" />
                        <div className="h-16 bg-gray-200 rounded" />
                        <div className="h-16 bg-gray-200 rounded" />
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="p-6 max-w-2xl mx-auto">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900">SMS Notifications</h1>
                <p className="mt-1 text-gray-600">
                    Receive important updates via text message
                </p>
            </div>

            {/* Error/Success Messages */}
            {error && (
                <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
                    <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                    <p className="text-red-700">{error}</p>
                    <button
                        onClick={() => setError(null)}
                        className="ml-auto text-red-500 hover:text-red-700"
                    >
                        ×
                    </button>
                </div>
            )}

            {success && (
                <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-3">
                    <Check className="w-5 h-5 text-green-500 flex-shrink-0" />
                    <p className="text-green-700">{success}</p>
                </div>
            )}

            {/* Phone Number Section */}
            <section className="bg-white rounded-xl border p-6 mb-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <Phone className="w-5 h-5" />
                    Phone Number
                </h2>

                <div className="flex flex-col sm:flex-row gap-3">
                    <div className="flex-1 relative">
                        <input
                            type="tel"
                            value={phone}
                            onChange={(e) => setPhone(formatPhone(e.target.value))}
                            placeholder="(555) 555-5555"
                            disabled={verified}
                            className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${verified ? 'bg-gray-50 text-gray-500' : ''
                                }`}
                            aria-label="Phone number"
                        />
                        {verified && (
                            <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 text-green-600">
                                <Check className="w-4 h-4" />
                                <span className="text-sm font-medium">Verified</span>
                            </div>
                        )}
                    </div>

                    {!verified && (
                        <button
                            onClick={sendVerificationCode}
                            disabled={sendingCode || !phone}
                            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                        >
                            {sendingCode ? 'Sending...' : 'Verify'}
                        </button>
                    )}

                    {verified && (
                        <button
                            onClick={() => {
                                setVerified(false);
                                setPhone('');
                            }}
                            className="px-6 py-3 border rounded-lg hover:bg-gray-50"
                        >
                            Change
                        </button>
                    )}
                </div>

                {/* Verification Code Input */}
                {showVerification && !verified && (
                    <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                        <p className="text-sm text-blue-700 mb-3">
                            Enter the 6-digit code sent to your phone
                        </p>
                        <div className="flex gap-3">
                            <input
                                type="text"
                                value={verificationCode}
                                onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                                placeholder="000000"
                                maxLength={6}
                                className="flex-1 px-4 py-3 border rounded-lg text-center text-2xl tracking-widest font-mono"
                                aria-label="Verification code"
                            />
                            <button
                                onClick={verifyCode}
                                disabled={saving || verificationCode.length !== 6}
                                className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                            >
                                {saving ? 'Verifying...' : 'Confirm'}
                            </button>
                        </div>
                        <button
                            onClick={sendVerificationCode}
                            disabled={sendingCode}
                            className="mt-2 text-sm text-blue-600 hover:underline"
                        >
                            Resend code
                        </button>
                    </div>
                )}
            </section>

            {/* Notification Preferences */}
            <section className="bg-white rounded-xl border p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                    Notification Types
                </h2>

                {!verified && (
                    <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-700">
                        Verify your phone number to enable SMS notifications
                    </div>
                )}

                <div className="space-y-4">
                    {/* New Leads */}
                    <div className={`flex items-center justify-between p-4 rounded-lg border ${!verified ? 'opacity-50' : ''
                        }`}>
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-blue-100 rounded-lg">
                                <MessageSquare className="w-5 h-5 text-blue-600" />
                            </div>
                            <div>
                                <p className="font-medium text-gray-900">New Leads</p>
                                <p className="text-sm text-gray-500">Get notified when you receive a new lead</p>
                            </div>
                        </div>
                        <button
                            onClick={() => togglePreference('sms_new_leads')}
                            disabled={!verified}
                            role="switch"
                            aria-checked={preferences.sms_new_leads}
                            className={`relative w-12 h-6 rounded-full transition-colors ${preferences.sms_new_leads ? 'bg-blue-600' : 'bg-gray-200'
                                }`}
                        >
                            <span className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform ${preferences.sms_new_leads ? 'translate-x-7' : 'translate-x-1'
                                }`} />
                        </button>
                    </div>

                    {/* Missed Calls */}
                    <div className={`flex items-center justify-between p-4 rounded-lg border ${!verified ? 'opacity-50' : ''
                        }`}>
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-red-100 rounded-lg">
                                <Bell className="w-5 h-5 text-red-600" />
                            </div>
                            <div>
                                <p className="font-medium text-gray-900">Missed Calls</p>
                                <p className="text-sm text-gray-500">Alert when you miss a video call</p>
                            </div>
                        </div>
                        <button
                            onClick={() => togglePreference('sms_missed_calls')}
                            disabled={!verified}
                            role="switch"
                            aria-checked={preferences.sms_missed_calls}
                            className={`relative w-12 h-6 rounded-full transition-colors ${preferences.sms_missed_calls ? 'bg-blue-600' : 'bg-gray-200'
                                }`}
                        >
                            <span className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform ${preferences.sms_missed_calls ? 'translate-x-7' : 'translate-x-1'
                                }`} />
                        </button>
                    </div>

                    {/* Scheduled Reminders */}
                    <div className={`flex items-center justify-between p-4 rounded-lg border ${!verified ? 'opacity-50' : ''
                        }`}>
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-purple-100 rounded-lg">
                                <Clock className="w-5 h-5 text-purple-600" />
                            </div>
                            <div>
                                <p className="font-medium text-gray-900">Scheduled Reminders</p>
                                <p className="text-sm text-gray-500">Reminder before scheduled calls</p>
                            </div>
                        </div>
                        <button
                            onClick={() => togglePreference('sms_scheduled_reminders')}
                            disabled={!verified}
                            role="switch"
                            aria-checked={preferences.sms_scheduled_reminders}
                            className={`relative w-12 h-6 rounded-full transition-colors ${preferences.sms_scheduled_reminders ? 'bg-blue-600' : 'bg-gray-200'
                                }`}
                        >
                            <span className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform ${preferences.sms_scheduled_reminders ? 'translate-x-7' : 'translate-x-1'
                                }`} />
                        </button>
                    </div>
                </div>

                {/* Save Button */}
                <button
                    onClick={savePreferences}
                    disabled={saving || !verified}
                    className="mt-6 w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
                >
                    {saving ? 'Saving...' : 'Save Preferences'}
                </button>
            </section>
        </div>
    );
}
