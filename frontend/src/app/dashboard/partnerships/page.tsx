'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api/client';

interface Partner {
  id: string;
  partner_name: string;
  partner_email: string;
  partner_type: 'realtor' | 'attorney' | 'title_rep';
  status: 'pending' | 'active' | 'inactive';
  commission_rate: number;
  total_referrals: number;
  total_earnings: number;
  created_at: string;
}

interface Referral {
  id: string;
  borrower_name: string;
  status: 'pending' | 'contacted' | 'converted' | 'lost';
  source_partner: string;
  commission_amount: number;
  created_at: string;
}

export default function PartnershipsPage() {
  const [partners, setPartners] = useState<Partner[]>([]);
  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'partners' | 'referrals'>('partners');
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteType, setInviteType] = useState<'realtor' | 'attorney' | 'title_rep'>('realtor');
  const [inviting, setInviting] = useState(false);
  const [payoutPartner, setPayoutPartner] = useState<Partner | null>(null);
  const [payingOut, setPayingOut] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [partnersRes, referralsRes] = await Promise.all([
        apiClient.get('/partnerships/my-partnerships'),
        apiClient.get('/partnerships/referrals'),
      ]);
      setPartners(Array.isArray(partnersRes.data) ? partnersRes.data : (partnersRes.data.partnerships || []));
      setReferrals(Array.isArray(referralsRes.data) ? referralsRes.data : (referralsRes.data.referrals || []));
    } catch (err) {
      console.error('Failed to load partnerships:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleInvite = async () => {
    if (!inviteEmail.trim()) return;
    setInviting(true);
    try {
      await apiClient.post('/partnerships/invite', {
        email: inviteEmail,
        partner_type: inviteType,
      });
      setShowInviteModal(false);
      setInviteEmail('');
      await loadData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to send invitation');
    } finally {
      setInviting(false);
    }
  };

  const handleInitiatePayout = (partner: Partner) => {
    setPayoutPartner(partner);
  };

  const handleConfirmPayout = async () => {
    if (!payoutPartner) return;
    setPayingOut(true);
    try {
      await apiClient.post(`/partnerships/${payoutPartner.id}/payout`, {
        amount: payoutPartner.total_earnings,
      });
      // Reset earnings after payout
      setPartners(prev => prev.map(p =>
        p.id === payoutPartner.id ? { ...p, total_earnings: 0 } : p
      ));
      setPayoutPartner(null);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to process payout');
    } finally {
      setPayingOut(false);
    }
  };

  const stats = {
    totalPartners: partners.filter(p => p.status === 'active').length,
    totalReferrals: referrals.length,
    totalEarnings: partners.reduce((sum, p) => sum + p.total_earnings, 0),
    pendingReferrals: referrals.filter(r => r.status === 'pending').length,
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-10 bg-gray-200 rounded w-1/3" />
          <div className="grid grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => <div key={i} className="h-24 bg-gray-200 rounded-lg" />)}
          </div>
          <div className="h-64 bg-gray-200 rounded-lg" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Partnerships</h1>
          <p className="mt-1 text-gray-600">Manage referral partners and track commissions</p>
        </div>
        <button
          onClick={() => setShowInviteModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium flex items-center"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Invite Partner
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Active Partners" value={stats.totalPartners} icon="👥" />
        <StatCard label="Total Referrals" value={stats.totalReferrals} icon="📋" />
        <StatCard label="Pending" value={stats.pendingReferrals} icon="⏳" color="yellow" />
        <StatCard label="Total Earnings" value={`$${stats.totalEarnings.toLocaleString()}`} icon="💰" color="green" />
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('partners')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${activeTab === 'partners'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
          >
            Partners ({partners.length})
          </button>
          <button
            onClick={() => setActiveTab('referrals')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${activeTab === 'referrals'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
          >
            Referrals ({referrals.length})
          </button>
        </nav>
      </div>

      {/* Partners tab */}
      {activeTab === 'partners' && (
        <div className="bg-white rounded-xl border overflow-hidden">
          {partners.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-5xl mb-4">🤝</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No Partners Yet</h3>
              <p className="text-gray-600 mb-4">Invite realtors and attorneys to start receiving referrals</p>
              <button
                onClick={() => setShowInviteModal(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Invite Your First Partner
              </button>
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Partner</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Type</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Status</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Referrals</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Earnings</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-900">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {partners.map(partner => (
                  <tr key={partner.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="font-medium text-gray-900">{partner.partner_name}</div>
                      <div className="text-sm text-gray-500">{partner.partner_email}</div>
                    </td>
                    <td className="px-6 py-4 capitalize text-gray-700">{partner.partner_type.replace('_', ' ')}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${partner.status === 'active' ? 'bg-green-100 text-green-800' :
                        partner.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                        {partner.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-gray-900">{partner.total_referrals}</td>
                    <td className="px-6 py-4 text-gray-900">${partner.total_earnings.toLocaleString()}</td>
                    <td className="px-6 py-4 text-right">
                      {partner.total_earnings > 0 && partner.status === 'active' && (
                        <button
                          onClick={() => handleInitiatePayout(partner)}
                          className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700"
                        >
                          💸 Payout
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Referrals tab */}
      {activeTab === 'referrals' && (
        <div className="bg-white rounded-xl border overflow-hidden">
          {referrals.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-5xl mb-4">📋</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No Referrals Yet</h3>
              <p className="text-gray-600">Referrals from your partners will appear here</p>
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Borrower</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">From Partner</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Status</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Commission</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {referrals.map(referral => (
                  <tr key={referral.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 font-medium text-gray-900">{referral.borrower_name}</td>
                    <td className="px-6 py-4 text-gray-700">{referral.source_partner}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${referral.status === 'converted' ? 'bg-green-100 text-green-800' :
                        referral.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                          referral.status === 'contacted' ? 'bg-blue-100 text-blue-800' :
                            'bg-red-100 text-red-800'
                        }`}>
                        {referral.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-gray-900">${referral.commission_amount.toLocaleString()}</td>
                    <td className="px-6 py-4 text-gray-500">{new Date(referral.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Invite Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Invite a Partner</h2>
            <p className="text-gray-600 mb-6">
              Send an invitation to a realtor, attorney, or title representative to start receiving referrals.
            </p>

            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Partner Type</label>
                <select
                  value={inviteType}
                  onChange={(e) => setInviteType(e.target.value as any)}
                  className="w-full px-4 py-2 border rounded-lg"
                >
                  <option value="realtor">Realtor</option>
                  <option value="attorney">Attorney</option>
                  <option value="title_rep">Title Representative</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
                <input
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  placeholder="partner@example.com"
                  className="w-full px-4 py-2 border rounded-lg"
                />
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowInviteModal(false)}
                className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleInvite}
                disabled={inviting || !inviteEmail.trim()}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {inviting ? 'Sending...' : 'Send Invitation'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Payout Confirmation Modal */}
      {payoutPartner && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">💸</span>
              </div>
              <h2 className="text-xl font-bold text-gray-900 mb-2">Confirm Payout</h2>
              <p className="text-gray-600 mb-4">
                Send <strong>${payoutPartner.total_earnings.toLocaleString()}</strong> to{' '}
                <strong>{payoutPartner.partner_name}</strong>?
              </p>
              <p className="text-sm text-gray-500 mb-6">
                Funds will be transferred via Stripe Connect to the partner's connected account.
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => setPayoutPartner(null)}
                  className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirmPayout}
                  disabled={payingOut}
                  className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  {payingOut ? 'Processing...' : 'Send Payout'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, icon, color = 'blue' }: { label: string; value: string | number; icon: string; color?: string }) {
  const colors = {
    blue: 'bg-blue-50 border-blue-200',
    green: 'bg-green-50 border-green-200',
    yellow: 'bg-yellow-50 border-yellow-200',
  };

  return (
    <div className={`p-4 rounded-xl border ${colors[color as keyof typeof colors] || colors.blue}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-2xl">{icon}</span>
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-sm text-gray-600">{label}</p>
    </div>
  );
}
