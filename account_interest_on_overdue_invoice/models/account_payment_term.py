# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ammu Raj(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountPaymentTerms(models.Model):
    """ Module for extending account.payment.term model to add interest
    computation configuration features for computation of Interest in overdue
    invoices."""
    _inherit = "account.payment.term"

    interest_overdue_act = fields.Boolean(string="Interest on Overdue Invoices")
    interest_type = fields.Selection(
        string='Interest Type', help="Base duration for interest calculation",
        selection=[('daily', 'Daily'),
                   ('weekly', 'Weekly'),
                   ('monthly', 'Monthly'),
                    ('fixed', 'Fixed')], default='daily', copy=False)
    interest_percentage = fields.Float(string="Interest Percentage",
                                       default="0", digits=(12, 6),
                                       help="Interest percentage ratio per"
                                            " selected Interest type duration.")
    fixed_interest_amount = fields.Monetary(
        string='Fixed Interest Amount',
        currency_field='currency_id'
    )
    interest_account_id = fields.Many2one('account.account',
                                          string='Account for Interest',
                                          company_dependent=True,
                                          domain="[('deprecated', '=', "
                                                 "False),('internal_group',"
                                                 "'=','income')]",
                                          help="Account used for creating "
                                               "accounting entries.")
    

    
    @api.constrains('interest_percentage')
    def _check_interest_percentage(self):
        """ check constrains for validating the interest rate in percentage
        is not negative"""
        for rec in self:
            if rec.interest_overdue_act and rec.interest_percentage <= 0:
                raise ValidationError(_('Enter Positive value as Interest '
                                      'percentage'))

class AccountPaymentTermLine(models.Model):
    """Extend account.payment.term.line to add fixed interest amount."""
    _inherit = "account.payment.term.line"
    
    currency_id = fields.Many2one(
            'res.currency',
            string="Currency",
            related='payment_id.company_id.currency_id',
            store=True,
            readonly=True
        )
    
    fixed_interest_amount = fields.Monetary(
        string='Fixed Interest Amount',
        currency_field='currency_id'
    )
    
    # @api.onchange('payment_id')
    # def _onchange_payment_id(self):
    #     """Update visibility of fixed_interest_amount depending on interest_type."""
    #     if self.payment_id.interest_type != 'fixed':
    #         self.fixed_interest_amount = 0.0    