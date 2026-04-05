from odoo import models, fields, api, _


class AccountAccount(models.Model):
    _inherit = "account.account"

    hidden_report = fields.Boolean(default= False, string="Hidden in Report")
