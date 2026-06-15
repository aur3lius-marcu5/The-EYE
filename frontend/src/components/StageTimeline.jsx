import { useTranslation } from 'react-i18next';

const STATUS_ICONS = {
  completed: '✓',
  running: '◉',
  failed: '✗',
  skipped: '—',
  pending: '○',
};

const STATUS_COLORS = {
  completed: 'text-green-400 border-green-400/50',
  running: 'text-gold-500 border-gold-500 animate-pulse',
  failed: 'text-crimson-500 border-crimson-500',
  skipped: 'text-gold-dim border-gold-600/30',
  pending: 'text-gold-dim border-gold-600/20',
};

export default function StageTimeline({ stages }) {
  const { t } = useTranslation();
  if (!stages || stages.length === 0) {
    return <p className="text-gold-dim italic">{t('pipeline.no_stages')}</p>;
  }

  return (
    <div className="space-y-0">
      {stages.map((stage, i) => {
        const status = stage.status || 'pending';
        const icon = STATUS_ICONS[status] || '○';
        const color = STATUS_COLORS[status] || 'text-gold-dim border-gold-600/20';
        const connector = i < stages.length - 1;

        const stageId = stage.id?.replace(/_/g, ' ') || 'unknown';
        return (
          <div key={stageId || i} className="flex gap-4">
            <div className="flex flex-col items-center">
              <div className={`w-8 h-8 rounded-full border-2 flex items-center justify-center text-xs font-bold font-mono ${color}`}>
                {icon}
              </div>
              {connector && (
                <div className="w-0.5 flex-1 min-h-[24px] bg-gold-600/20" />
              )}
            </div>
            <div className={`pb-6 ${connector ? '' : ''}`}>
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs uppercase tracking-wider text-parchment/80">
                  {stageId}
                </span>
                {stage.error && (
                  <span className="text-crimson-400 text-xs font-mono truncate max-w-[200px]" title={stage.error}>
                    {stage.error}
                  </span>
                )}
                {stage.findings_count > 0 && (
                  <span className="text-gold-500 text-xs font-mono">
                    {stage.findings_count} {t('pipeline.findings')}
                  </span>
                )}
              </div>
              {stage.completed_at && (
                <p className="text-gold-dim text-2xs font-mono mt-0.5">
                  {new Date(stage.completed_at).toLocaleTimeString()}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
