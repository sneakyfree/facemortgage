export const metadata = {
  title: "Contact — FaceMortgage",
  description: "Get in touch with the FaceMortgage support team.",
};

export default function ContactPage() {
  return (
    <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
      <h1 className="text-4xl font-bold text-gray-900 mb-4">Contact Us</h1>
      <p className="text-lg text-gray-600 mb-8">
        Questions, feedback, or need help? Reach out and we will respond within one business day.
      </p>
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4">
        <div>
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-1">Email</h2>
          <a href="mailto:support@facemortgage.com" className="text-blue-600 hover:underline">
            support@facemortgage.com
          </a>
        </div>
        <div>
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-1">Press</h2>
          <a href="mailto:press@facemortgage.com" className="text-blue-600 hover:underline">
            press@facemortgage.com
          </a>
        </div>
        <div>
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-1">Mail</h2>
          <p className="text-gray-700">FaceMortgage, Inc. — Customer Care</p>
        </div>
      </div>
    </main>
  );
}
