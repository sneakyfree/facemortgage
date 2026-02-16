'use client';
import { useState } from 'react';
import Link from 'next/link';

const FAQ_DATA = [
  { name: "For Borrowers", icon: "🏠", items: [
    { q: "How does FaceMortgage work?", a: "Browse loan officers in our video grid, filter by specialty, and click to start an instant video call. Get face-to-face advice from real professionals without leaving your home." },
    { q: "Is it free for borrowers?", a: "Yes, always free. No sign-up required. Just browse and click to connect with a licensed loan officer." },
    { q: "How do I find the right LO?", a: "Filter by: loan type (FHA, VA, Jumbo, etc.), location, language, specialty. Read reviews and watch their intro videos." },
    { q: "What information should I have ready?", a: "Helpful to have: income info, employment history, desired loan amount, property type. But you can start a conversation without anything." },
  ]},
  { name: "For Loan Officers", icon: "👔", items: [
    { q: "How do I get listed?", a: "Sign up, verify your NMLS license, complete your profile with a short video, choose a plan, and go live. Takes about 10 minutes." },
    { q: "How does pricing work?", a: "Starter ($99/mo): Grid presence, 20 calls/month. Pro ($249/mo): Unlimited calls, priority placement. Enterprise: Custom multi-LO solutions." },
    { q: "What's the lead quality like?", a: "High-intent leads. Borrowers actively looking who chose to click YOUR tile. No cold leads, no forms - real-time conversations." },
    { q: "Do I need special equipment?", a: "Just a webcam, mic, and stable internet (10+ Mbps). Professional lighting recommended but not required." },
  ]},
  { name: "Video Calls", icon: "📹", items: [
    { q: "Are calls recorded?", a: "No. Calls are live only, encrypted end-to-end. No recordings are stored. You may choose to record on your end for compliance." },
    { q: "What if I miss a call?", a: "Borrowers see your 'offline' status and can leave a callback request. You'll be notified to reach out when available." },
    { q: "Can I schedule calls?", a: "Yes! Pro and Enterprise plans include calendar integration. Borrowers can book future appointments." },
    { q: "What about mobile?", a: "Our app works on iOS and Android. Take calls from anywhere with a good connection." },
  ]},
  { name: "Compliance", icon: "⚖️", items: [
    { q: "Is FaceMortgage RESPA compliant?", a: "Yes. No referral fees, no kickbacks. Fair access for all licensed LOs. We don't influence borrower choice." },
    { q: "How is borrower data protected?", a: "GLBA compliant. Encrypted transmission. No data sold. Borrowers consent before each call. You can request data deletion." },
    { q: "Do you verify LO licenses?", a: "Yes. We verify NMLS licenses before activation and monitor for status changes. Suspended/revoked licenses are removed immediately." },
    { q: "What disclosures are required?", a: "Standard mortgage disclosures apply. We provide compliant disclosure templates. You're responsible for your lending compliance." },
  ]},
  { name: "Technical", icon: "🔧", items: [
    { q: "What are the system requirements?", a: "Modern browser (Chrome, Firefox, Safari, Edge), webcam, microphone, 10+ Mbps internet. Works on desktop and mobile." },
    { q: "Why is my video laggy?", a: "Usually bandwidth. Try: closing other apps, using ethernet instead of WiFi, moving closer to router. Our support can help diagnose." },
    { q: "Can I use a virtual background?", a: "Yes, supported in browser. We recommend a professional real background when possible." },
    { q: "Is there an API?", a: "Enterprise plans include API for CRM integration, lead routing, and analytics." },
  ]},
  { name: "Billing", icon: "💳", items: [
    { q: "Can I cancel anytime?", a: "Yes. Monthly plans cancel anytime. No long-term contracts. Your profile stays until end of billing period." },
    { q: "What payment methods?", a: "Credit card, debit card, ACH. Enterprise can use invoice billing." },
    { q: "Is there a free trial?", a: "14-day Pro trial for new LOs. Full features, no credit card required. Convert to paid to keep your placement." },
    { q: "Can I upgrade/downgrade?", a: "Anytime. Upgrades are instant. Downgrades take effect next billing cycle." },
  ]},
];

export default function FAQPage() {
  const [search, setSearch] = useState('');
  const [open, setOpen] = useState<Record<string, boolean>>({});
  const filtered = FAQ_DATA.map(cat => ({ ...cat, items: cat.items.filter(i => i.q.toLowerCase().includes(search.toLowerCase()) || i.a.toLowerCase().includes(search.toLowerCase())) })).filter(c => c.items.length > 0);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl font-bold mb-4">Help Center</h1>
          <p className="text-xl opacity-90 mb-8">24 answers about video mortgage leads</p>
          <input type="text" placeholder="Search..." value={search} onChange={e => setSearch(e.target.value)} className="w-full max-w-md px-6 py-3 rounded-full text-gray-900" />
        </div>
      </div>
      <div className="max-w-4xl mx-auto py-12 px-4">
        {filtered.map((cat, ci) => (
          <div key={cat.name} className="mb-10">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2"><span>{cat.icon}</span>{cat.name}</h2>
            <div className="space-y-3">
              {cat.items.map((faq, fi) => {
                const key = `${ci}-${fi}`;
                return (
                  <div key={key} className="bg-white rounded-lg shadow-sm border overflow-hidden">
                    <button onClick={() => setOpen(p => ({...p, [key]: !p[key]}))} className="w-full p-4 text-left flex justify-between items-center hover:bg-gray-50">
                      <span className="font-medium">{faq.q}</span>
                      <span className={`transition-transform ${open[key] ? 'rotate-180' : ''}`}>▼</span>
                    </button>
                    {open[key] && <div className="px-4 pb-4 text-gray-600 whitespace-pre-line">{faq.a}</div>}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
        <div className="mt-12 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl p-8 text-center text-white">
          <h3 className="text-2xl font-bold mb-2">Still have questions?</h3>
          <Link href="mailto:support@facemortgage.com" className="inline-block mt-4 px-6 py-3 bg-white text-blue-600 rounded-full font-semibold hover:bg-gray-100">Contact Support</Link>
        </div>
      </div>
    </div>
  );
}
