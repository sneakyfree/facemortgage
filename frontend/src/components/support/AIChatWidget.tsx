'use client';
import { useState, useRef, useEffect } from 'react';

interface ChatMessage { id: string; role: 'user' | 'assistant'; content: string; }
const QUICK_PROMPTS = ["How do video calls work?", "How do I get leads?", "Pricing for LOs", "Privacy and compliance", "Setup requirements", "Best practices"];

export function AIChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => { if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight; }, [messages]);

  const handleSend = (text?: string) => {
    const msg = text || input.trim();
    if (!msg || isLoading) return;
    setMessages(prev => [...prev, { id: `u-${Date.now()}`, role: 'user', content: msg }]);
    setInput('');
    setIsLoading(true);
    setTimeout(() => {
      setMessages(prev => [...prev, { id: `a-${Date.now()}`, role: 'assistant', content: getResponse(msg) }]);
      setIsLoading(false);
    }, 500);
  };

  if (!isOpen) return (
    <button onClick={() => setIsOpen(true)} className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg z-50 flex items-center justify-center hover:scale-105 transition-transform">
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
    </button>
  );

  return (
    <div className="fixed bottom-6 right-6 w-96 h-[500px] bg-white rounded-2xl shadow-2xl flex flex-col z-50 border overflow-hidden">
      <div className="p-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white flex justify-between items-center">
        <div><h3 className="font-semibold">FaceMortgage Support</h3><p className="text-sm opacity-90">Video lead gen help</p></div>
        <button onClick={() => setIsOpen(false)} className="hover:bg-white/20 p-1 rounded"><svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg></button>
      </div>
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
        {messages.length === 0 && (
          <div className="text-center py-4">
            <p className="text-gray-600 mb-4">How can I help with FaceMortgage?</p>
            <div className="flex flex-wrap gap-2 justify-center">
              {QUICK_PROMPTS.map((p, i) => (<button key={i} onClick={() => handleSend(p)} className="px-3 py-1 text-sm bg-white border rounded-full hover:border-blue-400">{p}</button>))}
            </div>
          </div>
        )}
        {messages.map(m => (
          <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] px-4 py-2 rounded-2xl whitespace-pre-line ${m.role === 'user' ? 'bg-blue-600 text-white' : 'bg-white border shadow-sm'}`}>{m.content}</div>
          </div>
        ))}
        {isLoading && <div className="flex justify-start"><div className="bg-white border px-4 py-2 rounded-2xl shadow-sm">Typing...</div></div>}
      </div>
      <div className="p-4 border-t bg-white">
        <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="flex gap-2">
          <input value={input} onChange={e => setInput(e.target.value)} placeholder="Ask about leads..." className="flex-1 px-4 py-2 border rounded-full focus:outline-none focus:border-blue-400" />
          <button type="submit" disabled={isLoading || !input.trim()} className="w-10 h-10 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white disabled:opacity-50 flex items-center justify-center">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
          </button>
        </form>
      </div>
    </div>
  );
}

function getResponse(q: string): string {
  const question = q.toLowerCase();
  if (question.includes('video') || question.includes('call') || question.includes('work')) return "FaceMortgage displays loan officers in a 'Hollywood Squares' style video grid. Borrowers browse, filter by specialty, and click to connect via instant video call. You're always camera-ready for incoming leads.";
  if (question.includes('lead')) return "Leads come directly to you via video:\n• Borrower browses the grid\n• Filters by loan type, location, language\n• Clicks your tile to start a call\n• You answer and close the deal\n\nNo lead forms, no waiting - instant connection.";
  if (question.includes('price') || question.includes('pricing') || question.includes('cost')) return "For Loan Officers:\n• Starter: $99/mo - Grid presence, 20 calls/mo\n• Pro: $249/mo - Unlimited calls, priority placement\n• Enterprise: Custom - Multi-LO, branch features\n\nFor Borrowers: Always free.";
  if (question.includes('privacy') || question.includes('compliance')) return "We're fully RESPA compliant. No kickbacks, fair access for all LOs. Calls are encrypted end-to-end. Borrower data protected per GLBA. Consent captured before each call.";
  if (question.includes('setup') || question.includes('require')) return "Requirements:\n• Webcam & microphone\n• Stable internet (10+ Mbps)\n• NMLS-licensed LO\n• Professional background\n\nSetup takes ~10 minutes.";
  if (question.includes('best') || question.includes('practice')) return "Best practices:\n• Keep camera on during business hours\n• Respond to calls within 3 rings\n• Have loan scenarios ready\n• Professional lighting & background\n• Follow up within 24h";
  return "I can help with: video calls, getting leads, pricing, compliance, setup, or best practices. What would you like to know?";
}

export default AIChatWidget;
