import { REQUIRED_DOCS } from './constants.js';
import { joinData, poDocuments, hasAcid, today } from './calc.js';
import { fmtMoney } from './format.js';

export const ALERT_TYPES = {
  delayed: 'Delayed shipment',
  eta_passed: 'ETA passed',
  arriving_soon: 'Arriving soon',
  payment_overdue: 'Overdue payment',
  payment_due_soon: 'Payment due soon',
  missing_document: 'Missing document',
  expired_document: 'Expired document',
  missing_acid: 'Missing ACID',
  missing_tracking: 'Missing tracking link',
};
const SEV_ORDER = { high: 0, medium: 1, low: 2 };

export function buildAlerts(data, now = today()) {
  const out = [];
  const add = (type, severity, row, title, detail) =>
    out.push({ id: `${type}:${row.po.id}:${title}`, type, severity, poId: row.po.id, poNumber: row.po.poNumber, title, detail });

  for (const row of joinData(data, now)) {
    const { po, shipment, sm, pm } = row;
    const open = sm ? sm.idx < 5 : true;
    if (sm) {
      if (sm.delayed && sm.idx >= 2) add('delayed', sm.daysDelayed >= 7 ? 'high' : 'medium', row, 'Delayed shipment', `${sm.daysDelayed} days past ETA`);
      if (sm.delayed && sm.idx < 2) add('eta_passed', sm.daysDelayed >= 7 ? 'high' : 'medium', row, 'ETA passed', `ETA passed ${sm.daysDelayed} days ago and shipment is still ${shipment.stage}`);
      if (sm.arrivingSoon) add('arriving_soon', 'low', row, 'Arriving soon', `ETA in ${sm.daysRemaining} day(s)`);
      if (sm.idx >= 2 && !shipment.trackingUrl) add('missing_tracking', 'low', row, 'Missing tracking link', 'Add a tracking URL for this shipment');
    }
    if (pm) {
      if (pm.overdue) add('payment_overdue', 'high', row, 'Overdue payment', `${fmtMoney(pm.remaining, po.currency)} overdue by ${pm.daysOverdue} days`);
      if (pm.dueSoon) add('payment_due_soon', 'medium', row, 'Payment due soon', `${fmtMoney(pm.remaining, po.currency)} due in ${pm.dueIn} day(s)`);
    }
    if (shipment && sm.idx >= 2) {
      const docs = poDocuments(data, po.id, now);
      docs.filter((d) => d.status === 'Expired').forEach((d) => add('expired_document', 'high', row, `Expired document: ${d.type}`, 'Replace the expired document'));
      docs.filter((d) => REQUIRED_DOCS.includes(d.type) && d.type !== 'ACID' && (d.status === 'Missing' || d.status === 'Pending'))
        .forEach((d) => add('missing_document', 'medium', row, `Missing document: ${d.type}`, d.status === 'Pending' ? 'Marked pending' : 'No document recorded'));
    }
    if (open && !hasAcid(data, shipment || { poId: po.id })) add('missing_acid', 'medium', row, 'Missing ACID', 'No ACID number registered for this PO');
  }
  return out.sort((a, b) => SEV_ORDER[a.severity] - SEV_ORDER[b.severity]);
}
