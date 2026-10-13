import { useMemo, useState } from 'react';
import { useStore } from '../lib/store.jsx';
import { joinData, poTotal, poQuantity, poDocuments } from '../lib/calc.js';
import { DOC_TYPES } from '../lib/constants.js';
import { fmtDate, fmtNum } from '../lib/format.js';
import { Badge, DataTable, PageHeader, toneFor } from '../components/ui.jsx';

const REPORTS = [
  ['po', 'PO Report'], ['shipment', 'Shipment Report'], ['payment', 'Payment Report'], ['supplier', 'Supplier Report'],
  ['documents', 'Documents Report'], ['delays', 'Delay Report'], ['outstanding', 'Outstanding Payments'],
];

export default function Reports() {
  const { data } = useStore();
  const [kind, setKind] = useState('po');
  const joined = useMemo(() => joinData(data), [data]);
  const sup = (r) => r.supplier?.company || '';

  const def = useMemo(() => {
    const c = (key, label, get, extra = {}) => ({ key, label, get, ...extra });
    switch (kind) {
      case 'po':
        return { rows: joined, cols: [c('po', 'PO', (r) => r.po.poNumber), c('date', 'Date', (r) => r.po.poDate), c('sup', 'Supplier', sup), c('rep', 'Rep', (r) => r.po.rep), c('cat', 'Category', (r) => r.po.category), c('cur', 'Cur', (r) => r.po.currency), c('lines', 'Lines', (r) => r.po.lines.length, { align: 'right' }), c('qty', 'Qty', (r) => poQuantity(r.po), { align: 'right' }), c('total', 'Total', (r) => +poTotal(r.po).toFixed(2), { align: 'right', render: (r) => fmtNum(poTotal(r.po), 2) }), c('stage', 'Stage', (r) => r.shipment?.stage || '')] };
      case 'shipment':
        return { rows: joined.filter((r) => r.shipment), cols: [c('po', 'PO', (r) => r.po.poNumber), c('sup', 'Supplier', sup), c('bl', 'BL', (r) => r.shipment.bl), c('cont', 'Container', (r) => r.shipment.container), c('trk', 'Tracking', (r) => r.shipment.trackingNumber), c('car', 'Carrier', (r) => r.shipment.carrier), c('etd', 'ETD', (r) => r.shipment.etd, { render: (r) => fmtDate(r.shipment.etd) }), c('eta', 'ETA', (r) => r.shipment.eta, { render: (r) => fmtDate(r.shipment.eta) }), c('stage', 'Stage', (r) => r.shipment.stage), c('state', 'Status', (r) => r.sm.state), c('late', 'Days Late', (r) => r.sm.daysDelayed, { align: 'right' }), c('cus', 'Customs', (r) => r.shipment.customs), c('acid', 'ACID', (r) => r.shipment.acid)] };
      case 'payment':
        return { rows: joined.filter((r) => r.payment), cols: [c('po', 'PO', (r) => r.po.poNumber), c('sup', 'Supplier', sup), c('inv', 'Invoice', (r) => r.payment.invoice), c('cur', 'Cur', (r) => r.po.currency), c('total', 'Total', (r) => r.pm.total, { align: 'right', render: (r) => fmtNum(r.pm.total, 2) }), c('paid', 'Paid', (r) => r.pm.paid, { align: 'right', render: (r) => fmtNum(r.pm.paid, 2) }), c('rem', 'Remaining', (r) => r.pm.remaining, { align: 'right', render: (r) => fmtNum(r.pm.remaining, 2) }), c('due', 'Due', (r) => r.payment.dueDate, { render: (r) => fmtDate(r.payment.dueDate) }), c('st', 'Status', (r) => (r.pm.overdue ? 'Overdue' : r.pm.status))], totals: true };
      case 'supplier': {
        const rows = data.suppliers.map((s) => { const m = joined.filter((r) => r.po.supplierId === s.id); return { id: s.id, company: s.company, country: s.country, pos: m.length, total: m.reduce((a, r) => a + (r.pm?.total || 0), 0), paid: m.reduce((a, r) => a + (r.pm?.paid || 0), 0), rem: m.reduce((a, r) => a + (r.pm?.remaining || 0), 0), delayed: m.filter((r) => r.sm?.delayed).length }; });
        return { rows, cols: [c('co', 'Company', (r) => r.company), c('ct', 'Country', (r) => r.country), c('pos', 'POs', (r) => r.pos, { align: 'right' }), c('tot', 'Order Value', (r) => +r.total.toFixed(2), { align: 'right', render: (r) => fmtNum(r.total) }), c('paid', 'Paid', (r) => +r.paid.toFixed(2), { align: 'right', render: (r) => fmtNum(r.paid) }), c('rem', 'Outstanding', (r) => +r.rem.toFixed(2), { align: 'right', render: (r) => fmtNum(r.rem) }), c('del', 'Delayed', (r) => r.delayed, { align: 'right' })] };
      }
      case 'documents': {
        const rows = data.pos.map((po) => { const d = poDocuments(data, po.id); return { id: po.id, po: po.poNumber, docs: Object.fromEntries(d.map((x) => [x.type, x.status])), missing: d.filter((x) => x.status === 'Missing').length }; });
        return { rows, cols: [c('po', 'PO', (r) => r.po), ...DOC_TYPES.map((t) => c(t, t, (r) => r.docs[t], { render: (r) => <Badge tone={toneFor.doc[r.docs[t]]}>{r.docs[t]}</Badge> })), c('miss', 'Missing', (r) => r.missing, { align: 'right' })] };
      }
      case 'delays':
        return { rows: joined.filter((r) => r.sm?.delayed).sort((a, b) => b.sm.daysDelayed - a.sm.daysDelayed), cols: [c('po', 'PO', (r) => r.po.poNumber), c('sup', 'Supplier', sup), c('trk', 'Tracking', (r) => r.shipment.trackingNumber), c('car', 'Carrier', (r) => r.shipment.carrier), c('stage', 'Stage', (r) => r.shipment.stage), c('eta', 'ETA', (r) => r.shipment.eta, { render: (r) => fmtDate(r.shipment.eta) }), c('late', 'Days Late', (r) => r.sm.daysDelayed, { align: 'right' }), c('url', 'Tracking URL', (r) => r.shipment.trackingUrl)] };
      default:
        return { rows: joined.filter((r) => r.pm?.remaining > 0).sort((a, b) => b.pm.remaining - a.pm.remaining), cols: [c('po', 'PO', (r) => r.po.poNumber), c('sup', 'Supplier', sup), c('cur', 'Cur', (r) => r.po.currency), c('total', 'Total', (r) => r.pm.total, { align: 'right', render: (r) => fmtNum(r.pm.total, 2) }), c('paid', 'Paid', (r) => r.pm.paid, { align: 'right', render: (r) => fmtNum(r.pm.paid, 2) }), c('rem', 'Remaining', (r) => r.pm.remaining, { align: 'right', render: (r) => <b>{fmtNum(r.pm.remaining, 2)}</b> }), c('due', 'Due', (r) => r.payment.dueDate, { render: (r) => fmtDate(r.payment.dueDate) }), c('st', 'Status', (r) => (r.pm.overdue ? 'Overdue' : r.pm.status))], totals: true };
    }
  }, [kind, joined, data]);

  const footer = useMemo(() => {
    if (!def.totals) return null;
    const t = {};
    def.rows.forEach((r) => { const k = r.po.currency; t[k] = t[k] || { total: 0, paid: 0, rem: 0 }; t[k].total += r.pm.total; t[k].paid += r.pm.paid; t[k].rem += r.pm.remaining; });
    return Object.entries(t).map(([k, v]) => (
      <tr key={k} className="total-row"><td colSpan={3}>Total {k}</td>{kind === 'payment' && <td />}{(<><td className="right">{fmtNum(v.total, 2)}</td><td className="right">{fmtNum(v.paid, 2)}</td><td className="right">{fmtNum(v.rem, 2)}</td><td colSpan={2} /></>)}</tr>
    ));
  }, [def, kind]);

  const label = REPORTS.find((r) => r[0] === kind)[1];
  return (
    <>
      <PageHeader title="Reports" subtitle="Pick a report, then export to Excel / CSV or print it" />
      <div className="chips noprint">{REPORTS.map(([k, l]) => <button key={k} className={`chip${kind === k ? ' on' : ''}`} onClick={() => setKind(k)}>{l}</button>)}</div>
      <DataTable key={kind} id="report-table" title={label} exportName={`report-${kind}`} columns={def.cols} rows={def.rows} footer={footer} pageSize={50} />
    </>
  );
}
