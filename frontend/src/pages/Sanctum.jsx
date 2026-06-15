import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import StatCard from '../components/StatCard';
import AiChat from '../components/AiChat';

const SCAN_PROFILES = ['quick', 'standard', 'deep', 'stealth'];

export default function Sanctum() {
  const { t } = useTranslation();
  const [stats, setStats] = useState({ scans: 0, recon: 0, cves: 0, reports: 0 });
  const [target, setTarget] = useState('');
  const [profile, setProfile] = useState('standard');
  const [recentScans, setRecentScans] = useState([]);

  useEffect(() => {
    fetch('/api/targets').then((r) => r.ok && r.json()).then((data) => setStats((s) => ({ ...s, targets: data?.length || 0 }))).catch(() => {});
    fetch('/api/scans?limit=5').then((r) => r.ok && r.json()).then((data) => setRecentScans(data || [])).catch(() => {});
    fetch('/api/scans').then((r) => r.ok && r.json()).then((data) => setStats((s) => ({ ...s, scans: data?.length || 0 }))).catch(() => {});
    fetch('/api/correlations/dashboard').then((r) => r.ok && r.json()).then((data) => {
      if (data) {
        setStats((s) => ({ ...s, pipelines: data.total_pipeline_runs || 0, discovered: data.discovered_targets || 0 }));
      }
    }).catch(() => {});
  }, []);

  const handleQuickScan = async () => {
    if (!target.trim()) return;
    const targets = await fetch('/api/targets').then((r) => r.json()).catch(() => []);
    let tid;
    const existing = targets.find((t) => t.ip_range === target || t.domain === target || t.name === target);
    if (existing) {
      tid = existing.id;
    } else {
      const created = await fetch('/api/targets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: target, ip_range: target, domain: target }),
      }).then((r) => r.json()).catch(() => null);
      if (!created) return;
      tid = created.id;
    }
    await fetch('/api/scans', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_id: tid, scan_profile: profile }),
    });
  };

  return (
    <div className="bg-noise">
      <h1 className="font-heading text-gold-500 text-xl uppercase tracking-widest mb-6">𓂀 {t('sanctum.title')}</h1>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <StatCard label={t('sanctum.scans')} value={stats.scans} icon="◎" />
        <StatCard label={t('sanctum.targets')} value={stats.targets || 0} icon="◇" />
        <StatCard label={t('sanctum.pipelines')} value={stats.pipelines || 0} icon="⚙" accent="parchment" />
      </div>
      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard label={t('sanctum.recon')} value={stats.recon || 0} icon="◎" />
        <StatCard label={t('sanctum.cves')} value={stats.cves || 0} icon="◇" accent="crimson" />
        <StatCard label={t('sanctum.discovered')} value={stats.discovered || 0} icon="◈" accent="gold" />
        <StatCard label={t('sanctum.reports')} value={stats.reports || 0} icon="▣" />
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-6">
          <div className="gothic-card">
            <h2 className="font-heading text-gold-500 text-sm uppercase tracking-wider mb-3">✠ {t('sanctum.quick_scan')}</h2>
            <div className="flex gap-3">
              <input
                className="gothic-input flex-1"
                placeholder={t('sanctum.target_placeholder')}
                value={target}
                onChange={(e) => setTarget(e.target.value)}
              />
              <select
                className="gothic-input w-36"
                value={profile}
                onChange={(e) => setProfile(e.target.value)}
              >
                {SCAN_PROFILES.map((p) => (
                  <option key={p} value={p} className="bg-midnight-900">{p}</option>
                ))}
              </select>
              <button className="gothic-btn-primary" onClick={handleQuickScan}>
                {t('sanctum.start_scan')}
              </button>
            </div>
          </div>

          <div className="gothic-card">
            <h2 className="font-heading text-gold-500 text-sm uppercase tracking-wider mb-3">✠ {t('sanctum.recent_vigils')}</h2>
            {recentScans.length === 0 ? (
              <p className="text-gold-dim italic text-sm">No vigils yet. Begin your first scan above.</p>
            ) : (
              <table className="gothic-table">
                <thead>
                  <tr>
                    <th>{t('common.target')}</th>
                    <th>{t('common.status')}</th>
                    <th>{t('common.profile')}</th>
                    <th>{t('common.ports')}</th>
                    <th>{t('common.risk')}</th>
                  </tr>
                </thead>
                <tbody>
                  {recentScans.map((s) => (
                    <tr key={s.id}>
                      <td>#{s.target_id}</td>
                      <td><span className={`gothic-badge gothic-badge-${s.status === 'completed' ? 'gold' : s.status === 'failed' ? 'crimson' : 'gold'}`}>{s.status}</span></td>
                      <td>{s.scan_profile}</td>
                      <td>{s.ports?.length || 0}</td>
                      <td>{s.risk_score ?? '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        <div>
          <AiChat />
        </div>
      </div>
    </div>
  );
}
