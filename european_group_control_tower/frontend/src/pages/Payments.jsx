import { useMemo, useState } from 'react';
import { useStore } from '../lib/store.jsx';
import { useNav } from '../lib/nav.jsx';
import { joinData } from '../lib/calc.js';
import { PAYMENT_STATUSES, CURRENCIES } from '../lib/constants.js';
import { fmtDate, fmtNum } from '../lib/format.js';
import { Badge, DataTable, PageHeader, Select, toneFor } from '../components/ui.jsx';

export default function Payments() {
  const { data, remove, notify } = useStore();
  const { edit, ask, openDetail } = useNav();
  const [status, setStatus] = useState('');
  const [cur, setCur] = useState('');
  const all = useMemo(() => joinData(data).filter((r) => r.payment), [data]);
  const rows = useMemo(() => all.filter((r) =>
    (!status || (status === 'Overdue' ? r.pm.overdue : r.pm.status === status)) && (!cur || r.po.currency === cur)), [all, status, cur]);

  const totals = useMemo(() => {
    const t = {};
    rows.forEach((r) => { const c = r.po.currency; t[c] = t[c] || { total: 0, paid: 0, remaining: 0 }; t[c].total += r.pm.total; t[c].paid += r.pm.paid; t[c].remaining += r.pm.remaining; });
    return t;
  }, [rows]);

  const columns = [
    { key: 'po', label: 'PO', get: (r) => r.po.poNumber, render: (r) => <b>{r.po.poNumber}</b> },
    { key: 'supplier', label: 'Supplier', get: (r) => r.supplier?.company || '', render: (r) => <span className="ell">{r.supplier?.company || '-'}</span> },
    { key: 'invoice', label: 'Invoice', get: (r) => r.payment.invoice },
    { key: 'cur', label: 'Cur', get: (r) => r.po.currency },
    { key: 'total', label: 'Total', align: 'right', get: (r) => r.pm.total, render: (r) => fmtNum(r.pm.total, 2) },
    { key: 'paid', label: 'Paid', align: 'right', get: (r) => r.pm.paid, render: (r) => fmtNum(r.pm.paid, 2) },
    { key: 'rem', label: 'Remaining', align: 'right', get: (r) => r.pm.remaining, render: (r) => <b>{fmtNum(r.pm.remaining, 2)}</b> },
    { key: 'due', label: 'Due Date', get: (r) => r.payment.dueDate, render: (r) => fmtDate(r.payment.dueDate) },
    { key: 'paidDate', label: 'Paid Date', get: (r) => r.payment.paidDate, render: (r) => fmtDate(r.payment.paidDate) },
    { key: 'status', label: 'Status', get: (r) => (r.pm.overdue ? 'Overdue' : r.pm.status), render: (r) => <Badge tone={toneFor.pay[r.pm.overdue ? 'Overdue' : r.pm.status]}>{r.pm.overdue ? `Overdue ${r.pm.daysOverdue}d` : r.pm.status}</Badge> },
    { key: 'method', label: 'Method', get: (r) => r.payment.method },
  ];

  return (
    <>
      <PageHeader title="Payments" subtitle="Invoices, paid amounts and balances. Remaining is always calculated as Total − Paid."
        actions={<button className="btn primary" onClick={() => {
          const free = data.pos.filter((p) => !data.payments.some((x) => x.poId === p.id));
          if (!free.length) notify('Every PO already has a payment record.', 'err'); else edit('payment');
        }}>+ New Payment</button>} />
      <div className="kpis small-kpis">
        {Object.entries(totals).map(([c, t]) => (
          <div className="kpi" key={c}><div className="kpi-label">{c} · filtered</div><div className="kpi-sub">Total {fmtNum(t.total)} · Paid {fmtNum(t.paid)}</div><div className="kpi-value">{fmtNum(t.remaining)}</div><div className="kpi-sub">remaining</div></div>
        ))}
      </div>
      <DataTable id="payment-table" title="Payments" exportName="payments" columns={columns} rows={rows} onRowClick={(r) => openDetail(r.po.id)}
        toolbar={<>
          <Select value={status} onChange={setStatus} options={[...PAYMENT_STATUSES, 'Overdue']} all="All statuses" />
          <Select value={cur} onChange={setCur} options={CURRENCIES} all="All currencies" />
        </>}
        rowActions={(r) => (
          <div className="row gap">
            <button className="btn sm" onClick={() => edit('payment', r.payment.id)}>Edit</button>
            <button className="btn sm danger" onClick={() => ask(`Delete the payment record of ${r.po.poNumber}?`, async () => { if (await remove('payments', r.payment.id, `payment ${r.po.poNumber}`)) notify('Payment deleted'); })}>Delete</button>
          </div>
        )} />
    </>
  );
}
