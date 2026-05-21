'use client';

import { useState, useEffect } from 'react';

import { MessageSquare, Bot, Send, X } from 'lucide-react';

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'bot', text: 'Halo! Saya asisten fraud detection. Fitur ini akan segera tersedia.' }
  ]);
  const [input, setInput] = useState('');

    const handleSend = async () => {
    if (!input.trim()) return;
    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);

    // Panggil backend API
    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg })
      });
      
      const data = await response.json();
      setMessages(prev => [...prev, { role: 'bot', text: data.reply || 'Maaf, terjadi kesalahan saat merespons.' }]);
    } catch (error) {
      console.error("Error communicating with AI Agent:", error);
      setMessages(prev => [...prev, { role: 'bot', text: 'Error: Tidak dapat menghubungi server AI Agent. Pastikan backend FastAPI sedang berjalan.' }]);
    }
  };

  return (
    <>
      {/* Floating Action Button */}
      <button className="chat-fab" onClick={() => setOpen(!open)} title="Buka Chat Assistant">
        {open ? <X size={24} /> : <MessageSquare size={24} />}
      </button>

      {/* Chat Panel */}
      {open && (
        <div className="chat-panel">
          <div className="chat-header">
            <span className="chat-header-title" style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, fontWeight: 600 }}>
              <Bot size={18} style={{ color: 'var(--primary)' }} /> Fraud Detection Assistant
            </span>
            <button
              onClick={() => setOpen(false)}
              style={{ background: 'none', border: 'none', color: 'var(--ink)', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
            >
              <X size={18} />
            </button>
          </div>

          <div className="chat-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-bubble ${msg.role}`}>
                {msg.text}
              </div>
            ))}
          </div>

          <div className="chat-input-area">
            <input
              className="chat-input"
              placeholder="Ketik pesan..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            />
            <button className="chat-send" onClick={handleSend}><Send size={16} /></button>
          </div>
        </div>
      )}
    </>
  );
}
