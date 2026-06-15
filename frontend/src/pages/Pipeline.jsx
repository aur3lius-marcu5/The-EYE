import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Card from '../components/ui/Card';

export default function Pipeline() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [runs, setRuns] = useState([]);
  const [targets, setTargets] = useState([]);
  const [profiles, setProfiles] = useState([]);
  const [selectedTarget, setSelectedTarget] = useState('');
  const [selectedProfile, setSelectedProfile] = useState('domain_standard');
  const [loading, setLoading] = useState(false);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetch('/api/runs'),
      fetch('/api/targets'),
      fetch('/api/pipeline/profiles'),
    ])
      .then(async ([runsRes, targetsRes, profilesRes]) => {
        if (runsRes.ok) {
          const data = await runsRes.json();
          setRuns(Array.isArray(data) ? data : []);
        }
        if (targetsRes.ok) {
          const data = await targetsRes.json();
          setTargets(Array.isArray(data) ? data : []);
        }
        if (profilesRes.ok) {
          const data = await profilesRes.json();
          setProfiles(Array.isArray(data) ? data : []);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const startPipeline = async () => {
    if (!selectedTarget || !selectedProfile) return;
    setStarting(true);
    try {
      const r = await fetch('/api/pipeline/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_id: parseInt(selectedTarget), profile_name: selectedProfile }),
      });
      if (r.ok) {
        const result = await r.json();
        navigate(`/pipeline/${result.pipeline_run_id || result.id || ''}`);
      }
    } catch (e) {
      console.error('Failed to start pipeline', e);
    } finally {
      setStarting(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="font-heading text-gold-500 text-xl uppercase tracking-widest">✠ {t('pipeline.title')}</h1>

      <Card className="p-4">
        <h2 className="font-heading text-gold-400 text-sm uppercase tracking-wider mb-3">{t('pipeline.start_new')}</h2>
        <div className="flex gap-3 items-end flex-wrap">
          <div>
            <label className="block text-gold-dim text-2xs font-mono uppercase mb-1">{t('common.target')}</label>
            <select
              className="bg-midnight-900 border border-gold-600/30 text-parchment text-sm px-3 py-2 rounded w-64 font-mono"
              value={selectedTarget}
              onChange={e => setSelectedTarget(e.target.value)}
            >
              <option value="">{t('pipeline.select_target')}</option>
              {targets.map(tg => (
                <option key={tg.id} value={tg.id}>{tg.name || tg.domain || tg.ip_range}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-gold-dim text-2xs font-mono uppercase mb-1">{t('common.profile')}</label>
            <select
              className="bg-midnight-900 border border-gold-600/30 text-parchment text-sm px-3 py-2 rounded w-48 font-mono"
              value={selectedProfile}
              onChange={e => setSelectedProfile(e.target.value)}
            >
              {profiles.map(p => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>
          <button
            className="gothic-btn text-sm px-4 py-2"
            onClick={startPipeline}
            disabled={starting || !selectedTarget}
          >
            {starting ? t('pipeline.starting') : t('pipeline.run')}
          </button>
        </div>
      </Card>

      <Card className="p-4">
        <h2 className="font-heading text-gold-400 text-sm uppercase tracking-wider mb-3">{t('pipeline.recent_runs')}</h2>
        {loading ? (
          <p className="text-gold-dim italic">{t('common.loading')}</p>
        ) : runs.length === 0 ? (
          <p className="text-gold-dim italic">{t('pipeline.no_runs')}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="text-gold-dim border-b border-gold-600/20">
                  <th className="py-2 pr-4">{t('pipeline.run_id')}</th>
                  <th className="py-2 pr-4">{t('common.target')}</th>
                  <th className="py-2 pr-4">{t('common.profile')}</th>
                  <th className="py-2 pr-4">{t('common.status')}</th>
                  <th className="py-2 pr-4">{t('pipeline.stages')}</th>
                  <th className="py-2">{t('common.date')}</th>
                </tr>
              </thead>
              <tbody>
                {runs.map(run => (
                  <tr
                    key={run.id}
                    className="border-b border-gold-600/10 hover:bg-gold-500/5 cursor-pointer transition-colors"
                    onClick={() => navigate(`/pipeline/${run.id}`)}
                  >
                    <td className="py-2 pr-4 text-gold-500">{run.id}</td>
                    <td className="py-2 pr-4 text-parchment/80">{run.target_name || run.target_id}</td>
                    <td className="py-2 pr-4">{run.profile_name}</td>
                    <td className="py-2 pr-4">
                      <span className={`px-2 py-0.5 rounded text-2xs uppercase tracking-wider ${
                        run.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                        run.status === 'running' ? 'bg-gold-500/20 text-gold-500' :
                        run.status === 'failed' ? 'bg-crimson-500/20 text-crimson-400' :
                        run.status === 'partial' ? 'bg-gold-500/10 text-gold-dim' :
                        'bg-midnight-700 text-parchment/60'
                      }`}>
                        {run.status}
                      </span>
                    </td>
                    <td className="py-2 pr-4 text-parchment/60">
                      {run.stage_results ? (Array.isArray(run.stage_results) ? run.stage_results.length : 0) : 0}
                    </td>
                    <td className="py-2 text-parchment/40">
                      {run.started_at ? new Date(run.started_at).toLocaleString() : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
