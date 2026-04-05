# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResUsersAccountType(models.Model):
    _name = "res.users.account.type"
    _description = "Account Types for Users"
    _rec_name = "name"

    name = fields.Char(string="Name", required=True)
    account_type = fields.Selection(
        selection=lambda self: self.env['account.account']._fields['account_type'].selection,
        string="Account Type",
        required=True,
        unique=True
    )


class ResUsers(models.Model):
    _inherit = 'res.users'

    allowed_account_type_ids = fields.Many2many(
        'res.users.account.type',
        string="Allowed Account Types"
    )

    @api.model
    def init(self):
        """Auto populate res.users.account.type with all account.account selection values"""
        Account = self.env['account.account']
        selection = Account._fields['account_type'].selection  # list of (value, label)
        TypeModel = self.env['res.users.account.type']

        for value, label in selection:
            if not TypeModel.search([('account_type', '=', value)], limit=1):
                TypeModel.create({
                    'name': label,
                    'account_type': value,
                })


# class AccountAccount(models.Model):
#     _inherit = "account.account"

#     def _search(self, args, offset=0, limit=None, order=None):
#         user = self.env.user
#         # Only filter for non-admins
#         if not user.has_group("base.group_system") and user.allowed_account_type_ids:
#             args = args + [("account_type", "in", user.allowed_account_type_ids.mapped("account_type"))]
#         return super()._search(args, offset=offset, limit=limit, order=order)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _search(self, args, offset=0, limit=None, order=None):
        user = self.env.user
        if not user.has_group("base.group_system") and user.allowed_account_type_ids:
            allowed_types = user.allowed_account_type_ids.mapped("account_type")
            args = args + [("account_id.account_type", "in", allowed_types)]
        return super()._search(args, offset=offset, limit=limit, order=order)

    @api.model
    def fields_view_get(self, view_id=None, view_type="form", toolbar=False, submenu=False):
        res = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        user = self.env.user
        if not user.has_group("base.group_system") and user.allowed_account_type_ids:
            allowed_types = user.allowed_account_type_ids.mapped("account_type")
            domain = [("account_type", "in", allowed_types)]
            if "fields" in res and "account_id" in res["fields"]:
                res["fields"]["account_id"]["domain"] = domain
        return res