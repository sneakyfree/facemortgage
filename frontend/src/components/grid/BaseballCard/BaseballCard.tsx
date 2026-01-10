'use client';

import { useState, useEffect, useCallback } from 'react';
import { X, Award, TrendingUp, MapPin, Building2, Shield, BarChart3 } from 'lucide-react';
import { useFocusTrap, useEscapeKey } from '@/hooks/useFocusTrap';

interface LoanMix {
  type: string;
  pct: number;
}

interface PurposeMix {
  type: string;
  pct: number;
}

interface Ranking {
  label: string;
  value: string;
}

interface BaseballCardData {
  nmls_id: string;
  name: string;
  company: string | null;
  license_status: string;
  license_status_color: string;
  years_experience_display: string;
  total_loans_display: string;
  total_volume_display: string;
  loans_12m_display: string;
  volume_12m_display: string;
  avg_loan_display: string;
  loan_mix: LoanMix[];
  purpose_mix: PurposeMix[];
  rankings: Ranking[];
  states_licensed: string[];
  top_markets: string[];
}

interface BaseballCardProps {
  nmlsId: string;
  professionalName?: string;
  professionalImage?: string;
  onClose: () => void;
}

const STATUS_COLORS: Record<string, string> = {
  green: 'bg-green-500',
  yellow: 'bg-yellow-500',
  red: 'bg-red-500',
  gray: 'bg-gray-500',
};

const LOAN_TYPE_COLORS: Record<string, string> = {
  Conventional: '#3B82F6',
  FHA: '#10B981',
  VA: '#8B5CF6',
  USDA: '#F59E0B',
  Jumbo: '#EF4444',
  Other: '#6B7280',
};

const PURPOSE_COLORS: Record<string, string> = {
  Purchase: '#3B82F6',
  Refinance: '#10B981',
};

export function BaseballCard({ nmlsId, professionalName, professionalImage, onClose }: BaseballCardProps) {
  const [data, setData] = useState<BaseballCardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Accessibility: Focus trap and escape key handling
  const modalRef = useFocusTrap<HTMLDivElement>(true);
  const handleEscape = useCallback(() => onClose(), [onClose]);
  useEscapeKey(true, handleEscape);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const response = await fetch(`/api/v1/stats/${nmlsId}/baseball-card`);
        if (!response.ok) {
          throw new Error('Failed to fetch stats');
        }
        const cardData = await response.json();
        setData(cardData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [nmlsId]);

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-2xl p-8 shadow-2xl max-w-2xl w-full mx-4 animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/2 mb-6"></div>
          <div className="space-y-4">
            <div className="h-24 bg-gray-200 rounded"></div>
            <div className="h-32 bg-gray-200 rounded"></div>
            <div className="h-24 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-2xl p-8 shadow-2xl max-w-md w-full mx-4">
          <div className="text-center">
            <p className="text-red-500 mb-4">{error || 'Failed to load stats'}</p>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="baseball-card-title"
        className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl shadow-2xl max-w-2xl w-full overflow-hidden"
      >
        {/* Header */}
        <div className="relative bg-gradient-to-r from-blue-600 to-blue-700 p-6">
          <button
            onClick={onClose}
            aria-label="Close professional details"
            className="absolute top-4 right-4 text-white/80 hover:text-white transition-colors"
          >
            <X className="h-6 w-6" aria-hidden="true" />
          </button>

          <div className="flex items-center gap-4">
            {professionalImage ? (
              <img
                src={professionalImage}
                alt={data.name}
                className="w-20 h-20 rounded-full border-4 border-white/20 object-cover"
              />
            ) : (
              <div className="w-20 h-20 rounded-full border-4 border-white/20 bg-blue-500 flex items-center justify-center" aria-hidden="true">
                <span className="text-2xl font-bold text-white">
                  {data.name.charAt(0)}
                </span>
              </div>
            )}
            <div className="flex-1">
              <h2 id="baseball-card-title" className="text-2xl font-bold text-white">{professionalName || data.name}</h2>
              {data.company && (
                <p className="text-blue-100 flex items-center gap-2 mt-1">
                  <Building2 className="h-4 w-4" />
                  {data.company}
                </p>
              )}
              <div className="flex items-center gap-3 mt-2">
                <span className="text-sm text-blue-100">NMLS# {data.nmls_id}</span>
                <span className="flex items-center gap-1 text-sm">
                  <span className={`w-2 h-2 rounded-full ${STATUS_COLORS[data.license_status_color]}`}></span>
                  <span className="text-blue-100">{data.license_status}</span>
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="p-6 space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-3 gap-4">
            <StatCard
              icon={<Award className="h-5 w-5 text-amber-400" />}
              label="Experience"
              value={data.years_experience_display}
            />
            <StatCard
              icon={<TrendingUp className="h-5 w-5 text-green-400" />}
              label="Career Loans"
              value={data.total_loans_display}
            />
            <StatCard
              icon={<BarChart3 className="h-5 w-5 text-blue-400" />}
              label="Career Volume"
              value={data.total_volume_display}
            />
          </div>

          {/* Last 12 Months */}
          <div className="bg-slate-800/50 rounded-xl p-4">
            <h3 className="text-sm font-medium text-slate-400 mb-3">Last 12 Months Performance</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-white">{data.loans_12m_display}</p>
                <p className="text-xs text-slate-400">Loans Closed</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-white">{data.volume_12m_display}</p>
                <p className="text-xs text-slate-400">Total Volume</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-white">{data.avg_loan_display}</p>
                <p className="text-xs text-slate-400">Avg Loan Size</p>
              </div>
            </div>
          </div>

          {/* Loan Mix and Purpose */}
          <div className="grid grid-cols-2 gap-4">
            {/* Loan Type Mix */}
            <div className="bg-slate-800/50 rounded-xl p-4">
              <h3 className="text-sm font-medium text-slate-400 mb-3">Loan Type Mix</h3>
              <div className="space-y-2">
                {data.loan_mix.map((item) => (
                  <div key={item.type} className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: LOAN_TYPE_COLORS[item.type] || LOAN_TYPE_COLORS.Other }}
                    />
                    <span className="text-sm text-slate-300 flex-1">{item.type}</span>
                    <span className="text-sm font-medium text-white">{item.pct.toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Purpose Mix */}
            <div className="bg-slate-800/50 rounded-xl p-4">
              <h3 className="text-sm font-medium text-slate-400 mb-3">Purpose Mix</h3>
              <div className="space-y-2">
                {data.purpose_mix.map((item) => (
                  <div key={item.type} className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: PURPOSE_COLORS[item.type] || '#6B7280' }}
                    />
                    <span className="text-sm text-slate-300 flex-1">{item.type}</span>
                    <span className="text-sm font-medium text-white">{item.pct.toFixed(1)}%</span>
                  </div>
                ))}
              </div>

              {/* Rankings */}
              {data.rankings.length > 0 && (
                <div className="mt-4 pt-4 border-t border-slate-700">
                  <h3 className="text-sm font-medium text-slate-400 mb-2">Rankings</h3>
                  <div className="space-y-1">
                    {data.rankings.map((ranking) => (
                      <div key={ranking.label} className="flex justify-between">
                        <span className="text-sm text-slate-300">{ranking.label}</span>
                        <span className="text-sm font-bold text-amber-400">{ranking.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Licensed States */}
          <div className="bg-slate-800/50 rounded-xl p-4">
            <h3 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
              <Shield className="h-4 w-4" />
              Licensed States
            </h3>
            <div className="flex flex-wrap gap-2">
              {data.states_licensed.map((state) => (
                <span
                  key={state}
                  className="px-3 py-1 bg-slate-700 rounded-full text-sm text-white"
                >
                  {state}
                </span>
              ))}
            </div>
          </div>

          {/* Top Markets */}
          {data.top_markets.length > 0 && (
            <div className="bg-slate-800/50 rounded-xl p-4">
              <h3 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
                <MapPin className="h-4 w-4" />
                Top Markets
              </h3>
              <div className="flex flex-wrap gap-2">
                {data.top_markets.map((market) => (
                  <span
                    key={market}
                    className="px-3 py-1 bg-blue-600/20 text-blue-300 rounded-full text-sm"
                  >
                    {market}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-slate-900 px-6 py-4 text-center">
          <p className="text-xs text-slate-500">
            Data provided by industry sources. Updated periodically.
          </p>
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="bg-slate-800/50 rounded-xl p-4 text-center">
      <div className="flex justify-center mb-2">{icon}</div>
      <p className="text-xl font-bold text-white">{value}</p>
      <p className="text-xs text-slate-400">{label}</p>
    </div>
  );
}
