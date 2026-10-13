import { useMemo, useState } from 'react';
import { useStore } from '../lib/store.jsx';
import { useNav } from '../lib/nav.jsx';
import { poDocuments } from '../lib/calc.js';
import { DOC_TYPES, DOC_STATUSES } from '../lib/constants.js';
import { fmtDate } from '../lib/format.js';
import { Badge, DataTable, PageHeader, Select, toneFor } from '../components/ui.jsx';

export default function Documents() {
  const { data, remove, notify } = useStore();
  const { edit, ask } = useNav();
  const [view, setView] = useState('matrix');
  const [type, setType] = useState('');
  const [status, setStatus] = useState('');
  const poNo = useMemo(() => new Map(data.pos.map((p) => [p.id, p.poNumber])), [data.pos]);

  const records = useMemo(() => data.documents.map((d) => ({ ...d, poNumber: poNo.get(d.poId) || '', shown: d.expiry && new Date(d.expiry) < new Date() && d.status !== 'Missing' ? 'Expired' : d.status }))
    .filter((d) => (!type || d.type === type) && (!status || d.shown === status)), [data.documents, poNo, type, status]);

  const matrix = useMemo(() => data.pos.map((po) => ({ id: po.id, poNumber: po.poNumber, docs: poDocuments(data, po.id) }))
    .filter((r) => (!type || r.docs.find((d) => d.type === type)) && (!status || r.docs.some((d) => (!type || d.type === type) && d.status === status))), [data, type, status]);

  const recCols = [
    { key: 'po', label: 'PO', get: (r) => r.poNumber, render: (r) => <b>{r.poNumber}</b> },
    { key: 'type', label: 'Type', get: (r) => r.type },
    { key: 'status', label: 'Status', get: (r) => r.shown, render: (r) => <Badge tone={toneFor.doc[r.shown]}>{r.shown}</Badge> },
    { key: 'ref', label: 'Reference', get: (r) => r.reference, render: (r) => <span className="mono">{r.reference || '-'}</span> },
    { key: 'url', label: 'URL', get: (r) => r.url, render: (r) => (r.url ? <a href={r.url} target="_blank" rel="noreferrer">Open ↗</a> : '-') },
    { key: 'exp', label: 'Expiry', get: (r) => r.expiry, render: (r) => fmtDate(r.expiry) },
    { key: 'notes', label: 'Notes', get: (r) => r.notes },
  ];

  const short = { Received: '✓', Pending: '…', Missing: '✕', Expired: '!' };
  const matCols = [
    { key: 'po', label: 'PO', get: (r) => r.poNumber, render: (r) => <b>{r.poNumber}</b> },
    ...DOC_TYPES.map((t) => ({
      key: t, label: t, align: 'center', get: (r) => r.docs.find((d) => d.type === t).status,
      render: (r) => {
        const d = r.docs.find((x) => x.type === t);
        return <button className={`cell-btn ${toneFor.doc[d.status]}`} title={`${t}: ${d.status} (click to edit)`}
          onClick={() => edit('document', d.record?.id || null, { poId: r.id, type: t, status: d.record ? d.record.status : 'Received' })}>{short[d.status]}</button>;
      },
    })),
  ];

  return (
    <>
      <PageHeader title="Documents" subtitle="Compliance matrix per PO and every recorded document, with links"
        actions={<>
          <div className="seg"><button className={view === 'matrix' ? 'on' : ''} onClick={() => setView('matrix')}>Matrix</button><button className={view === 'records' ? 'on' : ''} onClick={() => setView('records')}>Records</button></div>
          <button className="btn primary" onClick={() => edit('document')}>+ New Document</button></>} />
      <div className="legend noprint">{DOC_STATUSES.map((s) => <span key={s}><i className={`cell-btn ${toneFor.doc[s]}`}>{short[s]}</i> {s}</span>)}</div>
      {view === 'matrix' ? (
        <DataTable id="doc-matrix" title="Document Matrix" exportName="document-matrix" columns={matCols} rows={matrix} pageSize={30}
          toolbar={<><Select value={type} onChange={setType} options={DOC_TYPES} all="All types" /><Select value={status} onChange={setStatus} options={DOC_STATUSES} all="All statuses" /></>} />
      ) : (
        <DataTable id="doc-records" title="Documents" exportName="documents" columns={recCols} rows={records}
          toolbar={<><Select value={type} onChange={setType} options={DOC_TYPES} all="All types" /><Select value={status} onChange={setStatus} options={DOC_STATUSES.filter((s) => s !== 'Missing')} all="All statuses" /></>}
          rowActions={(r) => (
            <div className="row gap">
              <button className="btn sm" onClick={() => edit('document', r.id)}>Edit</button>
              <button className="btn sm danger" onClick={() => ask(`Delete ${r.type} of ${r.poNumber}?`, async () => { if (await remove('documents', r.id, `document ${r.type}`)) notify('Document deleted'); })}>Delete</button>
            </div>
          )} />
      )}
    </>
  );
}
