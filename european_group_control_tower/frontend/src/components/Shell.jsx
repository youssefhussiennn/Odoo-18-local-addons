import logo from '../assets/european-group-logo.jpeg';
import { useNav } from '../lib/nav.jsx';
import { useStore } from '../lib/store.jsx';
import { buildAlerts } from '../lib/alerts.js';
import { useMemo } from 'react';

const NAV = [
  ['dashboard', 'Control Tower', '◈'], ['pos', 'Purchase Orders', '▤'], ['shipments', 'Shipments', '⛴'], ['tracking', 'Tracking', '⌖'],
  ['payments', 'Payments', '$'], ['suppliers', 'Suppliers', '☗'], ['documents', 'Documents', '▣'], ['alerts', 'Alerts', '!'],
  ['reports', 'Reports', '▥'], ['settings', 'Settings', '⚙'],
];

export default function Shell({ children }) {
  const { page, go, menu, setMenu } = useNav();
  const { data, toast, saving } = useStore();
  const alertCount = useMemo(() => buildAlerts(data).filter((a) => a.severity !== 'low').length, [data]);
  const title = NAV.find((n) => n[0] === page)?.[1] || '';

  return (
    <div className="shell">
      <aside className={`sidebar${menu ? ' open' : ''}`}>
        <div className="brand"><img src={logo} alt="European Group" /></div>
        <div className="brand-sub">CONTROL TOWER</div>
        <nav>
          {NAV.map(([key, label, icon]) => (
            <button key={key} className={`nav-item${page === key ? ' active' : ''}`} onClick={() => go(key)}>
              <span className="nav-ic">{icon}</span><span>{label}</span>
              {key === 'alerts' && alertCount > 0 && <span className="pill">{alertCount}</span>}
            </button>
          ))}
        </nav>
        <div className="side-foot">
          <div className="small muted-d">European Group · Shipment Tracker</div>
        </div>
      </aside>
      {menu && <div className="scrim" onClick={() => setMenu(false)} />}
      <div className="main">
        <header className="topbar noprint">
          <button className="hamburger" onClick={() => setMenu(!menu)} aria-label="Menu">☰</button>
          <div className="top-title">{title}</div>
          <div className="spacer" />
          {saving && <span className="muted small">Saving…</span>}
          <span className="muted small hide-sm">{new Date().toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}</span>
        </header>
        <div className="print-brand"><img src={logo} alt="European Group" /><div>EUROPEAN GROUP | CONTROL TOWER</div></div>
        <main className="content">{children}</main>
      </div>
      {toast && <div className={`toast ${toast.type}`}>{toast.msg}</div>}
    </div>
  );
}

