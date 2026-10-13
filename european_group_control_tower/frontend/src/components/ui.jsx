import { useEffect, useMemo, useRef, useState } from 'react';
import { exportCSV, exportWorkbook } from '../lib/exporter.js';
import { printHtml } from '../lib/print.js';

export const toneFor = {
  stage: { 'PO Issued': 'grey', Booked: 'blue', 'At Sea': 'purple', 'Arrived Port': 'amber', 'Customs Cleared': 'teal', 'In Inventory': 'green' },
  state: { Delayed: 'red', 'Arriving Soon': 'amber', 'On Schedule': 'green', Arrived: 'teal', 'No ETA': 'grey' },
  pay: { Paid: 'green', Partial: 'amber', Unpaid: 'red', Overdue: 'red' },
  doc: { Received: 'green', Pending: 'amber', Missing: 'red', Expired: 'red' },
  sev: { high: 'red', medium: 'amber', low: 'blue' },
  customs: { Cleared: 'green', 'In Progress': 'amber', Held: 'red', 'Not Started': 'grey' },
};

export const Badge = ({ tone = 'grey', children }) => <span className={`badge ${tone}`}>{children}</span>;

export function Modal({ title, onClose, children, footer, wide }) {
  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);
  return (
    <div className="overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className={`modal${wide ? ' wide' : ''}`} role="dialog" aria-modal="true">
        <div className="modal-head"><h3>{title}</h3><button className="icon-btn" onClick={onClose} aria-label="Close">✕</button></div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-foot">{footer}</div>}
      </div>
    </div>
  );
}

export const Card = ({ title, actions, children, className = '' }) => (
  <section className={`card ${className}`}>
    {(title || actions) && <div className="card-head"><h4>{title}</h4><div className="row gap">{actions}</div></div>}
    {children}
  </section>
);

export const Kpi = ({ label, value, sub, tone = '', onClick }) => (
  <div className={`kpi ${tone}${onClick ? ' clickable' : ''}`} onClick={onClick}>
    <div className="kpi-label">{label}</div>
    <div className="kpi-value">{value}</div>
    {sub && <div className="kpi-sub">{sub}</div>}
  </div>
);

export const PageHeader = ({ title, subtitle, actions }) => (
  <div className="page-head">
    <div><h2>{title}</h2>{subtitle && <p className="muted">{subtitle}</p>}</div>
    <div className="row gap wrap noprint">{actions}</div>
  </div>
);

export const Empty = ({ children = 'No records found.' }) => <div className="empty">{children}</div>;

export function ConfirmModal({ state, onClose }) {
  if (!state) return null;
  return (
    <Modal title={state.title} onClose={onClose} footer={<>
      <button className="btn" onClick={onClose}>Cancel</button>
      <button className="btn danger" onClick={() => { onClose(); state.onYes(); }}>Confirm</button></>}>
      <p>{state.message}</p>
    </Modal>
  );
}

// Searchable, sortable, paginated table with built-in XLSX / CSV export and print.
// columns: [{ key, label, get(row), render?(row), align?, sortValue?, noExport? }]
export function DataTable({ id, title, columns, rows, onRowClick, rowActions, toolbar, footer, pageSize = 25, searchText, exportName }) {
  const [q, setQ] = useState('');
  const [sort, setSort] = useState({ key: null, dir: 1 });
  const [page, setPage] = useState(0);
  const [printing, setPrinting] = useState(false);
  const wrapRef = useRef(null);

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return rows;
    return rows.filter((r) => {
      const hay = columns.map((c) => String(c.get ? c.get(r) ?? '' : '')).join(' ') + ' ' + (searchText ? searchText(r) : '');
      return hay.toLowerCase().includes(needle);
    });
  }, [rows, q, columns, searchText]);

  const sorted = useMemo(() => {
    if (!sort.key) return filtered;
    const col = columns.find((c) => c.key === sort.key);
    if (!col) return filtered;
    const val = (r) => (col.sortValue ? col.sortValue(r) : col.get(r));
    return [...filtered].sort((a, b) => {
      const x = val(a); const y = val(b);
      if (x === y) return 0;
      if (x === '' || x === null || x === undefined) return 1;
      if (y === '' || y === null || y === undefined) return -1;
      return (typeof x === 'number' && typeof y === 'number' ? x - y : String(x).localeCompare(String(y), undefined, { numeric: true })) * sort.dir;
    });
  }, [filtered, sort, columns]);

  useEffect(() => { setPage(0); }, [q, rows.length]);
  useEffect(() => {
    if (!printing) return undefined;
    // Wait one tick so every row is rendered, then print this table through the hidden iframe.
    const t = setTimeout(() => {
      if (wrapRef.current) printHtml(`<div class="table-wrap">${wrapRef.current.innerHTML}</div>`, title || 'Control Tower');
      setPrinting(false);
    }, 80);
    return () => clearTimeout(t);
  }, [printing, title]);

  const pages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const view = printing ? sorted : sorted.slice(page * pageSize, page * pageSize + pageSize);
  const exportRows = () => sorted.map((r) => Object.fromEntries(columns.filter((c) => !c.noExport).map((c) => [c.label, c.get(r) ?? ''])));
  const base = exportName || id || 'export';
  const stamp = new Date().toISOString().slice(0, 10);

  return (
    <div className="table-wrap" id={id} ref={wrapRef}>
      <div className="table-tools noprint">
        <input className="search" placeholder="Search…" value={q} onChange={(e) => setQ(e.target.value)} />
        {toolbar}
        <div className="spacer" />
        <span className="muted small">{sorted.length} record{sorted.length === 1 ? '' : 's'}</span>
        <button className="btn sm" onClick={() => exportWorkbook({ [title || 'Export']: exportRows() }, `${base}-${stamp}.xlsx`)}>Excel</button>
        <button className="btn sm" onClick={() => exportCSV(exportRows(), `${base}-${stamp}.csv`)}>CSV</button>
        <button className="btn sm" onClick={() => setPrinting(true)}>Print</button>
      </div>
      {title && <div className="print-title">{title} <span>· {new Date().toLocaleDateString('en-GB')}</span></div>}
      <div className="scroll">
        <table className="grid">
          <thead>
            <tr>
              {columns.map((c) => (
                <th key={c.key} className={`${c.align || ''} sortable`} onClick={() => setSort((s) => ({ key: c.key, dir: s.key === c.key ? -s.dir : 1 }))}>
                  {c.label}{sort.key === c.key ? (sort.dir === 1 ? ' ▲' : ' ▼') : ''}
                </th>
              ))}
              {rowActions && <th className="noprint" />}
            </tr>
          </thead>
          <tbody>
            {view.map((r, i) => (
              <tr key={r.id || r.key || i} className={onRowClick ? 'click' : ''} onClick={onRowClick ? () => onRowClick(r) : undefined}>
                {columns.map((c) => <td key={c.key} className={c.align || ''}>{c.render ? c.render(r) : (c.get(r) ?? '') === '' ? '-' : c.get(r)}</td>)}
                {rowActions && <td className="actions noprint" onClick={(e) => e.stopPropagation()}>{rowActions(r)}</td>}
              </tr>
            ))}
            {!view.length && <tr><td colSpan={columns.length + (rowActions ? 1 : 0)}><Empty /></td></tr>}
          </tbody>
          {footer && <tfoot>{footer}</tfoot>}
        </table>
      </div>
      <div className="pager noprint">
        <button className="btn sm" disabled={page === 0} onClick={() => setPage(page - 1)}>← Prev</button>
        <span className="muted small">Page {page + 1} / {pages}</span>
        <button className="btn sm" disabled={page >= pages - 1} onClick={() => setPage(page + 1)}>Next →</button>
      </div>
    </div>
  );
}

export const Select = ({ value, onChange, options, all = 'All', ...rest }) => (
  <select className="filter" value={value} onChange={(e) => onChange(e.target.value)} {...rest}>
    <option value="">{all}</option>
    {options.map((o) => (typeof o === 'string' ? <option key={o} value={o}>{o}</option> : <option key={o.value} value={o.value}>{o.label}</option>))}
  </select>
);

// Schema-driven form. fields: [{ key, label, type: text|number|date|select|textarea|url|email|lines|readonly, options, required, span }]
export function FormModal({ title, fields, initial, onSave, onClose, wide = true, compute }) {
  const [v, setV] = useState(initial);
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);
  const set = (k, val) => setV((s) => ({ ...s, [k]: val }));
  const view = compute ? { ...v, ...compute(v) } : v;

  const submit = async () => {
    if (busy) return;
    const missing = fields.find((f) => f.required && (view[f.key] === '' || view[f.key] === undefined || view[f.key] === null));
    if (missing) { setErr(`${missing.label} is required`); return; }
    const out = { ...v };
    fields.forEach((f) => { if (f.type === 'number') out[f.key] = Number(out[f.key]) || 0; });
    setBusy(true);
    setErr('');
    let res = false;
    try { res = await onSave(out); } finally { setBusy(false); }
    if (res !== false) onClose();
    else setErr('Could not save: check the values and try again.');
  };

  return (
    <Modal title={title} onClose={onClose} wide={wide}
      footer={<>{err && <span className="err">{err}</span>}<div className="spacer" /><button className="btn" onClick={onClose}>Cancel</button><button className="btn primary" onClick={submit} disabled={busy}>{busy ? 'Saving…' : 'Save'}</button></>}>
      <div className="form-grid">
        {fields.map((f) => (
          <label key={f.key} className={`field${f.span === 2 || f.type === 'textarea' || f.type === 'lines' ? ' span2' : ''}`}>
            <span>{f.label}{f.required ? ' *' : ''}</span>
            {f.type === 'select' ? (
              <select value={view[f.key] ?? ''} onChange={(e) => set(f.key, e.target.value)} disabled={f.disabled}>
                {f.allowEmpty !== false && <option value="">-</option>}
                {f.options.map((o) => (typeof o === 'string' ? <option key={o} value={o}>{o}</option> : <option key={o.value} value={o.value}>{o.label}</option>))}
              </select>
            ) : f.type === 'textarea' ? (
              <textarea rows={3} value={view[f.key] ?? ''} onChange={(e) => set(f.key, e.target.value)} />
            ) : f.type === 'readonly' ? (
              <input value={view[f.key] ?? ''} readOnly className="ro" />
            ) : f.type === 'lines' ? (
              <LinesEditor value={view[f.key] || []} onChange={(x) => set(f.key, x)} />
            ) : (
              <input type={f.type === 'number' ? 'number' : f.type || 'text'} step={f.type === 'number' ? 'any' : undefined} value={view[f.key] ?? ''} onChange={(e) => set(f.key, e.target.value)} />
            )}
          </label>
        ))}
      </div>
    </Modal>
  );
}

function LinesEditor({ value, onChange }) {
  const upd = (i, k, val) => onChange(value.map((l, j) => (j === i ? { ...l, [k]: val } : l)));
  const total = value.reduce((s, l) => s + (Number(l.qty) || 0) * (Number(l.unitPrice) || 0), 0);
  return (
    <div className="lines">
      {value.map((l, i) => (
        <div className="line-row" key={i}>
          <input placeholder="Product" value={l.product} onChange={(e) => upd(i, 'product', e.target.value)} />
          <input type="number" placeholder="Qty" value={l.qty} onChange={(e) => upd(i, 'qty', e.target.value)} />
          <input placeholder="Unit" value={l.unit} onChange={(e) => upd(i, 'unit', e.target.value)} />
          <input type="number" step="any" placeholder="Unit price" value={l.unitPrice} onChange={(e) => upd(i, 'unitPrice', e.target.value)} />
          <button type="button" className="icon-btn" onClick={() => onChange(value.filter((_, j) => j !== i))} aria-label="Remove line">✕</button>
        </div>
      ))}
      <div className="row gap">
        <button type="button" className="btn sm" onClick={() => onChange([...value, { product: '', qty: 0, unit: '', unitPrice: 0 }])}>+ Add line</button>
        <span className="muted small">Total: {total.toLocaleString('en-US', { maximumFractionDigits: 2 })}</span>
      </div>
    </div>
  );
}
