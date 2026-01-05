import Link from 'next/link';

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <div className="bg-white shadow-sm rounded-lg p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Terms of Service</h1>

          <div className="prose prose-blue max-w-none">
            <p className="text-gray-600 mb-6">
              <strong>Last Updated:</strong> January 1, 2025
            </p>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">1. Acceptance of Terms</h2>
              <p className="text-gray-600 mb-4">
                By accessing and using FaceMortgage.com (&quot;the Service&quot;), you agree to be bound by these
                Terms of Service. If you do not agree to these terms, please do not use the Service.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">2. Description of Service</h2>
              <p className="text-gray-600 mb-4">
                FaceMortgage.com is a platform that connects borrowers with mortgage professionals
                through real-time video communication. The Service enables borrowers to browse,
                filter, and connect with licensed mortgage professionals including loan officers,
                realtors, title representatives, and attorneys.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">3. User Accounts</h2>
              <p className="text-gray-600 mb-4">
                To use certain features of the Service, you must create an account. You are
                responsible for maintaining the confidentiality of your account credentials and
                for all activities that occur under your account.
              </p>
              <ul className="list-disc list-inside text-gray-600 mb-4 space-y-2">
                <li>You must provide accurate and complete information when creating an account</li>
                <li>You must be at least 18 years old to use the Service</li>
                <li>You are responsible for keeping your password secure</li>
                <li>You must notify us immediately of any unauthorized use of your account</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">4. Professional Requirements</h2>
              <p className="text-gray-600 mb-4">
                Professionals using the Service must maintain valid licenses and certifications
                as required by their respective industries and jurisdictions. This includes but
                is not limited to:
              </p>
              <ul className="list-disc list-inside text-gray-600 mb-4 space-y-2">
                <li>Valid NMLS registration for loan officers</li>
                <li>Active real estate license for realtors</li>
                <li>Bar admission for attorneys</li>
                <li>Appropriate state licensure for all professionals</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">5. Prohibited Conduct</h2>
              <p className="text-gray-600 mb-4">Users may not:</p>
              <ul className="list-disc list-inside text-gray-600 mb-4 space-y-2">
                <li>Violate any applicable laws or regulations</li>
                <li>Impersonate another person or entity</li>
                <li>Provide false or misleading information</li>
                <li>Harass, abuse, or threaten other users</li>
                <li>Attempt to gain unauthorized access to the Service</li>
                <li>Use the Service for any unlawful purpose</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">6. Payment Terms</h2>
              <p className="text-gray-600 mb-4">
                Professional users may be subject to subscription fees and per-lead charges as
                outlined in our pricing. All payments are processed securely through our payment
                processor. Subscription fees are billed in advance and are non-refundable except
                as required by law.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">7. Disclaimer of Warranties</h2>
              <p className="text-gray-600 mb-4">
                THE SERVICE IS PROVIDED &quot;AS IS&quot; WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS
                OR IMPLIED. WE DO NOT GUARANTEE THE ACCURACY, COMPLETENESS, OR RELIABILITY OF
                ANY INFORMATION PROVIDED THROUGH THE SERVICE.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">8. Limitation of Liability</h2>
              <p className="text-gray-600 mb-4">
                TO THE MAXIMUM EXTENT PERMITTED BY LAW, FACEMORTGAGE.COM SHALL NOT BE LIABLE FOR
                ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES ARISING OUT
                OF OR RELATING TO YOUR USE OF THE SERVICE.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">9. Changes to Terms</h2>
              <p className="text-gray-600 mb-4">
                We reserve the right to modify these Terms at any time. We will notify users of
                any material changes via email or through the Service. Your continued use of the
                Service after such changes constitutes acceptance of the new Terms.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">10. Contact Information</h2>
              <p className="text-gray-600 mb-4">
                If you have any questions about these Terms, please contact us at:
              </p>
              <p className="text-gray-600">
                Email: legal@facemortgage.com<br />
                Address: 123 Main Street, Suite 100, City, State 12345
              </p>
            </section>
          </div>

          <div className="mt-8 pt-6 border-t border-gray-200">
            <Link
              href="/"
              className="text-blue-600 hover:text-blue-500 font-medium"
            >
              &larr; Back to Home
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
