import logging

from odoo import models, fields, api, _
from odoo import tools
from datetime import datetime
from num2words import num2words


from odoo.exceptions import UserError, ValidationError


class StockPayment(models.Model):
    _inherit = "account.payment"

    is_document = fields.Boolean()

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Customer/Vendor",
        store=True, readonly=False, ondelete='restrict',
        # compute='_compute_partner_id',
        # domain="[('user_id','=',uid)]",
        # '|', ('parent_id','=', False), ('is_company','=', True)
        tracking=True,
        check_company=True)
    destination_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Destination Account',
        store=True, readonly=False,
        compute='_compute_destination_account_id',
        # ('user_type_id.type', 'in', ('receivable', 'payable')),
        domain="[('company_ids', 'in', company_id)]",
        check_company=True)

    @api.onchange('payment_type')
    def compute_flag(self):
        for this in self:
            if this.payment_type == 'inbound':
                this.journal = 'in'
            elif this.payment_type == 'outbound':
                this.journal = 'out'

    journal = fields.Char(compute='compute_flag')

    @api.onchange('payment_type')
    def _check_on_post_type(self):
        for this in self:
            this.post_type = 'single'
        #     this.journal_id =
            # if any(line.partner_id != all_lines[0].partner_id for line in all_lines):
            #         raise UserError(_(
            #                 "The journal entry %s reached an invalid state relative to its payment.\n"
            #                 "To be consistent, the journal items must share the same partner."
            # ) % move.display_name) False

    # @api.depends('is_internal_transfer')
    # def _compute_destination_account_id(self):
    #         # self.destination_account_id = False
    #         for pay in self:
    #                 if pay.is_internal_transfer:
    #                         pay.destination_account_id = pay.journal_id.company_id.transfer_account_id
    #                 elif pay.partner_type == 'customer' and not pay.is_document:
    #                         # Receive money from invoice or send money to refund it.
    #                         if pay.partner_id:
    #                                 pay.destination_account_id = pay.partner_id.with_company(pay.company_id).property_account_receivable_id
    #                         else:
    #                                 pay.destination_account_id = self.env['account.account'].search([
    #                                         ('company_id', '=', pay.company_id.id),
    #                                         ('internal_type', '=', 'receivable'),
    #                                 ], limit=1)
    #                 elif pay.partner_type == 'supplier' and not pay.is_document:
    #                         # Send money to pay a bill or receive money to refund it.
    #                         if pay.partner_id:
    #                                 pay.destination_account_id = pay.partner_id.with_company(pay.company_id).property_account_payable_id
    #                         else:
    #                                 pay.destination_account_id = self.env['account.account'].search([
    #                                         ('company_id', '=', pay.company_id.id),
    #                                         ('internal_type', '=', 'payable'),
    #                                 ], limit=1)

    post_type = fields.Selection([('single', 'Single Account'), ('multi', 'Multiple Accounts')], default='single',
                                 string='Post Difference In To')

    writeoff_multi_acc_ids = fields.One2many('writeoff.accounts', 'payment_id', string='Write Off Accounts')

    numinwords = fields.Char(string='Total in words', compute='_getnumbernew', store=False)

    @api.depends('amount')
    def _getnumbernew(self):
        for rec in self:

            numinwords = num2words(float(rec.amount), lang='ar',)
            numinwords = ('مبلغ وقدره {} جنيه مصري فقط لاغير').format(numinwords)

            rec.numinwords = numinwords

    # @api.onchange('date')
    # def _compute_company_date(self):
    #         self.company_id = self.env.user.company_id.id

    # # @api.onchange('post_type')
    # # def _compute_empty_accounts(self):
    # #         if self.post_type == 'multi':
    # #                 self.writeoff_multi_acc_ids = [5,0,0]

    # #         if self.post_type == 'multi':
    # #                 self.destination_account_id = False
    # @api.onchange('writeoff_multi_acc_ids')
    # def _compute_multi_account(self):
    #         total = 0
    #         if self.writeoff_multi_acc_ids:
    #                 for line in self.writeoff_multi_acc_ids:
    #                         total += line.amount
    #         self.amount = total

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, *, force_balance=False, **kwargs):
        ''' Prepare the dictionary to create the default account.move.lines for the current payment. '''
        self.ensure_one()
        write_off_line_vals = write_off_line_vals or {}

        if not self.outstanding_account_id:
            raise UserError(_(
                "You can't create a new payment without an outstanding payments/receipts account set either "
                "on the company or the %s payment method in the %s journal.",
                self.payment_method_line_id.name, self.journal_id.display_name
            ))

        # Compute amounts.
        write_off_amount_currency = write_off_line_vals.get('amount', 0.0)
        if self.payment_type == 'inbound':
            liquidity_amount_currency = self.amount
        elif self.payment_type == 'outbound':
            liquidity_amount_currency = -self.amount
            write_off_amount_currency *= -1
        else:
            liquidity_amount_currency = write_off_amount_currency = 0.0

        write_off_balance = self.currency_id._convert(
            write_off_amount_currency,
            self.company_id.currency_id,
            self.company_id,
            self.date,
        )
        liquidity_balance = self.currency_id._convert(
            liquidity_amount_currency,
            self.company_id.currency_id,
            self.company_id,
            self.date,
        )
        counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
        counterpart_balance = -liquidity_balance - write_off_balance
        currency_id = self.currency_id.id

        # Label for journal items (no internal transfer anymore).
        payment_display_name = {
            'outbound-customer': _("Customer Reimbursement"),
            'inbound-customer': _("Customer Payment"),
            'outbound-supplier': _("Vendor Payment"),
            'inbound-supplier': _("Vendor Reimbursement"),
        }
        default_line_name = payment_display_name.get(
            f'{self.payment_type}-{self.partner_type}',
            _("Default Payment")
        )
        liquidity_line_name = self.payment_reference or default_line_name

        if self.post_type == 'single':
            line_vals_list = [
                # Liquidity line
                {
                    'name': self.payment_reference if self.payment_reference else liquidity_line_name,

                    'date_maturity': self.date,
                    'amount_currency': liquidity_amount_currency,
                    'currency_id': currency_id,
                    'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
                    'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': self.outstanding_account_id.id,
                },
                # Counterpart line
                {
                    'name': self.payment_reference if self.payment_reference else liquidity_line_name,

                    'date_maturity': self.date,
                    'amount_currency': counterpart_amount_currency,
                    'currency_id': currency_id,
                    'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
                    'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': self.destination_account_id.id,
                },
            ]
        else:  # multi
            line_vals_list = [
                {
                    'name': self.payment_reference if self.payment_reference else liquidity_line_name,
                    'date_maturity': self.date,
                    'amount_currency': liquidity_amount_currency,
                    'currency_id': currency_id,
                    'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
                    'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': self.outstanding_account_id.id,
                }
            ]
            for account_line in self.writeoff_multi_acc_ids:
                line_vals_list.append({
                    'name': self.payment_reference if self.payment_reference else account_line.name or default_line_name,
                    'date_maturity': self.date,
                    'amount_currency': account_line.amount,
                    'currency_id': currency_id,
                    'debit': account_line.amount if liquidity_balance < 0.0 else 0.0,
                    'credit': -account_line.amount if liquidity_balance > 0.0 else 0.0,
                    'partner_id': account_line.writeoff_partner_id.id,
                    'account_id': account_line.writeoff_account_id.id,
                    'analytic_distribution': account_line.analytic_distribution,
                    'analytic_tag_ids': [(4, tag, None) for tag in account_line.analytic_tag_ids.ids],
                })

        # Write-off line
        if not self.currency_id.is_zero(write_off_amount_currency):
            line_vals_list.append({
                'name': self.payment_reference if self.payment_reference else write_off_line_vals.get('name') or default_line_name,
                'amount_currency': write_off_amount_currency,
                'currency_id': currency_id,
                'debit': write_off_balance if write_off_balance > 0.0 else 0.0,
                'credit': -write_off_balance if write_off_balance < 0.0 else 0.0,
                'partner_id': self.partner_id.id,
                'account_id': write_off_line_vals.get('account_id'),
            })

        return line_vals_list

    def _synchronize_from_moves(self, changed_fields):
        ''' Update the account.payment regarding its related account.move.
        Also, check both models are still consistent.
        :param changed_fields: A set containing all modified fields on account.move.
        '''
        if self._context.get('skip_account_move_synchronization'):
            return

        for pay in self.with_context(skip_account_move_synchronization=True):
            # After the migration to 14.0, the journal entry could be shared between the account.payment and the
            # account.bank.statement.line. In that case, the synchronization will only be made with the statement line.
            if pay.move_id.statement_line_id:
                continue

            move = pay.move_id
            move_vals_to_write = {}
            payment_vals_to_write = {}
            if 'journal_id' in changed_fields:
                pay.with_context(skip_account_move_synchronization=False)
                pay._synchronize_to_moves({'journal_id'})

                if pay.journal_id.type not in ('bank', 'cash'):
                    raise UserError(_("A payment must always belongs to a bank or cash journal."))

            if 'line_ids' in changed_fields:
                all_lines = move.line_ids
                liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

                # if writeoff_lines and len(writeoff_lines.account_id) != 1:
                #         raise UserError(_(
                #         "Journal Entry %s is not valid. In order to proceed, "
                #         "all optional journal items must share the same account.",
                #         move.display_name,
                #         ))
                # if len(liquidity_lines) != 1:
                #         raise UserError(_(
                #                 "Journal Entry %s is not valid. In order to proceed, the journal items must "
                #                 "include one and only one outstanding payments/receipts account.",
                #                 move.display_name,
                #         ))

                # if len(counterpart_lines) != 1:
                #         raise UserError(_(
                #                 "Journal Entry %s is not valid. In order to proceed, the journal items must "
                #                 "include one and only one receivable/payable account (with an exception of "
                #                 "internal transfers).",
                #                 move.display_name,
                #         ))

                if any(line.currency_id != all_lines[0].currency_id for line in all_lines):
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, the journal items must "
                        "share the same currency.",
                        move.display_name,
                    ))

                # if any(line.partner_id != all_lines[0].partner_id for line in all_lines):
                #         raise UserError(_(
                #                 "The journal entry %s reached an invalid state relative to its payment.\n"
                #                 "To be consistent, the journal items must share the same partner."
                # ) % move.display_name)

                if counterpart_lines.account_id.account_type == 'receivable':
                    partner_type = 'customer'
                else:
                    partner_type = 'supplier'

                liquidity_amount = liquidity_lines.amount_currency

                move_vals_to_write.update({
                    'currency_id': liquidity_lines.currency_id.id,
                    'partner_id': liquidity_lines.partner_id.id,
                })
                payment_vals_to_write.update({
                    'amount': abs(liquidity_amount),
                    'partner_type': partner_type,
                    'currency_id': liquidity_lines.currency_id.id,
                    'destination_account_id': counterpart_lines.account_id.id if counterpart_lines else (writeoff_lines.account_id.id if len(writeoff_lines) == 1 else False),
                    'partner_id': liquidity_lines.partner_id.id,
                })
                if liquidity_amount > 0.0:
                    payment_vals_to_write.update({'payment_type': 'inbound'})
                elif liquidity_amount < 0.0:
                    payment_vals_to_write.update({'payment_type': 'outbound'})

            move.write(move._cleanup_write_orm_values(move, move_vals_to_write))
            pay.write(move._cleanup_write_orm_values(pay, payment_vals_to_write))

    def _synchronize_to_moves(self, changed_fields):
        for pay in self:
            move = pay.move_id

            vals = {}
            if 'date' in changed_fields and pay.date != move.date:
                vals['date'] = pay.date
            if 'payment_reference' in changed_fields and pay.payment_reference != move.payment_reference:
                vals['payment_reference'] = pay.payment_reference
            if 'journal_id' in changed_fields and pay.journal_id != move.journal_id:
                vals['journal_id'] = pay.journal_id.id
            if 'currency_id' in changed_fields and pay.currency_id != move.currency_id:
                vals['currency_id'] = pay.currency_id.id
            if vals:
                move.write(vals)

            liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

            # Update move lines according to payment type
            if liquidity_lines and 'payment_type' in changed_fields:
                if pay.payment_type == 'inbound':
                    liquidity_lines.write({
                        'debit': pay.amount,
                        'credit': 0.0,
                        'currency_id': pay.currency_id.id,
                        'amount_currency': pay.amount if pay.currency_id != pay.company_currency_id else 0.0,
                    })
                elif pay.payment_type == 'outbound':
                    liquidity_lines.write({
                        'debit': 0.0,
                        'credit': pay.amount,
                        'currency_id': pay.currency_id.id,
                        'amount_currency': -pay.amount if pay.currency_id != pay.company_currency_id else 0.0,
                    })

            if counterpart_lines and 'partner_type' in changed_fields:
                if pay.partner_type == 'customer':
                    counterpart_lines.write({'account_id': pay.destination_account_id.id})
                elif pay.partner_type == 'supplier':
                    counterpart_lines.write({'account_id': pay.destination_account_id.id})

            # Update partner
            if 'partner_id' in changed_fields and counterpart_lines:
                counterpart_lines.write({'partner_id': pay.partner_id.id})

    def unlink(self):
        if self.state == 'posted':
            raise UserError(_("You cannot delete an entry which has been posted once."))

        return super(StockPayment, self).unlink()

    @api.onchange('destination_account_id')
    def get_value_require(self):
        for this in self:
            if this.destination_account_id:

                this.partne_required = False

                if this.destination_account_id.is_vendor:
                    this.partne_required = True
                if this.destination_account_id.is_customer:
                    this.partne_required = True
            else:
                this.partne_required = False

    partne_required = fields.Boolean(compute="get_value_require")

    # @api.onchange('destination_account_id','post_type','partner_id','journal_id')
    # def onchange_account_id(self):
    #         b={}
    #         for this in self:
    #             if this.destination_account_id:
    #                 if this.destination_account_id.is_customer == True:
    #                         b ={'domain': {
    #                                 'partner_id': [('is_customer', '=', True)],
    #                                 },
    #                         'required': {'partner_id': [('is_customer', '=', True)]}}
    #                 elif this.destination_account_id.is_vendor == True:
    #                         b ={'domain': {
    #                                 'partner_id': [('is_vendor', '=', True)],
    #                                 },
    #                         'required': {'partner_id': [('is_vendor', '=', True)]}}
    #                 else:
    #                         b ={'domain': {
    #                                 'partner_id': [(1,'=',1)],
    #                                  }}
    #         return b

    def write(self, vals):
        # OVERRIDE
        res = super(StockPayment, self).write(vals)
        # Only allow valid journals for customer/supplier payments
        for rec in self:
            if rec.journal not in ['in', 'out'] and rec.is_document:
                raise UserError(_("Please Select Journal"))
        return res


class writeoff_accounts(models.Model):
    _name = 'writeoff.accounts'

    writeoff_account_id = fields.Many2one('account.account', string="Difference Account", copy=False, required="1")
    writeoff_partner_id = fields.Many2one('res.partner', string="Partner", copy=False)
    name = fields.Char('Description')
    analytic_distribution = fields.Json()
    analytic_tag_ids = fields.Many2many('account.analytic.tag')
    amount = fields.Monetary(string='Payment Amount', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    payment_id = fields.Many2one('account.payment', string='Payment Record')


#     required_analytical = fields.Boolean(related='writeoff_account_id.required_analytical')

    flag = fields.Boolean(default=False, compute='_compute_partner_filter_multi_lines')

    @api.onchange('writeoff_account_id')
    def _compute_partner_filter_multi_lines(self):
        b = {}
        for rec in self:
            user_flag = self.env.user.has_group('account.group_account_invoice')
            user_flag1 = self.env.user.has_group('__export__.res_groups_132_f7b30e69')
            if user_flag1 == True:
                rec.flag = True
                b = {'domain': {
                    'writeoff_partner_id': ['|', ('company_id', '=', False), ('company_id', '=', self.env.company.id)],
                }}
            elif user_flag == True:
                rec.flag = True
                b = {'domain': {
                    'writeoff_partner_id': ['|', ('company_id', '=', False), ('company_id', '=', self.env.company.id)],
                }}
            else:
                rec.flag = False
                b = {'domain': {
                    'writeoff_partner_id': ['|', ('company_id', '=', False), ('company_id', '=', self.env.company.id), ('user_id', '=', self.env.user.id)],
                }}
        return b

    @api.onchange('writeoff_account_id')
    def get_value_require(self):
        for this in self:
            if this.writeoff_account_id:

                this.partne_required = False
                # this.analytic_req = False
                # if this.writeoff_account_id.code[0] == '5':
                #         this.analytic_req = True
                # else:
                #         this.analytic_req = False

                if this.writeoff_account_id.is_vendor:
                    this.partne_required = True
                if this.writeoff_account_id.is_customer:
                    this.partne_required = True
            else:
                this.partne_required = False
                # this.analytic_req = False
    partne_required = fields.Boolean(compute="get_value_require")

#     @api.onchange('writeoff_account_id')
#     def onchange_account_id(self):
#         b={}
#         for this in self:
#             if this.writeoff_account_id.is_customer == True:
#                 b ={'domain': {'writeoff_partner_id': [('is_customer', '=', True)]},
#                     'required': {'writeoff_partner_id': [('is_customer', '=', True)]}}
#             elif this.writeoff_account_id.is_vendor == True:
#                 b ={'domain': {'writeoff_partner_id': [('is_vendor', '=', True)]},
#                     'required': {'writeoff_partner_id': [('is_vendor', '=', True)]}}

#             else:
#                 b ={'domain': {'writeoff_partner_id': [(1,'=',1)]}}
#             return b


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    pay_type = fields.Selection([('in', 'IN'), ('out', 'OUT')])


class AccountAccount(models.Model):

    _inherit = 'account.account'

    is_customer = fields.Boolean('Customer')
    is_vendor = fields.Boolean('Vendor')
