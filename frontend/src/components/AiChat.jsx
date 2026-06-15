import { useState } from 'react';
import { useTranslation } from 'react-i18next';

export default function AiChat() {
  const { t } = useTranslation();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [connected, setConnected] = useState(false);

  const connect = () => {
    const ws = new WebSocket(`ws://${window.location.host}/api/ai/ws/chat`);
    ws.onopen = () => setConnected(true);
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      setMessages((prev) => [...prev, { role: 'assistant', content: data.content }]);
    };
    ws.onclose = () => setConnected(false);
    return ws;
  };

  const handleSend = () => {
    if (!input.trim()) return;
    const msg = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: msg }]);
    const ws = connect();
    ws.onopen = () => ws.send(JSON.stringify({ content: msg }));
  };

  return (
    <div className="gothic-card flex flex-col h-80">
      <h3 className="font-heading text-gold-500 text-sm uppercase tracking-wider mb-3">
        ✠ {t('sanctum.ai_assistant')}
      </h3>
      <div className="flex-1 overflow-y-auto gothic-scrollbar space-y-2 mb-3 text-sm">
        {messages.length === 0 && (
          <p className="text-gold-dim italic">Ask the Oracle...</p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`${m.role === 'user' ? 'text-gold-500' : 'text-parchment'}`}>
            <span className="font-heading text-xs uppercase">{m.role === 'user' ? 'You' : 'Oracle'}:</span>
            <p className="font-body whitespace-pre-wrap">{m.content}</p>
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          className="gothic-input flex-1"
          placeholder={t('common.type_here')}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
        />
        <button className="gothic-btn-primary text-xs px-3" onClick={handleSend}>
          Ask
        </button>
      </div>
    </div>
  );
}
