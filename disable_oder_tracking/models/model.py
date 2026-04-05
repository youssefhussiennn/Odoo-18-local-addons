from odoo import models, fields

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    partner_id = fields.Many2one(tracking=False)
    company_id = fields.Many2one(tracking=False)
    partner_name = fields.Char(tracking=False)
    contact_name = fields.Char(tracking=False)
    email_from = fields.Char(tracking=False)
    phone = fields.Char(tracking=False)