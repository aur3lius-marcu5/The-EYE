export default function StatCard({ label, value, icon, accent = 'gold' }) {
  const accentColors = {
    gold: 'text-gold-500',
    crimson: 'text-crimson-400',
    parchment: 'text-parchment',
  };

  return (
    <div className="gothic-card flex items-center gap-3">
      <span className={`text-2xl ${accentColors[accent] || accentColors.gold}`}>{icon}</span>
      <div>
        <p className="text-gold-dim text-xs font-heading uppercase tracking-wider">{label}</p>
        <p className={`text-2xl font-display ${accentColors[accent] || accentColors.gold}`}>{value}</p>
      </div>
    </div>
  );
}
