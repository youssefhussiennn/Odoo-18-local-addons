import { useMemo, useState } from 'react';
import { useStore } from '../lib/store.jsx';
import { useNav } from '../lib/nav.jsx';
import { joinData } from '../lib/calc.js';
import { fmtDate } from '../lib/format.js';
import { Badge, DataTable, PageHeader, Select, toneFor } from '../components/ui.jsx';

const URL_RE = /^https?:\/\//i;

export default function Tracking() {
  const { data, upsert, notify } = useStore();
  const { openDetail } = useNav();
  const [scope, setScope] = useState('active');
  const [state, setState] = useState('');
  const all = useMemo(() => joinData(data).filter((r) => r.shipment), [data]);
  const rows = useMemo(() => all.filter((r) => (scope === 'all' || (r.sm.idx >= 1 && r.sm.idx <= 3)) && (!state || r.sm.state === state)), [all, scope, state]);

  // Inline manual editing: tracking URL and current location are saved when the field loses focus.
  const inline = (r, field, placeholder) => (
    <input className="inline" defaultValue={r.shipment[field]} placeholder={placeholder} key={`${r.shipment.id}-${field}-${r.shipment[field]}`}
      onClick={(e) => e.stopPropagation()}
      onBlur={async (e) => {
        const input = e.target;
        const v = input.value.trim();
        if (v === r.shipment[field]) return;
        if (field === 'trackingUrl' && v && !URL_RE.test(v)) { notify('Tracking URL must start with http:// or https://', 'err'); input.value = r.shipment[field]; return; }
        if (await upsert('shipments', { ...r.shipment, [field]: v }, 'shipment tracking')) notify('Saved');
        else input.value = r.shipment[field];
      }} />
  );

  const columns = [
    { key: 'po', label: 'PO', get: (r) => r.po.poNumber, render: (r) => <b>{r.po.poNumber}</b> },
    { key: 'supplier', label: 'Supplier', get: (r) => r.supplier?.company || '', render: (r) => <span className="ell">{r.supplier?.company || '-'}</span> },
    { key: 'carrier', label: 'Carrier', get: (r) => r.shipment.carrier },
    { key: 'tn', label: 'Tracking No.', get: (r) => r.shipment.trackingNumber || r.shipment.container, render: (r) => <span className="mono">{r.shipment.trackingNumber || r.shipment.container || '-'}</span> },
    { key: 'url', label: 'Tracking URL (editable)', get: (r) => r.shipment.trackingUrl, render: (r) => (
      <div className="row gap nowrap">{inline(r, 'trackingUrl', 'https://…')}{r.shipment.trackingUrl && <a className="btn sm" href={r.shipment.trackingUrl} target="_blank" rel="noreferrer" onClick={(e) => e.stopPropagation()}>Track ↗</a>}</div>) },
    { key: 'loc', label: 'Current location (editable)', get: (r) => r.shipment.location, render: (r) => inline(r, 'location', 'e.g. Red Sea') },
    { key: 'stage', label: 'Stage', get: (r) => r.shipment.stage, sortValue: (r) => r.sm.idx, render: (r) => <Badge tone={toneFor.stage[r.shipment.stage]}>{r.shipment.stage}</Badge> },
    { key: 'etd', label: 'ETD', get: (r) => r.shipment.etd, render: (r) => fmtDate(r.shipment.etd) },
    { key: 'eta', label: 'ETA', get: (r) => r.shipment.eta, render: (r) => fmtDate(r.shipment.eta) },
    { key: 'state', label: 'Status', get: (r) => r.sm.state, render: (r) => <Badge tone={toneFor.state[r.sm.state]}>{r.sm.state}</Badge> },
    { key: 'rem', label: 'Days Left', align: 'right', get: (r) => r.sm.daysRemaining ?? '' },
    { key: 'late', label: 'Days Late', align: 'right', get: (r) => r.sm.daysDelayed, render: (r) => (r.sm.daysDelayed ? <b className="red-t">{r.sm.daysDelayed}</b> : '-') },
    { key: 'transit', label: 'In Transit', align: 'right', get: (r) => r.sm.daysInTransit ?? '' },
  ];

  return (
    <>
      <PageHeader title="Tracking" subtitle="Manual tracking links and live schedule maths (no shipping API required)" />
      <DataTable id="tracking-table" title="Shipment Tracking" exportName="tracking" columns={columns} rows={rows} onRowClick={(r) => openDetail(r.po.id)}
        toolbar={<>
          <Select value={scope === 'all' ? 'all' : ''} onChange={(v) => setScope(v || 'active')} all="Active (booked → arrived)" options={[{ value: 'all', label: 'All shipments' }]} />
          <Select value={state} onChange={setState} options={['Delayed', 'Arriving Soon', 'On Schedule', 'Arrived', 'No ETA']} all="All statuses" />
        </>} />
    </>
  );
}
