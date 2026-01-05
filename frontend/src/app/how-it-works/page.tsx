'use client';

import Link from 'next/link';
import {
  Search,
  Video,
  MessageSquare,
  CheckCircle,
  ArrowRight,
  Filter,
  Star,
  Clock,
  Shield,
  Users,
  Phone,
  ThumbsUp,
} from 'lucide-react';

const steps = [
  {
    number: '01',
    title: 'Browse Professionals',
    description:
      'Explore our grid of mortgage professionals available right now. See their live video feeds, ratings, and specialties at a glance.',
    icon: Search,
    color: 'blue',
  },
  {
    number: '02',
    title: 'Filter by Your Needs',
    description:
      'Use filters to find the perfect match. Search by loan type, language, location, specialty, or minimum rating to narrow down your options.',
    icon: Filter,
    color: 'purple',
  },
  {
    number: '03',
    title: 'Click to Connect',
    description:
      'Found someone you like? Just click their card to start an instant video call. No scheduling, no waiting on hold, no phone tag.',
    icon: Video,
    color: 'green',
  },
  {
    number: '04',
    title: 'Get Expert Advice',
    description:
      'Discuss your mortgage needs face-to-face with a real professional. Ask questions, get personalized advice, and build a relationship.',
    icon: MessageSquare,
    color: 'orange',
  },
  {
    number: '05',
    title: 'Rate Your Experience',
    description:
      'After your call, rate your experience to help others find great professionals. Your feedback helps maintain quality on the platform.',
    icon: Star,
    color: 'amber',
  },
];

const benefits = [
  {
    icon: Clock,
    title: 'Save Time',
    description: 'No more phone tag or waiting for callbacks. Connect with professionals instantly.',
  },
  {
    icon: Shield,
    title: 'Verified Professionals',
    description: 'All professionals are NMLS verified with displayed credentials and reviews.',
  },
  {
    icon: Users,
    title: 'Wide Selection',
    description: 'Choose from loan officers, realtors, title reps, and attorneys all in one place.',
  },
  {
    icon: ThumbsUp,
    title: 'Quality Guaranteed',
    description: 'Our rating system ensures you connect with top-rated professionals.',
  },
];

const faqs = [
  {
    question: 'Is this service free for borrowers?',
    answer:
      'Yes! FaceMortgage is completely free for borrowers. You can browse professionals, make calls, and get advice at no cost.',
  },
  {
    question: 'How do I know the professionals are qualified?',
    answer:
      'All mortgage professionals on our platform are NMLS verified. We display their license numbers, ratings, and reviews so you can make informed decisions.',
  },
  {
    question: 'What if the professional I want is busy?',
    answer:
      'If a professional is currently on another call, you\'ll see their pre-recorded introduction video. You can wait for them to become available or connect with another professional.',
  },
  {
    question: 'Do I need to create an account?',
    answer:
      'You can browse the grid without an account, but you\'ll need to sign up (free) to make video calls and save your favorite professionals.',
  },
  {
    question: 'What types of professionals are available?',
    answer:
      'We have loan officers, mortgage brokers, realtors, title representatives, and real estate attorneys. Use our filters to find exactly what you need.',
  },
  {
    question: 'Is my information secure?',
    answer:
      'Yes! All video calls are encrypted, and we never share your personal information without your consent. Read our privacy policy for full details.',
  },
];

export default function HowItWorksPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero */}
      <section className="bg-gradient-to-br from-gray-900 to-gray-800 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-6">
            How FaceMortgage Works
          </h1>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto mb-8">
            Connect with mortgage professionals in real-time via video. It&apos;s simple, fast, and free for borrowers.
          </p>
          <Link
            href="/"
            className="inline-flex items-center px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition"
          >
            Browse Professionals
            <ArrowRight className="ml-2 w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* Steps */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              5 Simple Steps
            </h2>
            <p className="text-xl text-gray-600">
              From browsing to getting expert advice in minutes
            </p>
          </div>

          <div className="space-y-12">
            {steps.map((step, index) => (
              <div
                key={step.number}
                className={`flex flex-col md:flex-row items-center gap-8 ${
                  index % 2 === 1 ? 'md:flex-row-reverse' : ''
                }`}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-4 mb-4">
                    <span className="text-5xl font-bold text-gray-200">{step.number}</span>
                    <div
                      className={`w-14 h-14 rounded-xl flex items-center justify-center ${
                        step.color === 'blue'
                          ? 'bg-blue-100'
                          : step.color === 'purple'
                          ? 'bg-purple-100'
                          : step.color === 'green'
                          ? 'bg-green-100'
                          : step.color === 'orange'
                          ? 'bg-orange-100'
                          : 'bg-amber-100'
                      }`}
                    >
                      <step.icon
                        className={`w-7 h-7 ${
                          step.color === 'blue'
                            ? 'text-blue-600'
                            : step.color === 'purple'
                            ? 'text-purple-600'
                            : step.color === 'green'
                            ? 'text-green-600'
                            : step.color === 'orange'
                            ? 'text-orange-600'
                            : 'text-amber-600'
                        }`}
                      />
                    </div>
                  </div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-3">{step.title}</h3>
                  <p className="text-lg text-gray-600">{step.description}</p>
                </div>
                <div className="flex-1">
                  <div className="bg-gray-100 rounded-2xl aspect-video flex items-center justify-center">
                    <step.icon className="w-24 h-24 text-gray-300" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Why Choose FaceMortgage?
            </h2>
            <p className="text-xl text-gray-600">
              The smarter way to find mortgage professionals
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {benefits.map((benefit) => (
              <div key={benefit.title} className="bg-white rounded-xl border p-6 text-center">
                <div className="w-14 h-14 bg-blue-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <benefit.icon className="w-7 h-7 text-blue-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{benefit.title}</h3>
                <p className="text-gray-600">{benefit.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQs */}
      <section className="py-20">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Frequently Asked Questions
            </h2>
            <p className="text-xl text-gray-600">
              Got questions? We&apos;ve got answers.
            </p>
          </div>

          <div className="space-y-6">
            {faqs.map((faq, index) => (
              <div key={index} className="border-b pb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{faq.question}</h3>
                <p className="text-gray-600">{faq.answer}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-blue-600">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to Get Started?
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Browse our grid of available professionals and connect instantly via video.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/"
              className="inline-flex items-center justify-center px-8 py-4 bg-white text-blue-700 font-semibold rounded-lg hover:bg-blue-50 transition text-lg"
            >
              <Phone className="w-5 h-5 mr-2" />
              Find a Professional
            </Link>
            <Link
              href="/for-professionals"
              className="inline-flex items-center justify-center px-8 py-4 border-2 border-white text-white font-semibold rounded-lg hover:bg-white/10 transition text-lg"
            >
              I&apos;m a Professional
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
