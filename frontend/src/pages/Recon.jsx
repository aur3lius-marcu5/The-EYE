import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

export default function Recon() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [investigations, setInvestigations] = useState([]);

  useEffect(() => {
    fetch('/api/osint?limit=50').then((r) => r.json()).then(setInvestigations).catch(() => {});
  }, []);

  return (
    <div>
      <h1 className="font-heading text-gold-500 text-xl uppercase tracking-widest mb-6">✠ {t('recon.title')}</h1>
      {investigations.length === 0 ? (
        <p className="text-gold-dim italic">{t('recon.no_results')}</p>
      ) : (
        <div className="gothic-card p-0 overflow-x-auto">
          <table className="gothic-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>{t('common.target')}</th>
                <th>{t('common.status')}</th>
                <th>Module</th>
                <th>Source</th>
                <th>{t('common.date')}</th>
                <th>{t('common.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {investigations.map((inv) => (
                <tr key={inv.id} className="cursor-pointer" onClick={() => navigate(`/recon/${inv.id}`)}>
                  <td className="text-gold-dim">#{inv.id}</td>
                  <td>#{inv.target_id}</td>
                  <td>
                    <span className={`gothic-badge gothic-badge-${inv.status === 'completed' ? 'gold' : inv.status === 'failed' ? 'crimson' : 'gold'}`}>
                      {inv.status}
                    </span>
                  </td>
                  <td className="font-body text-xs">{inv.module}</td>
                  <td className="text-gold-dim text-xs">{inv.source || '-'}</td>
                  <td className="text-gold-dim text-xs">{inv.completed_at ? new Date(inv.completed_at).toLocaleDateString() : '-'}</td>
                  <td>
                    <button
                      className="text-crimson-400 hover:text-crimson-500 text-xs font-heading uppercase tracking-wider"
                      onClick={(e) => { e.stopPropagation(); fetch(`/api/osint/${inv.id}`, { method: 'DELETE' }); setInvestigations((prev) => prev.filter((i) => i.id !== inv.id)); }}
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
