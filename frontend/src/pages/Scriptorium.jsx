import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

export default function Scriptorium() {
  const { t } = useTranslation();
  const [reports, setReports] = useState([]);
  const [targets, setTargets] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ target_id: '', report_type: 'technical', format: 'html' });

  useEffect(() => {
    fetch('/api/reports?limit=50').then((r) => r.json()).then(setReports).catch(() => {});
    fetch('/api/targets?limit=100').then((r) => r.json()).then(setTargets).catch(() => {});
  }, []);

  const handleGenerate = async () => {
    await fetch('/api/reports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...form, target_id: parseInt(form.target_id) }),
    });
    setShowModal(false);
    fetch('/api/reports?limit=50').then((r) => r.json()).then(setReports).catch(() => {});
  };

  const handleDelete = async (id) => {
    await fetch(`/api/reports/${id}`, { method: 'DELETE' });
    setReports((prev) => prev.filter((r) => r.id !== id));
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-heading text-gold-500 text-xl uppercase tracking-widest">✠ {t('scriptorium.title')}</h1>
        <button className="gothic-btn-primary text-xs" onClick={() => setShowModal(true)}>
          + {t('scriptorium.generate')}
        </button>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setShowModal(false)}>
          <div className="gothic-card max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-heading text-gold-500 text-sm uppercase tracking-wider mb-4">✠ Generate Report</h3>
            <div className="space-y-3">
              <select className="gothic-input" value={form.target_id} onChange={(e) => setForm((f) => ({ ...f, target_id: e.target.value }))}>
                <option value="" className="bg-midnight-900">Select target...</option>
                {targets.map((t) => (
                  <option key={t.id} value={t.id} className="bg-midnight-900">{t.name}</option>
                ))}
              </select>
              <select className="gothic-input" value={form.report_type} onChange={(e) => setForm((f) => ({ ...f, report_type: e.target.value }))}>
                <option value="technical" className="bg-midnight-900">Technical</option>
                <option value="executive" className="bg-midnight-900">Executive</option>
                <option value="full" className="bg-midnight-900">Full</option>
              </select>
              <select className="gothic-input" value={form.format} onChange={(e) => setForm((f) => ({ ...f, format: e.target.value }))}>
                <option value="html" className="bg-midnight-900">HTML</option>
                <option value="pdf" className="bg-midnight-900">PDF</option>
                <option value="json" className="bg-midnight-900">JSON</option>
                <option value="csv" className="bg-midnight-900">CSV</option>
              </select>
              <div className="flex gap-3 justify-end">
                <button className="gothic-btn" onClick={() => setShowModal(false)}>{t('common.cancel')}</button>
                <button className="gothic-btn-primary" onClick={handleGenerate}>Generate</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {reports.length === 0 ? (
        <p className="text-gold-dim italic">{t('scriptorium.no_reports')}</p>
      ) : (
        <div className="gothic-card p-0 overflow-x-auto">
          <table className="gothic-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Target</th>
                <th>Type</th>
                <th>Format</th>
                <th>{t('common.date')}</th>
                <th>{t('common.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((r) => (
                <tr key={r.id}>
                  <td className="text-gold-dim">#{r.id}</td>
                  <td>#{r.target_id}</td>
                  <td className="font-body text-sm">{r.report_type}</td>
                  <td><span className="gothic-badge gothic-badge-gold">{r.format}</span></td>
                  <td className="text-gold-dim text-xs">{new Date(r.generated_at).toLocaleDateString()}</td>
                  <td>
                    <div className="flex gap-2">
                      <button className="text-gold-500 hover:text-gold-400 text-xs font-heading uppercase"
                        onClick={() => window.open(`/api/reports/${r.id}/download`)}>
                        {t('common.download')}
                      </button>
                      <button className="text-crimson-400 hover:text-crimson-500 text-xs font-heading uppercase"
                        onClick={() => handleDelete(r.id)}>
                        {t('common.delete')}
                      </button>
                    </div>
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
