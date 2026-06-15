import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

const NAV_ITEMS = [
  { path: '/', label: 'nav.sanctum', icon: '◈' },
  { path: '/vigils', label: 'nav.vigils', icon: '◎' },
  { path: '/recon', label: 'nav.recon', icon: '◎' },
  { path: '/targets', label: 'nav.targets', icon: '◇' },
  { path: '/pipeline', label: 'nav.pipeline', icon: '⚙' },
  { path: '/reports', label: 'nav.scriptorium', icon: '▣' },
];

export default function Sidebar() {
  const { t } = useTranslation();

  return (
    <aside className="fixed left-0 top-0 h-screen w-56 bg-midnight-800 border-r border-gold-600/30 flex flex-col z-50">
      <div className="p-4 text-center border-b border-gold-600/30">
        <div className="text-3xl mb-1" style={{ color: '#c9952e' }}>𓂀</div>
        <h1 className="font-display text-gold-500 text-lg tracking-wider">THE EYE</h1>
        <p className="text-gold-dim text-xs italic font-body mt-1">Security Intelligence</p>
      </div>
      <nav className="flex-1 py-4">
        {NAV_ITEMS.map(({ path, label, icon }) => (
          <NavLink
            key={path}
            to={path}
            end={path === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                isActive
                  ? 'text-gold-500 bg-gold-500/10 border-r-2 border-gold-500'
                  : 'text-parchment/60 hover:text-parchment hover:bg-midnight-700'
              }`
            }
          >
            <span className="w-5 text-center">{icon}</span>
            <span className="font-heading tracking-wider text-xs uppercase">{t(label)}</span>
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-gold-600/30 text-center">
        <p className="text-gold-dim text-xs font-body">v1.0.0</p>
      </div>
    </aside>
  );
}
