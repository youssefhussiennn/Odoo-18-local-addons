# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Account_Payment(models.Model):
    _inherit="account.payment"


    partner_id = fields.Many2one(
            comodel_name='res.partner',
            string="Customer/Vendor",
            store=True, readonly=False, ondelete='restrict',
            # compute='_compute_partner_id',
            # domain="['|',('company_id','!=',False),('company_id','=',company_id),('user_id', '=', uid)]",
            tracking=True,
            check_company=True)

    flag = fields.Boolean(default=False, compute='_compute_partner_filter')

    @api.onchange('date')
    def _compute_partner_filter(self):
        b={}
        for rec in self:
            user_flag = self.env.user.has_group('account.group_account_invoice')
            user_flag1 = self.env.user.has_group('__export__.res_groups_132_f7b30e69')
            if user_flag1 == True:
                rec.flag = True
                b ={'domain': {
                        'partner_id': ['|',('company_id','=',False),('company_id','=',self.env.company.id)],
                    }}
            elif user_flag == True:
                rec.flag = True
                b ={'domain': {
                        'partner_id': ['|',('company_id','=',False),('company_id','=',self.env.company.id)],
                    }}
            else:
                rec.flag = False
                b ={'domain': {
                        'partner_id': ['|',('company_id','=',False),('company_id','=',self.env.company.id),('user_id', '=', self.env.user.id)],
                    }}
        return b


