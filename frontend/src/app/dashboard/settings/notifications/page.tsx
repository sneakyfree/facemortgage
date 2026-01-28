'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api/client';

interface NotificationPreferences {
    email_enabled: boolean;
    sms_enabled: boolean;
    push_enabled: boolean;

    // Email notifications
    email_new_lead: boolean;
    email_call_missed: boolean;
    email_daily_summary: boolean;
    email_weekly_report: boolean;

    // SMS notifications
    sms_new_lead: boolean;
    sms_call_missed: boolean;
    sms_urgent_only: boolean;

    // Push notifications
    push_new_lead: boolean;
    push_call_incoming: boolean;
    push_borrower_online: boolean;

    // Thresholds
    quiet_hours_start?: string;  // "22:00"
    quiet_hours_end?: string;    // "08:00"
    min_lead_score: number;      // Only notify for leads above this score
}

export default function NotificationsSettingsPage() {
    const [preferences, setPreferences] = useState<NotificationPreferences>({
        email_enabled: true,
        sms_enabled: false,
        push_enabled: true,
        email_new_lead: true,
        email_call_missed: true,
        email_daily_summary: true,
        email_weekly_report: false,
        sms_new_lead: false,
        sms_call_missed: false,
        sms_urgent_only: true,
        push_new_lead: true,
        push_call_incoming: true,
        push_borrower_online: false,
        quiet_hours_start: '22:00',
        quiet_hours_end: '08:00',
        min_lead_score: 5,
    });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);

    useEffect(() => {
        async function fetchPreferences() {
            try {
                const response = await apiClient.get('/api/v1/users/me/notifications');
                setPreferences(response.data);
            } catch (err) {
                console.log('Using default preferences');
            } finally {
                setLoading(false);
            }
        }
        fetchPreferences();
    }, []);

    const handleSave = async () => {
        setSaving(true);
        try {
            await apiClient.put('/api/v1/users/me/notifications', preferences);
            setSaved(true);
            setTimeout(() => setSaved(false), 3000);
        } catch (err) {
            console.error('Failed to save preferences:', err);
        } finally {
            setSaving(false);
        }
    };

    const handleToggle = (key: keyof NotificationPreferences, value: boolean) => {
        setPreferences(prev => ({ ...prev, [key]: value }));
    };

    if (loading) {
        return (
            <div className="p-8 text-center">
                <div className="animate-spin h-8 w-8 border-b-2 border-blue-600 rounded-full mx-auto"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 py-8">
            <div className="max-w-2xl mx-auto px-4">
                <h1 className="text-2xl font-bold text-gray-900 mb-6">
                    🔔 Notification Settings
                </h1>

                <div className="space-y-6">
                    {/* Email Notifications */}
                    <section className="bg-white rounded-lg shadow-sm overflow-hidden">
                        <div className="px-6 py-4 bg-gray-50 border-b flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <span className="text-2xl">📧</span>
                                <h2 className="font-semibold text-gray-800">Email Notifications</h2>
                            </div>
                            <ToggleSwitch
                                checked={preferences.email_enabled}
                                onChange={(v) => handleToggle('email_enabled', v)}
                            />
                        </div>
                        {preferences.email_enabled && (
                            <div className="p-6 space-y-4">
                                <ToggleRow
                                    label="New lead alerts"
                                    description="Instant email when you receive a new lead"
                                    checked={preferences.email_new_lead}
                                    onChange={(v) => handleToggle('email_new_lead', v)}
                                />
                                <ToggleRow
                                    label="Missed call notifications"
                                    description="When a borrower tries to call while you're away"
                                    checked={preferences.email_call_missed}
                                    onChange={(v) => handleToggle('email_call_missed', v)}
                                />
                                <ToggleRow
                                    label="Daily summary"
                                    description="Overview of your leads and calls each day"
                                    checked={preferences.email_daily_summary}
                                    onChange={(v) => handleToggle('email_daily_summary', v)}
                                />
                                <ToggleRow
                                    label="Weekly report"
                                    description="Performance metrics and trends"
                                    checked={preferences.email_weekly_report}
                                    onChange={(v) => handleToggle('email_weekly_report', v)}
                                />
                            </div>
                        )}
                    </section>

                    {/* SMS Notifications */}
                    <section className="bg-white rounded-lg shadow-sm overflow-hidden">
                        <div className="px-6 py-4 bg-gray-50 border-b flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <span className="text-2xl">📱</span>
                                <h2 className="font-semibold text-gray-800">SMS Notifications</h2>
                            </div>
                            <ToggleSwitch
                                checked={preferences.sms_enabled}
                                onChange={(v) => handleToggle('sms_enabled', v)}
                            />
                        </div>
                        {preferences.sms_enabled && (
                            <div className="p-6 space-y-4">
                                <ToggleRow
                                    label="New lead alerts"
                                    description="Text message for new leads"
                                    checked={preferences.sms_new_lead}
                                    onChange={(v) => handleToggle('sms_new_lead', v)}
                                />
                                <ToggleRow
                                    label="Missed call alerts"
                                    description="Text when you miss a borrower call"
                                    checked={preferences.sms_call_missed}
                                    onChange={(v) => handleToggle('sms_call_missed', v)}
                                />
                                <ToggleRow
                                    label="Urgent leads only"
                                    description="Only text for high-intent, hot leads"
                                    checked={preferences.sms_urgent_only}
                                    onChange={(v) => handleToggle('sms_urgent_only', v)}
                                />
                            </div>
                        )}
                    </section>

                    {/* Push Notifications */}
                    <section className="bg-white rounded-lg shadow-sm overflow-hidden">
                        <div className="px-6 py-4 bg-gray-50 border-b flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <span className="text-2xl">🔔</span>
                                <h2 className="font-semibold text-gray-800">Push Notifications</h2>
                            </div>
                            <ToggleSwitch
                                checked={preferences.push_enabled}
                                onChange={(v) => handleToggle('push_enabled', v)}
                            />
                        </div>
                        {preferences.push_enabled && (
                            <div className="p-6 space-y-4">
                                <ToggleRow
                                    label="New lead alerts"
                                    description="Browser push for new leads"
                                    checked={preferences.push_new_lead}
                                    onChange={(v) => handleToggle('push_new_lead', v)}
                                />
                                <ToggleRow
                                    label="Incoming call"
                                    description="Alert when a borrower is calling you"
                                    checked={preferences.push_call_incoming}
                                    onChange={(v) => handleToggle('push_call_incoming', v)}
                                />
                                <ToggleRow
                                    label="Borrower online"
                                    description="When a previous borrower comes back online"
                                    checked={preferences.push_borrower_online}
                                    onChange={(v) => handleToggle('push_borrower_online', v)}
                                />
                            </div>
                        )}
                    </section>

                    {/* Advanced Settings */}
                    <section className="bg-white rounded-lg shadow-sm overflow-hidden">
                        <div className="px-6 py-4 bg-gray-50 border-b flex items-center gap-3">
                            <span className="text-2xl">⚙️</span>
                            <h2 className="font-semibold text-gray-800">Advanced Settings</h2>
                        </div>
                        <div className="p-6 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Quiet Hours
                                </label>
                                <div className="flex items-center gap-3">
                                    <input
                                        type="time"
                                        value={preferences.quiet_hours_start || '22:00'}
                                        onChange={(e) => setPreferences(prev => ({ ...prev, quiet_hours_start: e.target.value }))}
                                        className="border rounded-lg px-3 py-2 text-sm"
                                    />
                                    <span className="text-gray-500">to</span>
                                    <input
                                        type="time"
                                        value={preferences.quiet_hours_end || '08:00'}
                                        onChange={(e) => setPreferences(prev => ({ ...prev, quiet_hours_end: e.target.value }))}
                                        className="border rounded-lg px-3 py-2 text-sm"
                                    />
                                </div>
                                <p className="text-xs text-gray-500 mt-1">
                                    No notifications during these hours
                                </p>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Minimum Lead Score for Alerts
                                </label>
                                <input
                                    type="range"
                                    min="1"
                                    max="10"
                                    value={preferences.min_lead_score}
                                    onChange={(e) => setPreferences(prev => ({ ...prev, min_lead_score: parseInt(e.target.value) }))}
                                    className="w-full"
                                />
                                <div className="flex justify-between text-xs text-gray-500">
                                    <span>All leads</span>
                                    <span className="font-medium text-blue-600">{preferences.min_lead_score}/10+</span>
                                    <span>Hot only</span>
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* Save Button */}
                    <div className="flex justify-end gap-4">
                        {saved && (
                            <span className="text-green-600 flex items-center gap-1">
                                ✓ Saved
                            </span>
                        )}
                        <button
                            onClick={handleSave}
                            disabled={saving}
                            className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
                        >
                            {saving ? 'Saving...' : 'Save Preferences'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

function ToggleSwitch({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
    return (
        <button
            onClick={() => onChange(!checked)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${checked ? 'bg-blue-600' : 'bg-gray-300'
                }`}
        >
            <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${checked ? 'translate-x-6' : 'translate-x-1'
                    }`}
            />
        </button>
    );
}

function ToggleRow({
    label,
    description,
    checked,
    onChange
}: {
    label: string;
    description: string;
    checked: boolean;
    onChange: (v: boolean) => void;
}) {
    return (
        <div className="flex items-center justify-between py-2">
            <div>
                <p className="font-medium text-gray-800">{label}</p>
                <p className="text-sm text-gray-500">{description}</p>
            </div>
            <ToggleSwitch checked={checked} onChange={onChange} />
        </div>
    );
}
