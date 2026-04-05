# Copyright 2016-2022 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, exceptions, fields, models


class CommissionCommission(models.Model):
    _name = "commission.commission"
    _description = "Commission"

    move_id = fields.Many2one(comodel_name="account.move", string="Journal Entry")
    name = fields.Many2one(comodel_name="account.move.line", string="Journal Item")
    scope = fields.Selection([("2023-2024", "2023-2024"), ("2024-2025", "2024-2025")],string="Scope",required=True)
    sales_person = fields.Many2one(comodel_name="res.users", string="Sales Person" , store=True)
    percent = fields.Float(string="Percent")
    partner = fields.Many2one(comodel_name="res.partner", related="name.partner_id", string="Partner")
    commission_date = fields.Date(related="name.date", string="Journal Item Date", store=True)
    amount = fields.Monetary(string='Amount', related='name.balance', currency_field='currency_id', store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', related='name.currency_id', store=True, readonly=True)
    # journal_id = fields.Many2one(comodel_name='account.move', string='Journal ID', related='name.id', readonly=True)
    # sales_team = fields.Many2one(comodel_name="crm.team", string="Sales Team", related='partner.team_id' , store=True, readonly=True)
    commission_amount = fields.Float(string="Commission Amount", compute="_compute_commission_amount", store=True)


    @api.depends('percent', 'amount')
    def _compute_commission_amount(self):
        for record in self:
            record.commission_amount = (record.percent / 100) * record.amount if record.percent else 0.0


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    has_commission = fields.Boolean(string="Has Commission")