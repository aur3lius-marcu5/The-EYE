import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

export default function Vigils() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [scans, setScans] = useState([]);

  useEffect(() => {
    fetch('/api/scans?limit=50').then((r) => r.json()).then(setScans).catch(() => {});
  }, []);

  const handleDelete = async (id) => {
    await fetch(`/api/scans/${id}`, { method: 'DELETE' });
    setScans((prev) => prev.filter((s) => s.id !== id));
  };

  return (
    <div>
      <h1 className="font-heading text-gold-500 text-xl uppercase tracking-widest mb-6">✠ {t('vigils.title')}</h1>
      {scans.length === 0 ? (
        <p className="text-gold-dim italic">{t('vigils.no_results')}</p>
      ) : (
        <div className="gothic-card p-0 overflow-x-auto">
          <table className="gothic-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>{t('common.target')}</th>
                <th>{t('common.status')}</th>
                <th>{t('common.profile')}</th>
                <th>{t('common.ports')}</th>
                <th>{t('common.risk')}</th>
                <th>{t('common.date')}</th>
                <th>{t('common.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {scans.map((s) => (
                <tr key={s.id} className="cursor-pointer" onClick={() => navigate(`/vigils/${s.id}`)}>
                  <td className="text-gold-dim">#{s.id}</td>
                  <td>#{s.target_id}</td>
                  <td>
                    <span className={`gothic-badge gothic-badge-${s.status === 'completed' ? 'gold' : s.status === 'failed' || s.status === 'interrupted' ? 'crimson' : 'gold'}`}>
                      {t(`vigils.status.${s.status}`) || s.status}
                    </span>
                  </td>
                  <td className="font-body">{s.scan_profile}</td>
                  <td>{s.ports?.length || 0}</td>
                  <td className={`${(s.risk_score || 0) >= 50 ? 'text-crimson-400' : 'text-gold-500'}`}>
                    {s.risk_score ?? '-'}
                  </td>
                  <td className="text-gold-dim text-xs">{s.started_at ? new Date(s.started_at).toLocaleDateString() : '-'}</td>
                  <td>
                    <button
                      className="text-crimson-400 hover:text-crimson-500 text-xs font-heading uppercase tracking-wider"
                      onClick={(e) => { e.stopPropagation(); handleDelete(s.id); }}
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
