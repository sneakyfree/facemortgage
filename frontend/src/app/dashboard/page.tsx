'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Phone,
  Users,
  Star,
  Clock,
  TrendingUp,
  DollarSign,
  Calendar,
  Video,
  Settings,
  BarChart3,
  Bell,
  ChevronRight,
  Wifi,
  WifiOff,
  Camera,
  CameraOff,
} from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { useProfessionalPresence } from '@/hooks/useProfessionalPresence';
import { apiClient } from '@/lib/api/client';
import type { AnalyticsOverview, ProfessionalStatus } from '@/types';
import { logger } from '@/lib/utils';

interface QuickStats {
  calls_today: number;
  leads_today: number;
  avg_rating: number;
  total_reviews: number;
  avg_pickup_time_seconds: number;
  time_online_today_seconds: number;
}

interface RecentActivity {
  id: string;
  type: 'call' | 'lead' | 'review';
  title: string;
  description: string;
  time: string;
}

export default function DashboardHome() {
  const { user } = useAuthStore();
  const {
    isConnected,
    currentStatus,
    goOnline,
    goOffline,
    setAvailable,
    setAway,
  } = useProfessionalPresence();

  const [stats, setStats] = useState<QuickStats | null>(null);
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [cameraOn, setCameraOn] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  async function fetchDashboardData() {
    try {
      setLoading(true);

      // Fetch overview stats
      const overviewRes = await apiClient.get<AnalyticsOverview>('/analytics/overview');
      if (overviewRes.data) {
        setStats({
          calls_today: overviewRes.data.total_calls,
          leads_today: overviewRes.data.total_leads,
          avg_rating: overviewRes.data.avg_rating,
          total_reviews: overviewRes.data.total_reviews,
          avg_pickup_time_seconds: overviewRes.data.avg_pickup_time_seconds,
          time_online_today_seconds: overviewRes.data.total_time_online_seconds,
        });
      }

      // Fetch recent activity from API
      try {
        const activityRes = await apiClient.get<{ activities: RecentActivity[] }>('/analytics/recent-activity?limit=5');
        if (activityRes.data?.activities) {
          setRecentActivity(activityRes.data.activities.map((a) => ({
            id: a.id,
            type: a.type as 'call' | 'lead' | 'review',
            title: a.title,
            description: a.description,
            time: a.time,
          })));
        }
      } catch {
        // Fallback to empty if API not available yet
        setRecentActivity([]);
      }
    } catch (error) {
      logger.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  }

  function formatDuration(seconds: number): string {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  }

  const statusColor: Record<ProfessionalStatus, string> = {
    online_available: 'bg-green-500',
    online_busy: 'bg-yellow-500',
    in_call: 'bg-red-500',
    away: 'bg-gray-400',
    offline: 'bg-gray-300',
  };

  const statusLabel: Record<ProfessionalStatus, string> = {
    online_available: 'Online - Available',
    online_busy: 'Online - Busy',
    in_call: 'In Call',
    away: 'Away',
    offline: 'Offline',
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Status Bar */}
      <div className="bg-white border-b px-8 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${statusColor[currentStatus]}`} />
              <span className="font-medium text-gray-900">
                {statusLabel[currentStatus]}
              </span>
            </div>

            {isConnected ? (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setAway()}
                  className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition"
                >
                  Set Away
                </button>
                <button
                  onClick={goOffline}
                  className="px-3 py-1.5 text-sm bg-red-100 text-red-700 hover:bg-red-200 rounded-lg transition"
                >
                  Go Offline
                </button>
              </div>
            ) : (
              <button
                onClick={goOnline}
                className="px-4 py-1.5 text-sm bg-green-600 text-white hover:bg-green-700 rounded-lg transition flex items-center gap-2"
              >
                <Wifi className="w-4 h-4" />
                Go Online
              </button>
            )}
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={() => setCameraOn(!cameraOn)}
              className={`p-2 rounded-lg transition ${
                cameraOn ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-500'
              }`}
              title={cameraOn ? 'Camera On' : 'Camera Off'}
            >
              {cameraOn ? <Camera className="w-5 h-5" /> : <CameraOff className="w-5 h-5" />}
            </button>
            <Link
              href="/dashboard/settings"
              className="p-2 rounded-lg bg-gray-100 hover:bg-gray-200 transition"
            >
              <Settings className="w-5 h-5 text-gray-600" />
            </Link>
          </div>
        </div>
      </div>

      {/* Header */}
      <div className="bg-white border-b px-8 py-6">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome back, {user?.first_name}!
          </h1>
          <p className="text-gray-500 mt-1">
            Here&apos;s what&apos;s happening with your profile today.
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-8 py-6 space-y-6">
        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            icon={<Phone className="w-6 h-6 text-blue-600" />}
            label="Calls Today"
            value={loading ? '-' : String(stats?.calls_today ?? 0)}
            bgColor="bg-blue-50"
          />
          <StatCard
            icon={<Users className="w-6 h-6 text-green-600" />}
            label="New Leads"
            value={loading ? '-' : String(stats?.leads_today ?? 0)}
            bgColor="bg-green-50"
          />
          <StatCard
            icon={<Star className="w-6 h-6 text-amber-600" />}
            label="Rating"
            value={loading ? '-' : `${(stats?.avg_rating ?? 0).toFixed(1)}`}
            subValue={`${stats?.total_reviews ?? 0} reviews`}
            bgColor="bg-amber-50"
          />
          <StatCard
            icon={<Clock className="w-6 h-6 text-purple-600" />}
            label="Avg Pickup Time"
            value={loading ? '-' : formatDuration(stats?.avg_pickup_time_seconds ?? 0)}
            bgColor="bg-purple-50"
          />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Activity */}
          <div className="lg:col-span-2 bg-white rounded-xl border p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Recent Activity</h2>
              <Link
                href="/dashboard/analytics"
                className="text-sm text-blue-600 hover:underline flex items-center gap-1"
              >
                View all <ChevronRight className="w-4 h-4" />
              </Link>
            </div>

            {recentActivity.length > 0 ? (
              <div className="space-y-4">
                {recentActivity.map((activity) => (
                  <div
                    key={activity.id}
                    className="flex items-start gap-4 p-3 rounded-lg hover:bg-gray-50 transition"
                  >
                    <div
                      className={`p-2 rounded-lg ${
                        activity.type === 'call'
                          ? 'bg-blue-100'
                          : activity.type === 'lead'
                          ? 'bg-green-100'
                          : 'bg-amber-100'
                      }`}
                    >
                      {activity.type === 'call' ? (
                        <Phone className="w-4 h-4 text-blue-600" />
                      ) : activity.type === 'lead' ? (
                        <Users className="w-4 h-4 text-green-600" />
                      ) : (
                        <Star className="w-4 h-4 text-amber-600" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900">{activity.title}</p>
                      <p className="text-sm text-gray-500 truncate">{activity.description}</p>
                    </div>
                    <span className="text-xs text-gray-400 whitespace-nowrap">{activity.time}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Bell className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p>No recent activity</p>
                <p className="text-sm">Go online to start receiving calls!</p>
              </div>
            )}
          </div>

          {/* Quick Actions */}
          <div className="space-y-6">
            <div className="bg-white rounded-xl border p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
              <div className="space-y-3">
                <Link
                  href="/dashboard/leads"
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition"
                >
                  <div className="p-2 bg-green-100 rounded-lg">
                    <Users className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Manage Leads</p>
                    <p className="text-sm text-gray-500">View and update your leads</p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-400 ml-auto" />
                </Link>

                <Link
                  href="/dashboard/analytics"
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition"
                >
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <BarChart3 className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">View Analytics</p>
                    <p className="text-sm text-gray-500">Track your performance</p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-400 ml-auto" />
                </Link>

                <Link
                  href="/dashboard/billing"
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition"
                >
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <DollarSign className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Billing & Bids</p>
                    <p className="text-sm text-gray-500">Manage subscription & bids</p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-400 ml-auto" />
                </Link>

                <Link
                  href="/dashboard/settings"
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition"
                >
                  <div className="p-2 bg-gray-100 rounded-lg">
                    <Settings className="w-5 h-5 text-gray-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Settings</p>
                    <p className="text-sm text-gray-500">Update profile & preferences</p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-400 ml-auto" />
                </Link>
              </div>
            </div>

            {/* Time Online Today */}
            <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl p-6 text-white">
              <div className="flex items-center gap-3 mb-4">
                <Clock className="w-6 h-6" />
                <h3 className="font-semibold">Time Online Today</h3>
              </div>
              <p className="text-4xl font-bold">
                {loading ? '-' : formatDuration(stats?.time_online_today_seconds ?? 0)}
              </p>
              <p className="text-blue-200 text-sm mt-2">
                Keep your camera on to appear in the grid!
              </p>
            </div>
          </div>
        </div>

        {/* Tips Section */}
        <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-xl p-6">
          <div className="flex items-start gap-4">
            <div className="p-2 bg-amber-100 rounded-lg">
              <TrendingUp className="w-6 h-6 text-amber-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Pro Tip</h3>
              <p className="text-gray-600 mt-1">
                Professionals who respond within 10 seconds have 3x higher conversion rates.
                Keep your notifications on and stay ready!
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  subValue,
  bgColor,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  subValue?: string;
  bgColor: string;
}) {
  return (
    <div className="bg-white rounded-xl border p-6">
      <div className={`w-12 h-12 ${bgColor} rounded-lg flex items-center justify-center mb-4`}>
        {icon}
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-sm font-medium text-gray-600 mt-1">{label}</p>
      {subValue && <p className="text-xs text-gray-400 mt-1">{subValue}</p>}
    </div>
  );
}
