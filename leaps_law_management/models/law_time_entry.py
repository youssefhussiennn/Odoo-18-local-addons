from odoo import api, fields, models, _


class LawTimeEntry(models.Model):
    _name = 'law.time.entry'
    _description = 'سجل وقت العمل'
    _order = 'date desc'

    case_id = fields.Many2one('law.case', string='القضية', required=True, ondelete='cascade')
    attorney_id = fields.Many2one('res.users', string='المحامي',
        default=lambda self: self.env.user, required=True)
    date = fields.Date('التاريخ', default=fields.Date.today, required=True)
    description = fields.Char('وصف العمل', required=True)

    hours = fields.Float('عدد الساعات', required=True, digits=(16, 2))
    hourly_rate = fields.Monetary('سعر الساعة', currency_field='currency_id', required=True)
    amount = fields.Monetary('المبلغ', compute='_compute_amount', store=True,
        currency_field='currency_id')

    currency_id = fields.Many2one(related='case_id.currency_id', store=True)
    invoiced = fields.Boolean('مفوتر', default=False, readonly=True)
    invoice_id = fields.Many2one('account.move', string='الفاتورة', readonly=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    @api.depends('hours', 'hourly_rate')
    def _compute_amount(self):
        for rec in self:
            rec.amount = rec.hours * rec.hourly_rate
