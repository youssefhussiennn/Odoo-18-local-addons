from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class LawCase(models.Model):
    _name = 'law.case'
    _description = 'القضية القانونية'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_opened desc, id desc'
    _rec_name = 'name'

    name = fields.Char('رقم القضية', required=True, copy=False, default='New', readonly=True)
    title = fields.Char('عنوان القضية', required=True, tracking=True)

    case_type = fields.Selection([
        ('civil', 'مدني'),
        ('criminal', 'جنائي'),
        ('commercial', 'تجاري'),
        ('family', 'أحوال شخصية'),
        ('labor', 'عمالي'),
        ('real_estate', 'عقاري'),
        ('administrative', 'إداري'),
        ('other', 'أخرى'),
    ], string='نوع القضية', required=True, default='civil', tracking=True)

    state = fields.Selection([
        ('draft', 'مسودة'),
        ('open', 'مفتوحة'),
        ('in_progress', 'قيد النظر'),
        ('won', 'مكسوبة'),
        ('lost', 'خاسرة'),
        ('settled', 'تسوية'),
        ('closed', 'مغلقة'),
    ], string='الحالة', default='draft', tracking=True)

    priority = fields.Selection([
        ('0', 'عادي'),
        ('1', 'مهم'),
        ('2', 'عاجل'),
    ], string='الأولوية', default='0')

    client_id = fields.Many2one('res.partner', string='الموكل', required=True, tracking=True)
    opposing_party = fields.Char('الطرف المقابل', tracking=True)
    attorney_id = fields.Many2one('res.users', string='المحامي المسؤول',
        default=lambda self: self.env.user, tracking=True)

    court = fields.Char('المحكمة', tracking=True)
    court_case_number = fields.Char('رقم القضية لدى المحكمة')
    judge = fields.Char('القاضي')

    date_opened = fields.Date('تاريخ الفتح', default=fields.Date.today)
    date_closed = fields.Date('تاريخ الإغلاق')

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    retainer_fee = fields.Monetary('أتعاب الارتباط', currency_field='currency_id')

    description = fields.Text('وصف القضية')
    notes = fields.Html('ملاحظات داخلية')

    hearing_ids = fields.One2many('law.hearing', 'case_id', string='جلسات القضية')
    hearing_count = fields.Integer(compute='_compute_hearing_count', string='عدد الجلسات')

    time_entry_ids = fields.One2many('law.time.entry', 'case_id', string='سجل الوقت')
    total_hours = fields.Float(compute='_compute_totals', string='إجمالي الساعات', store=True)
    total_billable = fields.Monetary(compute='_compute_totals', string='إجمالي قابل للفوترة',
        store=True, currency_field='currency_id')

    invoice_ids = fields.One2many('account.move', 'law_case_id', string='فواتير القضية')
    invoice_count = fields.Integer(compute='_compute_invoice_count', string='عدد الفواتير')
    total_invoiced = fields.Monetary(compute='_compute_invoice_count', string='إجمالي الفواتير',
        currency_field='currency_id')

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('law.case') or 'New'
        return super().create(vals_list)

    @api.depends('hearing_ids')
    def _compute_hearing_count(self):
        for rec in self:
            rec.hearing_count = len(rec.hearing_ids.filtered(lambda h: h.state != 'cancelled'))

    @api.depends('time_entry_ids.hours', 'time_entry_ids.amount')
    def _compute_totals(self):
        for rec in self:
            rec.total_hours = sum(rec.time_entry_ids.mapped('hours'))
            rec.total_billable = sum(rec.time_entry_ids.mapped('amount'))

    def _compute_invoice_count(self):
        for rec in self:
            valid = rec.invoice_ids.filtered(lambda i: i.state != 'cancel')
            rec.invoice_count = len(valid)
            rec.total_invoiced = sum(valid.mapped('amount_total'))

    def action_open(self):
        self.state = 'open'

    def action_in_progress(self):
        self.state = 'in_progress'

    def action_won(self):
        self.state = 'won'
        self.date_closed = fields.Date.today()

    def action_lost(self):
        self.state = 'lost'
        self.date_closed = fields.Date.today()

    def action_settle(self):
        self.state = 'settled'
        self.date_closed = fields.Date.today()

    def action_close(self):
        self.state = 'closed'
        self.date_closed = fields.Date.today()

    def action_draft(self):
        self.state = 'draft'
        self.date_closed = False

    def action_create_invoice(self):
        self.ensure_one()
        uninvoiced = self.time_entry_ids.filtered(lambda t: not t.invoiced)
        if not uninvoiced:
            raise UserError(_('لا توجد ساعات عمل غير مفوترة لهذه القضية.'))
        lines = [(0, 0, {
            'name': '%s - %s' % (t.description or _('خدمات قانونية'), t.date),
            'quantity': t.hours,
            'price_unit': t.hourly_rate,
        }) for t in uninvoiced]
        inv = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.client_id.id,
            'law_case_id': self.id,
            'invoice_line_ids': lines,
        })
        uninvoiced.write({'invoiced': True, 'invoice_id': inv.id})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': inv.id,
            'view_mode': 'form',
        }

    def action_view_hearings(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'الجلسات',
            'res_model': 'law.hearing',
            'view_mode': 'list,form,calendar',
            'domain': [('case_id', '=', self.id)],
            'context': {'default_case_id': self.id},
        }

    def action_view_invoices(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'الفواتير',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('law_case_id', '=', self.id)],
            'context': {'default_law_case_id': self.id, 'default_move_type': 'out_invoice'},
        }


class AccountMoveExtend(models.Model):
    _inherit = 'account.move'

    law_case_id = fields.Many2one('law.case', string='القضية', ondelete='set null')
