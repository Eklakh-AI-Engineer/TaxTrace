'use client';

import { useState, useRef, useEffect } from 'react';
import { api } from '@/lib/api';
import { Send, Bot, User, CheckCircle2 } from 'lucide-react';

interface ChatMessage {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  timestamp: Date;
}

export default function ChatSimulatorPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'bot',
      text: '🤖 *TaxTrace Bot* — Available commands:\n\n• *help* — Show this menu\n• *show pending tasks* — List your open/overdue tasks\n• *review tasks* — Task summary by status\n• *show deadlines* — Upcoming notice deadlines (next 7 days)\n• *explain mismatch <exception_id>* — Get AI explanation for an exception\n\nType any command to get started.',
      timestamp: new Date(),
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userText = input.trim();
    setInput('');
    
    // Add user message to UI immediately
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      sender: 'user',
      text: userText,
      timestamp: new Date()
    }]);

    setLoading(true);

    try {
      const response = await api.chat.send(userText);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        text: response.reply,
        timestamp: new Date()
      }]);
    } catch {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        text: '❌ Error: Failed to reach the backend.',
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const formatText = (text: string) => {
    // Basic formatting for WhatsApp-style markdown (*bold*, _italic_, etc.)
    // Note: React doesn't natively parse markdown, this is a very simple custom renderer for the simulator
    const formatted = text.replace(/\*(.*?)\*/g, '<strong>$1</strong>');
    return <div dangerouslySetInnerHTML={{ __html: formatted.replace(/\n/g, '<br />') }} />;
  };

  return (
    <div className="flex flex-col h-full bg-slate-50">
      <div className="px-6 py-4 bg-white border-b border-slate-200 flex items-center justify-between shadow-sm z-10">
        <div>
          <h1 className="text-xl font-semibold text-slate-900 flex items-center gap-2">
            <Bot className="w-6 h-6 text-emerald-500" />
            WhatsApp Simulator
          </h1>
          <p className="text-sm text-slate-500">Test bot flows without Meta API credentials</p>
        </div>
        <div className="flex items-center gap-2 text-xs font-medium text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-full border border-emerald-200">
          <CheckCircle2 className="w-4 h-4" /> Webhook Connected
        </div>
      </div>

      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-6 space-y-6"
        style={{ backgroundImage: 'radial-gradient(#e2e8f0 1px, transparent 1px)', backgroundSize: '20px 20px' }}
      >
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[70%] flex gap-3 ${msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.sender === 'user' ? 'bg-indigo-100 text-indigo-600' : 'bg-emerald-100 text-emerald-600'}`}>
                {msg.sender === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
              </div>
              <div className={`px-4 py-3 rounded-2xl shadow-sm text-[15px] leading-relaxed ${
                msg.sender === 'user' 
                  ? 'bg-indigo-600 text-white rounded-tr-sm' 
                  : 'bg-white border border-slate-200 text-slate-800 rounded-tl-sm'
              }`}>
                {formatText(msg.text)}
                <div className={`text-[10px] mt-2 text-right ${msg.sender === 'user' ? 'text-indigo-200' : 'text-slate-400'}`}>
                  {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="max-w-[70%] flex gap-3 flex-row">
              <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-emerald-100 text-emerald-600">
                <Bot className="w-5 h-5" />
              </div>
              <div className="px-4 py-3 rounded-2xl shadow-sm bg-white border border-slate-200 text-slate-400 rounded-tl-sm flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></span>
                <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="p-4 bg-white border-t border-slate-200">
        <form onSubmit={handleSend} className="max-w-4xl mx-auto relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a command (e.g. 'show pending tasks')..."
            className="w-full pl-5 pr-14 py-4 bg-slate-50 border border-slate-200 rounded-full text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all shadow-sm"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="absolute right-2 p-2.5 bg-emerald-500 text-white rounded-full hover:bg-emerald-600 disabled:opacity-50 disabled:hover:bg-emerald-500 transition-colors shadow-sm"
          >
            <Send className="w-5 h-5 ml-0.5" />
          </button>
        </form>
      </div>
    </div>
  );
}
