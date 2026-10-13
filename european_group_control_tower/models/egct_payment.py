from odoo import api, fields, models


class EgctPayment(models.Model):
    _name = 'egct.payment'
    _description = 'Control Tower Payment'
    _rec_name = 'po_id'
    _order = 'id'
    _sql_constraints = [('po_uniq', 'unique(po_id)', 'A purchase order can only have one payment record.')]

    po_id = fields.Many2one('egct.po', string='Purchase Order', required=True, ondelete='cascade', index=True)
    currency = fields.Char(related='po_id.currency', string='Currency')
    invoice = fields.Char('Invoice No.')
    total = fields.Float(digits=(16, 2))
    paid = fields.Float(digits=(16, 2))
    remaining = fields.Float(compute='_compute_balance', store=True, digits=(16, 2))
    status = fields.Selection(
        [('Unpaid', 'Unpaid'), ('Partial', 'Partial'), ('Paid', 'Paid')],
        compute='_compute_balance', store=True, index=True)
    due_date = fields.Date('Due Date')
    paid_date = fields.Date('Paid Date')
    method = fields.Char('Payment Method')
    notes = fields.Text()

    @api.depends('total', 'paid')
    def _compute_balance(self):
        for pay in self:
            remaining = max(0.0, round(pay.total - pay.paid, 2))
            pay.remaining = remaining
            if pay.total > 0 and remaining == 0:
                pay.status = 'Paid'
            elif pay.paid > 0:
                pay.status = 'Partial'
            else:
                pay.status = 'Unpaid'
