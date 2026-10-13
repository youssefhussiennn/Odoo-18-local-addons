import { useMemo, useState } from 'react';
import { useStore } from '../lib/store.jsx';
import { useNav } from '../lib/nav.jsx';
import { joinData, poTotal, poQuantity, hasAcid } from '../lib/calc.js';
import { STAGES, PAYMENT_STATUSES, CURRENCIES } from '../lib/constants.js';
import { fmtDate, fmtNum } from '../lib/format.js';
import { Badge, DataTable, PageHeader, Select, toneFor } from '../components/ui.jsx';
import ImportModal from '../components/ImportModal.jsx';

export default function POs() {
  const { data, deletePO, notify } = useStore();
  const { edit, ask, openDetail } = useNav();
  const [stage, setStage] = useState('');
  const [supplier, setSupplier] = useState('');
  const [pay, setPay] = useState('');
  const [cur, setCur] = useState('');
  const [rep, setRep] = useState('');
  const [importing, setImporting] = useState(false);

  const all = useMemo(() => joinData(data), [data]);
  const reps = useMemo(() => [...new Set(data.pos.map((p) => p.rep).filter(Boolean))], [data.pos]);
  const rows = useMemo(() => all.filter((r) =>
    (!stage || r.shipment?.stage === stage) && (!supplier || r.po.supplierId === supplier) &&
    (!pay || r.pm?.status === pay) && (!cur || r.po.currency === cur) && (!rep || r.po.rep === rep)), [all, stage, supplier, pay, cur, rep]);

  const columns = [
    { key: 'po', label: 'PO', get: (r) => r.po.poNumber, render: (r) => <b>{r.po.poNumber}</b> },
    { key: 'date', label: 'Date', get: (r) => r.po.poDate, render: (r) => fmtDate(r.po.poDate) },
    { key: 'supplier', label: 'Supplier', get: (r) => r.supplier?.company || '', render: (r) => <span className="ell">{r.supplier?.company || '-'}</span> },
    { key: 'product', label: 'Product', get: (r) => r.po.lines.map((l) => l.product).join(' | '), render: (r) => <span className="ell">{r.po.lines[0]?.product || '-'}{r.po.lines.length > 1 ? ` (+${r.po.lines.length - 1})` : ''}</span> },
    { key: 'category', label: 'Category', get: (r) => r.po.category },
    { key: 'rep', label: 'Rep', get: (r) => r.po.rep },
    { key: 'qty', label: 'Qty', align: 'right', get: (r) => poQuantity(r.po), render: (r) => fmtNum(poQuantity(r.po)) },
    { key: 'cur', label: 'Cur', get: (r) => r.po.currency },
    { key: 'total', label: 'Total', align: 'right', get: (r) => +poTotal(r.po).toFixed(2), render: (r) => fmtNum(poTotal(r.po), 2) },
    { key: 'stage', label: 'Stage', get: (r) => r.shipment?.stage || '', render: (r) => r.shipment ? <Badge tone={toneFor.stage[r.shipment.stage]}>{r.shipment.stage}</Badge> : '-' },
    { key: 'pay', label: 'Payment', get: (r) => r.pm?.status || '', render: (r) => r.pm ? <Badge tone={toneFor.pay[r.pm.status]}>{r.pm.status}</Badge> : '-' },
    { key: 'acid', label: 'ACID', get: (r) => (hasAcid(data, r.shipment || { poId: r.po.id }) ? 'Yes' : 'No'), render: (r) => (hasAcid(data, r.shipment || { poId: r.po.id }) ? <Badge tone="green">Yes</Badge> : <Badge tone="red">No</Badge>) },
  ];

  return (
    <>
      <PageHeader title="Purchase Orders" subtitle="Create, review and track every PO"
        actions={<><button className="btn" onClick={() => setImporting(true)}>Import Excel</button><button className="btn primary" onClick={() => edit('po')}>+ New PO</button></>} />
      <DataTable id="po-table" title="Purchase Orders" exportName="purchase-orders" columns={columns} rows={rows} onRowClick={(r) => openDetail(r.po.id)}
        toolbar={<>
          <Select value={stage} onChange={setStage} options={STAGES} all="All stages" />
          <Select value={supplier} onChange={setSupplier} options={data.suppliers.map((s) => ({ value: s.id, label: s.company.slice(0, 40) }))} all="All suppliers" />
          <Select value={pay} onChange={setPay} options={PAYMENT_STATUSES} all="All payments" />
          <Select value={cur} onChange={setCur} options={CURRENCIES} all="All currencies" />
          <Select value={rep} onChange={setRep} options={reps} all="All reps" />
        </>}
        rowActions={(r) => (
          <div className="row gap">
            <button className="btn sm" onClick={() => openDetail(r.po.id)}>View</button>
            <button className="btn sm" onClick={() => edit('po', r.po.id)}>Edit</button>
            <button className="btn sm danger" onClick={() => ask(`Delete PO ${r.po.poNumber}? Its shipment, payment and documents will also be deleted.`, async () => { if (await deletePO(r.po.id)) notify('PO deleted'); })}>Delete</button>
          </div>
        )} />
      {importing && <ImportModal onClose={() => setImporting(false)} />}
    </>
  );
}
