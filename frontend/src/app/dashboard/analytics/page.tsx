'use client';

import { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Phone,
  Star,
  Clock,
  Users,
  DollarSign,
  BarChart3,
  Calendar,
  ChevronDown,
  ArrowUpRight,
  ArrowDownRight,
  Lightbulb,
  Target,
} from 'lucide-react';
import { logger } from '@/lib/utils';

interface TimeSeriesPoint {
  date: string;
  value: number;
}

interface PerformanceMetrics {
  total_calls: number;
  completed_calls: number;
  missed_calls: number;
  avg_call_duration_seconds: number;
  avg_pickup_time_seconds: number;
  total_reviews: number;
  avg_rating: number;
  five_star_count: number;
  total_leads_generated: number;
  leads_converted: number;
  conversion_rate: number;
}

interface CallAnalytics {
  calls_by_day: TimeSeriesPoint[];
  calls_by_hour: Record<number, number>;
  calls_by_day_of_week: Record<string, number>;
  busiest_hour: number | null;
  busiest_day: string | null;
}

interface RatingAnalytics {
  rating_distribution: Record<number, number>;
  ratings_over_time: TimeSeriesPoint[];
  recent_reviews: Array<{
    rating: number;
    content: string;
    created_at: string;
  }>;
}

interface LeadAnalytics {
  leads_by_status: Record<string, number>;
  leads_by_day: TimeSeriesPoint[];
  total_pipeline_value: number;
}

interface BillingAnalytics {
  current_subscription_tier: string;
  bid_wallet_balance: number;
  total_bid_spend_month: number;
}

interface GridAnalytics {
  current_position: number | null;
  impressions_today: number;
  impressions_week: number;
  impressions_month: number;
}

interface AnalyticsDashboard {
  period_start: string;
  period_end: string;
  performance: PerformanceMetrics;
  calls: CallAnalytics;
  ratings: RatingAnalytics;
  leads: LeadAnalytics;
  billing: BillingAnalytics;
  grid: GridAnalytics;
  insights: string[];
  recommendations: string[];
}

type Period = '7d' | '30d' | '90d' | '12m';

const PERIOD_LABELS: Record<Period, string> = {
  '7d': 'Last 7 Days',
  '30d': 'Last 30 Days',
  '90d': 'Last 90 Days',
  '12m': 'Last 12 Months',
};

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const minutes = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${minutes}m ${secs}s`;
}

function formatNumber(num: number): string {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
}

function formatCurrency(amount: number): string {
  if (amount >= 1000000) return `$${(amount / 1000000).toFixed(1)}M`;
  if (amount >= 1000) return `$${(amount / 1000).toFixed(0)}K`;
  return `$${amount.toFixed(0)}`;
}

export default function AnalyticsDashboard() {
  const [data, setData] = useState<AnalyticsDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState<Period>('30d');
  const [showPeriodDropdown, setShowPeriodDropdown] = useState(false);

  useEffect(() => {
    fetchData();
  }, [period]);

  async function fetchData() {
    try {
      setLoading(true);
      const res = await fetch(`/api/v1/analytics/dashboard?period=${period}`);
      if (res.ok) {
        const dashboardData = await res.json();
        setData(dashboardData);
      }
    } catch (error) {
      logger.error('Failed to fetch analytics:', error);
    } finally {
      setLoading(false);
    }
  }

  if (loading && !data) {
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
            <div className="grid grid-cols-2 gap-6">
              {[1, 2].map((i) => (
                <div key={i} className="h-64 bg-gray-200 rounded-xl"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-500">Failed to load analytics</p>
      </div>
    );
  }

  const { performance, calls, ratings, leads, billing, grid, insights, recommendations } = data;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-8 py-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
            <p className="text-gray-500 mt-1">
              {new Date(data.period_start).toLocaleDateString()} - {new Date(data.period_end).toLocaleDateString()}
            </p>
          </div>

          {/* Period Selector */}
          <div className="relative">
            <button
              onClick={() => setShowPeriodDropdown(!showPeriodDropdown)}
              className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-gray-50"
            >
              <Calendar className="w-4 h-4" />
              {PERIOD_LABELS[period]}
              <ChevronDown className="w-4 h-4" />
            </button>

            {showPeriodDropdown && (
              <div className="absolute top-full mt-2 right-0 bg-white border rounded-lg shadow-lg z-10 min-w-[180px]">
                {(Object.entries(PERIOD_LABELS) as [Period, string][]).map(([value, label]) => (
                  <button
                    key={value}
                    onClick={() => {
                      setPeriod(value);
                      setShowPeriodDropdown(false);
                    }}
                    className={`w-full text-left px-4 py-2 hover:bg-gray-50 ${
                      period === value ? 'bg-blue-50 text-blue-700' : ''
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-8 py-6 space-y-6">
        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard
            icon={<Phone className="w-6 h-6 text-blue-600" />}
            label="Total Calls"
            value={performance.total_calls.toString()}
            subValue={`${performance.completed_calls} completed`}
            bgColor="bg-blue-50"
            trend={performance.completed_calls / Math.max(performance.total_calls, 1)}
            trendLabel={`${((performance.completed_calls / Math.max(performance.total_calls, 1)) * 100).toFixed(0)}% answer rate`}
          />
          <MetricCard
            icon={<Star className="w-6 h-6 text-amber-600" />}
            label="Average Rating"
            value={performance.avg_rating.toFixed(1)}
            subValue={`${performance.total_reviews} reviews`}
            bgColor="bg-amber-50"
            trend={performance.avg_rating / 5}
            trendLabel={`${performance.five_star_count} five-star`}
          />
          <MetricCard
            icon={<Clock className="w-6 h-6 text-green-600" />}
            label="Avg Pickup Time"
            value={formatDuration(performance.avg_pickup_time_seconds)}
            subValue="Response time"
            bgColor="bg-green-50"
            trend={performance.avg_pickup_time_seconds < 10 ? 1 : 0.5}
            trendLabel={performance.avg_pickup_time_seconds < 10 ? 'Excellent' : 'Could improve'}
          />
          <MetricCard
            icon={<Target className="w-6 h-6 text-purple-600" />}
            label="Conversion Rate"
            value={`${performance.conversion_rate}%`}
            subValue={`${performance.leads_converted}/${performance.total_leads_generated} leads`}
            bgColor="bg-purple-50"
            trend={performance.conversion_rate / 100}
            trendLabel={performance.conversion_rate > 20 ? 'Above average' : 'Room to grow'}
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Call Distribution */}
          <div className="bg-white rounded-xl border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Call Distribution</h3>

            {/* By Day of Week */}
            <div className="mb-6">
              <p className="text-sm text-gray-500 mb-3">By Day of Week</p>
              <div className="flex gap-2">
                {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => {
                  const count = calls.calls_by_day_of_week[day] || 0;
                  const maxCount = Math.max(...Object.values(calls.calls_by_day_of_week), 1);
                  const height = (count / maxCount) * 100;

                  return (
                    <div key={day} className="flex-1 flex flex-col items-center">
                      <div className="h-20 w-full flex items-end justify-center">
                        <div
                          className={`w-8 rounded-t ${
                            day === calls.busiest_day ? 'bg-blue-600' : 'bg-blue-200'
                          }`}
                          style={{ height: `${Math.max(height, 4)}%` }}
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-2">{day}</p>
                      <p className="text-xs font-medium text-gray-700">{count}</p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Busiest Times */}
            <div className="pt-4 border-t">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm text-gray-500">Busiest Day</p>
                  <p className="font-semibold text-gray-900">{calls.busiest_day || '-'}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500">Peak Hour</p>
                  <p className="font-semibold text-gray-900">
                    {calls.busiest_hour !== null ? `${calls.busiest_hour}:00` : '-'}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Rating Distribution */}
          <div className="bg-white rounded-xl border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Rating Distribution</h3>

            <div className="space-y-3">
              {[5, 4, 3, 2, 1].map((rating) => {
                const count = ratings.rating_distribution[rating] || 0;
                const total = Object.values(ratings.rating_distribution).reduce((a, b) => a + b, 0);
                const pct = total > 0 ? (count / total) * 100 : 0;

                return (
                  <div key={rating} className="flex items-center gap-3">
                    <div className="flex items-center gap-1 w-12">
                      <span className="text-sm font-medium text-gray-700">{rating}</span>
                      <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
                    </div>
                    <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          rating >= 4 ? 'bg-green-500' : rating === 3 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-500 w-12 text-right">{count}</span>
                  </div>
                );
              })}
            </div>

            {/* Recent Reviews */}
            {ratings.recent_reviews.length > 0 && (
              <div className="mt-6 pt-4 border-t">
                <p className="text-sm text-gray-500 mb-3">Recent Reviews</p>
                <div className="space-y-3">
                  {ratings.recent_reviews.slice(0, 3).map((review, i) => (
                    <div key={i} className="flex items-start gap-2">
                      <div className="flex">
                        {[...Array(5)].map((_, j) => (
                          <Star
                            key={j}
                            className={`w-3 h-3 ${
                              j < review.rating
                                ? 'text-amber-400 fill-amber-400'
                                : 'text-gray-300'
                            }`}
                          />
                        ))}
                      </div>
                      {review.content && (
                        <p className="text-sm text-gray-600 truncate flex-1">
                          {review.content}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Lead Funnel & Billing */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Lead Funnel */}
          <div className="bg-white rounded-xl border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Lead Funnel</h3>

            <div className="space-y-3">
              {[
                { status: 'new', label: 'New', color: 'bg-blue-500' },
                { status: 'contacted', label: 'Contacted', color: 'bg-purple-500' },
                { status: 'qualified', label: 'Qualified', color: 'bg-green-500' },
                { status: 'proposal_sent', label: 'Proposal Sent', color: 'bg-amber-500' },
                { status: 'won', label: 'Won', color: 'bg-emerald-500' },
              ].map((stage) => {
                const count = leads.leads_by_status[stage.status] || 0;
                const total = performance.total_leads_generated || 1;
                const pct = (count / total) * 100;

                return (
                  <div key={stage.status} className="flex items-center gap-3">
                    <span className="text-sm text-gray-600 w-28">{stage.label}</span>
                    <div className="flex-1 h-6 bg-gray-100 rounded-lg overflow-hidden">
                      <div
                        className={`h-full rounded-lg ${stage.color} flex items-center justify-end pr-2`}
                        style={{ width: `${Math.max(pct, 5)}%` }}
                      >
                        <span className="text-xs font-medium text-white">{count}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="mt-6 pt-4 border-t flex justify-between">
              <div>
                <p className="text-sm text-gray-500">Pipeline Value</p>
                <p className="text-xl font-bold text-gray-900">
                  {formatCurrency(leads.total_pipeline_value)}
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-500">Total Leads</p>
                <p className="text-xl font-bold text-gray-900">{performance.total_leads_generated}</p>
              </div>
            </div>
          </div>

          {/* Billing Summary */}
          <div className="bg-white rounded-xl border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Billing Summary</h3>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm text-gray-500">Current Plan</p>
                  <p className="font-semibold text-gray-900 capitalize">{billing.current_subscription_tier}</p>
                </div>
                <button className="text-sm text-blue-600 font-medium hover:underline">
                  Upgrade
                </button>
              </div>

              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm text-gray-500">Bid Wallet Balance</p>
                  <p className="font-semibold text-gray-900">${billing.bid_wallet_balance.toFixed(2)}</p>
                </div>
                <button className="text-sm text-blue-600 font-medium hover:underline">
                  Add Funds
                </button>
              </div>

              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm text-gray-500">This Month&apos;s Spend</p>
                  <p className="font-semibold text-gray-900">${billing.total_bid_spend_month.toFixed(2)}</p>
                </div>
              </div>
            </div>

            {/* Grid Stats */}
            <div className="mt-6 pt-4 border-t">
              <p className="text-sm text-gray-500 mb-3">Grid Performance</p>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center">
                  <p className="text-2xl font-bold text-gray-900">{formatNumber(grid.impressions_today)}</p>
                  <p className="text-xs text-gray-500">Today</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-gray-900">{formatNumber(grid.impressions_week)}</p>
                  <p className="text-xs text-gray-500">This Week</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-gray-900">{formatNumber(grid.impressions_month)}</p>
                  <p className="text-xs text-gray-500">This Month</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Insights & Recommendations */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Insights */}
          <div className="bg-white rounded-xl border p-6">
            <div className="flex items-center gap-2 mb-4">
              <Lightbulb className="w-5 h-5 text-amber-500" />
              <h3 className="text-lg font-semibold text-gray-900">Insights</h3>
            </div>
            {insights.length > 0 ? (
              <ul className="space-y-3">
                {insights.map((insight, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="w-1.5 h-1.5 bg-amber-500 rounded-full mt-2" />
                    <p className="text-gray-600">{insight}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500">No insights available yet.</p>
            )}
          </div>

          {/* Recommendations */}
          <div className="bg-white rounded-xl border p-6">
            <div className="flex items-center gap-2 mb-4">
              <Target className="w-5 h-5 text-blue-500" />
              <h3 className="text-lg font-semibold text-gray-900">Recommendations</h3>
            </div>
            {recommendations.length > 0 ? (
              <ul className="space-y-3">
                {recommendations.map((rec, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2" />
                    <p className="text-gray-600">{rec}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500">No recommendations available yet.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({
  icon,
  label,
  value,
  subValue,
  bgColor,
  trend,
  trendLabel,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  subValue: string;
  bgColor: string;
  trend: number;
  trendLabel: string;
}) {
  const isPositive = trend >= 0.7;

  return (
    <div className="bg-white rounded-xl border p-6">
      <div className="flex items-start justify-between">
        <div className={`p-3 rounded-lg ${bgColor}`}>{icon}</div>
        <div className={`flex items-center gap-1 text-sm ${isPositive ? 'text-green-600' : 'text-amber-600'}`}>
          {isPositive ? (
            <ArrowUpRight className="w-4 h-4" />
          ) : (
            <ArrowDownRight className="w-4 h-4" />
          )}
          <span>{trendLabel}</span>
        </div>
      </div>
      <p className="text-3xl font-bold text-gray-900 mt-4">{value}</p>
      <p className="text-sm font-medium text-gray-600 mt-1">{label}</p>
      <p className="text-xs text-gray-400 mt-1">{subValue}</p>
    </div>
  );
}
