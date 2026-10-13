import { useMemo, useState } from 'react';
import { useStore } from '../lib/store.jsx';
import { useNav } from '../lib/nav.jsx';
import { joinData, poQuantity } from '../lib/calc.js';
import { STAGES, CUSTOMS_STATUSES, PAYMENT_STATUSES } from '../lib/constants.js';
import { fmtDate, fmtNum } from '../lib/format.js';
import { Badge, DataTable, PageHeader, Select, toneFor } from '../components/ui.jsx';

const STATES = ['Delayed', 'Arriving Soon', 'On Schedule', 'Arrived', 'No ETA'];

export default function Shipments() {
  const { data, remove, notify } = useStore();
  const { edit, ask, openDetail } = useNav();
  const [stage, setStage] = useState('');
  const [state, setState] = useState('');
  const [carrier, setCarrier] = useState('');
  const [customs, setCustoms] = useState('');
  const [pay, setPay] = useState('');

  const all = useMemo(() => joinData(data).filter((r) => r.shipment), [data]);
  const carriers = useMemo(() => [...new Set(data.shipments.map((s) => s.carrier).filter(Boolean))], [data.shipments]);
  const rows = useMemo(() => all.filter((r) =>
    (!stage || r.shipment.stage === stage) && (!state || r.sm.state === state) && (!carrier || r.shipment.carrier === carrier) &&
    (!customs || r.shipment.customs === customs) && (!pay || r.pm?.status === pay)), [all, stage, state, carrier, customs, pay]);

  const columns = [
    { key: 'po', label: 'PO', get: (r) => r.po.poNumber, render: (r) => <b>{r.po.poNumber}</b> },
    { key: 'supplier', label: 'Supplier', get: (r) => r.supplier?.company || '', render: (r) => <span className="ell">{r.supplier?.company || '-'}</span> },
    { key: 'product', label: 'Product', get: (r) => r.po.lines.map((l) => l.product).join(' | '), render: (r) => <span className="ell">{r.po.lines[0]?.product || '-'}{r.po.lines.length > 1 ? ` (+${r.po.lines.length - 1})` : ''}</span> },
    { key: 'qty', label: 'Qty', align: 'right', get: (r) => poQuantity(r.po), render: (r) => fmtNum(poQuantity(r.po)) },
    { key: 'bl', label: 'BL', get: (r) => r.shipment.bl, render: (r) => <span className="mono">{r.shipment.bl || '-'}</span> },
    { key: 'booking', label: 'Booking', get: (r) => r.shipment.booking },
    { key: 'container', label: 'Container', get: (r) => r.shipment.container },
    { key: 'tracking', label: 'Tracking No.', get: (r) => r.shipment.trackingNumber, render: (r) => <span className="mono">{r.shipment.trackingNumber || '-'}</span> },
    { key: 'url', label: 'Tracking URL', get: (r) => r.shipment.trackingUrl, noExport: false, render: (r) => r.shipment.trackingUrl ? <a href={r.shipment.trackingUrl} target="_blank" rel="noreferrer" onClick={(e) => e.stopPropagation()}>Open ↗</a> : '-' },
    { key: 'carrier', label: 'Carrier', get: (r) => r.shipment.carrier },
    { key: 'vessel', label: 'Vessel / Voyage', get: (r) => [r.shipment.vessel, r.shipment.voyage].filter(Boolean).join(' / ') },
    { key: 'etd', label: 'ETD', get: (r) => r.shipment.etd, render: (r) => fmtDate(r.shipment.etd) },
    { key: 'eta', label: 'ETA', get: (r) => r.shipment.eta, render: (r) => fmtDate(r.shipment.eta) },
    { key: 'arr', label: 'Actual Arrival', get: (r) => r.shipment.actualArrival, render: (r) => fmtDate(r.shipment.actualArrival) },
    { key: 'loc', label: 'Location', get: (r) => r.shipment.location },
    { key: 'dest', label: 'Destination', get: (r) => r.shipment.destination },
    { key: 'stage', label: 'Stage', get: (r) => r.shipment.stage, sortValue: (r) => r.sm.idx, render: (r) => <Badge tone={toneFor.stage[r.shipment.stage]}>{r.shipment.stage}</Badge> },
    { key: 'state', label: 'Status', get: (r) => r.sm.state, render: (r) => <Badge tone={toneFor.state[r.sm.state]}>{r.sm.state}</Badge> },
    { key: 'delay', label: 'Days Late', align: 'right', get: (r) => r.sm.daysDelayed, render: (r) => (r.sm.daysDelayed ? <b className="red-t">{r.sm.daysDelayed}</b> : '-') },
    { key: 'remaining', label: 'Days Left', align: 'right', get: (r) => r.sm.daysRemaining ?? '' },
    { key: 'transit', label: 'In Transit', align: 'right', get: (r) => r.sm.daysInTransit ?? '' },
    { key: 'reg', label: 'Registration', get: (r) => r.shipment.registration },
    { key: 'customs', label: 'Customs', get: (r) => r.shipment.customs, render: (r) => <Badge tone={toneFor.customs[r.shipment.customs]}>{r.shipment.customs}</Badge> },
    { key: 'pay', label: 'Payment', get: (r) => r.pm?.status || '', render: (r) => (r.pm ? <Badge tone={toneFor.pay[r.pm.status]}>{r.pm.status}</Badge> : '-') },
    { key: 'acid', label: 'ACID', get: (r) => r.shipment.acid, render: (r) => <span className="mono">{r.shipment.acid || <Badge tone="red">Missing</Badge>}</span> },
    { key: 'notes', label: 'Notes', get: (r) => r.shipment.notes },
  ];

  return (
    <>
      <PageHeader title="Shipments" subtitle="Booking, vessel, tracking, customs and arrival status for every PO"
        actions={<button className="btn primary" onClick={() => {
          const free = data.pos.filter((p) => !data.shipments.some((s) => s.poId === p.id));
          if (!free.length) notify('Every PO already has a shipment. Create a new PO first.', 'err'); else edit('shipment');
        }}>+ New Shipment</button>} />
      <DataTable id="shipment-table" title="Shipments" exportName="shipments" columns={columns} rows={rows} onRowClick={(r) => openDetail(r.po.id)}
        searchText={(r) => `${r.shipment.acid} ${r.shipment.notes}`}
        toolbar={<>
          <Select value={stage} onChange={setStage} options={STAGES} all="All stages" />
          <Select value={state} onChange={setState} options={STATES} all="All statuses" />
          <Select value={carrier} onChange={setCarrier} options={carriers} all="All carriers" />
          <Select value={customs} onChange={setCustoms} options={CUSTOMS_STATUSES} all="All customs" />
          <Select value={pay} onChange={setPay} options={PAYMENT_STATUSES} all="All payments" />
        </>}
        rowActions={(r) => (
          <div className="row gap">
            <button className="btn sm" onClick={() => edit('shipment', r.shipment.id)}>Edit</button>
            <button className="btn sm danger" onClick={() => ask(`Delete the shipment record of ${r.po.poNumber}? The PO itself stays.`, async () => { if (await remove('shipments', r.shipment.id, `shipment ${r.po.poNumber}`)) notify('Shipment deleted'); })}>Delete</button>
          </div>
        )} />
    </>
  );
}
