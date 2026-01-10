'use client';

import { useState, useEffect } from 'react';
import { Users, UserPlus, TrendingUp, DollarSign, Mail, MoreVertical, Trash2 } from 'lucide-react';
import { partnershipsApi, PartnershipDetail } from '@/lib/api/endpoints';
import { InvitePartnerModal } from '@/components/partnership';
import { logger } from '@/lib/utils';

interface PartnershipStats {
  activePartners: number;
  totalReferrals: number;
  closedDeals: number;
  pipelineValue: number;
}

interface StatCardProps {
  icon: React.ElementType;
  value: string | number;
  label: string;
  color: 'blue' | 'green' | 'purple' | 'amber';
}

function StatCard({ icon: Icon, value, label, color }: StatCardProps) {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    purple: 'bg-purple-100 text-purple-600',
    amber: 'bg-amber-100 text-amber-600',
  };

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm">
      <div className="flex items-center gap-4">
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
        <div>
          <p className="text-2xl font-bold">{value}</p>
          <p className="text-gray-600">{label}</p>
        </div>
      </div>
    </div>
  );
}

interface PartnershipRowProps {
  partnership: PartnershipDetail;
  onTerminate: (id: string) => void;
}

function PartnershipRow({ partnership, onTerminate }: PartnershipRowProps) {
  const [showMenu, setShowMenu] = useState(false);

  return (
    <div className="p-6 flex items-center justify-between hover:bg-gray-50">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center">
          <span className="text-indigo-600 font-medium">
            {partnership.realtor_name?.charAt(0) || 'R'}
          </span>
        </div>
        <div>
          <p className="font-medium">{partnership.realtor_name || partnership.realtor_email}</p>
          <p className="text-sm text-gray-600">
            {partnership.referral_count} referrals
          </p>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <span className={`px-3 py-1 rounded-full text-sm ${
          partnership.status === 'active'
            ? 'bg-green-100 text-green-700'
            : partnership.status === 'pending'
            ? 'bg-yellow-100 text-yellow-700'
            : 'bg-gray-100 text-gray-700'
        }`}>
          {partnership.status}
        </span>
        <span className="text-sm text-gray-500">
          {partnership.tier}
        </span>
        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <MoreVertical className="w-5 h-5 text-gray-500" />
          </button>
          {showMenu && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setShowMenu(false)}
              />
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border z-20">
                <button
                  onClick={() => {
                    onTerminate(partnership.id);
                    setShowMenu(false);
                  }}
                  className="w-full flex items-center gap-2 px-4 py-2 text-red-600 hover:bg-red-50 text-left"
                >
                  <Trash2 className="w-4 h-4" />
                  End Partnership
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function PartnershipsPage() {
  const [partnerships, setPartnerships] = useState<PartnershipDetail[]>([]);
  const [stats, setStats] = useState<PartnershipStats>({
    activePartners: 0,
    totalReferrals: 0,
    closedDeals: 0,
    pipelineValue: 0,
  });
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const data = await partnershipsApi.getMyPartnerships();
      setPartnerships(data);

      // Calculate stats
      const active = data.filter(p => p.status === 'active').length;
      const totalReferrals = data.reduce((sum, p) => sum + (p.referral_count || 0), 0);

      setStats({
        activePartners: active,
        totalReferrals,
        closedDeals: 0, // Would need API to get this
        pipelineValue: 0,
      });
    } catch (error) {
      logger.error('Failed to load partnerships:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTerminate = async (partnershipId: string) => {
    if (!confirm('Are you sure you want to end this partnership? This action cannot be undone.')) {
      return;
    }

    try {
      await partnershipsApi.terminatePartnership(partnershipId);
      loadData();
    } catch (error) {
      logger.error('Failed to terminate partnership:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-start mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Realtor Partnerships</h1>
          <p className="text-gray-600">Manage your realtor network and track referrals</p>
        </div>
        <button
          onClick={() => setShowInviteModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <UserPlus className="w-5 h-5" />
          Invite Partner
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <StatCard icon={Users} value={stats.activePartners} label="Active Partners" color="blue" />
        <StatCard icon={Mail} value={stats.totalReferrals} label="Total Referrals" color="green" />
        <StatCard icon={TrendingUp} value={stats.closedDeals} label="Closed Deals" color="purple" />
        <StatCard
          icon={DollarSign}
          value={stats.pipelineValue > 0 ? `$${(stats.pipelineValue / 1000).toFixed(0)}K` : '$0'}
          label="Pipeline Value"
          color="amber"
        />
      </div>

      {/* Partnerships List */}
      <div className="bg-white rounded-xl shadow-sm">
        <div className="p-6 border-b">
          <h2 className="text-xl font-semibold">Your Partners</h2>
        </div>

        {partnerships.length === 0 ? (
          <div className="p-12 text-center">
            <Users className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No partners yet</h3>
            <p className="text-gray-600 mb-4">
              Start building your realtor network to get more referrals
            </p>
            <button
              onClick={() => setShowInviteModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Invite Your First Partner
            </button>
          </div>
        ) : (
          <div className="divide-y">
            {partnerships.map((p) => (
              <PartnershipRow
                key={p.id}
                partnership={p}
                onTerminate={handleTerminate}
              />
            ))}
          </div>
        )}
      </div>

      {/* How It Works Section */}
      <div className="mt-8 bg-gradient-to-br from-indigo-50 to-blue-50 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">How Partner Referrals Work</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
              1
            </div>
            <div>
              <p className="font-medium text-gray-900">Invite a Realtor</p>
              <p className="text-sm text-gray-600">
                Send an invitation to realtors you work with
              </p>
            </div>
          </div>
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
              2
            </div>
            <div>
              <p className="font-medium text-gray-900">They Send Referrals</p>
              <p className="text-sm text-gray-600">
                Partners can refer clients directly or use the embed widget
              </p>
            </div>
          </div>
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
              3
            </div>
            <div>
              <p className="font-medium text-gray-900">Close More Deals</p>
              <p className="text-sm text-gray-600">
                Track referrals and grow together
              </p>
            </div>
          </div>
        </div>
      </div>

      {showInviteModal && (
        <InvitePartnerModal
          onClose={() => setShowInviteModal(false)}
          onSuccess={() => {
            setShowInviteModal(false);
            loadData();
          }}
        />
      )}
    </div>
  );
}
