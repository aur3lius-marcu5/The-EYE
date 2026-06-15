import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Card from '../components/ui/Card';
import StageTimeline from '../components/StageTimeline';

export default function PipelineRun() {
  const { t } = useTranslation();
  const { id } = useParams();
  const navigate = useNavigate();
  const [run, setRun] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/runs/${id}`)
      .then(async r => {
        if (r.ok) setRun(await r.json());
        else setRun(null);
      })
      .catch(() => setRun(null))
      .finally(() => setLoading(false));
  }, [id]);

  const cancelRun = async () => {
    if (!run) return;
    try {
      const r = await fetch(`/api/pipeline/cancel/${run.id || run.pipeline_run_id}`, { method: 'POST' });
      if (r.ok) {
        setRun(prev => ({ ...prev, status: 'cancelled' }));
      }
    } catch (e) {
      console.error('Cancel failed', e);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="font-heading text-gold-500 text-xl uppercase tracking-widest">✠ {t('pipeline.run_detail')}</h1>
        <p className="text-gold-dim italic">{t('common.loading')}</p>
      </div>
    );
  }

  if (!run) {
    return (
      <div className="space-y-6">
        <h1 className="font-heading text-gold-500 text-xl uppercase tracking-widest">✠ {t('pipeline.run_detail')}</h1>
        <p className="text-gold-dim italic">{t('pipeline.run_not_found')}</p>
        <button className="gothic-btn text-sm px-3 py-1.5" onClick={() => navigate('/pipeline')}>
          ← {t('pipeline.back')}
        </button>
      </div>
    );
  }

  const stages = run.stage_results || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <button className="gothic-btn text-xs px-3 py-1.5" onClick={() => navigate('/pipeline')}>
          ← {t('pipeline.back')}
        </button>
        <h1 className="font-heading text-gold-500 text-xl uppercase tracking-widest">✠ {t('pipeline.run_detail')}</h1>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-3">
          <p className="text-gold-dim text-2xs font-mono uppercase">{t('pipeline.run_id')}</p>
          <p className="text-gold-500 font-mono text-sm mt-1">{run.id || run.pipeline_run_id || '-'}</p>
        </Card>
        <Card className="p-3">
          <p className="text-gold-dim text-2xs font-mono uppercase">{t('common.target')}</p>
          <p className="text-parchment font-mono text-sm mt-1">{run.target_name || run.target_id}</p>
        </Card>
        <Card className="p-3">
          <p className="text-gold-dim text-2xs font-mono uppercase">{t('common.profile')}</p>
          <p className="text-parchment font-mono text-sm mt-1">{run.profile_name}</p>
        </Card>
        <Card className="p-3">
          <p className="text-gold-dim text-2xs font-mono uppercase">{t('common.status')}</p>
          <p className="font-mono text-sm mt-1 uppercase tracking-wider"
             style={{ color: run.status === 'completed' ? '#4ade80' : run.status === 'running' ? '#c9952e' : run.status === 'failed' ? '#dc2626' : '#a0a0a0' }}>
            {run.status}
          </p>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-4">
          <h2 className="font-heading text-gold-400 text-sm uppercase tracking-wider mb-4">{t('pipeline.timeline')}</h2>
          <StageTimeline stages={stages} />
        </Card>

        <div className="space-y-4">
          <Card className="p-4">
            <h2 className="font-heading text-gold-400 text-sm uppercase tracking-wider mb-3">{t('pipeline.details')}</h2>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-gold-dim">{t('pipeline.started')}</span>
                <span className="text-parchment/80">{run.started_at ? new Date(run.started_at).toLocaleString() : '-'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gold-dim">{t('pipeline.completed')}</span>
                <span className="text-parchment/80">{run.completed_at ? new Date(run.completed_at).toLocaleString() : '-'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gold-dim">{t('pipeline.total_stages')}</span>
                <span className="text-parchment/80">{stages.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gold-dim">{t('pipeline.completed_stages')}</span>
                <span className="text-green-400">{stages.filter(s => s.status === 'completed').length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gold-dim">{t('pipeline.failed_stages')}</span>
                <span className="text-crimson-400">{stages.filter(s => s.status === 'failed').length}</span>
              </div>
            </div>
          </Card>

          {run.status === 'running' && (
            <Card className="p-4 border-crimson-500/30">
              <div className="flex items-center justify-between">
                <span className="text-crimson-400 font-mono text-xs">{t('pipeline.running_hint')}</span>
                <button className="text-xs px-3 py-1.5 bg-crimson-500/20 border border-crimson-500/40 text-crimson-400 rounded hover:bg-crimson-500/30 transition-colors font-mono" onClick={cancelRun}>
                  {t('pipeline.cancel_run')}
                </button>
              </div>
            </Card>
          )}

          <Card className="p-4">
            <h2 className="font-heading text-gold-400 text-sm uppercase tracking-wider mb-3">{t('pipeline.stages_raw')}</h2>
            <pre className="text-2xs text-parchment/60 font-mono overflow-auto max-h-64">
              {JSON.stringify(stages, null, 2)}
            </pre>
          </Card>
        </div>
      </div>
    </div>
  );
}
