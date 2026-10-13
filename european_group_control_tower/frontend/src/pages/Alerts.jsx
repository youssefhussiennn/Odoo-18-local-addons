import { useMemo, useState } from 'react';
import { useStore } from '../lib/store.jsx';
import { useNav } from '../lib/nav.jsx';
import { buildAlerts, ALERT_TYPES } from '../lib/alerts.js';
import { Badge, DataTable, PageHeader, Select, toneFor } from '../components/ui.jsx';

export default function Alerts() {
  const { data } = useStore();
  const { openDetail } = useNav();
  const [type, setType] = useState('');
  const [sev, setSev] = useState('');
  const all = useMemo(() => buildAlerts(data), [data]);
  const counts = useMemo(() => { const c = {}; all.forEach((a) => { c[a.type] = (c[a.type] || 0) + 1; }); return c; }, [all]);
  const rows = useMemo(() => all.filter((a) => (!type || a.type === type) && (!sev || a.severity === sev)), [all, type, sev]);

  const columns = [
    { key: 'sev', label: 'Severity', get: (r) => r.severity, sortValue: (r) => ({ high: 0, medium: 1, low: 2 }[r.severity]), render: (r) => <Badge tone={toneFor.sev[r.severity]}>{r.severity}</Badge> },
    { key: 'type', label: 'Type', get: (r) => ALERT_TYPES[r.type] },
    { key: 'po', label: 'PO', get: (r) => r.poNumber, render: (r) => <b>{r.poNumber}</b> },
    { key: 'title', label: 'Alert', get: (r) => r.title },
    { key: 'detail', label: 'Detail', get: (r) => r.detail },
  ];

  return (
    <>
      <PageHeader title="Alerts" subtitle="Generated automatically from shipments, payments and documents" />
      <div className="chips noprint">
        {Object.entries(ALERT_TYPES).map(([k, label]) => (
          <button key={k} className={`chip${type === k ? ' on' : ''}`} onClick={() => setType(type === k ? '' : k)}>{label} <b>{counts[k] || 0}</b></button>
        ))}
      </div>
      <DataTable id="alert-table" title="Alerts" exportName="alerts" columns={columns} rows={rows} onRowClick={(r) => openDetail(r.poId)}
        toolbar={<Select value={sev} onChange={setSev} options={['high', 'medium', 'low']} all="All severities" />}
        rowActions={(r) => <button className="btn sm" onClick={() => openDetail(r.poId)}>Open</button>} />
    </>
  );
}
