// Pure data logic (no browser APIs): flexible column mapping and row -> dataset conversion.
// Merging / replacing / ACID application happens on the Odoo server (models/egct_api.py).
import { IMPORT_FIELDS, STAGES } from './constants.js';
import { str, num, toISODate, slug, normName, normHeader } from './format.js';

export const EMPTY_DATA = { suppliers: [], pos: [], shipments: [], payments: [], documents: [], activity: [] };

// Suggest a header for every known field using exact label / synonym matching.
export function autoMap(headers) {
  const mapping = {};
  const used = new Set();
  for (const f of IMPORT_FIELDS) {
    const cands = [normHeader(f.label), ...f.syn];
    const h = headers.find((x) => !used.has(x) && cands.includes(normHeader(x)));
    if (h) { mapping[f.key] = h; used.add(h); }
  }
  return mapping;
}

export function statusToStage(text) {
  const t = str(text).toLowerCase();
  if (!t) return 'Booked';
  if (/inventor|warehouse|received|delivered|stock/.test(t)) return 'In Inventory';
  if (/cleared|released/.test(t)) return 'Customs Cleared';
  if (/arrived|port|discharg|customs/.test(t)) return 'Arrived Port';
  if (/sea|transit|sail|shipped|on board|departed|vessel/.test(t)) return 'At Sea';
  if (/book/.test(t)) return 'Booked';
  if (/issued|draft|open|new/.test(t)) return 'PO Issued';
  return 'Booked';
}

const first = (rows, get) => { for (const r of rows) { const v = get(r); if (v !== '' && v !== null && v !== undefined) return v; } return ''; };

export function acidMap(rows, mapping) {
  const out = new Map();
  for (const r of rows) {
    const po = str(r[mapping.poNumber]).toUpperCase();
    const acid = str(r[mapping.acid]);
    if (po && acid) out.set(po, acid);
  }
  return out;
}

export function buildDataset(rows, mapping, acid = new Map(), sourceLabel = 'Excel import') {
  const get = (r, k) => (mapping[k] ? r[mapping[k]] : undefined);
  const groups = new Map();
  for (const r of rows) {
    const po = str(get(r, 'poNumber')).toUpperCase();
    if (!po) continue;
    if (!groups.has(po)) groups.set(po, []);
    groups.get(po).push(r);
  }

  const suppliers = new Map();
  const ensureSupplier = (name, country = '') => {
    const key = normName(name);
    if (!key) return '';
    if (!suppliers.has(key)) suppliers.set(key, { id: `s-${slug(key) || suppliers.size}`, company: str(name).replace(/\s+/g, ' '), country: str(country), contact: '', email: '', phone: '', website: '', notes: '' });
    return suppliers.get(key).id;
  };

  const ds = { suppliers: [], pos: [], shipments: [], payments: [], documents: [], activity: [] };
  const addDoc = (poNumber, type, status, reference) =>
    ds.documents.push({ id: `doc-${poNumber}-${slug(type)}`, poId: `po-${poNumber}`, type, status, url: '', expiry: '', reference: str(reference), notes: '' });

  for (const [poNumber, rs] of groups) {
    const lines = rs
      .filter((r) => str(get(r, 'product')) || num(get(r, 'quantity')))
      .map((r) => ({ product: str(get(r, 'product')), qty: num(get(r, 'quantity')), unit: str(get(r, 'unit')), unitPrice: num(get(r, 'unitPrice')) }));
    const f = (k) => first(rs, (r) => get(r, k));
    const stageIdx = Math.max(...rs.map((r) => STAGES.indexOf(statusToStage(get(r, 'status')))));
    const stage = STAGES[stageIdx];
    const notes = [...new Set(rs.map((r) => str(get(r, 'notes'))).filter(Boolean))].join(' · ');
    const currency = str(f('currency')) || 'USD';
    const total = rs.reduce((s, r) => s + (num(get(r, 'total')) || num(get(r, 'quantity')) * num(get(r, 'unitPrice'))), 0);
    const paid = rs.reduce((s, r) => s + num(get(r, 'paid')), 0);
    const acidNo = str(f('acid')) || acid.get(poNumber) || '';

    ds.pos.push({
      id: `po-${poNumber}`, poNumber, poDate: toISODate(f('poDate')), supplierId: ensureSupplier(f('supplier'), f('country')),
      rep: str(f('rep')), category: str(f('category')), currency, lines, notes: '',
    });
    ds.shipments.push({
      id: `sh-${poNumber}`, poId: `po-${poNumber}`, stage, bl: str(f('bl')), booking: str(f('booking')), container: str(f('container')),
      trackingNumber: str(f('tracking')), trackingUrl: str(f('trackingUrl')), carrier: str(f('carrier')), vessel: str(f('vessel')), voyage: str(f('voyage')),
      etd: toISODate(f('etd')), eta: toISODate(f('eta')), actualArrival: toISODate(f('actualArrival')), location: str(f('location')),
      destination: str(f('destination')), registration: str(f('registration')),
      customs: stageIdx >= 4 ? 'Cleared' : /held/i.test(str(f('customs'))) ? 'Held' : stageIdx === 3 ? 'In Progress' : 'Not Started',
      acid: acidNo, notes,
    });
    ds.payments.push({
      id: `pay-${poNumber}`, poId: `po-${poNumber}`, invoice: str(f('invoice')), total: +total.toFixed(2), paid: +paid.toFixed(2),
      dueDate: toISODate(f('paymentDue')), paidDate: '', method: '', notes: '',
    });
    if (str(f('bl'))) addDoc(poNumber, 'Bill of Lading', 'Received', f('bl'));
    if (acidNo) addDoc(poNumber, 'ACID', 'Received', acidNo);
  }

  // ACID numbers whose PO has no shipment line become placeholder POs so no ACID record is lost.
  for (const [poNumber, acidNo] of acid) {
    if (groups.has(poNumber)) continue;
    ds.pos.push({ id: `po-${poNumber}`, poId: undefined, poNumber, poDate: '', supplierId: '', rep: '', category: '', currency: 'USD', lines: [], notes: 'Created from the ACID list - no shipment line found.' });
    ds.shipments.push({ id: `sh-${poNumber}`, poId: `po-${poNumber}`, stage: 'PO Issued', bl: '', booking: '', container: '', trackingNumber: '', trackingUrl: '', carrier: '', vessel: '', voyage: '', etd: '', eta: '', actualArrival: '', location: '', destination: '', registration: '', customs: 'Not Started', acid: acidNo, notes: '' });
    ds.payments.push({ id: `pay-${poNumber}`, poId: `po-${poNumber}`, invoice: '', total: 0, paid: 0, dueDate: '', paidDate: '', method: '', notes: '' });
    addDoc(poNumber, 'ACID', 'Received', acidNo);
  }
  ds.pos.forEach((p) => delete p.poId);
  ds.suppliers = [...suppliers.values()];
  ds.activity = [{ id: `act-${Date.now()}`, ts: new Date().toISOString(), kind: 'system', text: `${sourceLabel}: ${ds.pos.length} POs, ${ds.suppliers.length} suppliers, ${rows.length} lines` }];
  return ds;
}
