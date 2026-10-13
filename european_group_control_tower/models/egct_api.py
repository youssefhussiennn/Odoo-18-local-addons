"""Server side of the Control Tower single page app.

The React front end keeps one in-memory dataset (suppliers, pos, shipments, payments, documents, activity).
This model converts between that client shape (camelCase keys, string ids, ISO dates) and the Odoo models, and
implements every write operation the UI needs. All methods run with the current user's rights.
"""
import re

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools import float_round

MANAGER_GROUP = 'european_group_control_tower.group_egct_manager'
USER_GROUP = 'european_group_control_tower.group_egct_user'

# (client key, odoo field, kind)   kinds: char | req (required: blank is ignored) | date | float | m2o
SUPPLIER_SPEC = [
    ('company', 'name', 'req'), ('country', 'country', 'char'), ('contact', 'contact', 'char'),
    ('email', 'email', 'char'), ('phone', 'phone', 'char'), ('website', 'website', 'char'), ('notes', 'notes', 'char'),
]
PO_SPEC = [
    ('poNumber', 'name', 'req'), ('poDate', 'po_date', 'date'), ('supplierId', 'supplier_id', 'm2o'),
    ('rep', 'rep', 'char'), ('category', 'category', 'char'), ('currency', 'currency', 'req'), ('notes', 'notes', 'char'),
]
SHIPMENT_SPEC = [
    ('poId', 'po_id', 'm2o'), ('stage', 'stage', 'req'), ('bl', 'bl', 'char'), ('booking', 'booking', 'char'),
    ('container', 'container', 'char'), ('trackingNumber', 'tracking_number', 'char'),
    ('trackingUrl', 'tracking_url', 'char'), ('carrier', 'carrier', 'char'), ('vessel', 'vessel', 'char'),
    ('voyage', 'voyage', 'char'), ('etd', 'etd', 'date'), ('eta', 'eta', 'date'),
    ('actualArrival', 'actual_arrival', 'date'), ('location', 'location', 'char'),
    ('destination', 'destination', 'char'), ('registration', 'registration', 'char'),
    ('customs', 'customs', 'req'), ('acid', 'acid', 'char'), ('notes', 'notes', 'char'),
]
PAYMENT_SPEC = [
    ('poId', 'po_id', 'm2o'), ('invoice', 'invoice', 'char'), ('total', 'total', 'float'), ('paid', 'paid', 'float'),
    ('dueDate', 'due_date', 'date'), ('paidDate', 'paid_date', 'date'), ('method', 'method', 'char'),
    ('notes', 'notes', 'char'),
]
DOCUMENT_SPEC = [
    ('poId', 'po_id', 'm2o'), ('type', 'type', 'req'), ('status', 'status', 'req'), ('reference', 'reference', 'char'),
    ('url', 'url', 'char'), ('expiry', 'expiry', 'date'), ('notes', 'notes', 'char'),
]
SPECS = {
    'suppliers': ('egct.supplier', SUPPLIER_SPEC),
    'pos': ('egct.po', PO_SPEC),
    'shipments': ('egct.shipment', SHIPMENT_SPEC),
    'payments': ('egct.payment', PAYMENT_SPEC),
    'documents': ('egct.document', DOCUMENT_SPEC),
}
ACTIVITY_LIMIT = 200


def _empty(value):
    """Same notion of 'empty' as the JS importer: null, '' and empty arrays (0 is a real value)."""
    return value is None or value == '' or (isinstance(value, (list, tuple)) and not value)


def _num(value):
    if value is None or value == '' or isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(re.sub(r'[^0-9.\-]', '', str(value)))
    except ValueError:
        return 0.0


def _norm_name(value):
    return re.sub(r'\s+', ' ', (value or '').strip().lower())


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


class EgctApi(models.AbstractModel):
    _name = 'egct.api'
    _description = 'Control Tower API'

    # ------------------------------------------------------------------
    # conversion helpers
    # ------------------------------------------------------------------
    @api.model
    def _to_client(self, rec, spec):
        out = {'id': str(rec.id)}
        for key, fname, kind in spec:
            value = rec[fname]
            if kind == 'date':
                out[key] = fields.Date.to_string(value) if value else ''
            elif kind == 'm2o':
                out[key] = str(value.id) if value else ''
            elif kind == 'float':
                out[key] = value or 0.0
            else:
                out[key] = value or ''
        return out

    @api.model
    def _vals(self, spec, rec):
        """Client record -> Odoo values, only for the keys present in ``rec``."""
        vals = {}
        for key, fname, kind in spec:
            if key not in rec:
                continue
            value = rec[key]
            if kind == 'date':
                if _empty(value):
                    vals[fname] = False
                else:
                    try:
                        vals[fname] = fields.Date.to_date(str(value)[:10])
                    except (ValueError, TypeError):
                        raise UserError(_('Invalid date: %s', value))
            elif kind == 'm2o':
                vals[fname] = _to_int(value) or False
            elif kind == 'float':
                vals[fname] = _num(value)
            elif kind == 'req':
                text = '' if value is None else str(value).strip()
                if text:
                    vals[fname] = text
            else:
                text = '' if value is None else str(value).strip()
                vals[fname] = text or False
        return vals

    @api.model
    def _line_vals(self, line):
        return {
            'product': str(line.get('product') or '').strip() or False,
            'qty': _num(line.get('qty')),
            'unit': str(line.get('unit') or '').strip() or False,
            'unit_price': _num(line.get('unitPrice')),
        }

    @api.model
    def _serialize_po(self, po):
        out = self._to_client(po, PO_SPEC)
        out['lines'] = [
            {'product': l.product or '', 'qty': l.qty, 'unit': l.unit or '', 'unitPrice': l.unit_price}
            for l in po.line_ids
        ]
        return out

    @api.model
    def _is_manager(self):
        return self.env.user.has_group(MANAGER_GROUP)

    @api.model
    def _require_manager(self):
        if not self._is_manager():
            raise AccessError(_('Only Control Tower managers can do this.'))

    @api.model
    def _log(self, text, kind='update'):
        self.env['egct.activity'].create({'text': text, 'kind': kind})

    @api.model
    def _spec(self, coll):
        if coll not in SPECS or coll == 'pos':
            raise UserError(_('Unknown collection: %s', coll))
        return SPECS[coll]

    # ------------------------------------------------------------------
    # read
    # ------------------------------------------------------------------
    @api.model
    def get_dataset(self):
        env = self.env
        data = {}
        for key, (model, spec) in SPECS.items():
            recs = env[model].search([])
            if key == 'pos':
                data[key] = [self._serialize_po(r) for r in recs]
            else:
                data[key] = [self._to_client(r, spec) for r in recs]
        data['activity'] = [
            {
                'id': str(a.id),
                'ts': a.create_date.strftime('%Y-%m-%dT%H:%M:%SZ') if a.create_date else '',
                'kind': a.kind or 'update',
                'text': a.text,
            }
            for a in env['egct.activity'].search([], limit=ACTIVITY_LIMIT)
        ]
        return data

    @api.model
    def bootstrap(self):
        if not (self.env.user.has_group(USER_GROUP) or self.env.user.has_group(MANAGER_GROUP)):
            raise AccessError(_('You do not have access to the Control Tower.'))
        return {
            'data': self.get_dataset(),
            'user': {'id': self.env.user.id, 'name': self.env.user.name, 'isManager': self._is_manager()},
        }

    # ------------------------------------------------------------------
    # generic save / remove (suppliers, shipments, payments, documents)
    # ------------------------------------------------------------------
    @api.model
    def save_record(self, coll, rec, label=''):
        model, spec = self._spec(coll)
        Model = self.env[model]
        record = Model.browse(_to_int(rec.get('id'))).exists() if rec.get('id') else Model
        vals = self._vals(spec, rec)

        po = self.env['egct.po']
        if coll == 'suppliers':
            if not vals.get('name'):
                raise UserError(_('Company is required.'))
        else:
            po = self.env['egct.po'].browse(vals.get('po_id') or 0).exists()
            if not po:
                raise UserError(_('Select a purchase order.'))
            if coll in ('shipments', 'payments'):
                dup = Model.search([('po_id', '=', po.id), ('id', '!=', record.id)], limit=1)
                if dup:
                    kind = _('shipment') if coll == 'shipments' else _('payment record')
                    raise UserError(_('PO %(po)s already has a %(kind)s.', po=po.name, kind=kind))

        existed = bool(record)
        previous_acid = record.acid if (record and coll == 'shipments') else False
        if record:
            record.write(vals)
        else:
            record = Model.create(vals)

        if coll == 'shipments' and record.acid and record.acid != previous_acid:
            self._apply_acid(po, record.acid)

        suffix = f' {po.name}' if po else ''
        self._log(f"{'Updated' if existed else 'Added'} {label}{suffix}", 'update' if existed else 'create')
        return {'data': self.get_dataset()}

    @api.model
    def remove_record(self, coll, rec_id, label=''):
        model = self._spec(coll)[0]
        record = self.env[model].browse(_to_int(rec_id)).exists()
        if record:
            if coll == 'suppliers' and record.po_ids:
                raise UserError(_('%(name)s has %(count)s PO(s). Reassign them first.',
                                  name=record.name, count=len(record.po_ids)))
            record.unlink()
        self._log(f'Deleted {label}', 'delete')
        return {'data': self.get_dataset()}

    # ------------------------------------------------------------------
    # purchase orders
    # ------------------------------------------------------------------
    @api.model
    def save_po(self, po):
        Po = self.env['egct.po']
        number = str(po.get('poNumber') or '').strip().upper()
        if not number:
            raise UserError(_('PO Number is required.'))
        record = Po.browse(_to_int(po.get('id'))).exists() if po.get('id') else Po
        if Po.search_count([('name', '=', number), ('id', '!=', record.id)]):
            raise UserError(_('PO %s already exists', number))

        vals = self._vals(PO_SPEC, po)
        vals['name'] = number
        lines = [self._line_vals(l) for l in (po.get('lines') or []) if l.get('product') or _num(l.get('qty'))]
        line_cmds = [(5, 0, 0)] + [(0, 0, l) for l in lines]

        if not record:
            vals['line_ids'] = [(0, 0, l) for l in lines]
            record = Po.create(vals)
            self.env['egct.shipment'].create({'po_id': record.id, 'stage': 'PO Issued', 'customs': 'Not Started'})
            self.env['egct.payment'].create({
                'po_id': record.id, 'total': float_round(record.total_amount, precision_digits=2), 'paid': 0.0,
            })
            self._log(f'Created PO {number}', 'create')
        else:
            old_total = record.total_amount
            payment = record.payment_ids[:1]
            synced = bool(payment) and abs(payment.total - old_total) < 0.01
            vals['line_ids'] = line_cmds
            record.write(vals)
            if synced:
                payment.total = float_round(record.total_amount, precision_digits=2)
            self._log(f'Updated PO {number}')
        return {'data': self.get_dataset(), 'id': str(record.id)}

    @api.model
    def delete_po(self, po_id):
        record = self.env['egct.po'].browse(_to_int(po_id)).exists()
        if record:
            number = record.name
            record.unlink()
            self._log(f'Deleted PO {number} and its shipment, payment and documents', 'delete')
        return {'data': self.get_dataset()}

    # ------------------------------------------------------------------
    # ACID
    # ------------------------------------------------------------------
    @api.model
    def _apply_acid(self, po, acid):
        """Make sure the PO has a 'Received' ACID document carrying this number."""
        Doc = self.env['egct.document']
        doc = Doc.search([('po_id', '=', po.id), ('type', '=', 'ACID')], order='id', limit=1)
        if doc:
            doc.write({'status': 'Received', 'reference': acid})
        else:
            Doc.create({'po_id': po.id, 'type': 'ACID', 'status': 'Received', 'reference': acid})

    @api.model
    def import_acid(self, items):
        """items: [[poNumber, acid], ...]. Existing POs only get their ACID updated; unknown POs become stubs."""
        env = self.env
        count = 0
        for item in items or []:
            number = str(item[0] or '').strip().upper()
            acid = str(item[1] or '').strip()
            if not number or not acid:
                continue
            po = env['egct.po'].search([('name', '=', number)], limit=1)
            if po:
                po.shipment_ids[:1].write({'acid': acid})
            else:
                po = env['egct.po'].create({
                    'name': number, 'currency': 'USD',
                    'notes': 'Created from the ACID list - no shipment line found.',
                })
                env['egct.shipment'].create({'po_id': po.id, 'stage': 'PO Issued', 'customs': 'Not Started', 'acid': acid})
                env['egct.payment'].create({'po_id': po.id, 'total': 0.0, 'paid': 0.0})
            self._apply_acid(po, acid)
            count += 1
        self._log(f'Imported {count} ACID numbers', 'import')
        return {'data': self.get_dataset(), 'count': count}

    # ------------------------------------------------------------------
    # bulk import (Excel -> client dataset -> here)
    # ------------------------------------------------------------------
    @api.model
    def _wipe(self):
        env = self.env
        for model in ('egct.document', 'egct.payment', 'egct.shipment', 'egct.po', 'egct.supplier'):
            env[model].search([]).unlink()

    @api.model
    def import_dataset(self, ds, mode='merge', label=''):
        """Merge (update by natural key, only non-empty incoming values win) or replace everything.

        Natural keys: supplier = normalised company name, PO = PO number, shipment / payment = their PO,
        document = (PO, type). Client ids inside ``ds`` are only used to link the records together.
        """
        if mode not in ('merge', 'replace'):
            raise UserError(_('Unknown import mode: %s', mode))
        if mode == 'replace':
            self._require_manager()
            self._wipe()
        env = self.env

        def keep(rec, skip=()):
            """Incoming record without empty values (the 'merge' rule) and without the skipped keys."""
            return {k: v for k, v in rec.items() if not _empty(v) and k not in skip}

        # suppliers
        suppliers = {_norm_name(s.name): s for s in env['egct.supplier'].search([])}
        sup_map = {}
        for s in ds.get('suppliers') or []:
            key = _norm_name(s.get('company'))
            if not key:
                continue
            rec = suppliers.get(key)
            if rec:
                vals = self._vals(SUPPLIER_SPEC, keep(s))
                if vals:
                    rec.write(vals)
            else:
                rec = env['egct.supplier'].create(self._vals(SUPPLIER_SPEC, s))
                suppliers[key] = rec
            sup_map[str(s.get('id'))] = rec

        # purchase orders (+ lines)
        pos = {p.name: p for p in env['egct.po'].search([])}
        po_map = {}
        for p in ds.get('pos') or []:
            number = str(p.get('poNumber') or '').strip().upper()
            if not number:
                continue
            p = dict(p, poNumber=number)
            sup = sup_map.get(str(p.get('supplierId')))
            p['supplierId'] = sup.id if sup else ''
            lines = [self._line_vals(l) for l in (p.get('lines') or [])]
            rec = pos.get(number)
            if rec:
                vals = self._vals(PO_SPEC, keep(p, skip=('lines',)))
                if lines:
                    vals['line_ids'] = [(5, 0, 0)] + [(0, 0, l) for l in lines]
                rec.write(vals)
            else:
                vals = self._vals(PO_SPEC, p)
                vals['line_ids'] = [(0, 0, l) for l in lines]
                rec = env['egct.po'].create(vals)
                pos[number] = rec
            po_map[str(p.get('id'))] = rec

        def upsert_by_po(model, spec, items, existing):
            for item in items or []:
                po = po_map.get(str(item.get('poId')))
                if not po:
                    continue
                rec = existing.get(po.id)
                if rec:
                    vals = self._vals(spec, keep(item, skip=('poId',)))
                    if vals:
                        rec.write(vals)
                else:
                    vals = self._vals(spec, dict(item, poId=po.id))
                    existing[po.id] = env[model].create(vals)

        upsert_by_po('egct.shipment', SHIPMENT_SPEC, ds.get('shipments'),
                     {s.po_id.id: s for s in env['egct.shipment'].search([])})
        upsert_by_po('egct.payment', PAYMENT_SPEC, ds.get('payments'),
                     {p.po_id.id: p for p in env['egct.payment'].search([])})

        # documents
        docs = {}
        for d in env['egct.document'].search([], order='id'):
            docs.setdefault((d.po_id.id, d.type), d)
        for d in ds.get('documents') or []:
            po = po_map.get(str(d.get('poId')))
            if not po:
                continue
            key = (po.id, d.get('type'))
            rec = docs.get(key)
            if rec:
                vals = self._vals(DOCUMENT_SPEC, keep(d, skip=('poId',)))
                if vals:
                    rec.write(vals)
            else:
                docs[key] = env['egct.document'].create(self._vals(DOCUMENT_SPEC, dict(d, poId=po.id)))

        self._log(f'{label or "Import"} ({mode})', 'import')
        return {'data': self.get_dataset()}
