import { useMemo } from 'react';
import { useStore } from '../lib/store.jsx';
import { useNav } from '../lib/nav.jsx';
import { joinData, poDocuments, poTotal } from '../lib/calc.js';
import { STAGES } from '../lib/constants.js';
import { fmtDate, fmtNum } from '../lib/format.js';
import { Badge, Modal, toneFor } from './ui.jsx';
import { printHtml } from '../lib/print.js';

const TIMELINE = ['PO Created', 'Payment', 'Booking', 'Departed', 'In Transit', 'Arrival', 'Customs', 'Clearance', 'Warehouse', 'Completed'];

// Derives every timeline step from stage, payment and customs data. First unfinished step is "current".
function buildTimeline(sm, shipment, pm) {
  const i = sm.idx;
  const done = [
    true,
    pm?.status === 'Paid',
    i >= 1,
    i >= 2,
    i >= 3,
    i >= 3,
    i >= 4 || shipment.customs === 'Cleared',
    i >= 4,
    i >= 5,
    i >= 5 && pm?.status === 'Paid',
  ];
  const dates = [null, null, null, shipment.etd, null, shipment.actualArrival || (i < 3 ? shipment.eta : ''), null, null, null, null];
  const cur = done.findIndex((d) => !d);
  return TIMELINE.map((label, k) => ({ label, done: done[k], current: k === cur, date: dates[k], hint: k === 1 && pm?.status === 'Partial' ? 'Partially paid' : '' }));
}

const Info = ({ label, children }) => <div className="info"><span>{label}</span><div>{children || '-'}</div></div>;

export default function ShipmentDetail() {
  const { data, upsert, notify } = useStore();
  const { detail, closeDetail, edit } = useNav();
  const row = useMemo(() => joinData(data).find((r) => r.po.id === detail), [data, detail]);
  if (!detail) return null;
  if (!row) return <Modal title="Not found" onClose={closeDetail}><p>This PO no longer exists.</p></Modal>;

  const { po, supplier, shipment: s, payment: p, sm, pm } = row;
  const docs = poDocuments(data, po.id);
  const timeline = s ? buildTimeline(sm, s, pm) : [];
  const next = s ? STAGES[Math.min(STAGES.length - 1, sm.idx + 1)] : '';

  return (
    <Modal wide title={`PO ${po.poNumber}`} onClose={closeDetail}
      footer={<>
        <button className="btn" onClick={(e) => printHtml(`<div class="overlay"><div class="modal wide">${e.currentTarget.closest('.modal').innerHTML}</div></div>`, `PO ${po.poNumber}`)}>Print</button>
        <div className="spacer" />
        <button className="btn" onClick={() => edit('po', po.id)}>Edit PO</button>
        {p ? <button className="btn" onClick={() => edit('payment', p.id)}>Edit payment</button> : <button className="btn" onClick={() => edit('payment', null, { poId: po.id })}>Add payment</button>}
        {s ? <button className="btn" onClick={() => edit('shipment', s.id)}>Edit shipment</button> : <button className="btn" onClick={() => edit('shipment', null, { poId: po.id })}>Add shipment</button>}
        {s && sm.idx < STAGES.length - 1 && (
          <button className="btn primary" onClick={async () => { const ok = await upsert('shipments', { ...s, stage: next, ...(next === 'Arrived Port' && !s.actualArrival ? { actualArrival: new Date().toISOString().slice(0, 10) } : {}), ...(next === 'Customs Cleared' ? { customs: 'Cleared' } : {}) }, 'shipment'); if (ok) notify(`Moved to ${next}`); }}>Advance to {next}</button>
        )}
      </>}>
      <div className="detail-head">
        <div><div className="muted small">Supplier</div><b>{supplier?.company || '-'}</b></div>
        {s && <Badge tone={toneFor.stage[s.stage]}>{s.stage}</Badge>}
        {s && <Badge tone={toneFor.state[sm.state]}>{sm.state}</Badge>}
        {pm && <Badge tone={toneFor.pay[pm.overdue ? 'Overdue' : pm.status]}>{pm.overdue ? 'Payment overdue' : `Payment ${pm.status}`}</Badge>}
      </div>

      {s && (
        <div className="tiles">
          <div className="tile"><span>ETA</span><b>{fmtDate(s.eta)}</b></div>
          <div className={`tile ${sm.delayed ? 'bad' : ''}`}><span>Delay</span><b>{sm.daysDelayed ? `${sm.daysDelayed} days` : 'None'}</b></div>
          <div className="tile"><span>Days remaining</span><b>{sm.daysRemaining ?? '-'}</b></div>
          <div className="tile"><span>Days in transit</span><b>{sm.daysInTransit ?? '-'}</b></div>
          <div className="tile"><span>Current location</span><b>{s.location || '-'}</b></div>
          <div className="tile"><span>Destination port</span><b>{s.destination || '-'}</b></div>
        </div>
      )}

      {s && (
        <>
          <h4 className="sec">Shipment timeline</h4>
          <ol className="timeline">
            {timeline.map((t) => (
              <li key={t.label} className={`${t.done ? 'done' : ''}${t.current ? ' current' : ''}`}>
                <span className="t-dot">{t.done ? '✓' : ''}</span>
                <b>{t.label}</b>
                <small>{t.hint || (t.date ? fmtDate(t.date) : t.done ? 'Done' : t.current ? 'In progress' : 'Pending')}</small>
              </li>
            ))}
          </ol>
          <h4 className="sec">Shipment information</h4>
          <div className="info-grid">
            <Info label="Booking">{s.booking}</Info><Info label="BL number">{s.bl}</Info><Info label="Container">{s.container}</Info>
            <Info label="Tracking number">{s.trackingNumber}</Info>
            <Info label="Tracking URL">{s.trackingUrl ? <a href={s.trackingUrl} target="_blank" rel="noreferrer">Open tracking page ↗</a> : <span className="red-t">Missing</span>}</Info>
            <Info label="Carrier">{s.carrier}</Info><Info label="Vessel">{s.vessel}</Info><Info label="Voyage">{s.voyage}</Info>
            <Info label="ETD">{fmtDate(s.etd)}</Info><Info label="ETA">{fmtDate(s.eta)}</Info><Info label="Actual arrival">{fmtDate(s.actualArrival)}</Info>
            <Info label="Registration">{s.registration}</Info>
            <Info label="Customs"><Badge tone={toneFor.customs[s.customs]}>{s.customs}</Badge></Info>
            <Info label="ACID">{s.acid ? <span className="mono">{s.acid}</span> : <span className="red-t">Missing</span>}</Info>
          </div>
        </>
      )}

      <h4 className="sec">Payment</h4>
      {p ? (
        <div className="info-grid">
          <Info label="Invoice">{p.invoice}</Info><Info label="Total">{po.currency} {fmtNum(pm.total, 2)}</Info><Info label="Paid">{po.currency} {fmtNum(pm.paid, 2)}</Info>
          <Info label="Remaining"><b>{po.currency} {fmtNum(pm.remaining, 2)}</b></Info><Info label="Due date">{fmtDate(p.dueDate)}</Info><Info label="Paid date">{fmtDate(p.paidDate)}</Info>
          <Info label="Method">{p.method}</Info>
        </div>
      ) : <p className="muted">No payment record.</p>}

      <h4 className="sec">Products ({po.lines.length}) · {po.currency} {fmtNum(poTotal(po), 2)}</h4>
      <div className="scroll"><table className="grid compact"><thead><tr><th>Product</th><th className="right">Qty</th><th>Unit</th><th className="right">Unit price</th><th className="right">Amount</th></tr></thead>
        <tbody>{po.lines.map((l, i) => <tr key={i}><td>{l.product || '-'}</td><td className="right">{fmtNum(l.qty)}</td><td>{l.unit || '-'}</td><td className="right">{fmtNum(l.unitPrice, 2)}</td><td className="right">{fmtNum(l.qty * l.unitPrice, 2)}</td></tr>)}</tbody></table></div>

      <h4 className="sec">Documents</h4>
      <div className="scroll"><table className="grid compact"><thead><tr><th>Type</th><th>Status</th><th>Reference</th><th>Link</th><th className="noprint" /></tr></thead>
        <tbody>{docs.map((d) => (
          <tr key={d.type}><td>{d.type}</td><td><Badge tone={toneFor.doc[d.status]}>{d.status}</Badge></td><td className="mono">{d.record?.reference || '-'}</td>
            <td>{d.record?.url ? <a href={d.record.url} target="_blank" rel="noreferrer">Open ↗</a> : '-'}</td>
            <td className="noprint right"><button className="btn sm" onClick={() => edit('document', d.record?.id || null, { poId: po.id, type: d.type, status: d.record ? d.record.status : 'Received' })}>{d.record ? 'Edit' : 'Add'}</button></td></tr>
        ))}</tbody></table></div>

      {(s?.notes || po.notes) && <><h4 className="sec">Notes</h4><p className="notes">{[po.notes, s?.notes].filter(Boolean).join('\n')}</p></>}
    </Modal>
  );
}
