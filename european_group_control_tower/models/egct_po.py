from odoo import api, fields, models


class EgctPo(models.Model):
    _name = 'egct.po'
    _description = 'Control Tower Purchase Order'
    _order = 'name'
    _sql_constraints = [('name_uniq', 'unique(name)', 'PO numbers must be unique.')]

    name = fields.Char('PO Number', required=True, index=True, copy=False)
    po_date = fields.Date('PO Date')
    supplier_id = fields.Many2one('egct.supplier', string='Supplier', ondelete='restrict', index=True)
    rep = fields.Char('Purchase Rep.')
    category = fields.Char()
    currency = fields.Char(required=True, default='USD')
    notes = fields.Text()
    line_ids = fields.One2many('egct.po.line', 'po_id', string='Product lines', copy=True)
    shipment_ids = fields.One2many('egct.shipment', 'po_id', string='Shipments')
    payment_ids = fields.One2many('egct.payment', 'po_id', string='Payments')
    document_ids = fields.One2many('egct.document', 'po_id', string='Documents')
    total_amount = fields.Float('Total', compute='_compute_totals', store=True, digits=(16, 2))
    quantity = fields.Float('Quantity', compute='_compute_totals', store=True, digits=(16, 2))

    @api.depends('line_ids.qty', 'line_ids.unit_price')
    def _compute_totals(self):
        for po in self:
            po.total_amount = sum(line.qty * line.unit_price for line in po.line_ids)
            po.quantity = sum(line.qty for line in po.line_ids)

    @staticmethod
    def _normalize_number(vals):
        if vals.get('name'):
            vals['name'] = vals['name'].strip().upper()
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        return super().create([self._normalize_number(dict(v)) for v in vals_list])

    def write(self, vals):
        return super().write(self._normalize_number(dict(vals)))


class EgctPoLine(models.Model):
    _name = 'egct.po.line'
    _description = 'Control Tower PO Line'
    _order = 'po_id, sequence, id'

    po_id = fields.Many2one('egct.po', string='Purchase Order', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    product = fields.Char()
    qty = fields.Float('Quantity', digits=(16, 2))
    unit = fields.Char()
    unit_price = fields.Float('Unit price', digits=(16, 4))
    amount = fields.Float('Amount', compute='_compute_amount', digits=(16, 2))

    @api.depends('qty', 'unit_price')
    def _compute_amount(self):
        for line in self:
            line.amount = line.qty * line.unit_price
