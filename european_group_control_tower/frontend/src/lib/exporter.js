import * as XLSX from 'xlsx';
import { shipmentMetrics, paymentMetrics } from './calc.js';

export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function exportWorkbook(sheets, filename) {
  const wb = XLSX.utils.book_new();
  Object.entries(sheets).forEach(([name, rows]) => {
    const ws = XLSX.utils.json_to_sheet(rows.length ? rows : [{}]);
    XLSX.utils.book_append_sheet(wb, ws, name.slice(0, 31));
  });
  XLSX.writeFile(wb, filename);
}

export function exportCSV(rows, filename) {
  const ws = XLSX.utils.json_to_sheet(rows);
  const csv = '\uFEFF' + XLSX.utils.sheet_to_csv(ws);
  downloadBlob(new Blob([csv], { type: 'text/csv;charset=utf-8' }), filename);
}

// Reads the first sheet (or every sheet) of an uploaded workbook as arrays of header-keyed objects.
export async function readWorkbookFile(file) {
  const buf = await file.arrayBuffer();
  const wb = XLSX.read(buf, { type: 'array', cellDates: true });
  const sheets = {};
  wb.SheetNames.forEach((n) => { sheets[n] = XLSX.utils.sheet_to_json(wb.Sheets[n], { defval: null, raw: true }); });
  return { sheetNames: wb.SheetNames, sheets };
}

// One row per PO line, using the same headers as the original Excel file (re-importable).
export function flatRows(data) {
  const sup = new Map(data.suppliers.map((s) => [s.id, s]));
  const sh = new Map(data.shipments.map((s) => [s.poId, s]));
  const pay = new Map(data.payments.map((p) => [p.poId, p]));
  const rows = [];
  data.pos.forEach((po) => {
    const s = sh.get(po.id) || {};
    const p = pay.get(po.id) || {};
    const pm = paymentMetrics(p);
    const lines = po.lines.length ? po.lines : [{ product: '', qty: 0, unit: '', unitPrice: 0 }];
    lines.forEach((l, i) => rows.push({
      'PO Number': po.poNumber, 'PO Date': po.poDate, Supplier: sup.get(po.supplierId)?.company || '', Product: l.product, Category: po.category,
      'Purchase Rep.': po.rep, Quantity: l.qty, Unit: l.unit, 'Unit Price': l.unitPrice, Invoice: p.invoice || '', 'BL Number': s.bl || '', ACID: s.acid || '',
      Booking: s.booking || '', Container: s.container || '', Tracking: s.trackingNumber || '', 'Shipping Line': s.carrier || '', Vessel: s.vessel || '', Voyage: s.voyage || '',
      ETD: s.etd || '', ETA: s.eta || '', 'Actual Arrival': s.actualArrival || '', 'Current Location': s.location || '', Destination: s.destination || '',
      Status: s.stage || '', 'Payment Status': pm.status, 'Payment Due': p.dueDate || '',
      Total: i === 0 ? pm.total : '', Paid: i === 0 ? pm.paid : '', Remaining: i === 0 ? pm.remaining : '', Currency: po.currency,
      'Tracking URL': s.trackingUrl || '', Notes: s.notes || '',
    }));
  });
  return rows;
}

export function exportAll(data) {
  const sup = new Map(data.suppliers.map((s) => [s.id, s]));
  const poNo = new Map(data.pos.map((p) => [p.id, p.poNumber]));
  exportWorkbook({
    'Shipments (import format)': flatRows(data),
    'Purchase Orders': data.pos.map((p) => ({ 'PO Number': p.poNumber, Date: p.poDate, Supplier: sup.get(p.supplierId)?.company || '', Category: p.category, Rep: p.rep, Currency: p.currency, Lines: p.lines.length, Total: p.lines.reduce((s, l) => s + l.qty * l.unitPrice, 0) })),
    Shipments: data.shipments.map((s) => { const m = shipmentMetrics(s); return { PO: poNo.get(s.poId), Stage: s.stage, BL: s.bl, Booking: s.booking, Container: s.container, Tracking: s.trackingNumber, 'Tracking URL': s.trackingUrl, Carrier: s.carrier, Vessel: s.vessel, Voyage: s.voyage, ETD: s.etd, ETA: s.eta, 'Actual Arrival': s.actualArrival, Location: s.location, Destination: s.destination, Customs: s.customs, ACID: s.acid, 'Days Delayed': m.daysDelayed, 'Days Remaining': m.daysRemaining ?? '', 'Days In Transit': m.daysInTransit ?? '', Notes: s.notes }; }),
    Payments: data.payments.map((p) => { const m = paymentMetrics(p); const po = data.pos.find((x) => x.id === p.poId); return { PO: poNo.get(p.poId), Currency: po?.currency, Invoice: p.invoice, Total: m.total, Paid: m.paid, Remaining: m.remaining, 'Due Date': p.dueDate, 'Paid Date': p.paidDate, Status: m.status, Method: p.method }; }),
    Suppliers: data.suppliers.map((s) => ({ Company: s.company, Country: s.country, Contact: s.contact, Email: s.email, Phone: s.phone, Website: s.website, Notes: s.notes })),
    Documents: data.documents.map((d) => ({ PO: poNo.get(d.poId), Type: d.type, Status: d.status, Reference: d.reference, URL: d.url, Expiry: d.expiry, Notes: d.notes })),
  }, `european-group-control-tower-${new Date().toISOString().slice(0, 10)}.xlsx`);
}
