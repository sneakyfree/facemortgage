'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { apiClient } from '@/lib/api/client';

const STRIPE_PK = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY;
const stripePromise = STRIPE_PK && STRIPE_PK.startsWith('pk_') ? loadStripe(STRIPE_PK) : null;

interface Plan {
    id: string;
    name: string;
    price: number;
    interval: string;
    features: string[];
    popular?: boolean;
}

function CheckoutForm({ selectedPlan }: { selectedPlan: Plan | null }) {
    const stripe = useStripe();
    const elements = useElements();
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!stripe || !elements || !selectedPlan) return;

        setLoading(true);
        setError(null);

        try {
            // Create subscription via backend
            const { data } = await apiClient.post('/billing/create-subscription', {
                plan_id: selectedPlan.id,
            });

            if (data.client_secret) {
                // Confirm payment with Stripe
                const cardElement = elements.getElement(CardElement);
                if (!cardElement) throw new Error('Card element not found');

                const { error: stripeError, paymentIntent } = await stripe.confirmCardPayment(
                    data.client_secret,
                    {
                        payment_method: {
                            card: cardElement,
                        },
                    }
                );

                if (stripeError) {
                    setError(stripeError.message || 'Payment failed');
                } else if (paymentIntent?.status === 'succeeded') {
                    router.push('/checkout?redirect_status=succeeded');
                }
            } else {
                // No payment required (free plan or trial)
                router.push('/dashboard?subscription=active');
            }
        } catch (err: any) {
            console.error('Subscription error:', err);
            setError(err.response?.data?.detail || 'Failed to create subscription. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-6">
            {/* Card input */}
            <div>
                <label htmlFor="card-element" className="block text-sm font-medium text-gray-700 mb-2">
                    Card Details
                </label>
                <div className="p-4 border border-gray-300 rounded-lg bg-white">
                    <CardElement
                        id="card-element"
                        options={{
                            style: {
                                base: {
                                    fontSize: '16px',
                                    color: '#32325d',
                                    fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                                    '::placeholder': {
                                        color: '#9ca3af',
                                    },
                                },
                                invalid: {
                                    color: '#ef4444',
                                    iconColor: '#ef4444',
                                },
                            },
                            hidePostalCode: false,
                        }}
                    />
                </div>
            </div>

            {/* Error display */}
            {error && (
                <div role="alert" className="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex items-start">
                        <svg className="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <div>
                            <p className="text-sm font-medium text-red-800">{error}</p>
                            <p className="mt-1 text-sm text-red-600">Please check your card details and try again.</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Submit button */}
            <button
                type="submit"
                disabled={!stripe || loading || !selectedPlan}
                className="w-full py-4 px-6 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
                {loading ? (
                    <span className="flex items-center justify-center">
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        Processing...
                    </span>
                ) : selectedPlan ? (
                    `Subscribe to ${selectedPlan.name} - $${selectedPlan.price}/${selectedPlan.interval}`
                ) : (
                    'Select a plan to continue'
                )}
            </button>

            {/* Security notice */}
            <p className="text-center text-xs text-gray-500 flex items-center justify-center">
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                Secured by Stripe. Your payment information is encrypted.
            </p>
        </form>
    );
}

export default function SubscribePage() {
    const [plans, setPlans] = useState<Plan[]>([]);
    const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Fetch plans from API
        apiClient.get('/billing/plans')
            .then(({ data }) => {
                setPlans(data.plans || [
                    // Fallback plans if API doesn't return them
                    {
                        id: 'basic',
                        name: 'Basic',
                        price: 99,
                        interval: 'month',
                        features: ['Up to 50 leads/month', 'Standard support', 'Basic analytics'],
                    },
                    {
                        id: 'pro',
                        name: 'Pro',
                        price: 199,
                        interval: 'month',
                        features: ['Unlimited leads', 'Priority support', 'Advanced analytics', 'Custom branding'],
                        popular: true,
                    },
                    {
                        id: 'enterprise',
                        name: 'Enterprise',
                        price: 499,
                        interval: 'month',
                        features: ['Everything in Pro', 'Dedicated account manager', 'API access', 'White-label option'],
                    },
                ]);
            })
            .catch(() => {
                // Use fallback plans on error
                setPlans([
                    { id: 'basic', name: 'Basic', price: 99, interval: 'month', features: ['Up to 50 leads/month'] },
                    { id: 'pro', name: 'Pro', price: 199, interval: 'month', features: ['Unlimited leads'], popular: true },
                    { id: 'enterprise', name: 'Enterprise', price: 499, interval: 'month', features: ['Everything in Pro'] },
                ]);
            })
            .finally(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="animate-pulse space-y-8 max-w-4xl w-full p-6">
                    <div className="h-12 bg-gray-200 rounded w-1/3 mx-auto" />
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="h-64 bg-gray-200 rounded-lg" />
                        ))}
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 py-12 px-4">
            <div className="max-w-5xl mx-auto">
                {/* Header */}
                <div className="text-center mb-12">
                    <h1 className="text-4xl font-bold text-gray-900 mb-4">Choose Your Plan</h1>
                    <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                        Start connecting with borrowers today. All plans include a 14-day free trial.
                    </p>
                </div>

                {/* Plan cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                    {plans.map((plan) => (
                        <div
                            key={plan.id}
                            onClick={() => setSelectedPlan(plan)}
                            className={`relative bg-white rounded-2xl p-6 cursor-pointer transition-all ${selectedPlan?.id === plan.id
                                    ? 'ring-2 ring-blue-600 shadow-lg'
                                    : 'border border-gray-200 hover:shadow-md'
                                }`}
                        >
                            {plan.popular && (
                                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                                    <span className="bg-blue-600 text-white text-xs font-semibold px-3 py-1 rounded-full">
                                        Most Popular
                                    </span>
                                </div>
                            )}

                            <div className="text-center mb-6">
                                <h3 className="text-xl font-semibold text-gray-900 mb-2">{plan.name}</h3>
                                <div className="flex items-baseline justify-center">
                                    <span className="text-4xl font-bold text-gray-900">${plan.price}</span>
                                    <span className="text-gray-500 ml-1">/{plan.interval}</span>
                                </div>
                            </div>

                            <ul className="space-y-3 mb-6">
                                {plan.features.map((feature, idx) => (
                                    <li key={idx} className="flex items-start">
                                        <svg className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                        </svg>
                                        <span className="text-sm text-gray-600">{feature}</span>
                                    </li>
                                ))}
                            </ul>

                            <div
                                className={`w-full py-2 px-4 rounded-lg text-center font-medium ${selectedPlan?.id === plan.id
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-100 text-gray-700'
                                    }`}
                            >
                                {selectedPlan?.id === plan.id ? 'Selected' : 'Select Plan'}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Payment form */}
                {selectedPlan && (
                    <div className="max-w-md mx-auto bg-white rounded-2xl shadow-lg p-8">
                        <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
                            Complete Your Subscription
                        </h2>
                        {stripePromise ? (
                            <Elements stripe={stripePromise}>
                                <CheckoutForm selectedPlan={selectedPlan} />
                            </Elements>
                        ) : (
                            <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900" role="alert">
                                Payments are not configured in this environment. Set <code>NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY</code> to enable checkout.
                            </div>
                        )}
                    </div>
                )}

                {/* FAQ or benefits */}
                <div className="mt-16 text-center">
                    <p className="text-sm text-gray-500">
                        Questions? <a href="/contact" className="text-blue-600 hover:underline">Contact our support team</a>
                    </p>
                    <p className="mt-2 text-xs text-gray-400">
                        Cancel anytime. No hidden fees. 30-day money-back guarantee.
                    </p>
                </div>
            </div>
        </div>
    );
}
