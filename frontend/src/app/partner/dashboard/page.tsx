'use client';

import { useState, useEffect } from 'react';
import { Users, TrendingUp, Phone, Plus, ExternalLink, Copy, Check } from 'lucide-react';
import { partnershipsApi, PartnershipDetail, ReferralDetail } from '@/lib/api/endpoints';
import { ReferralModal } from '@/components/partnership';
import { logger } from '@/lib/utils';

interface PartnerStats {
  total: number;
  converted: number;
  pending: number;
}

export default function RealtorDashboard() {
  const [partnerships, setPartnerships] = useState<PartnershipDetail[]>([]);
  const [stats, setStats] = useState<PartnerStats>({ total: 0, converted: 0, pending: 0 });
  const [showReferralModal, setShowReferralModal] = useState(false);
  const [selectedPartnership, setSelectedPartnership] = useState<PartnershipDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [copiedWidget, setCopiedWidget] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const partnershipsData = await partnershipsApi.getMyPartnerships();
      setPartnerships(partnershipsData);

      // Aggregate stats from all partnerships
      let total = 0;
      let converted = 0;
      let pending = 0;

      for (const p of partnershipsData) {
        try {
          const refs = await partnershipsApi.getReferrals(p.id);
          refs.forEach((r: ReferralDetail) => {
            total++;
            if (r.status === 'closed') converted++;
            if (['new', 'contacted'].includes(r.status)) pending++;
          });
        } catch (e) {
          // Skip if can't get referrals
        }
      }
      setStats({ total, converted, pending });
    } catch (error) {
      logger.error('Failed to load partnerships:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyWidget = async (partnershipId: string) => {
    try {
      const { embed_code } = await partnershipsApi.getWidgetCode(partnershipId);
      await navigator.clipboard.writeText(embed_code);
      setCopiedWidget(true);
      setTimeout(() => setCopiedWidget(false), 2000);
    } catch (error) {
      logger.error('Failed to copy widget code:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Partner Dashboard</h1>
          <p className="text-gray-600">Manage your loan officer partnerships and referrals</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-100 rounded-lg">
                <Users className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.total}</p>
                <p className="text-gray-600">Total Referrals</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-100 rounded-lg">
                <TrendingUp className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.converted}</p>
                <p className="text-gray-600">Closed Deals</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-amber-100 rounded-lg">
                <Phone className="w-6 h-6 text-amber-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.pending}</p>
                <p className="text-gray-600">In Progress</p>
              </div>
            </div>
          </div>
        </div>

        {/* Partnerships */}
        <div className="bg-white rounded-xl shadow-sm mb-8">
          <div className="p-6 border-b">
            <h2 className="text-xl font-semibold">My Loan Officer Partners</h2>
          </div>

          {partnerships.length === 0 ? (
            <div className="p-12 text-center">
              <Users className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No partnerships yet</h3>
              <p className="text-gray-600">
                You&apos;ll see your loan officer partners here once they invite you.
              </p>
            </div>
          ) : (
            <div className="divide-y">
              {partnerships.map((partnership) => (
                <div key={partnership.id} className="p-6 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-blue-600 font-medium">
                        {partnership.loan_officer_name?.charAt(0) || 'L'}
                      </span>
                    </div>
                    <div>
                      <p className="font-medium">{partnership.loan_officer_name}</p>
                      <p className="text-sm text-gray-600">{partnership.loan_officer_company}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className={`px-3 py-1 rounded-full text-sm ${
                      partnership.status === 'active'
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      {partnership.status}
                    </span>
                    <span className="text-sm text-gray-500">
                      {partnership.referral_count} referrals
                    </span>
                    <button
                      onClick={() => {
                        setSelectedPartnership(partnership);
                        setShowReferralModal(true);
                      }}
                      disabled={partnership.status !== 'active'}
                      className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Plus className="w-4 h-4" />
                      Send Referral
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Widget Section */}
        {partnerships.some(p => p.status === 'active') && (
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl p-6 text-white">
            <h3 className="text-xl font-semibold mb-2">Embed on Your Website</h3>
            <p className="text-blue-100 mb-4">
              Add a &quot;Get Financing&quot; button to your property listings that connects
              your clients directly to your loan officer partner.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => {
                  const activePartnership = partnerships.find(p => p.status === 'active');
                  if (activePartnership) handleCopyWidget(activePartnership.id);
                }}
                className="flex items-center gap-2 px-4 py-2 bg-white text-blue-600 rounded-lg hover:bg-blue-50"
              >
                {copiedWidget ? (
                  <>
                    <Check className="w-4 h-4" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    Copy Embed Code
                  </>
                )}
              </button>
              <a
                href="/docs/widget"
                className="flex items-center gap-2 px-4 py-2 border border-white/30 text-white rounded-lg hover:bg-white/10"
              >
                <ExternalLink className="w-4 h-4" />
                View Documentation
              </a>
            </div>
          </div>
        )}
      </div>

      {/* Referral Modal */}
      {showReferralModal && selectedPartnership && (
        <ReferralModal
          partnership={selectedPartnership}
          onClose={() => setShowReferralModal(false)}
          onSuccess={() => {
            setShowReferralModal(false);
            loadData();
          }}
        />
      )}
    </div>
  );
}
