'use client';

import { useState, useEffect } from 'react';
import {
  Users,
  Phone,
  TrendingUp,
  Activity,
  Search,
  Check,
  X,
  Star,
  Video,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  MessageSquare,
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

interface ModerationItem {
  id: string;
  professional_id: string;
  video_url: string;
  status: 'pending' | 'approved' | 'rejected';
  reviewed_by: string | null;
  reviewed_at: string | null;
  rejection_reason: string | null;
  created_at: string;
  professional_name: string | null;
  professional_email: string | null;
}

interface ModerationStats {
  pending_count: number;
  approved_today: number;
  rejected_today: number;
  avg_review_time_hours: number;
}

interface DisputeItem {
  id: string;
  user_id: string;
  user_name: string | null;
  user_email: string | null;
  dispute_type: 'billing' | 'service' | 'technical' | 'other';
  subject: string;
  description: string;
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  created_at: string;
  updated_at: string;
}

interface DisputeStats {
  open_count: number;
  in_progress_count: number;
  resolved_today: number;
  avg_resolution_time_hours: number;
}

type Tab = 'overview' | 'users' | 'professionals' | 'moderation' | 'disputes';

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
  const [moderationItems, setModerationItems] = useState<ModerationItem[]>([]);
  const [moderationStats, setModerationStats] = useState<ModerationStats | null>(null);
  const [disputeItems, setDisputeItems] = useState<DisputeItem[]>([]);
  const [disputeStats, setDisputeStats] = useState<DisputeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [selectedItem, setSelectedItem] = useState<ModerationItem | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

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

      if (activeTab === 'moderation') {
        try {
          const [queueRes, modStatsRes] = await Promise.all([
            apiClient.get('/moderation/pending?page=1&page_size=20'),
            apiClient.get('/moderation/stats'),
          ]);
          setModerationItems(queueRes.data.items);
          setModerationStats(modStatsRes.data);
        } catch (err) {
          logger.error('Failed to fetch moderation data:', err);
        }
      }

      if (activeTab === 'disputes') {
        try {
          const [disputesRes, dStatsRes] = await Promise.all([
            apiClient.get('/disputes/admin/all?page=1&page_size=20'),
            apiClient.get('/disputes/admin/stats'),
          ]);
          setDisputeItems(disputesRes.data.items);
          setDisputeStats(dStatsRes.data);
        } catch (err) {
          logger.error('Failed to fetch moderation data:', err);
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

  async function handleApprove(item: ModerationItem) {
    setActionLoading(true);
    try {
      await apiClient.post(`/moderation/${item.id}/approve`);
      setModerationItems(prev => prev.filter(i => i.id !== item.id));
      setModerationStats(prev => prev ? {
        ...prev,
        pending_count: prev.pending_count - 1,
        approved_today: prev.approved_today + 1,
      } : null);
    } catch (error) {
      logger.error('Failed to approve video:', error);
    } finally {
      setActionLoading(false);
    }
  }

  function openRejectModal(item: ModerationItem) {
    setSelectedItem(item);
    setRejectReason('');
    setShowRejectModal(true);
  }

  async function handleReject() {
    if (!selectedItem || rejectReason.length < 10) return;

    setActionLoading(true);
    try {
      await apiClient.post(`/moderation/${selectedItem.id}/reject`, {
        reason: rejectReason,
      });
      setModerationItems(prev => prev.filter(i => i.id !== selectedItem.id));
      setModerationStats(prev => prev ? {
        ...prev,
        pending_count: prev.pending_count - 1,
        rejected_today: prev.rejected_today + 1,
      } : null);
      setShowRejectModal(false);
      setSelectedItem(null);
    } catch (error) {
      logger.error('Failed to reject video:', error);
    } finally {
      setActionLoading(false);
    }
  }

  // Close modal on Escape
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        setShowRejectModal(false);
      }
    }
    if (showRejectModal) {
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [showRejectModal]);

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
              { id: 'moderation', label: 'Video Moderation', badge: moderationStats?.pending_count },
              { id: 'disputes', label: 'Disputes', badge: disputeStats?.open_count },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as Tab)}
                className={`py-4 border-b-2 font-medium transition-colors flex items-center gap-2 ${activeTab === tab.id
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
              >
                {tab.label}
                {tab.badge !== undefined && tab.badge > 0 && (
                  <span className="px-2 py-0.5 text-xs bg-yellow-100 text-yellow-800 rounded-full">
                    {tab.badge}
                  </span>
                )}
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
                        className={`px-3 py-1 rounded text-sm ${user.is_active
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
                      <span className={`px-2 py-1 rounded text-xs font-medium capitalize ${pro.status === 'online_available' ? 'bg-green-100 text-green-700' :
                        pro.status === 'in_call' ? 'bg-blue-100 text-blue-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                        {pro.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded text-xs font-medium capitalize ${pro.subscription_tier === 'premium' ? 'bg-purple-100 text-purple-700' :
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

        {activeTab === 'moderation' && (
          <div className="space-y-6">
            {/* Stats Bar */}
            {moderationStats && (
              <div className="grid grid-cols-4 gap-4">
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="text-3xl font-bold text-yellow-700">{moderationStats.pending_count}</div>
                  <div className="text-sm text-yellow-600">Pending Review</div>
                </div>
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="text-3xl font-bold text-green-700">{moderationStats.approved_today}</div>
                  <div className="text-sm text-green-600">Approved Today</div>
                </div>
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="text-3xl font-bold text-red-700">{moderationStats.rejected_today}</div>
                  <div className="text-sm text-red-600">Rejected Today</div>
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="text-3xl font-bold text-blue-700">{moderationStats.avg_review_time_hours}h</div>
                  <div className="text-sm text-blue-600">Avg Review Time</div>
                </div>
              </div>
            )}

            {/* Loading State */}
            {loading && (
              <div className="flex justify-center items-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" aria-label="Loading"></div>
              </div>
            )}

            {/* Empty State */}
            {!loading && moderationItems.length === 0 && (
              <div className="text-center py-12 bg-white rounded-xl border">
                <CheckCircle className="mx-auto h-12 w-12 text-green-500" />
                <h3 className="mt-2 text-lg font-medium text-gray-900">Queue Empty</h3>
                <p className="mt-1 text-gray-500">All videos have been reviewed. Great work!</p>
              </div>
            )}

            {/* Moderation Queue */}
            {!loading && moderationItems.length > 0 && (
              <div className="space-y-6">
                {moderationItems.map((item) => (
                  <div
                    key={item.id}
                    className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden"
                  >
                    <div className="flex flex-col md:flex-row">
                      {/* Video Player */}
                      <div className="md:w-1/2 bg-black">
                        <video
                          src={item.video_url}
                          controls
                          className="w-full h-64 object-contain"
                          preload="metadata"
                        >
                          Your browser does not support video playback.
                        </video>
                      </div>

                      {/* Info & Actions */}
                      <div className="md:w-1/2 p-6 flex flex-col justify-between">
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">
                            {item.professional_name || 'Unknown Professional'}
                          </h3>
                          <p className="text-sm text-gray-500">{item.professional_email}</p>
                          <p className="text-sm text-gray-400 mt-2 flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            Submitted: {new Date(item.created_at).toLocaleString()}
                          </p>
                          <p className="text-sm text-gray-400">
                            Waiting: {Math.round((Date.now() - new Date(item.created_at).getTime()) / (1000 * 60 * 60))} hours
                          </p>
                        </div>

                        <div className="flex gap-4 mt-4">
                          <button
                            onClick={() => handleApprove(item)}
                            disabled={actionLoading}
                            className="flex-1 bg-green-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                          >
                            <CheckCircle className="w-5 h-5" />
                            {actionLoading ? 'Processing...' : 'Approve'}
                          </button>
                          <button
                            onClick={() => openRejectModal(item)}
                            disabled={actionLoading}
                            className="flex-1 bg-red-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                          >
                            <XCircle className="w-5 h-5" />
                            Reject
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'disputes' && (
          <div className="space-y-6">
            {/* Stats Bar */}
            {disputeStats && (
              <div className="grid grid-cols-4 gap-4">
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                  <div className="text-3xl font-bold text-orange-700">{disputeStats.open_count}</div>
                  <div className="text-sm text-orange-600">Open</div>
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="text-3xl font-bold text-blue-700">{disputeStats.in_progress_count}</div>
                  <div className="text-sm text-blue-600">In Progress</div>
                </div>
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="text-3xl font-bold text-green-700">{disputeStats.resolved_today}</div>
                  <div className="text-sm text-green-600">Resolved Today</div>
                </div>
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                  <div className="text-3xl font-bold text-purple-700">{disputeStats.avg_resolution_time_hours}h</div>
                  <div className="text-sm text-purple-600">Avg Resolution</div>
                </div>
              </div>
            )}

            {/* Disputes Table */}
            <div className="bg-white rounded-xl border">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Subject</th>
                    <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">User</th>
                    <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Type</th>
                    <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Priority</th>
                    <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Created</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {disputeItems.map((dispute) => (
                    <tr key={dispute.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <AlertTriangle className={`w-4 h-4 ${dispute.priority === 'urgent' ? 'text-red-500' :
                              dispute.priority === 'high' ? 'text-orange-500' :
                                'text-gray-400'
                            }`} />
                          <span className="font-medium text-gray-900">{dispute.subject}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div>
                          <p className="text-sm text-gray-900">{dispute.user_name || 'Unknown'}</p>
                          <p className="text-xs text-gray-500">{dispute.user_email}</p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs capitalize">
                          {dispute.dispute_type}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${dispute.status === 'open' ? 'bg-orange-100 text-orange-700' :
                            dispute.status === 'in_progress' ? 'bg-blue-100 text-blue-700' :
                              dispute.status === 'resolved' ? 'bg-green-100 text-green-700' :
                                'bg-gray-100 text-gray-700'
                          }`}>
                          {dispute.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded text-xs font-medium capitalize ${dispute.priority === 'urgent' ? 'bg-red-100 text-red-700' :
                            dispute.priority === 'high' ? 'bg-orange-100 text-orange-700' :
                              dispute.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                                'bg-gray-100 text-gray-700'
                          }`}>
                          {dispute.priority}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {formatDate(dispute.created_at)}
                      </td>
                    </tr>
                  ))}
                  {disputeItems.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                        <MessageSquare className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                        <p>No disputes found</p>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Reject Modal */}
      {showRejectModal && selectedItem && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          role="dialog"
          aria-modal="true"
          aria-labelledby="reject-modal-title"
        >
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h2 id="reject-modal-title" className="text-xl font-bold text-gray-900 mb-4">
              Reject Video
            </h2>
            <p className="text-gray-600 mb-4">
              Please provide a clear reason for rejection. This will be shown to the professional.
            </p>
            <label htmlFor="reject-reason" className="block text-sm font-medium text-gray-700 mb-2">
              Rejection Reason
            </label>
            <textarea
              id="reject-reason"
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-red-500 focus:border-red-500"
              rows={4}
              placeholder="Explain why this video cannot be approved (minimum 10 characters)..."
              minLength={10}
              maxLength={500}
            />
            <p className="text-sm text-gray-500 mt-1">
              {rejectReason.length}/500 characters (minimum 10)
            </p>

            <div className="flex gap-4 mt-6">
              <button
                onClick={() => setShowRejectModal(false)}
                className="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-lg font-medium hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                Cancel
              </button>
              <button
                onClick={handleReject}
                disabled={rejectReason.length < 10 || actionLoading}
                className="flex-1 bg-red-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {actionLoading ? 'Rejecting...' : 'Confirm Rejection'}
              </button>
            </div>
          </div>
        </div>
      )}
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
