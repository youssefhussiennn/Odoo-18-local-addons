from odoo import api, fields, models


class EgctSupplier(models.Model):
    _name = 'egct.supplier'
    _description = 'Control Tower Supplier'
    _order = 'name'

    name = fields.Char('Company', required=True, index=True)
    country = fields.Char()
    contact = fields.Char('Contact person')
    email = fields.Char()
    phone = fields.Char()
    website = fields.Char()
    notes = fields.Text()
    po_ids = fields.One2many('egct.po', 'supplier_id', string='Purchase Orders')
    po_count = fields.Integer(compute='_compute_po_count')

    @api.depends('po_ids')
    def _compute_po_count(self):
        data = self.env['egct.po']._read_group([('supplier_id', 'in', self.ids)], ['supplier_id'], ['__count'])
        counts = {supplier.id: count for supplier, count in data}
        for rec in self:
            rec.po_count = counts.get(rec.id, 0)
