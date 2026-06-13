from odoo import api, fields, models, _
from odoo.exceptions import UserError


class LawConsultation(models.Model):
    _name = 'law.consultation'
    _description = 'الاستشارة القانونية'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'
    _rec_name = 'name'

    name = fields.Char('رقم الاستشارة', required=True, copy=False, default='New', readonly=True)
    client_id = fields.Many2one('res.partner', string='الموكل / العميل', required=True, tracking=True)
    attorney_id = fields.Many2one('res.users', string='المحامي',
        default=lambda self: self.env.user, required=True, tracking=True)

    date = fields.Datetime('تاريخ الاستشارة', default=fields.Datetime.now, required=True, tracking=True)
    duration = fields.Float('المدة (ساعات)', default=1.0)

    case_type = fields.Selection([
        ('civil', 'مدني'),
        ('criminal', 'جنائي'),
        ('commercial', 'تجاري'),
        ('family', 'أحوال شخصية'),
        ('labor', 'عمالي'),
        ('real_estate', 'عقاري'),
        ('administrative', 'إداري'),
        ('other', 'أخرى'),
    ], string='مجال الاستشارة', required=True, default='civil')

    state = fields.Selection([
        ('scheduled', 'مجدولة'),
        ('done', 'منتهية'),
        ('cancelled', 'ملغاة'),
    ], string='الحالة', default='scheduled', tracking=True)

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    fee = fields.Monetary('رسوم الاستشارة', currency_field='currency_id')

    summary = fields.Text('ملخص الاستشارة')
    result_action = fields.Selection([
        ('new_case', 'فتح قضية جديدة'),
        ('no_action', 'لا إجراء'),
        ('refer', 'تحويل'),
    ], string='الإجراء المتخذ', default='no_action')
    case_id = fields.Many2one('law.case', string='القضية المرتبطة')

    invoice_id = fields.Many2one('account.move', string='الفاتورة', readonly=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('law.consultation') or 'New'
        return super().create(vals_list)

    def action_done(self):
        self.state = 'done'

    def action_cancel(self):
        self.state = 'cancelled'

    def action_reschedule(self):
        self.state = 'scheduled'

    def action_create_invoice(self):
        self.ensure_one()
        if not self.fee:
            raise UserError(_('يرجى تحديد رسوم الاستشارة أولاً.'))
        inv = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.client_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': _('استشارة قانونية - %s') % self.name,
                'quantity': 1,
                'price_unit': self.fee,
            })],
        })
        self.invoice_id = inv.id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': inv.id,
            'view_mode': 'form',
        }
