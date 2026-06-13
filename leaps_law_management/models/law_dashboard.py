from odoo import api, fields, models
from datetime import date, timedelta


class LawDashboard(models.TransientModel):
    _name = 'law.dashboard'
    _description = 'لوحة تحكم المكتب القانوني'
    _rec_name = 'name'

    name = fields.Char(default='لوحة تحكم المكتب القانوني', readonly=True)

    active_cases = fields.Integer(string='القضايا النشطة', readonly=True)
    won_cases = fields.Integer(string='القضايا المكسوبة', readonly=True)
    lost_cases = fields.Integer(string='القضايا الخاسرة', readonly=True)
    settled_cases = fields.Integer(string='قضايا التسوية', readonly=True)
    hearings_this_week = fields.Integer(string='جلسات هذا الأسبوع', readonly=True)
    hearings_today = fields.Integer(string='جلسات اليوم', readonly=True)
    consultations_today = fields.Integer(string='استشارات اليوم', readonly=True)
    consultations_this_month = fields.Integer(string='استشارات هذا الشهر', readonly=True)
    pending_invoices = fields.Integer(string='فواتير غير مدفوعة', readonly=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    pending_amount = fields.Monetary(string='المبلغ غير المدفوع', readonly=True,
        currency_field='currency_id')
    unbilled_hours = fields.Float(string='ساعات غير مفوترة', readonly=True, digits=(16, 1))

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        today = date.today()
        week_end = today + timedelta(days=7)
        month_start = today.replace(day=1)

        Case = self.env['law.case']
        Hearing = self.env['law.hearing']
        Consultation = self.env['law.consultation']
        TimeEntry = self.env['law.time.entry']
        Invoice = self.env['account.move']

        res.update({
            'active_cases': Case.search_count([('state', 'in', ('open', 'in_progress'))]),
            'won_cases': Case.search_count([('state', '=', 'won')]),
            'lost_cases': Case.search_count([('state', '=', 'lost')]),
            'settled_cases': Case.search_count([('state', '=', 'settled')]),
            'hearings_this_week': Hearing.search_count([
                ('date', '>=', str(today)),
                ('date', '<=', str(week_end)),
                ('state', '=', 'scheduled'),
            ]),
            'hearings_today': Hearing.search_count([
                ('date', '>=', str(today)),
                ('date', '<', str(today + timedelta(days=1))),
                ('state', '=', 'scheduled'),
            ]),
            'consultations_today': Consultation.search_count([
                ('date', '>=', str(today)),
                ('date', '<', str(today + timedelta(days=1))),
                ('state', '=', 'scheduled'),
            ]),
            'consultations_this_month': Consultation.search_count([
                ('date', '>=', str(month_start)),
                ('state', '!=', 'cancelled'),
            ]),
        })

        invoices = Invoice.search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'not in', ('paid', 'in_payment')),
            ('law_case_id', '!=', False),
        ])
        res['pending_invoices'] = len(invoices)
        res['pending_amount'] = sum(invoices.mapped('amount_residual'))

        unbilled = TimeEntry.search([('invoiced', '=', False)])
        res['unbilled_hours'] = sum(unbilled.mapped('hours'))

        return res

    def action_refresh(self):
        new = self.env['law.dashboard'].create({})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'law.dashboard',
            'view_mode': 'form',
            'res_id': new.id,
            'target': 'main',
            'flags': {'mode': 'readonly'},
        }
