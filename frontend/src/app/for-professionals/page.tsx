'use client';

import Link from 'next/link';
import {
  Video,
  Users,
  DollarSign,
  TrendingUp,
  Clock,
  Star,
  BarChart3,
  Shield,
  Check,
  ArrowRight,
  Phone,
  Zap,
} from 'lucide-react';

const features = [
  {
    icon: Video,
    title: 'Live Video Presence',
    description:
      'Show borrowers you\'re available with live video streaming. When you\'re busy, your pre-recorded intro plays instead.',
  },
  {
    icon: Zap,
    title: 'Instant Connections',
    description:
      'Borrowers click your card to start a video call immediately. No scheduling, no phone tag, no missed opportunities.',
  },
  {
    icon: BarChart3,
    title: 'Detailed Analytics',
    description:
      'Track your performance with comprehensive analytics. See call volume, ratings, conversion rates, and more.',
  },
  {
    icon: Users,
    title: 'Lead Management',
    description:
      'Built-in CRM to track leads from first call to closing. Never lose track of a prospect again.',
  },
  {
    icon: TrendingUp,
    title: 'Bid for Visibility',
    description:
      'Boost your grid position with strategic bidding. Pay only for impressions that matter to you.',
  },
  {
    icon: Shield,
    title: 'Verified Profiles',
    description:
      'NMLS verification and professional credentials displayed prominently. Build trust before the call.',
  },
];

const plans = [
  {
    name: 'Basic',
    price: 49,
    description: 'Perfect for getting started',
    features: [
      'Grid listing',
      'Up to 50 calls/month',
      'Basic analytics',
      'Email support',
    ],
  },
  {
    name: 'Professional',
    price: 149,
    description: 'Most popular for active professionals',
    features: [
      'Priority grid placement',
      'Unlimited calls',
      'Advanced analytics',
      'Lead management CRM',
      'Custom branding',
      'Priority support',
    ],
    popular: true,
  },
  {
    name: 'Premium',
    price: 299,
    description: 'For high-volume professionals',
    features: [
      'Top grid placement',
      'Unlimited calls',
      'Full analytics suite',
      'Advanced CRM features',
      'API access',
      'Dedicated account manager',
      'White-label options',
    ],
  },
];

const stats = [
  { value: '10,000+', label: 'Monthly Connections' },
  { value: '4.8', label: 'Average Rating' },
  { value: '< 8 sec', label: 'Avg Response Time' },
  { value: '35%', label: 'Conversion Rate' },
];

export default function ForProfessionalsPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-blue-600 to-blue-800 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h1 className="text-4xl md:text-5xl font-bold mb-6">
                Turn Your Availability Into Qualified Leads
              </h1>
              <p className="text-xl text-blue-100 mb-8">
                Join the first real-time lead generation platform built for mortgage professionals.
                Connect with borrowers instantly via video when you&apos;re available.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Link
                  href="/auth/register"
                  className="inline-flex items-center justify-center px-6 py-3 bg-white text-blue-700 font-semibold rounded-lg hover:bg-blue-50 transition"
                >
                  Start Free Trial
                  <ArrowRight className="ml-2 w-5 h-5" />
                </Link>
                <Link
                  href="#pricing"
                  className="inline-flex items-center justify-center px-6 py-3 border-2 border-white text-white font-semibold rounded-lg hover:bg-white/10 transition"
                >
                  View Pricing
                </Link>
              </div>
            </div>
            <div className="relative">
              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
                    <Video className="w-8 h-8" />
                  </div>
                  <div>
                    <p className="font-semibold text-lg">Your Live Video Card</p>
                    <p className="text-blue-200 text-sm">Visible to thousands of borrowers</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div className="bg-white/10 rounded-lg p-4">
                    <Phone className="w-6 h-6 mx-auto mb-2" />
                    <p className="text-2xl font-bold">24</p>
                    <p className="text-xs text-blue-200">Calls This Week</p>
                  </div>
                  <div className="bg-white/10 rounded-lg p-4">
                    <Star className="w-6 h-6 mx-auto mb-2" />
                    <p className="text-2xl font-bold">4.9</p>
                    <p className="text-xs text-blue-200">Average Rating</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-12 bg-gray-50 border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat) => (
              <div key={stat.label} className="text-center">
                <p className="text-3xl md:text-4xl font-bold text-blue-600">{stat.value}</p>
                <p className="text-gray-600 mt-1">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Everything You Need to Succeed
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Our platform gives you the tools to connect with borrowers, manage leads, and grow your business.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature) => (
              <div key={feature.title} className="p-6 bg-white border rounded-xl hover:shadow-lg transition">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-blue-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              How It Works
            </h2>
            <p className="text-xl text-gray-600">
              Get started in minutes and start receiving calls today
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                step: '01',
                title: 'Create Your Profile',
                description: 'Sign up, verify your NMLS, and set up your professional profile with your specialties and service areas.',
              },
              {
                step: '02',
                title: 'Go Live',
                description: 'Turn on your camera and appear in the grid. Borrowers can see you\'re available and ready to help.',
              },
              {
                step: '03',
                title: 'Connect & Convert',
                description: 'Answer video calls instantly, help borrowers with their questions, and convert conversations into leads.',
              },
            ].map((item) => (
              <div key={item.step} className="relative">
                <div className="text-6xl font-bold text-blue-100 absolute -top-4 left-0">{item.step}</div>
                <div className="relative pt-8 pl-4">
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">{item.title}</h3>
                  <p className="text-gray-600">{item.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Simple, Transparent Pricing
            </h2>
            <p className="text-xl text-gray-600">
              Choose the plan that fits your business
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {plans.map((plan) => (
              <div
                key={plan.name}
                className={`relative rounded-2xl border-2 p-8 ${
                  plan.popular ? 'border-blue-600 shadow-xl' : 'border-gray-200'
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-blue-600 text-white px-4 py-1 rounded-full text-sm font-medium">
                    Most Popular
                  </div>
                )}
                <h3 className="text-2xl font-bold text-gray-900">{plan.name}</h3>
                <p className="text-gray-600 mt-1">{plan.description}</p>
                <div className="my-6">
                  <span className="text-4xl font-bold text-gray-900">${plan.price}</span>
                  <span className="text-gray-500">/month</span>
                </div>
                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-2">
                      <Check className="w-5 h-5 text-green-500" />
                      <span className="text-gray-600">{feature}</span>
                    </li>
                  ))}
                </ul>
                <Link
                  href="/auth/register"
                  className={`block w-full text-center py-3 rounded-lg font-semibold transition ${
                    plan.popular
                      ? 'bg-blue-600 text-white hover:bg-blue-700'
                      : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                  }`}
                >
                  Get Started
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-blue-600">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to Grow Your Business?
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Join thousands of mortgage professionals who are already connecting with borrowers on FaceMortgage.
          </p>
          <Link
            href="/auth/register"
            className="inline-flex items-center px-8 py-4 bg-white text-blue-700 font-semibold rounded-lg hover:bg-blue-50 transition text-lg"
          >
            Start Your Free Trial
            <ArrowRight className="ml-2 w-5 h-5" />
          </Link>
          <p className="text-blue-200 mt-4 text-sm">
            No credit card required. 14-day free trial.
          </p>
        </div>
      </section>
    </div>
  );
}
