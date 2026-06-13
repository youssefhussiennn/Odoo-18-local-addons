from odoo import api, fields, models, _


class LawHearing(models.Model):
    _name = 'law.hearing'
    _description = 'جلسة المحكمة'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'
    _rec_name = 'name'

    name = fields.Char('رقم الجلسة', required=True, copy=False, default='New', readonly=True)
    case_id = fields.Many2one('law.case', string='القضية', required=True, ondelete='cascade')
    client_id = fields.Many2one(related='case_id.client_id', store=True, string='الموكل')
    attorney_id = fields.Many2one(related='case_id.attorney_id', store=True, string='المحامي')

    date = fields.Datetime('تاريخ ووقت الجلسة', required=True, tracking=True)
    court = fields.Char('المحكمة', related='case_id.court', store=True)
    judge = fields.Char('القاضي', tracking=True)

    hearing_type = fields.Selection([
        ('first', 'أولى'),
        ('follow_up', 'متابعة'),
        ('pleading', 'مرافعة'),
        ('verdict', 'حكم'),
        ('appeal', 'استئناف'),
        ('other', 'أخرى'),
    ], string='نوع الجلسة', default='first', required=True)

    state = fields.Selection([
        ('scheduled', 'مجدولة'),
        ('held', 'منعقدة'),
        ('postponed', 'مؤجلة'),
        ('cancelled', 'ملغاة'),
    ], string='الحالة', default='scheduled', tracking=True)

    result = fields.Text('نتيجة الجلسة')
    next_hearing_date = fields.Date('موعد الجلسة القادمة')
    notes = fields.Text('ملاحظات')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('law.hearing') or 'New'
        return super().create(vals_list)

    def action_held(self):
        self.state = 'held'

    def action_postpone(self):
        self.state = 'postponed'

    def action_cancel(self):
        self.state = 'cancelled'

    def action_reschedule(self):
        self.state = 'scheduled'
