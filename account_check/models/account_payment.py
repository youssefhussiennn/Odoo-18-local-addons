# -*- coding: utf-8 -*-
import logging

from odoo import fields, models, _, api
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountPaymentMethodLine(models.Model):
    _inherit = "account.payment.method.line"

    safety_check = fields.Boolean()

class AccountPaymentMethod(models.Model):
    _inherit = "account.payment.method"

    @api.model
    def _get_payment_method_information(self):
        """
        Contains details about how to initialize a payment method with the code x.
        The contained info are:
            mode: Either unique if we only want one of them at a single time (payment acquirers for example)
                   or multi if we want the method on each journal fitting the domain.
            domain: The domain defining the eligible journals.
            currency_id: The id of the currency necessary on the journal (or company) for it to be eligible.
            country_id: The id of the country needed on the company for it to be eligible.
            hidden: If set to true, the method will not be automatically added to the journal,
                    and will not be selectable by the user.
        """
        return {
            'manual': {'mode': 'multi', 'domain': [('type', 'in', ('bank', 'cash'))]},
            'received_third_check': {'mode': 'multi', 'domain': [('type', 'in', ('bank', 'cash'))]},

            'received_safty_check': {'mode': 'multi', 'domain': [('type', 'in', ('bank', 'cash'))]},

            'delivered_third_check': {'mode': 'multi', 'domain': [('type', 'in', ('bank', 'cash'))]},
            'issue_check': {'mode': 'multi', 'domain': [('type', 'in', ('bank', 'cash'))]},
        }
        
class AccountPayment(models.Model):
    _inherit = 'account.payment'

    safety_check = fields.Boolean()

    check_ids = fields.Many2many(comodel_name="account.check", relation="payment_id", string="Checks",
                                 states={'draft': [('readonly', '=', False)]})

    # only for v8 comatibility where more than one check could be received
    # or issued
    check_ids_copy = fields.Many2many(
        related='check_ids',
        readonly=True,
    )
    readonly_currency_id = fields.Many2one(
        related='currency_id',
        readonly=True,
    )
    readonly_amount = fields.Monetary(
        related='amount',
        readonly=True,
    )
    # we add this field for better usability on issue checks and received
    # checks. We keep m2m field for backward compatibility where we allow to
    # use more than one check per payment
    check_id = fields.Many2one(
        'account.check',
        compute='_compute_check',
        string='Check',
    )

    treasury_journal_id = fields.Many2one(comodel_name='account.journal', string='Treasury')

    @api.onchange('journal_id')
    def _onchange_journal_id_treasury(self):
        for this in self:
            this.treasury_journal_id = this.journal_id


    @api.depends('check_ids')
    def _compute_check(self):
        for rec in self:
            # we only show checks for issue checks or received thid checks
            # if len of checks is 1
            if rec.payment_method_code in (
                    'received_third_check',
                    'received_safty_check',
                    'issue_check',) and len(rec.check_ids) == 1:
                rec.check_id = rec.check_ids[0].id
            else:
                rec.check_id = False


    # check fields, just to make it easy to load checks without need to create
    # them by a m2o record
    check_name = fields.Char(
        'Check Name',
        readonly=True,
        copy=False,
        states={'draft': [('readonly', False)]},
    )
    check_number = fields.Char(
        'Check Number',
        readonly=True,
        force_save=True,
        states={'draft': [('readonly', False)]},
        copy=False
    )
    # check_number_id = fields.Many2one(comodel_name='checkbook.sequence', string='Check Number',
    #                                   states={'draft': [('readonly', False)]})
    check_issue_date = fields.Date(
        'Check Issue Date',
        readonly=True,
        copy=True,
        states={'draft': [('readonly', False)]},
        default=fields.Date.context_today,
    )
    check_payment_date = fields.Date(
        'Check Payment Date',
        readonly=True,
        copy=True,
        help="Only if this check is post dated",
        states={'draft': [('readonly', False)]}
    )
    # checkbook_id = fields.Many2one(
    #     'account.checkbook',
    #     'Checkbook',
    #     readonly=True,
    #     states={'draft': [('readonly', False)]},
    # )
    # check_subtype = fields.Selection(
    #     related='checkbook_id.issue_check_subtype',
    #     readonly=True,
    # )
    check_bank_id = fields.Many2one(
        'res.bank',
        'Check Bank',
        readonly=True,
        copy=True,
        states={'draft': [('readonly', False)]}
    )
    # check_owner_vat = fields.Char(
    #     'Check Owner Vat',
    #     readonly=True,
    #     copy=False,
    #     states={'draft': [('readonly', False)]}
    # )
    check_owner_name = fields.Char(
        'Check Owner Name',
        readonly=True,
        copy=True,
        states={'draft': [('readonly', False)]}
    )
    # this fields is to help with code and view
    check_type = fields.Char(
        compute='_compute_check_type',
    )
    # checkbook_block_manual_number = fields.Boolean(
    #     related='checkbook_id.block_manual_number',
    # )


    check_count = fields.Integer(compute='compute_count')


    @api.onchange('partner_id','partner_type','payment_method_line_id')
    def _compute_destination_account_id(self):
        # self.destination_account_id = False
        for pay in self:
            # if pay.is_internal_transfer:
            #     pay.destination_account_id = pay.journal_id.company_id.transfer_account_id
            
            if self.payment_method_line_id.safety_check:
                    pay.safety_check = True
                    pay.destination_account_id = self.journal_id.safty_check_account_id 

            if pay.is_document == False:
                if pay.partner_type == 'customer':
                    # Receive money from invoice or send money to refund it.
                    if self.payment_method_line_id.safety_check:
                        pay.safety_check = True
                        pay.destination_account_id = self.journal_id.safty_check_account_id 
                    elif pay.partner_id:
                        pay.destination_account_id = pay.partner_id.with_company(pay.company_id).property_account_receivable_id
                    else:
                        pay.destination_account_id = self.env['account.account'].search([
                            
                            ('account_type', '=', 'receivable'),
                            ('deprecated', '=', False),
                        ], limit=1)
                elif pay.partner_type == 'supplier':
                    # Send money to pay a bill or receive money to refund it.
                    if self.payment_method_line_id.safety_check:
                        pay.safety_check = True
                        pay.destination_account_id = self.journal_id.safty_check_account_id 

                    elif pay.partner_id:
                        pay.destination_account_id = pay.partner_id.with_company(pay.company_id).property_account_payable_id
                    else:
                        pay.destination_account_id = self.env['account.account'].search([
                            
                            ('account_type', '=', 'payable'),
                            ('deprecated', '=', False),
                        ], limit=1)

    # @api.onchange('payment_method_line_id','partner_id')
    # def onchange_payment_method_line_check_safty(self):
    #     if self.payment_method_line_id and self.payment_method_line_id.safety_check:
    #         self.safety_check = True
    #         if self.destination_account_id and self.destination_account_id != self.journal_id.safty_check_account_id:
    #             self.destination_account_id = self.journal_id.safty_check_account_id 

    def compute_count(self):
        for record in self:
            record.check_count = self.env['account.check'].search_count(
                [('payment_id', '=', self.id)])

    def get_checks(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Checks',
            'view_mode': 'list,form',
            'res_model': 'account.check',
            'domain': [('payment_id', '=', self.id)],
            'context': "{'create': False}"
        }

    @api.depends('payment_method_code')
    def _compute_check_type(self):
        for rec in self:
            if rec.payment_method_code:
                if rec.payment_method_code == 'issue_check':
                    rec.check_type = 'issue_check'
                elif rec.payment_method_code in ['received_third_check', 'received_safty_check', 'delivered_third_check']:
                    rec.check_type = 'third_check'
                else:
                    rec.check_type = ''
            else:
                rec.check_type = ''

    # @api.constrains('check_ids')
    @api.onchange('check_ids', 'payment_method_code')
    def onchange_checks(self):
        # we only overwrite if payment method is delivered
        if self.payment_method_code == 'delivered_third_check':
            self.amount = sum(self.check_ids.mapped('amount'))

    # # TODo activar
    @api.model
    @api.onchange('check_number')
    def change_check_number(self):
        # TODO make default padding a parameter
        if self.payment_method_code in ['received_third_check', 'received_safty_check', 'issue_check']:
            if not self.check_number:
                check_name = False
            else:
                # TODO make optional
                padding = 8
                if len(str(self.check_number)) > padding:
                    padding = len(str(self.check_number))
                check_name = ('%%0%sd' % padding % int(self.check_number))
            self.check_name = check_name


    @api.onchange('check_issue_date', 'check_payment_date')
    def onchange_date(self):
        if (
                self.check_issue_date and self.check_payment_date and
                self.check_issue_date > self.check_payment_date):
            self.check_payment_date = False
            raise UserError(
                _('Check Payment Date must be greater than Issue Date'))

    @api.model
    @api.onchange('partner_id')
    def onchange_partner_check(self):
        commercial_partner = self.partner_id.commercial_partner_id
        self.check_bank_id = (
                commercial_partner.bank_ids and
                commercial_partner.bank_ids[0].bank_id.id or False)
        self.check_owner_name = commercial_partner.name
        # TODO use document number instead of vat?
        # self.check_owner_vat = commercial_partner.vat

    def cancel(self):
        res = super(AccountPayment, self).cancel()
        for rec in self:
            checks = self.env['account.check'].search([('payment_id', '=', rec.id)])
            checks.filtered(lambda check: check.state != 'draft').cancel_action()

        return res

    def create_check(self, check_type, operation, bank, safty_type = False):
        # , bank
        self.ensure_one()
        # if self.payment_method_code == 'received_third_check':
        check_number = self.check_number
        # else:
        #     check_number = self.check_number_id.name
        # print('check_number')
        # print(check_number)
        # print('check_number')
        check_vals = {
            'bank_id': self.check_bank_id.id,
            'partner_id': self.partner_id.id,
            'owner_name': self.check_owner_name,
            # 'owner_vat': self.check_owner_vat,
            'number': check_number or self.payment_reference,
            'name': check_number or self.payment_reference,
            # 'checkbook_id': self.checkbook_id.id,
            'issue_date': self.check_issue_date,
            'type': self.check_type,
            'journal_id': self.journal_id.id,
            'treasury_journal_id': self.treasury_journal_id.id,
            'amount': self.amount,
            'payment_date': self.check_payment_date,
            'currency_id': self.currency_id.id,
            'payment_id': self.id,
            'payment_method_line_id': self.payment_method_line_id.id,

            'safety_check': safty_type
        }
        # print("emp")
        # print(self.currency_id)
        # print(self.amount)
        check = self.env['account.check'].create(check_vals)
        # print("??")
        # print(stop)
        self.check_ids = [(4, check.id, False)]
        check._add_operation(
            operation, self, self.partner_id, date=self.check_payment_date)
        return check

    # # override default method
    # def action_draft(self):
    #     res = super(AccountPayment, self).action_draft()
    #     # checks = self.env['account.check'].search([('payment_id', '=', self.id)])
    #     # checks.filtered(lambda check: check.state != 'draft').button_draft()
    #     # checks.with_context(force_delete=True).unlink()
    #     return res

    # override default method
    # def _prepare_move_line_default_vals(self, write_off_line_vals=None):
    #     ''' Prepare the dictionary to create the default account.move.lines for the current payment.
    #     :param write_off_line_vals: Optional dictionary to create a write-off account.move.line easily containing:
    #         * amount:       The amount to be added to the counterpart amount.
    #         * name:         The label to set on the line.
    #         * account_id:   The account on which create the write-off.
    #     :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
    #     '''
    #     self.ensure_one()
    #     write_off_line_vals = write_off_line_vals or {}

    #     if not self.outstanding_account_id:
    #         raise UserError(_(
    #             "You can't create a new payment without an outstanding payments/receipts account set on the %s journal.",
    #             self.journal_id.display_name))

    #     # Compute amounts.
    #     write_off_amount_currency = write_off_line_vals.get('amount', 0.0)

    #     # print(write_off_line_vals)
    #     # print(write_off_amount_currency)
    #     # print(self.amount)
    #     # print(self.payment_type)
    #     # print(s)
        
    #     if self.payment_type == 'inbound':
    #         # Receive money.
    #         liquidity_amount_currency = self.amount
    #     elif self.payment_type == 'outbound':
    #         # Send money.
    #         liquidity_amount_currency = -self.amount
    #         write_off_amount_currency *= -1
    #     else:
    #         liquidity_amount_currency = write_off_amount_currency = 0.0

    #     write_off_balance = self.currency_id._convert(
    #         write_off_amount_currency,
    #         self.company_id.currency_id,
    #         self.company_id,
    #         self.date,
    #     )
    #     liquidity_balance = self.currency_id._convert(
    #         liquidity_amount_currency,
    #         self.company_id.currency_id,
    #         self.company_id,
    #         self.date,
    #     )

    #     # new
    #     liquidity_account = False
    #     if self.payment_type in ('outbound', 'transfer'):
    #         if self.payment_method_code == 'issue_check':
    #             liquidity_account = self.journal_id.deferred_check_account_id.id
    #         else:
    #             liquidity_account = self.outstanding_account_id.id
    #     else:
    #         if self.payment_method_code == 'received_third_check':
    #             liquidity_account = self.journal_id.holding_check_account_id.id
    #         else:
    #             liquidity_account = self.destination_account_id.id
    #     # new
        
                
    #     counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
    #     counterpart_balance = -liquidity_balance - write_off_balance
    #     currency_id = self.currency_id.id

    #     if self.is_internal_transfer:
    #         if self.payment_type == 'inbound':
    #             liquidity_line_name = _('Transfer to %s', self.journal_id.name)
    #         else: # payment.payment_type == 'outbound':
    #             liquidity_line_name = _('Transfer from %s', self.journal_id.name)
    #     else:
    #         liquidity_line_name = self.payment_reference

    #     payment_display_name = {
    #         'outbound-customer': _("Customer Reimbursement"),
    #         'inbound-customer': _("Customer Payment"),
    #         'outbound-supplier': _("Vendor Payment"),
    #         'inbound-supplier': _("Vendor Reimbursement"),
    #     }

    #     default_line_name = self.env['account.move.line']._get_default_line_name(
    #         _("Internal Transfer") if self.is_internal_transfer else payment_display_name['%s-%s' % (self.payment_type, self.partner_type)],
    #         self.amount,
    #         self.currency_id,
    #         self.date,
    #         partner=self.partner_id,
    #     )

    #     line_vals_list = [
    #         # Liquidity line.
    #         {
    #             'name': liquidity_line_name or default_line_name,
    #             'date_maturity': self.date,
    #             'amount_currency': liquidity_amount_currency,
    #             'currency_id': currency_id,
    #             'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
    #             'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
    #             'partner_id': self.partner_id.id,
    #             'account_id': liquidity_account,
    #         },
    #         # Receivable / Payable.
    #         {
    #             'name': self.payment_reference or default_line_name,
    #             'date_maturity': self.date,
    #             'amount_currency': counterpart_amount_currency,
    #             'currency_id': currency_id,
    #             'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
    #             'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
    #             'partner_id': self.partner_id.id,
    #             'account_id': self.destination_account_id.id,
    #         },
    #     ]
    #     if not self.currency_id.is_zero(write_off_amount_currency):
    #         # Write-off line.
    #         line_vals_list.append({
    #             'name': write_off_line_vals.get('name') or default_line_name,
    #             'amount_currency': write_off_amount_currency,
    #             'currency_id': currency_id,
    #             'debit': write_off_balance if write_off_balance > 0.0 else 0.0,
    #             'credit': -write_off_balance if write_off_balance < 0.0 else 0.0,
    #             'partner_id': self.partner_id.id,
    #             'account_id': write_off_line_vals.get('account_id'),
    #         })

    #     # print('all_move_vals')
    #     # print(line_vals_list)
    #     # print('all_move_vals')
    #     # print(ha)
        
    #     return line_vals_list

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        # print(self.name)
        for rec in self:
            if rec.payment_method_code == 'received_third_check':
                # print("in")
                # print(res)
                rec.create_check('third_check', 'holding', rec.check_bank_id, False)


            #for the safty payment method
            elif rec.payment_method_code == 'received_safty_check':
                # print("in")
                # print(res)
                rec.create_check('third_check', 'holding', rec.check_bank_id, safty_type=True)


            elif rec.payment_method_code == 'issue_check':
                rec.create_check('issue_check', 'handed', rec.check_bank_id)
                # check = 
                # # checkbooks_sequence = self.env['checkbook.sequence'].search([('name', '=', check.number)])
                # checkbooks_sequence.write({'state': 'issued'})
            # print(re)
        
        return res

    def get_third_check_account(self):
        """
        For third checks, if we use a journal only for third checks, we use
        accounts on journal, if not we use company account
        """
        self.ensure_one()
        if self.payment_type in ('outbound', 'transfer'):
            account = self.journal_id.default_account_id
            methods_field = 'outbound_payment_method_line_ids'
        else:
            account = self.journal_id.payment_credit_account_id
            methods_field = 'inbound_payment_method_line_ids'
        if len(self.journal_id[methods_field]) > 1 or not account:
            account = self.journal_id._get_check_account('holding')
        return account

    def do_checks_operations(self, vals=None, cancel=False):
        """
        Check attached .ods file on this module to understand checks workflows
        This method is called from:
        * cancellation of payment to execute delete the right operation and
            unlink check if needed
        * from _get_liquidity_move_line_vals to add check operation and, if
            needded, change payment vals and/or create check and
        TODO si queremos todos los del operation podriamos moverlos afuera y
        simplificarlo ya que es el mismo en casi todos
        Tambien podemos simplficiar las distintas opciones y como se recorren
        los if
        """
        self.ensure_one()
        rec = self
        if not rec.check_type:
            # continue
            return vals
        if (
                rec.payment_method_code == 'received_third_check' and
                rec.payment_type == 'inbound'
                # and rec.partner_type == 'customer'
        ):
            operation = 'holding'
            if cancel:
                _logger.info('Cancel Receive Check')
                rec.check_ids._del_operation(self)
                rec.check_ids.unlink()
                return None

            _logger.info('Receive Check')
            self.create_check('third_check', operation, self.check_bank_id)
            vals['date_maturity'] = self.check_payment_date
            vals['account_id'] = self.get_third_check_account().id
            
        elif (
                rec.payment_method_code == 'received_safty_check' and
                rec.payment_type == 'inbound'
                # and rec.partner_type == 'customer'
        ):
            operation = 'holding'
            if cancel:
                _logger.info('Cancel Receive Check')
                rec.check_ids._del_operation(self)
                rec.check_ids.unlink()
                return None

            _logger.info('Receive Check')
            self.create_check('third_check', operation, self.check_bank_id, safty_type=True)
            vals['date_maturity'] = self.check_payment_date
            vals['account_id'] = self.get_third_check_account().id

        elif (
                rec.payment_method_code == 'delivered_third_check' and
                rec.payment_type == 'transfer'):

            # TODO we should make this method selectable for transfers
            inbound_method = (
                rec.destination_journal_id.inbound_payment_method_line_ids)
            if len(inbound_method) == 1 and (
                    inbound_method.code == 'received_third_check'):
                if cancel:
                    _logger.info('Cancel Transfer Check')
                    for check in rec.check_ids:
                        check._del_operation(self)
                        check._del_operation(self)
                        receive_op = check._get_operation('holding')
                        if receive_op.origin._name == 'account.payment':
                            check.journal_id = receive_op.origin.journal_id.id
                    return None

                _logger.info('Transfer Check')
                rec.check_ids._add_operation(
                    'transfered', rec, False, date=rec.payment_date)
                rec.check_ids._add_operation(
                    'holding', rec, False, date=rec.payment_date)
                rec.check_ids.write({
                    'journal_id': rec.destination_journal_id.id})
                vals['account_id'] = self.get_third_check_account().id
            elif rec.destination_journal_id.type == 'cash':
                if cancel:
                    _logger.info('Cancel Sell Check')
                    rec.check_ids._del_operation(self)
                    return None

                _logger.info('Sell Check')
                rec.check_ids._add_operation(
                    'selled', rec, False, date=rec.payment_date)
                vals['account_id'] = self.get_third_check_account().id
            else:
                if cancel:
                    _logger.info('Cancel Deposit Check')
                    rec.check_ids._del_operation(self)
                    return None

                _logger.info('Deposit Check')
                rec.check_ids._add_operation(
                    'deposited', rec, False, date=rec.payment_date)
                vals['account_id'] = self.get_third_check_account().id
        elif (
                rec.payment_method_code == 'delivered_third_check' and
                rec.payment_type == 'outbound'
                # and rec.partner_type == 'supplier'
        ):
            if cancel:
                _logger.info('Cancel Deliver Check')
                rec.check_ids._del_operation(self)
                return None

            _logger.info('Deliver Check')
            rec.check_ids._add_operation(
                'delivered', rec, rec.partner_id, date=rec.payment_date)
            vals['account_id'] = self.get_third_check_account().id
        elif (
                rec.payment_method_code == 'issue_check' and
                rec.payment_type == 'outbound'
                # and rec.partner_type == 'supplier'
        ):
            if cancel:
                _logger.info('Cancel Hand Check')
                rec.check_ids._del_operation(self)
                rec.check_ids.unlink()
                return None

            _logger.info('Hand Check')
            self.create_check('issue_check', 'handed', self.check_bank_id)
            vals['date_maturity'] = self.check_payment_date
            # if check is deferred, change account
            # if self.check_subtype == 'deferred':
            #     vals['account_id'] = self.journal_id._get_check_account(
            #         'deferred').id
        elif (
                rec.payment_method_code == 'issue_check' and
                rec.payment_type == 'transfer' and
                rec.destination_journal_id.type == 'cash'):
            if cancel:
                _logger.info('Cancel Withdrawal Check')
                rec.check_ids._del_operation(self)
                rec.check_ids.unlink()
                return None

            _logger.info('Hand Check')
            self.create_check('issue_check', 'withdrawed', self.check_bank_id)
            vals['date_maturity'] = self.check_payment_date
            # if check is deferred, change account
            # if self.check_subtype == 'deferred':
            #     vals['account_id'] = self.company_id._get_check_account(
            #         'deferred').id
        else:
            raise UserError(_(
                'This operatios is not implemented for checks:\n'
                '* Payment type: %s\n'
                '* Partner type: %s\n'
                '* Payment method: %s\n'
                '* Destination journal: %s\n' % (
                    rec.payment_type,
                    rec.partner_type,
                    rec.payment_method_code,
                    rec.destination_journal_id.type)))
        return vals

    def _get_liquidity_move_line_vals(self, amount):
        vals = super(AccountPayment, self)._get_liquidity_move_line_vals(
            amount)
        vals = self.do_checks_operations(vals=vals)
        return vals


    # def _seek_for_lines(self):
    #     ''' Helper used to dispatch the journal items between:
    #     - The lines using the temporary liquidity account.
    #     - The lines using the counterpart account.
    #     - The lines being the write-off lines.
    #     :return: (liquidity_lines, counterpart_lines, writeoff_lines)
    #     '''
    #     self.ensure_one()

    #     liquidity_lines = self.env['account.move.line']
    #     counterpart_lines = self.env['account.move.line']
    #     writeoff_lines = self.env['account.move.line']

    #     for line in self.move_id.line_ids:
    #         if line.account_id in (
    #                 self.journal_id.default_account_id,
    #                 self.journal_id.default_account_id,
    #                 self.journal_id.payment_credit_account_id,
    #                 # check this
    #                 self.journal_id.holding_check_account_id,
    #                 self.journal_id.deferred_check_account_id
    #                 # check this
    #         ):
    #             liquidity_lines += line
    #         elif line.account_id.internal_type in ('receivable', 'payable') or line.partner_id == line.company_id.partner_id:
    #             counterpart_lines += line
    #         else:
    #             writeoff_lines += line

    #     return liquidity_lines, counterpart_lines, writeoff_lines

    def _get_valid_liquidity_accounts(self):
        return (
            self.journal_id.default_account_id,
            # self.payment_method_line_id.payment_account_id,
            # self.journal_id.company_id.account_journal_payment_debit_account_id,
            # self.journal_id.company_id.account_journal_payment_credit_account_id,
            # check this  
            self.journal_id.holding_check_account_id,
            self.journal_id.deferred_check_account_id,
            # self.journal_id.safty_check_account_id
            # check this  
        )
class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'
    _description = 'Register Payment'

    
    # payment_method_code = fields.Char(
    #     related='payment_method_id.code',
    #     help="Technical field used to adapt the interface to the payment type selected.")
    # check fields, just to make it easy to load checks without need to create
    # them by a m2o record
    check_name = fields.Char(
        'Check Name',
        copy=False,
    )
    check_number = fields.Char(
        'Check Number',
        copy=False
    )
    check_bank_id = fields.Many2one(
        'res.bank',
        'Check Bank',
        copy=True,
    )
    check_owner_name = fields.Char(
        'Check Owner Name',
        copy=True,
    )
    check_payment_date = fields.Date(
        'Check Payment Date',
        copy=True,
        help="Only if this check is post dated",
    )

    @api.model
    @api.onchange('partner_id')
    def onchange_partner_check(self):
        commercial_partner = self.partner_id.commercial_partner_id
        self.check_bank_id = (
                commercial_partner.bank_ids and
                commercial_partner.bank_ids[0].bank_id.id or False)
        self.check_owner_name = commercial_partner.name

    @api.model
    @api.onchange('check_number')
    def change_check_number(self):
        # TODO make default padding a parameter
        if self.payment_method_code in ['received_third_check','received_safty_check']:
            if not self.check_number:
                check_name = False
            else:
                # TODO make optional
                padding = 8
                if len(str(self.check_number)) > padding:
                    padding = len(str(self.check_number))
                check_name = ('%%0%sd' % padding % int(self.check_number))
            self.check_name = check_name


    def _create_payment_vals_from_wizard(self):
        self.ensure_one()
    
        payment_vals = {
            'date': self.payment_date,
            'amount': self.amount,
            'payment_type': self.payment_type,
            'partner_type': self.partner_type,
            'payment_reference': self.communication,  # ✅ Odoo 18 uses payment_reference instead of ref
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'partner_bank_id': self.partner_bank_id.id,
            'destination_account_id': self.line_ids[0].account_id.id if self.line_ids else False,
    
            # ✅ Custom check fields (safe to keep)
            'check_number': self.check_number,
            'check_name': self.check_name,
            'check_payment_date': self.check_payment_date,
            'check_bank_id': self.check_bank_id.id,
            'check_owner_name': self.check_owner_name,
    
            # ✅ Odoo 18 requires payment_method_line_id
            'payment_method_line_id': self.payment_method_line_id.id,
        }
    
        # Handle write-off if there's a difference
        if (
            not self.currency_id.is_zero(self.payment_difference)
            and self.payment_difference_handling == 'reconcile'
        ):
            payment_vals['write_off_line_vals'] = {
                'name': self.writeoff_label,
                'amount': self.payment_difference,
                'account_id': self.writeoff_account_id.id,
            }
    
        return payment_vals


    def _create_payments(self):
        self.ensure_one()
        batches = []
        # Skip invalid batches (bank account setup check)
        for batch in self.batches:
            batch_account = self._get_batch_account(batch)
            if self.require_partner_bank_account and (not batch_account or not batch_account.allow_out_payment):
                continue
            batches.append(batch)
    
        if not batches:
            raise UserError(_(
                "To record payments with %(payment_method)s, the recipient bank account must be manually validated. "
                "You should go on the partner bank account in order to validate it.",
                payment_method=self.payment_method_line_id.name,
            ))
    
        first_batch_result = batches[0]
        edit_mode = self.can_edit_wizard and (len(first_batch_result['lines']) == 1 or self.group_payment)
        to_process = []
    
        if edit_mode:
            payment_vals = self._create_payment_vals_from_wizard()
            to_process_values = {
                'create_vals': payment_vals,
                'to_reconcile': first_batch_result['lines'],
                'batch': first_batch_result,
            }
    
            # Handle FX writeoff
            if self.writeoff_is_exchange_account and self.currency_id == self.company_currency_id:
                total_batch_residual = sum(first_batch_result['lines'].mapped('amount_residual_currency'))
                to_process_values['rate'] = abs(total_batch_residual / self.amount) if self.amount else 0.0
    
            to_process.append(to_process_values)
        else:
            if not self.group_payment:
                # Don’t group payments: one batch per line
                lines_to_pay = (
                    self._get_total_amounts_to_pay(batches)['lines']
                    if self.installments_mode in ('next', 'overdue', 'before_date')
                    else self.line_ids
                )
                new_batches = []
                for batch_result in batches:
                    for line in batch_result['lines']:
                        if line not in lines_to_pay:
                            continue
                        new_batches.append({
                            **batch_result,
                            'payment_values': {
                                **batch_result['payment_values'],
                                'payment_type': 'inbound' if line.balance > 0 else 'outbound',
                            },
                            'lines': line,
                        })
                batches = new_batches
    
            for batch_result in batches:
                to_process.append({
                    'create_vals': self._create_payment_vals_from_batch(batch_result),
                    'to_reconcile': batch_result['lines'],
                    'batch': batch_result,
                })
    
        # Create payments the Odoo 18 way
        payments = self._init_payments(to_process, edit_mode=edit_mode)
    
        # ✅ Customization for received checks
        if self.payment_method_code in ('received_third_check', 'received_safty_check'):
            for payment in payments:
                receivable_account = self.line_ids._origin.account_id
                for move_line in payment.move_id.line_ids:
                    if move_line.account_id.id != receivable_account.id:
                        move_line.account_id = self.journal_id.holding_check_account_id.id
    
        # Post and reconcile as per Odoo 18 flow
        self._post_payments(to_process, edit_mode=edit_mode)
        self._reconcile_payments(to_process, edit_mode=edit_mode)
    
        return payments

