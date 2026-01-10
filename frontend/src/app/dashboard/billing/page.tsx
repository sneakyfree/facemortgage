'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { apiClient } from '@/lib/api/client';
import { logger } from '@/lib/utils';

interface SubscriptionPlan {
  tier: string;
  name: string;
  price: number;
  features: string[];
}

interface Subscription {
  id: string;
  tier: string;
  status: string;
  current_period_end?: string;
  cancel_at_period_end: boolean;
}

interface BidWallet {
  available_credits: number;
  reserved_credits: number;
  total_deposited: number;
  total_spent: number;
}

function BillingPageContent() {
  const searchParams = useSearchParams();
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [wallet, setWallet] = useState<BidWallet | null>(null);
  const [bidAmount, setBidAmount] = useState('0');
  const [dailyBudget, setDailyBudget] = useState('');
  const [depositAmount, setDepositAmount] = useState('50');
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Check for deposit success/cancel from redirect
  useEffect(() => {
    const deposit = searchParams.get('deposit');
    if (deposit === 'success') {
      setMessage({ type: 'success', text: 'Deposit successful! Your credits have been added.' });
    } else if (deposit === 'cancelled') {
      setMessage({ type: 'error', text: 'Deposit cancelled.' });
    }
  }, [searchParams]);

  // Fetch billing data
  useEffect(() => {
    async function fetchData() {
      try {
        const [plansRes, subRes, walletRes] = await Promise.all([
          apiClient.get('/billing/plans'),
          apiClient.get('/billing/subscription'),
          apiClient.get('/billing/wallet'),
        ]);

        setPlans(plansRes.data);
        setSubscription(subRes.data);
        setWallet(walletRes.data);
      } catch (error) {
        logger.error('Failed to fetch billing data:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  const handleSubscribe = async (tier: string) => {
    try {
      setLoading(true);
      const response = await apiClient.post('/billing/subscription', { tier });

      if (response.data.client_secret) {
        // Redirect to Stripe Checkout (in real app, use Stripe.js)
        window.location.href = `/checkout?client_secret=${response.data.client_secret}`;
      } else {
        setSubscription({
          ...subscription!,
          tier,
          status: 'active',
        });
        setMessage({ type: 'success', text: 'Subscription updated successfully!' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to update subscription' });
    } finally {
      setLoading(false);
    }
  };

  const handleCancelSubscription = async () => {
    if (!confirm('Are you sure you want to cancel your subscription?')) return;

    try {
      await apiClient.post('/billing/subscription/cancel');
      setSubscription({
        ...subscription!,
        cancel_at_period_end: true,
      });
      setMessage({ type: 'success', text: 'Subscription will be cancelled at the end of the billing period.' });
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to cancel subscription' });
    }
  };

  const handleDeposit = async () => {
    try {
      const response = await apiClient.post('/billing/wallet/deposit', {
        amount: parseFloat(depositAmount),
      });

      // Redirect to Stripe Checkout
      window.location.href = response.data.checkout_url;
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to create deposit session' });
    }
  };

  const handleUpdateBid = async () => {
    try {
      await apiClient.put('/billing/bid-settings', {
        bid_amount: parseFloat(bidAmount),
        daily_budget: dailyBudget ? parseFloat(dailyBudget) : null,
      });
      setMessage({ type: 'success', text: 'Bid settings updated!' });
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to update bid settings' });
    }
  };

  const handleOpenPortal = async () => {
    try {
      const response = await apiClient.post('/billing/portal');
      window.location.href = response.data.portal_url;
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to open billing portal' });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-6xl mx-auto">
          <div className="animate-pulse space-y-8">
            <div className="h-8 bg-gray-200 rounded w-1/4"></div>
            <div className="grid grid-cols-3 gap-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-64 bg-gray-200 rounded-lg"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Billing & Subscription</h1>
          <p className="text-gray-600 mt-2">
            Manage your subscription, bid settings, and payment methods
          </p>
        </div>

        {/* Message */}
        {message && (
          <div
            className={`p-4 rounded-lg ${
              message.type === 'success'
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'
            }`}
          >
            {message.text}
          </div>
        )}

        {/* Current Subscription */}
        {subscription && (
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-xl font-semibold mb-4">Current Subscription</h2>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-2xl font-bold capitalize">{subscription.tier}</p>
                <p className="text-gray-600">
                  Status: <span className="capitalize">{subscription.status}</span>
                </p>
                {subscription.current_period_end && (
                  <p className="text-gray-500 text-sm">
                    {subscription.cancel_at_period_end
                      ? 'Cancels on'
                      : 'Renews on'}{' '}
                    {new Date(subscription.current_period_end).toLocaleDateString()}
                  </p>
                )}
              </div>
              <div className="space-x-4">
                {subscription.tier !== 'free' && !subscription.cancel_at_period_end && (
                  <button
                    onClick={handleCancelSubscription}
                    className="px-4 py-2 text-red-600 border border-red-600 rounded-lg hover:bg-red-50"
                  >
                    Cancel Subscription
                  </button>
                )}
                <button
                  onClick={handleOpenPortal}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                >
                  Manage Billing
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Subscription Plans */}
        <div>
          <h2 className="text-xl font-semibold mb-4">Subscription Plans</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {plans.map((plan) => (
              <div
                key={plan.tier}
                className={`bg-white rounded-xl shadow-sm p-6 border-2 ${
                  subscription?.tier === plan.tier
                    ? 'border-blue-500'
                    : 'border-transparent'
                }`}
              >
                <h3 className="text-lg font-semibold">{plan.name}</h3>
                <p className="text-3xl font-bold mt-2">
                  ${plan.price}
                  <span className="text-sm text-gray-500 font-normal">/mo</span>
                </p>

                <ul className="mt-4 space-y-2">
                  {plan.features.map((feature, idx) => (
                    <li key={idx} className="flex items-start text-sm">
                      <svg
                        className="w-5 h-5 text-green-500 mr-2 flex-shrink-0"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                      {feature}
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => handleSubscribe(plan.tier)}
                  disabled={subscription?.tier === plan.tier}
                  className={`w-full mt-6 py-2 rounded-lg font-medium ${
                    subscription?.tier === plan.tier
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  {subscription?.tier === plan.tier ? 'Current Plan' : 'Select Plan'}
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Bid Wallet */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Wallet Balance */}
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-xl font-semibold mb-4">Bid Wallet</h2>

            {wallet && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-green-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-600">Available Credits</p>
                    <p className="text-2xl font-bold text-green-600">
                      ${wallet.available_credits.toFixed(2)}
                    </p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-600">Reserved</p>
                    <p className="text-2xl font-bold text-gray-600">
                      ${wallet.reserved_credits.toFixed(2)}
                    </p>
                  </div>
                </div>

                <div className="text-sm text-gray-500">
                  <p>Total Deposited: ${wallet.total_deposited.toFixed(2)}</p>
                  <p>Total Spent: ${wallet.total_spent.toFixed(2)}</p>
                </div>

                {/* Deposit Form */}
                <div className="pt-4 border-t">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Add Credits
                  </label>
                  <div className="flex space-x-2">
                    <select
                      value={depositAmount}
                      onChange={(e) => setDepositAmount(e.target.value)}
                      className="flex-1 px-4 py-2 border rounded-lg"
                    >
                      <option value="25">$25</option>
                      <option value="50">$50</option>
                      <option value="100">$100</option>
                      <option value="250">$250</option>
                      <option value="500">$500</option>
                    </select>
                    <button
                      onClick={handleDeposit}
                      className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      Deposit
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Bid Settings */}
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-xl font-semibold mb-4">Bid Settings</h2>
            <p className="text-sm text-gray-600 mb-4">
              Set your bid amount per click to improve your grid position. Higher bids mean
              better visibility.
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Bid Per Click ($)
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.25"
                  value={bidAmount}
                  onChange={(e) => setBidAmount(e.target.value)}
                  className="w-full px-4 py-2 border rounded-lg"
                  placeholder="0.00"
                />
                <p className="text-xs text-gray-500 mt-1">
                  You'll be charged this amount each time someone clicks to call you
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Daily Budget Limit (Optional)
                </label>
                <input
                  type="number"
                  min="0"
                  max="1000"
                  step="1"
                  value={dailyBudget}
                  onChange={(e) => setDailyBudget(e.target.value)}
                  className="w-full px-4 py-2 border rounded-lg"
                  placeholder="No limit"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Stop charging after spending this much per day
                </p>
              </div>

              <button
                onClick={handleUpdateBid}
                className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Update Bid Settings
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function BillingLoadingFallback() {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="animate-pulse space-y-8">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="grid grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-64 bg-gray-200 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function BillingPage() {
  return (
    <Suspense fallback={<BillingLoadingFallback />}>
      <BillingPageContent />
    </Suspense>
  );
}
