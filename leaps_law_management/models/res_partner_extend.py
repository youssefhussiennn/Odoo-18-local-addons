from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_legal_client = fields.Boolean('موكل قانوني')
    case_ids = fields.One2many('law.case', 'client_id', string='القضايا')
    case_count = fields.Integer(compute='_compute_case_count', string='عدد القضايا')
    consultation_ids = fields.One2many('law.consultation', 'client_id', string='الاستشارات القانونية')
    consultation_count = fields.Integer(compute='_compute_consultation_count', string='عدد الاستشارات')

    def _compute_case_count(self):
        for rec in self:
            rec.case_count = len(rec.case_ids)

    def _compute_consultation_count(self):
        for rec in self:
            rec.consultation_count = len(rec.consultation_ids)
