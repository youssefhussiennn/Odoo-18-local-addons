import { useMemo } from 'react';
import { useStore } from '../lib/store.jsx';
import { useNav } from '../lib/nav.jsx';
import { joinData } from '../lib/calc.js';
import { fmtNum } from '../lib/format.js';
import { DataTable, PageHeader } from '../components/ui.jsx';

export default function Suppliers() {
  const { data, remove, notify } = useStore();
  const { edit, ask } = useNav();
  const rows = useMemo(() => {
    const joined = joinData(data);
    return data.suppliers.map((s) => {
      const mine = joined.filter((r) => r.po.supplierId === s.id);
      return { ...s, pos: mine.length, value: mine.reduce((a, r) => a + (r.pm?.total || 0), 0), outstanding: mine.reduce((a, r) => a + (r.pm?.remaining || 0), 0) };
    });
  }, [data]);

  const columns = [
    { key: 'company', label: 'Company', get: (r) => r.company, render: (r) => <b className="ell">{r.company}</b> },
    { key: 'country', label: 'Country', get: (r) => r.country },
    { key: 'contact', label: 'Contact', get: (r) => r.contact },
    { key: 'email', label: 'Email', get: (r) => r.email, render: (r) => (r.email ? <a href={`mailto:${r.email}`}>{r.email}</a> : '-') },
    { key: 'phone', label: 'Phone', get: (r) => r.phone },
    { key: 'website', label: 'Website', get: (r) => r.website, render: (r) => (r.website ? <a href={r.website} target="_blank" rel="noreferrer">{r.website.replace(/^https?:\/\//, '')}</a> : '-') },
    { key: 'pos', label: 'POs', align: 'right', get: (r) => r.pos },
    { key: 'value', label: 'Order Value', align: 'right', get: (r) => +r.value.toFixed(2), render: (r) => fmtNum(r.value) },
    { key: 'out', label: 'Outstanding', align: 'right', get: (r) => +r.outstanding.toFixed(2), render: (r) => fmtNum(r.outstanding) },
    { key: 'notes', label: 'Notes', get: (r) => r.notes },
  ];

  return (
    <>
      <PageHeader title="Suppliers" subtitle="Supplier directory with contacts and exposure" actions={<button className="btn primary" onClick={() => edit('supplier')}>+ New Supplier</button>} />
      <DataTable id="supplier-table" title="Suppliers" exportName="suppliers" columns={columns} rows={rows} onRowClick={(r) => edit('supplier', r.id)}
        rowActions={(r) => (
          <div className="row gap">
            <button className="btn sm" onClick={() => edit('supplier', r.id)}>Edit</button>
            <button className="btn sm danger" onClick={() => {
              if (r.pos) { notify(`${r.company} has ${r.pos} PO(s). Reassign them first.`, 'err'); return; }
              ask(`Delete supplier ${r.company}?`, async () => { if (await remove('suppliers', r.id, `supplier ${r.company}`)) notify('Supplier deleted'); });
            }}>Delete</button>
          </div>
        )} />
    </>
  );
}
