'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api/client';
import { AlertTriangle } from 'lucide-react';

interface UsageData {
    current: number;
    limit: number;
    period_start: string;
    period_end: string;
    unit: string;
}

interface UsageMeterProps {
    className?: string;
}

export default function UsageMeter({ className = '' }: UsageMeterProps) {
    const [usage, setUsage] = useState<UsageData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchUsage();
        // Auto-refresh every 30 seconds
        const interval = setInterval(fetchUsage, 30000);
        return () => clearInterval(interval);
    }, []);

    const fetchUsage = async () => {
        try {
            const { data } = await apiClient.get('/billing/usage');
            setUsage(data);
        } catch {
            // Silently fail - not critical
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className={`animate-pulse ${className}`}>
                <div className="h-4 bg-gray-200 rounded w-24 mb-1" />
                <div className="h-2 bg-gray-200 rounded w-full" />
            </div>
        );
    }

    if (!usage) return null;

    const percentage = Math.min((usage.current / usage.limit) * 100, 100);
    const isWarning = percentage >= 80;
    const isNearLimit = percentage >= 95;

    return (
        <div className={`${className}`}>
            <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-gray-700">
                    Usage This Period
                </span>
                <span className={`text-sm font-medium ${isNearLimit ? 'text-red-600' : isWarning ? 'text-yellow-600' : 'text-gray-600'
                    }`}>
                    {usage.current.toLocaleString()} / {usage.limit.toLocaleString()} {usage.unit}
                </span>
            </div>

            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                    className={`h-full transition-all duration-500 ${isNearLimit ? 'bg-red-500' : isWarning ? 'bg-yellow-500' : 'bg-blue-500'
                        }`}
                    style={{ width: `${percentage}%` }}
                />
            </div>

            {isWarning && (
                <div className={`flex items-center gap-1 mt-2 text-xs ${isNearLimit ? 'text-red-600' : 'text-yellow-600'
                    }`}>
                    <AlertTriangle className="w-3 h-3" />
                    {isNearLimit
                        ? 'You are near your usage limit'
                        : 'You have used 80% of your limit'
                    }
                </div>
            )}

            <p className="text-xs text-gray-400 mt-1">
                Resets {new Date(usage.period_end).toLocaleDateString()}
            </p>
        </div>
    );
}
