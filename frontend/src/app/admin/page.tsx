'use client';

import { useState, useEffect } from 'react';
import {
  Users,
  UserPlus,
  Phone,
  Clock,
  TrendingUp,
  DollarSign,
  Activity,
  Search,
  ChevronDown,
  MoreVertical,
  Check,
  X,
  Star,
} from 'lucide-react';
import { apiClient } from '@/lib/api/client';
import { logger } from '@/lib/utils';

interface PlatformStats {
  total_users: number;
  total_professionals: number;
  total_borrowers: number;
  new_users_today: number;
  new_users_this_week: number;
  professionals_online: number;
  professionals_in_call: number;
  calls_today: number;
  calls_this_week: number;
  avg_call_duration: number;
  leads_today: number;
  leads_this_week: number;
  conversion_rate: number;
  active_subscriptions: number;
  mrr: number;
}

interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  user_type: string;
  is_active: boolean;
  created_at: string;
}

interface Professional {
  id: string;
  user_id: string;
  name: string;
  email: string;
  company: string | null;
  nmls_id: string | null;
  status: string;
  subscription_tier: string;
  avg_rating: number;
  total_calls: number;
  created_at: string;
}

type Tab = 'overview' | 'users' | 'professionals';

function formatDuration(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${minutes}m ${secs}s`;
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [stats, setStats] = useState<PlatformStats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [professionals, setProfessionals] = useState<Professional[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  async function fetchData() {
    setLoading(true);
    try {
      if (activeTab === 'overview' || !stats) {
        try {
          const statsRes = await apiClient.get('/admin/stats');
          setStats(statsRes.data);
        } catch (err) {
          logger.error('Failed to fetch admin stats:', err);
        }
      }

      if (activeTab === 'users') {
        try {
          const usersRes = await apiClient.get(`/admin/users?page=1&page_size=50${searchQuery ? `&search=${searchQuery}` : ''}`);
          setUsers(usersRes.data.users);
        } catch (err) {
          logger.error('Failed to fetch users:', err);
        }
      }

      if (activeTab === 'professionals') {
        try {
          const prosRes = await apiClient.get(`/admin/professionals?page=1&page_size=50${searchQuery ? `&search=${searchQuery}` : ''}`);
          setProfessionals(prosRes.data.professionals);
        } catch (err) {
          logger.error('Failed to fetch professionals:', err);
        }
      }
    } catch (error) {
      logger.error('Failed to fetch admin data:', error);
    } finally {
      setLoading(false);
    }
  }

  async function toggleUserStatus(userId: string, isActive: boolean) {
    try {
      await apiClient.patch(`/admin/users/${userId}/status`, { is_active: isActive });
      fetchData();
    } catch (error) {
      logger.error('Failed to toggle user status:', error);
    }
  }

  async function toggleFeatured(professionalId: string, isFeatured: boolean) {
    try {
      await fetch(`/api/v1/admin/professionals/${professionalId}/featured`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_featured: isFeatured }),
      });
      fetchData();
    } catch (error) {
      logger.error('Failed to toggle featured:', error);
    }
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
              <p className="text-gray-500">Platform management and analytics</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-sm">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                <span className="text-gray-600">{stats?.professionals_online || 0} online</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-6">
          <nav className="flex gap-8">
            {[
              { id: 'overview', label: 'Overview' },
              { id: 'users', label: 'Users' },
              { id: 'professionals', label: 'Professionals' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as Tab)}
                className={`py-4 border-b-2 font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {activeTab === 'overview' && stats && (
          <div className="space-y-8">
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <StatCard
                icon={<Users className="w-6 h-6 text-blue-600" />}
                label="Total Users"
                value={stats.total_users.toLocaleString()}
                subLabel={`+${stats.new_users_today} today`}
                bgColor="bg-blue-50"
              />
              <StatCard
                icon={<Activity className="w-6 h-6 text-green-600" />}
                label="Professionals Online"
                value={stats.professionals_online.toString()}
                subLabel={`${stats.professionals_in_call} in calls`}
                bgColor="bg-green-50"
              />
              <StatCard
                icon={<Phone className="w-6 h-6 text-purple-600" />}
                label="Calls Today"
                value={stats.calls_today.toString()}
                subLabel={`Avg: ${formatDuration(stats.avg_call_duration)}`}
                bgColor="bg-purple-50"
              />
              <StatCard
                icon={<TrendingUp className="w-6 h-6 text-amber-600" />}
                label="Conversion Rate"
                value={`${stats.conversion_rate}%`}
                subLabel={`${stats.leads_today} leads today`}
                bgColor="bg-amber-50"
              />
            </div>

            {/* User Breakdown */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-xl border p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">User Breakdown</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Professionals</span>
                    <span className="font-semibold">{stats.total_professionals.toLocaleString()}</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-600 rounded-full"
                      style={{ width: `${(stats.total_professionals / stats.total_users) * 100}%` }}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Borrowers</span>
                    <span className="font-semibold">{stats.total_borrowers.toLocaleString()}</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-green-600 rounded-full"
                      style={{ width: `${(stats.total_borrowers / stats.total_users) * 100}%` }}
                    />
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl border p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Weekly Activity</h3>
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <p className="text-3xl font-bold text-gray-900">{stats.new_users_this_week}</p>
                    <p className="text-sm text-gray-500">New users this week</p>
                  </div>
                  <div>
                    <p className="text-3xl font-bold text-gray-900">{stats.calls_this_week}</p>
                    <p className="text-sm text-gray-500">Calls this week</p>
                  </div>
                  <div>
                    <p className="text-3xl font-bold text-gray-900">{stats.leads_this_week}</p>
                    <p className="text-sm text-gray-500">Leads this week</p>
                  </div>
                  <div>
                    <p className="text-3xl font-bold text-gray-900">{stats.active_subscriptions}</p>
                    <p className="text-sm text-gray-500">Active subscriptions</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'users' && (
          <div className="bg-white rounded-xl border">
            <div className="p-4 border-b flex items-center gap-4">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search users..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && fetchData()}
                  className="w-full pl-10 pr-4 py-2 border rounded-lg"
                />
              </div>
            </div>

            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">User</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Type</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Joined</th>
                  <th className="px-6 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <p className="font-medium text-gray-900">{user.first_name} {user.last_name}</p>
                        <p className="text-sm text-gray-500">{user.email}</p>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-sm capitalize">
                        {user.user_type.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {user.is_active ? (
                        <span className="flex items-center gap-1 text-green-600">
                          <Check className="w-4 h-4" /> Active
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-red-600">
                          <X className="w-4 h-4" /> Inactive
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {formatDate(user.created_at)}
                    </td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => toggleUserStatus(user.id, !user.is_active)}
                        className={`px-3 py-1 rounded text-sm ${
                          user.is_active
                            ? 'bg-red-50 text-red-600 hover:bg-red-100'
                            : 'bg-green-50 text-green-600 hover:bg-green-100'
                        }`}
                      >
                        {user.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'professionals' && (
          <div className="bg-white rounded-xl border">
            <div className="p-4 border-b flex items-center gap-4">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search professionals..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && fetchData()}
                  className="w-full pl-10 pr-4 py-2 border rounded-lg"
                />
              </div>
            </div>

            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Professional</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Tier</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Rating</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Calls</th>
                  <th className="px-6 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {professionals.map((pro) => (
                  <tr key={pro.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <p className="font-medium text-gray-900">{pro.name}</p>
                        <p className="text-sm text-gray-500">{pro.company || pro.email}</p>
                        {pro.nmls_id && (
                          <p className="text-xs text-gray-400">NMLS# {pro.nmls_id}</p>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded text-xs font-medium capitalize ${
                        pro.status === 'online_available' ? 'bg-green-100 text-green-700' :
                        pro.status === 'in_call' ? 'bg-blue-100 text-blue-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {pro.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded text-xs font-medium capitalize ${
                        pro.subscription_tier === 'premium' ? 'bg-purple-100 text-purple-700' :
                        pro.subscription_tier === 'professional' ? 'bg-blue-100 text-blue-700' :
                        pro.subscription_tier === 'basic' ? 'bg-green-100 text-green-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {pro.subscription_tier}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-1">
                        <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
                        <span>{pro.avg_rating.toFixed(1)}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {pro.total_calls}
                    </td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => toggleFeatured(pro.id, true)}
                        className="px-3 py-1 bg-amber-50 text-amber-600 hover:bg-amber-100 rounded text-sm"
                      >
                        Feature
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  subLabel,
  bgColor,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  subLabel: string;
  bgColor: string;
}) {
  return (
    <div className="bg-white rounded-xl border p-6">
      <div className={`inline-flex p-3 rounded-lg ${bgColor} mb-4`}>{icon}</div>
      <p className="text-3xl font-bold text-gray-900">{value}</p>
      <p className="text-sm font-medium text-gray-600 mt-1">{label}</p>
      <p className="text-xs text-gray-400 mt-1">{subLabel}</p>
    </div>
  );
}
