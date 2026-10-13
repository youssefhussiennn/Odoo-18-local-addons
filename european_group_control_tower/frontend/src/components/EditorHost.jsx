import { useStore } from '../lib/store.jsx';
import { useNav } from '../lib/nav.jsx';
import { FormModal, ConfirmModal } from './ui.jsx';
import { STAGES, CUSTOMS_STATUSES, PAYMENT_METHODS, CURRENCIES, DOC_TYPES, DOC_STATUSES } from '../lib/constants.js';
import { paymentMetrics } from '../lib/calc.js';
import { num } from '../lib/format.js';

const isoToday = () => new Date().toISOString().slice(0, 10);

// Renders the single active create/edit modal and the confirm dialog for the whole app.
export default function EditorHost() {
  const { data, upsert, savePO, notify } = useStore();
  const { editor, closeEdit, confirmState, closeConfirm } = useNav();
  const poOptions = data.pos.map((p) => ({ value: p.id, label: p.poNumber })).sort((a, b) => a.label.localeCompare(b.label));
  const poNo = (id) => data.pos.find((p) => p.id === id)?.poNumber || '';

  let form = null;
  if (editor) {
    const { kind, id, preset } = editor;
    const key = `${kind}-${id || 'new'}`;

    if (kind === 'po') {
      const cur = data.pos.find((p) => p.id === id);
      const initial = cur || { id: '', poNumber: '', poDate: isoToday(), supplierId: '', rep: '', category: '', currency: 'USD', lines: [{ product: '', qty: 0, unit: '', unitPrice: 0 }], notes: '', ...preset };
      form = (
        <FormModal key={key} title={cur ? `Edit PO ${cur.poNumber}` : 'New Purchase Order'} initial={initial} onClose={closeEdit}
          fields={[
            { key: 'poNumber', label: 'PO Number', required: true },
            { key: 'poDate', label: 'PO Date', type: 'date' },
            { key: 'supplierId', label: 'Supplier', type: 'select', options: data.suppliers.map((s) => ({ value: s.id, label: s.company })).sort((a, b) => a.label.localeCompare(b.label)) },
            { key: 'rep', label: 'Purchase Rep.' },
            { key: 'category', label: 'Category' },
            { key: 'currency', label: 'Currency', type: 'select', options: CURRENCIES, allowEmpty: false },
            { key: 'lines', label: 'Product lines', type: 'lines' },
            { key: 'notes', label: 'Notes', type: 'textarea' },
          ]}
          onSave={async (v) => {
            const poNumber = v.poNumber.trim().toUpperCase();
            if (!cur && data.pos.some((p) => p.poNumber === poNumber)) { notify(`PO ${poNumber} already exists`, 'err'); return false; }
            const lines = v.lines.filter((l) => l.product || num(l.qty)).map((l) => ({ product: l.product, qty: num(l.qty), unit: l.unit, unitPrice: num(l.unitPrice) }));
            // A new PO also gets its shipment and payment record created by the server.
            const ok = await savePO({ ...v, poNumber, id: cur ? cur.id : '', lines });
            if (ok) notify(cur ? 'PO updated' : 'PO created');
            return ok;
          }} />
      );
    }

    if (kind === 'shipment') {
      const cur = data.shipments.find((s) => s.id === id);
      const free = poOptions.filter((o) => !data.shipments.some((s) => s.poId === o.value));
      const initial = cur || { id: '', poId: free[0]?.value || '', stage: 'Booked', bl: '', booking: '', container: '', trackingNumber: '', trackingUrl: '', carrier: '', vessel: '', voyage: '', etd: '', eta: '', actualArrival: '', location: '', destination: '', registration: '', customs: 'Not Started', acid: '', notes: '', ...preset };
      form = (
        <FormModal key={key} title={cur ? `Edit shipment ${poNo(cur.poId)}` : 'New Shipment'} initial={initial} onClose={closeEdit}
          fields={[
            { key: 'poId', label: 'Purchase Order', type: 'select', options: cur ? poOptions : free, required: true, disabled: !!cur, allowEmpty: false },
            { key: 'stage', label: 'Stage', type: 'select', options: STAGES, allowEmpty: false },
            { key: 'bl', label: 'BL Number' }, { key: 'booking', label: 'Booking No.' },
            { key: 'container', label: 'Container' }, { key: 'trackingNumber', label: 'Tracking Number' },
            { key: 'trackingUrl', label: 'Tracking URL (manual)', type: 'url', span: 2 },
            { key: 'carrier', label: 'Carrier / Shipping Line' }, { key: 'vessel', label: 'Vessel' },
            { key: 'voyage', label: 'Voyage' }, { key: 'location', label: 'Current Location' },
            { key: 'etd', label: 'ETD', type: 'date' }, { key: 'eta', label: 'ETA', type: 'date' },
            { key: 'actualArrival', label: 'Actual Arrival', type: 'date' }, { key: 'destination', label: 'Destination Port' },
            { key: 'registration', label: 'Registration' }, { key: 'customs', label: 'Customs', type: 'select', options: CUSTOMS_STATUSES, allowEmpty: false },
            { key: 'acid', label: 'ACID Number', span: 2 },
            { key: 'notes', label: 'Notes', type: 'textarea' },
          ]}
          onSave={async (v) => {
            if (!v.poId) return false;
            // The server also keeps the ACID document of the PO in sync when the ACID number changes.
            const ok = await upsert('shipments', v, 'shipment');
            if (ok) notify('Shipment saved');
            return ok;
          }} />
      );
    }

    if (kind === 'payment') {
      const cur = data.payments.find((p) => p.id === id);
      const free = poOptions.filter((o) => !data.payments.some((p) => p.poId === o.value));
      const initial = cur || { id: '', poId: free[0]?.value || '', invoice: '', total: 0, paid: 0, dueDate: '', paidDate: '', method: '', notes: '', ...preset };
      form = (
        <FormModal key={key} title={cur ? `Edit payment ${poNo(cur.poId)}` : 'New Payment Record'} initial={initial} onClose={closeEdit}
          compute={(v) => { const m = paymentMetrics(v); return { remaining: m.remaining.toFixed(2), status: m.status }; }}
          fields={[
            { key: 'poId', label: 'Purchase Order', type: 'select', options: cur ? poOptions : free, required: true, disabled: !!cur, allowEmpty: false },
            { key: 'invoice', label: 'Invoice No.' },
            { key: 'total', label: 'Total', type: 'number' }, { key: 'paid', label: 'Paid', type: 'number' },
            { key: 'remaining', label: 'Remaining (auto)', type: 'readonly' }, { key: 'status', label: 'Status (auto)', type: 'readonly' },
            { key: 'dueDate', label: 'Due Date', type: 'date' }, { key: 'paidDate', label: 'Paid Date', type: 'date' },
            { key: 'method', label: 'Payment Method', type: 'select', options: PAYMENT_METHODS.filter(Boolean) },
            { key: 'notes', label: 'Notes', type: 'textarea' },
          ]}
          onSave={async (v) => {
            if (!v.poId) return false;
            const { remaining, status, ...rest } = v;
            const ok = await upsert('payments', rest, 'payment');
            if (ok) notify('Payment saved');
            return ok;
          }} />
      );
    }

    if (kind === 'supplier') {
      const cur = data.suppliers.find((s) => s.id === id);
      const initial = cur || { id: '', company: '', country: '', contact: '', email: '', phone: '', website: '', notes: '', ...preset };
      form = (
        <FormModal key={key} title={cur ? 'Edit supplier' : 'New Supplier'} initial={initial} onClose={closeEdit}
          fields={[
            { key: 'company', label: 'Company', required: true, span: 2 }, { key: 'country', label: 'Country' }, { key: 'contact', label: 'Contact person' },
            { key: 'email', label: 'Email', type: 'email' }, { key: 'phone', label: 'Phone' }, { key: 'website', label: 'Website', type: 'url', span: 2 },
            { key: 'notes', label: 'Notes', type: 'textarea' },
          ]}
          onSave={async (v) => { const ok = await upsert('suppliers', v, 'supplier'); if (ok) notify('Supplier saved'); return ok; }} />
      );
    }

    if (kind === 'document') {
      const cur = data.documents.find((d) => d.id === id);
      const initial = cur || { id: '', poId: poOptions[0]?.value || '', type: 'Commercial Invoice', status: 'Received', reference: '', url: '', expiry: '', notes: '', ...preset };
      form = (
        <FormModal key={key} title={cur ? `Edit document ${poNo(cur.poId)}` : 'New Document'} initial={initial} onClose={closeEdit}
          fields={[
            { key: 'poId', label: 'Purchase Order', type: 'select', options: poOptions, required: true, allowEmpty: false },
            { key: 'type', label: 'Document Type', type: 'select', options: DOC_TYPES, allowEmpty: false },
            { key: 'status', label: 'Status', type: 'select', options: DOC_STATUSES, allowEmpty: false },
            { key: 'reference', label: 'Reference / Number' },
            { key: 'url', label: 'Document URL', type: 'url', span: 2 },
            { key: 'expiry', label: 'Expiry Date', type: 'date' },
            { key: 'notes', label: 'Notes', type: 'textarea' },
          ]}
          onSave={async (v) => {
            if (!v.poId) return false;
            const ok = await upsert('documents', v, 'document');
            if (ok) notify('Document saved');
            return ok;
          }} />
      );
    }
  }

  return <>{form}<ConfirmModal state={confirmState} onClose={closeConfirm} /></>;
}

