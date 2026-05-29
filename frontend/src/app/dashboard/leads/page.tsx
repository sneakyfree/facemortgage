'use client';

import { useState, useEffect } from 'react';
import {
  Users,
  UserPlus,
  TrendingUp,
  DollarSign,
  Calendar,
  Phone,
  Mail,
  Search,
  Filter,
  ChevronDown,
  Plus,
  MoreVertical,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Download,
  Upload,
  Star,
} from 'lucide-react';
import { leadsApi } from '@/lib/api/endpoints';
import { apiClient } from '@/lib/api/client';
import type { LeadStatus as LeadStatusType } from '@/types';
import { logger } from '@/lib/utils';

type LeadStatus = 'new' | 'contacted' | 'qualified' | 'proposal_sent' | 'negotiation' | 'won' | 'lost' | 'nurturing';

interface LeadStats {
  total_leads: number;
  leads_by_status: Record<string, number>;
  new_leads_today: number;
  new_leads_this_week: number;
  new_leads_this_month: number;
  conversion_rate: number;
  total_value_won: number;
  total_value_pipeline: number;
  leads_needing_followup: number;
}

interface Lead {
  id: string;
  lead_status: LeadStatus;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  loan_purpose?: string;
  estimated_loan_amount?: number;
  next_followup_at?: string;
  estimated_value?: number;
  last_activity_at?: string;
  activity_count?: number;
  created_at?: string;
  updated_at?: string;
  lead_score?: number; // 0-100 AI-generated score
  source?: string;
}

const STATUS_CONFIG: Record<LeadStatus, { label: string; color: string; bgColor: string; icon: React.ComponentType<{ className?: string }> }> = {
  new: { label: 'New', color: 'text-blue-700', bgColor: 'bg-blue-100', icon: UserPlus },
  contacted: { label: 'Contacted', color: 'text-purple-700', bgColor: 'bg-purple-100', icon: Phone },
  qualified: { label: 'Qualified', color: 'text-green-700', bgColor: 'bg-green-100', icon: CheckCircle },
  proposal_sent: { label: 'Proposal Sent', color: 'text-amber-700', bgColor: 'bg-amber-100', icon: Mail },
  negotiation: { label: 'Negotiation', color: 'text-orange-700', bgColor: 'bg-orange-100', icon: TrendingUp },
  won: { label: 'Won', color: 'text-emerald-700', bgColor: 'bg-emerald-100', icon: CheckCircle },
  lost: { label: 'Lost', color: 'text-red-700', bgColor: 'bg-red-100', icon: XCircle },
  nurturing: { label: 'Nurturing', color: 'text-gray-700', bgColor: 'bg-gray-100', icon: Clock },
};

function formatCurrency(amount: number): string {
  amount = Number(amount) || 0;
  if (amount >= 1000000) {
    return `$${(amount / 1000000).toFixed(1)}M`;
  }
  if (amount >= 1000) {
    return `$${(amount / 1000).toFixed(0)}K`;
  }
  return `$${amount.toFixed(0)}`;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
}

export default function LeadsDashboard() {
  const [stats, setStats] = useState<LeadStats | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<LeadStatus | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showStatusDropdown, setShowStatusDropdown] = useState(false);

  useEffect(() => {
    fetchData();
  }, [statusFilter, searchQuery]);

  async function fetchData() {
    try {
      setLoading(true);

      // Fetch stats
      try {
        const statsData = await leadsApi.getStats();
        setStats(statsData);
      } catch (err) {
        logger.error('Failed to fetch lead stats:', err);
      }

      // Fetch leads
      const params: {
        status?: LeadStatusType;
        search?: string;
        page?: number;
        page_size?: number;
      } = { page: 1, page_size: 50 };
      if (statusFilter !== 'all') {
        params.status = statusFilter as LeadStatusType;
      }
      if (searchQuery) {
        params.search = searchQuery;
      }

      const leadsData = await leadsApi.list(params);
      if (leadsData) {
        setLeads(leadsData.leads);
      }
    } catch (error) {
      logger.error('Failed to fetch lead data:', error);
    } finally {
      setLoading(false);
    }
  }

  async function updateLeadStatus(leadId: string, newStatus: LeadStatus) {
    try {
      const res = await fetch(`/api/v1/leads/${leadId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lead_status: newStatus }),
      });

      if (res.ok) {
        // Refresh data
        fetchData();
      }
    } catch (error) {
      logger.error('Failed to update lead status:', error);
    }
  }

  if (loading && !stats) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse space-y-6">
            <div className="h-10 bg-gray-200 rounded w-1/4"></div>
            <div className="grid grid-cols-4 gap-6">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-32 bg-gray-200 rounded-xl"></div>
              ))}
            </div>
            <div className="h-96 bg-gray-200 rounded-xl"></div>
          </div>
        </div>
      </div>
    );
  }

  const handleExport = async () => {
    try {
      const response = await apiClient.get('/leads/export', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `leads_export_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      logger.error('Export failed:', err);
      alert('Failed to export leads');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-8 py-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Lead Management</h1>
            <p className="text-gray-500 mt-1">Track and manage your leads</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleExport}
              className="flex items-center gap-2 border px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Download className="w-4 h-4" />
              Export
            </button>
            <a
              href="/dashboard/leads/import"
              className="flex items-center gap-2 border px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Upload className="w-4 h-4" />
              Import
            </a>
            <button className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
              <Plus className="w-5 h-5" />
              Add Lead
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-8 py-6 space-y-6">
        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              icon={<Users className="w-6 h-6 text-blue-600" />}
              label="Total Leads"
              value={stats.total_leads.toString()}
              subLabel={`${stats.new_leads_this_month} this month`}
              bgColor="bg-blue-50"
            />
            <StatCard
              icon={<UserPlus className="w-6 h-6 text-green-600" />}
              label="New Today"
              value={stats.new_leads_today.toString()}
              subLabel={`${stats.new_leads_this_week} this week`}
              bgColor="bg-green-50"
            />
            <StatCard
              icon={<TrendingUp className="w-6 h-6 text-amber-600" />}
              label="Conversion Rate"
              value={`${stats.conversion_rate}%`}
              subLabel="Won / Total"
              bgColor="bg-amber-50"
            />
            <StatCard
              icon={<DollarSign className="w-6 h-6 text-emerald-600" />}
              label="Pipeline Value"
              value={formatCurrency(stats.total_value_pipeline)}
              subLabel={`${formatCurrency(stats.total_value_won)} won`}
              bgColor="bg-emerald-50"
            />
          </div>
        )}

        {/* Followup Alert */}
        {stats && stats.leads_needing_followup > 0 && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-center gap-4">
            <AlertCircle className="w-6 h-6 text-amber-600" />
            <div className="flex-1">
              <p className="font-medium text-amber-800">
                {stats.leads_needing_followup} leads need follow-up
              </p>
              <p className="text-sm text-amber-600">
                Review overdue follow-ups to maintain engagement
              </p>
            </div>
            <button className="text-amber-700 font-medium hover:underline">
              View All
            </button>
          </div>
        )}

        {/* Pipeline Overview */}
        {stats && (
          <div className="bg-white rounded-xl border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Pipeline Overview</h2>
            <div className="flex gap-2 overflow-x-auto pb-2">
              {Object.entries(STATUS_CONFIG).slice(0, -2).map(([status, config]) => {
                const count = stats.leads_by_status[status] || 0;
                const Icon = config.icon;
                return (
                  <button
                    key={status}
                    onClick={() => setStatusFilter(status as LeadStatus)}
                    className={`flex-1 min-w-[120px] p-4 rounded-lg border-2 transition-all ${statusFilter === status
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-transparent hover:border-gray-200'
                      }`}
                  >
                    <div className={`inline-flex p-2 rounded-lg ${config.bgColor} mb-2`}>
                      <Icon className={`w-4 h-4 ${config.color}`} />
                    </div>
                    <p className="text-2xl font-bold text-gray-900">{count}</p>
                    <p className="text-sm text-gray-500">{config.label}</p>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Leads Table */}
        <div className="bg-white rounded-xl border">
          {/* Table Header */}
          <div className="p-4 border-b flex items-center gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search leads..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div className="relative">
              <button
                onClick={() => setShowStatusDropdown(!showStatusDropdown)}
                className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                <Filter className="w-4 h-4" />
                {statusFilter === 'all' ? 'All Status' : STATUS_CONFIG[statusFilter].label}
                <ChevronDown className="w-4 h-4" />
              </button>

              {showStatusDropdown && (
                <div className="absolute top-full mt-2 right-0 bg-white border rounded-lg shadow-lg z-10 min-w-[200px]">
                  <button
                    onClick={() => {
                      setStatusFilter('all');
                      setShowStatusDropdown(false);
                    }}
                    className={`w-full text-left px-4 py-2 hover:bg-gray-50 ${statusFilter === 'all' ? 'bg-blue-50 text-blue-700' : ''
                      }`}
                  >
                    All Status
                  </button>
                  {Object.entries(STATUS_CONFIG).map(([status, config]) => (
                    <button
                      key={status}
                      onClick={() => {
                        setStatusFilter(status as LeadStatus);
                        setShowStatusDropdown(false);
                      }}
                      className={`w-full text-left px-4 py-2 hover:bg-gray-50 flex items-center gap-2 ${statusFilter === status ? 'bg-blue-50 text-blue-700' : ''
                        }`}
                    >
                      <span className={`w-2 h-2 rounded-full ${config.bgColor}`}></span>
                      {config.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Contact
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Loan Purpose
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Est. Amount
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Next Followup
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Score
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Activity
                  </th>
                  <th className="px-6 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {leads.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                      No leads found
                    </td>
                  </tr>
                ) : (
                  leads.map((lead) => {
                    const statusConfig = STATUS_CONFIG[lead.lead_status];
                    const isOverdue = lead.next_followup_at && new Date(lead.next_followup_at) < new Date();

                    return (
                      <tr key={lead.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4">
                          <div>
                            <p className="font-medium text-gray-900">
                              {lead.contact_name || 'Unknown'}
                            </p>
                            <p className="text-sm text-gray-500">
                              {lead.contact_email || lead.contact_phone || 'No contact info'}
                            </p>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${statusConfig.bgColor} ${statusConfig.color}`}>
                            {statusConfig.label}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-900">
                          {lead.loan_purpose || '-'}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-900">
                          {lead.estimated_loan_amount
                            ? formatCurrency(lead.estimated_loan_amount)
                            : '-'}
                        </td>
                        <td className="px-6 py-4">
                          {lead.next_followup_at ? (
                            <span className={`text-sm ${isOverdue ? 'text-red-600 font-medium' : 'text-gray-900'}`}>
                              {formatDate(lead.next_followup_at)}
                              {isOverdue && ' (Overdue)'}
                            </span>
                          ) : (
                            <span className="text-sm text-gray-400">-</span>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                              <div
                                className={`h-full transition-all ${(lead.lead_score || 0) >= 80 ? 'bg-green-500' :
                                    (lead.lead_score || 0) >= 50 ? 'bg-yellow-500' : 'bg-red-400'
                                  }`}
                                style={{ width: `${lead.lead_score || 0}%` }}
                              />
                            </div>
                            <span className="text-sm font-medium text-gray-900 w-8">
                              {lead.lead_score || 0}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-sm">
                            <p className="text-gray-900">{lead.activity_count} activities</p>
                            {lead.last_activity_at && (
                              <p className="text-gray-500 text-xs">
                                Last: {formatDateTime(lead.last_activity_at)}
                              </p>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <button className="p-2 hover:bg-gray-100 rounded-lg">
                            <MoreVertical className="w-4 h-4 text-gray-400" />
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
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
      <div className="flex items-start justify-between">
        <div className={`p-3 rounded-lg ${bgColor}`}>{icon}</div>
      </div>
      <p className="text-3xl font-bold text-gray-900 mt-4">{value}</p>
      <p className="text-sm font-medium text-gray-600 mt-1">{label}</p>
      <p className="text-xs text-gray-400 mt-1">{subLabel}</p>
    </div>
  );
}
