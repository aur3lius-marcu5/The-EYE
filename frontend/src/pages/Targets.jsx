import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Card from '../components/ui/Card';

export default function Targets() {
  const { t } = useTranslation();
  const [targets, setTargets] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', ip_range: '', domain: '', notes: '', tags: '' });

  useEffect(() => {
    fetch('/api/targets?limit=100').then((r) => r.json()).then(setTargets).catch(() => {});
  }, []);

  const handleCreate = async () => {
    const tags = form.tags ? form.tags.split(',').map((t) => t.trim()) : [];
    const r = await fetch('/api/targets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...form, tags }),
    });
    if (r.ok) {
      const created = await r.json();
      setTargets((prev) => [created, ...prev]);
      setShowForm(false);
      setForm({ name: '', ip_range: '', domain: '', notes: '', tags: '' });
    }
  };

  const handleDelete = async (id) => {
    await fetch(`/api/targets/${id}`, { method: 'DELETE' });
    setTargets((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-heading text-gold-500 text-xl uppercase tracking-widest">✠ {t('targets.title')}</h1>
        <button className="gothic-btn-primary text-xs" onClick={() => setShowForm(!showForm)}>
          + {t('targets.add')}
        </button>
      </div>

      {showForm && (
        <div className="gothic-card mb-6 space-y-3 max-w-lg">
          <input className="gothic-input" placeholder="Name *" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
          <input className="gothic-input" placeholder="IP/CIDR" value={form.ip_range} onChange={(e) => setForm((f) => ({ ...f, ip_range: e.target.value }))} />
          <input className="gothic-input" placeholder="Domain" value={form.domain} onChange={(e) => setForm((f) => ({ ...f, domain: e.target.value }))} />
          <input className="gothic-input" placeholder="Tags (comma-separated)" value={form.tags} onChange={(e) => setForm((f) => ({ ...f, tags: e.target.value }))} />
          <textarea className="gothic-input" placeholder="Notes" rows={2} value={form.notes} onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))} />
          <button className="gothic-btn-primary" onClick={handleCreate}>Save Target</button>
        </div>
      )}

      {targets.length === 0 ? (
        <p className="text-gold-dim italic">{t('targets.no_targets')}</p>
      ) : (
        <div className="gothic-card p-0 overflow-x-auto">
          <table className="gothic-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>{t('common.target')}</th>
                <th>IP/CIDR</th>
                <th>Domain</th>
                <th>Tags</th>
                <th>{t('common.date')}</th>
                <th>{t('common.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {targets.map((t) => (
                <tr key={t.id}>
                  <td className="text-gold-dim">#{t.id}</td>
                  <td className="font-body">{t.name}</td>
                  <td className="font-mono text-xs">{t.ip_range || '-'}</td>
                  <td className="text-gold-dim text-xs">{t.domain || '-'}</td>
                  <td>
                    <div className="flex gap-1 flex-wrap">
                      {(t.tags || []).map((tag, i) => (
                        <span key={i} className="gothic-badge gothic-badge-gold text-xs">{tag}</span>
                      ))}
                    </div>
                  </td>
                  <td className="text-gold-dim text-xs">{new Date(t.created_at).toLocaleDateString()}</td>
                  <td>
                    <button
                      className="text-crimson-400 hover:text-crimson-500 text-xs font-heading uppercase tracking-wider"
                      onClick={() => handleDelete(t.id)}
                    >
                      {t('common.delete')}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
