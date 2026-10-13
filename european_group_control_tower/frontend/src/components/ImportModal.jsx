import { useState } from 'react';
import { Modal } from './ui.jsx';
import { useStore } from '../lib/store.jsx';
import { IMPORT_FIELDS } from '../lib/constants.js';
import { autoMap, buildDataset, acidMap } from '../lib/importer.js';
import { readWorkbookFile } from '../lib/exporter.js';

// Excel / CSV import with flexible column mapping. kind: 'shipments' (full PO lines) | 'acid' (PO + ACID number).
export default function ImportModal({ onClose, kind = 'shipments' }) {
  const { importDataset, importAcid, notify, user } = useStore();
  const [busy, setBusy] = useState(false);
  const [wb, setWb] = useState(null);
  const [sheet, setSheet] = useState('');
  const [mapping, setMapping] = useState({});
  const [mode, setMode] = useState('merge');
  const [error, setError] = useState('');
  const [fileName, setFileName] = useState('');

  const fields = kind === 'acid' ? IMPORT_FIELDS.filter((f) => ['poNumber', 'acid'].includes(f.key)) : IMPORT_FIELDS;
  const rows = wb ? wb.sheets[sheet] || [] : [];
  const headers = [...new Set(rows.slice(0, 50).flatMap((r) => Object.keys(r)))];

  const pick = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError('');
    try {
      const res = await readWorkbookFile(file);
      const first = res.sheetNames[0];
      setWb(res); setSheet(first); setFileName(file.name);
      setMapping(autoMap([...new Set((res.sheets[first] || []).slice(0, 50).flatMap((r) => Object.keys(r)))]));
    } catch (err) { setError(`Could not read the file: ${err.message}`); }
  };

  const changeSheet = (name) => {
    setSheet(name);
    setMapping(autoMap([...new Set((wb.sheets[name] || []).slice(0, 50).flatMap((r) => Object.keys(r)))]));
  };

  const run = async () => {
    if (!mapping.poNumber) { setError('Map the PO Number column first.'); return; }
    setBusy(true);
    setError('');
    let ok = false;
    if (kind === 'acid') {
      if (!mapping.acid) { setError('Map the ACID column first.'); setBusy(false); return; }
      const map = acidMap(rows, mapping);
      ok = await importAcid(map);
      if (ok) notify(`${map.size} ACID numbers imported`);
    } else {
      const ds = buildDataset(rows, mapping, new Map(), `Excel import ${fileName}`);
      if (!ds.pos.length) { setError('No rows with a PO number were found.'); setBusy(false); return; }
      ok = await importDataset(ds, mode, `Imported ${ds.pos.length} POs from ${fileName}`);
      if (ok) notify(`${ds.pos.length} POs imported (${mode})`);
    }
    setBusy(false);
    if (ok) onClose();
    else setError('The import failed. See the message shown on screen and try again.');
  };

  return (
    <Modal wide title={kind === 'acid' ? 'Import ACID list' : 'Import Purchase Orders & Shipments'} onClose={onClose}
      footer={<>{error && <span className="err">{error}</span>}<div className="spacer" /><button className="btn" onClick={onClose}>Cancel</button><button className="btn primary" disabled={!wb || busy} onClick={run}>{busy ? 'Importing…' : 'Import'}</button></>}>
      <p className="muted">{kind === 'acid' ? 'Choose a file with an order reference and an ACID number column.' : 'Choose an .xlsx / .xls / .csv file. Column names are matched automatically and can be changed below. Rows sharing a PO number become product lines of one PO.'}</p>
      <input type="file" accept=".xlsx,.xls,.csv" onChange={pick} />
      {wb && (
        <>
          <div className="row gap wrap top-gap">
            {wb.sheetNames.length > 1 && <label className="field"><span>Sheet</span><select value={sheet} onChange={(e) => changeSheet(e.target.value)}>{wb.sheetNames.map((n) => <option key={n}>{n}</option>)}</select></label>}
            {kind === 'shipments' && <label className="field"><span>Mode</span><select value={mode} onChange={(e) => setMode(e.target.value)}><option value="merge">Merge (update by PO number, keep other data)</option>{user.isManager && <option value="replace">Replace all data</option>}</select></label>}
            <span className="muted small">{rows.length} rows detected</span>
          </div>
          <div className="scroll map-table">
            <table className="grid compact">
              <thead><tr><th>Field</th><th>Excel column</th><th>Sample</th></tr></thead>
              <tbody>
                {fields.map((f) => (
                  <tr key={f.key}>
                    <td>{f.label}{f.required || (kind === 'acid' && f.key === 'acid') ? ' *' : ''}</td>
                    <td><select value={mapping[f.key] || ''} onChange={(e) => setMapping((m) => ({ ...m, [f.key]: e.target.value }))}><option value="">- not mapped -</option>{headers.map((h) => <option key={h} value={h}>{h}</option>)}</select></td>
                    <td className="ell muted">{mapping[f.key] ? String(rows.find((r) => r[mapping[f.key]] !== null && r[mapping[f.key]] !== undefined)?.[mapping[f.key]] ?? '') : ''}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </Modal>
  );
}
