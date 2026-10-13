import { STAGES, ARRIVING_SOON_DAYS, PAYMENT_SOON_DAYS, DOC_TYPES } from './constants.js';
import { parseISO, num } from './format.js';

export const today = () => {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  return d;
};
const diffDays = (a, b) => Math.round((a.getTime() - b.getTime()) / 86400000);
export const stageIndex = (s) => Math.max(0, STAGES.indexOf(s));

// Everything the UI needs to know about a shipment's schedule, derived (never stored).
export function shipmentMetrics(s, now = today()) {
  const idx = stageIndex(s.stage);
  const eta = parseISO(s.eta);
  const etd = parseISO(s.etd);
  const arrAt = parseISO(s.actualArrival);
  const arrived = idx >= 3 || !!arrAt;
  const daysToEta = eta ? diffDays(eta, now) : null;
  const daysDelayed = eta && !arrived && daysToEta < 0 ? -daysToEta : 0;
  const daysRemaining = eta && !arrived ? Math.max(0, daysToEta) : null;
  let daysInTransit = null;
  if (etd && idx >= 2) daysInTransit = Math.max(0, diffDays(arrAt || now, etd));
  const delayed = !arrived && daysDelayed > 0;
  const arrivingSoon = !arrived && eta !== null && daysToEta >= 0 && daysToEta <= ARRIVING_SOON_DAYS;
  const state = arrived ? 'Arrived' : delayed ? 'Delayed' : arrivingSoon ? 'Arriving Soon' : eta ? 'On Schedule' : 'No ETA';
  return { idx, arrived, daysDelayed, daysRemaining, daysInTransit, delayed, arrivingSoon, state, inFlight: idx >= 1 && idx < 3 };
}

// Remaining is always calculated: total - paid.
export function paymentMetrics(p, now = today()) {
  const total = num(p.total);
  const paid = num(p.paid);
  const remaining = Math.max(0, +(total - paid).toFixed(2));
  const status = total > 0 && remaining === 0 ? 'Paid' : paid > 0 ? 'Partial' : 'Unpaid';
  const due = parseISO(p.dueDate);
  const dueIn = due ? diffDays(due, now) : null;
  const overdue = remaining > 0 && dueIn !== null && dueIn < 0;
  const dueSoon = remaining > 0 && dueIn !== null && dueIn >= 0 && dueIn <= PAYMENT_SOON_DAYS;
  return { total, paid, remaining, status, overdue, dueSoon, daysOverdue: overdue ? -dueIn : 0, dueIn };
}

export const poTotal = (po) => (po.lines || []).reduce((s, l) => s + num(l.qty) * num(l.unitPrice), 0);
export const poQuantity = (po) => (po.lines || []).reduce((s, l) => s + num(l.qty), 0);

// One row per document type for a PO (virtual "Missing" row when nothing is recorded).
export function poDocuments(data, poId, now = today()) {
  return DOC_TYPES.map((type) => {
    const recs = data.documents.filter((d) => d.poId === poId && d.type === type);
    const rec = recs.find((r) => r.status === 'Received') || recs[0] || null;
    let status = rec ? rec.status : 'Missing';
    const exp = rec ? parseISO(rec.expiry) : null;
    if (rec && exp && exp < now && status !== 'Missing') status = 'Expired';
    return { type, status, record: rec };
  });
}

export const hasAcid = (data, shipment) =>
  !!(shipment && shipment.acid) ||
  data.documents.some((d) => d.poId === shipment?.poId && d.type === 'ACID' && d.status === 'Received');

// Joined view used by most pages.
export function joinData(data, now = today()) {
  const sup = new Map(data.suppliers.map((s) => [s.id, s]));
  const shipByPo = new Map(data.shipments.map((s) => [s.poId, s]));
  const payByPo = new Map(data.payments.map((p) => [p.poId, p]));
  return data.pos.map((po) => {
    const shipment = shipByPo.get(po.id) || null;
    const payment = payByPo.get(po.id) || null;
    return {
      po,
      supplier: sup.get(po.supplierId) || null,
      shipment,
      payment,
      sm: shipment ? shipmentMetrics(shipment, now) : null,
      pm: payment ? paymentMetrics(payment, now) : null,
    };
  });
}
