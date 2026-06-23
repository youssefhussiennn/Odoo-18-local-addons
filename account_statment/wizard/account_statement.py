# -*- coding: utf-8 -*-
import io
import time
from odoo import models, fields, api, _, exceptions, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
import datetime
import base64
from datetime import date
from io import BytesIO
import xlsxwriter
from odoo.tools import html2plaintext

class AccountStatementWizard(models.TransientModel):
    _name = 'account.statement.wizard'
    
    excel_file = fields.Binary()
    excel_filename = fields.Char()
    partner_id = fields.Many2one('res.partner', string="Partner", domain=['|',('customer_rank','>=',1),('supplier_rank','>=',1), '|', ('invoice_ids','!=', False), ('total_due', '!=', 0)])
    team_id = fields.Many2one('crm.team', string="Sales Team")
    user_ids = fields.Many2many('res.users', string='SalesPerson')
    allowed_members = fields.Many2many('res.users', string='SalesPerson', compute='_compute_allowed')
    currency_id = fields.Many2one('res.currency', string='Currency')
    report_type =fields.Selection(
        string='field_name',
        selection=[('partner', 'Partner'), ('sales_team', 'Sales Team'), ('sales_team_total', 'Sales Team Total')]
    )
    date_start = fields.Date(string='Start Date',default=time.strftime('2025-01-01'))
    date_end = fields.Date(string='End Date')
    hide_zero_balance=fields.Boolean("Hide Partners with Zero Balance")
    
    
    def _date_domain(self):
        """Date bounds pushed into the SQL search so Postgres filters the rows
        instead of loading the full move-line history into memory and filtering
        in Python. The form makes date_start required, so this is almost always
        a major reduction of the fetched recordset."""
        domain = []
        if self.date_start:
            domain.append(('date', '>=', self.date_start))
        if self.date_end:
            domain.append(('date', '<=', self.date_end))
        return domain

    @api.onchange('team_id')
    def _compute_allowed(self):
        for this in self:
            this.allowed_members = [(5,0,0)]
            # for team in this.team_ids:
            this.allowed_members = [(4,user.id) for user in this.team_id.member_ids]

    def _get_total_due_currency(self, partner_id):
        """
        Compute the fields 'total_due', 'total_overdue','followup_level' and 'followup_status'
        """

        today = fields.Date.context_today(self)
        for record in partner_id:
            total_due = 0
            total_overdue = 0
            for aml in record.unreconciled_aml_ids:
                if aml.company_id == self.env.company :
                    amount = aml.amount_residual
                    amount = self.env.company.currency_id._convert(
                        amount, self.currency_id, aml.company_id, aml.date or fields.Date.today())
                    total_due += amount
                    is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
                    if is_overdue:
                        total_overdue += amount
            # record.total_due = total_due
            # record.total_overdue = total_overdue
            return total_overdue

    def get_account_statement_total_report(self):
        if self.date_start and self.date_end and self.date_start > self.date_end:
            raise UserError("The Start date cannot be greater than the end date.")
        
        
        elif self.partner_id:
            moves = self.env['account.move.line'].search([('partner_id','=',self.partner_id.id),'|','|','|',('account_id.account_type','in',('liability_payable', 'asset_receivable')), ('account_id.is_safty_account','=', True), ('account_id.is_collection_account','=', True), ('account_id.customer_allowed_discount','=', True), ('parent_state', '=', 'posted')] + self._date_domain())
        else:
            if self.team_id and not self.user_ids:
                moves = self.env['account.move.line'].search([('partner_id.team_id','=',self.team_id.id),'|','|','|',('account_id.account_type','in',('liability_payable', 'asset_receivable')), ('account_id.is_safty_account','=', True), ('account_id.is_collection_account','=', True), ('account_id.customer_allowed_discount','=', True), ('parent_state', '=', 'posted')] + self._date_domain())

            else:
                moves = self.env['account.move.line'].search([('partner_id.user_id.id','in',self.user_ids.ids),'|','|','|',('account_id.account_type','in',('liability_payable', 'asset_receivable')), ('account_id.is_safty_account','=', True), ('account_id.is_collection_account','=', True), ('account_id.customer_allowed_discount','=', True), ('parent_state', '=', 'posted')] + self._date_domain())

        
        if self.date_start and not self.date_end:
            all_record = moves.filtered(lambda x:x.date >= self.date_start)

        elif not self.date_start and self.date_end:
            all_record = moves.filtered(lambda x:x.date <= self.date_end)
        elif self.date_start and self.date_end:
            all_record = moves.filtered(lambda x:x.date >= self.date_start and x.date <= self.date_end)
        else:
            all_record = moves
        
        if not all_record:
            raise UserError(_('No Posted Entries'))
        if self.report_type == 'partner':
            return self.env.ref('account_statment.action_report_account_statment_layout').report_action(all_record)
            
        if self.report_type == 'sales_team':
            return self.env.ref('account_statment.action_report_account_statment_team_layout').report_action(all_record)
        
    def get_account_statement_total_report_new(self):
        
        if self.date_start and self.date_end and self.date_start > self.date_end:
            raise UserError(
                "The Start date cannot be greater than the end date.")


        if self.partner_id:
            moves = self.env['account.move.line'].search([('partner_id', '=', self.partner_id.id), '|', '|', '|', (
                'account_id.account_type', 'in', ('asset_receivable', 'liability_payable')),
                ('account_id.is_safty_account', '=', True),
                ('account_id.is_collection_account', '=', True),
                ('account_id.customer_allowed_discount', '=', True),
                ('parent_state', '=', 'posted'), ('partner_id.property_purchase_currency_id', '=', self.currency_id.id)] + self._date_domain())
        else:
            if self.team_id and not self.user_ids:
                moves = self.env['account.move.line'].search(
                    [('partner_id.team_id', '=', self.team_id.id), '|', '|', '|',
                     ('account_id.account_type', 'in',
                      ('asset_receivable', 'liability_payable')),
                     ('account_id.is_safty_account', '=',
                      True), ('account_id.is_collection_account', '=', True),
                     ('account_id.customer_allowed_discount', '=', True), ('parent_state', '=', 'posted'), ('partner_id.property_purchase_currency_id', '=', self.currency_id.id)] + self._date_domain())

            else:
                moves = self.env['account.move.line'].search(
                    [('partner_id.user_id.id', 'in', self.user_ids.ids), '|', '|', '|',
                     ('account_id.account_type', 'in',
                      ('asset_receivable', 'liability_payable')),
                     ('account_id.is_safty_account', '=',
                      True), ('account_id.is_collection_account', '=', True),
                     ('account_id.customer_allowed_discount', '=', True), ('parent_state', '=', 'posted'), ('partner_id.property_purchase_currency_id', '=', self.currency_id.id)] + self._date_domain())
        if self.date_start and not self.date_end:
            all_record = moves.filtered(lambda x: x.date >= self.date_start)

        elif not self.date_start and self.date_end:
            all_record = moves.filtered(lambda x: x.date <= self.date_end)
        elif self.date_start and self.date_end:
            all_record = moves.filtered(
                lambda x: x.date >= self.date_start and x.date <= self.date_end)
        else:
            all_record = moves

        # if not all_record:
        #     raise UserError(_('No Posted Entries'))
        report_lines = []
        lines = self.user_ids
        total_initial_balance_sales_person = 0
        total_sales_after_discount_sales_person = 0
        total_sales_before_discount_sales_person = 0
        total_purchase_sales_person = 0
        total_refund_sales_person = 0
        total_payment_sales_person = 0
        total_safty_checks_sales_person = 0
        total_collection_checks_sales_person = 0
        total_customer_allowed_discount_sales_person = 0
        total_discount_sales_person = 0
        balance_sales_person = 0
        total_due_amount_sales_person = 0
        for o in lines:

            data = all_record.filtered(
                lambda x: x.partner_id.user_id.name == o.name and x.partner_id.property_purchase_currency_id == self.currency_id).sorted(key=lambda y: y.date)
            total_initial_balance_sales_person = 0
            total_sales_after_discount_sales_person = 0
            total_sales_before_discount_sales_person = 0
            total_purchase_sales_person = 0
            total_refund_sales_person = 0
            total_payment_sales_person = 0
            total_safty_checks_sales_person = 0
            total_collection_checks_sales_person = 0
            total_customer_allowed_discount_sales_person = 0
            total_discount_sales_person = 0
            balance_sales_person = 0
            total_due_amount = 0
            total_due_amount_sales_person = 0

            accountings = self.env['res.partner'].search(
                [('user_id', 'in', self.user_ids.ids), ('property_purchase_currency_id', '=', self.currency_id.id)])
            sales_person_lines = []
            for account in accountings:
                # line.move_id.move_type in ['out_invoice', 'in_refund'] and line.move_id.payment_state in ['not_paid', 'partial', 'in_payment'] and line.move_id.invoice_date_due < datetime.datetime.today().date()

                x_studio_taxed_amount = 0  # Initialize the variable before the loop
                x_studio_taxed_amount_refund = 0  # Initialize the variable before the loop
                x_studio_taxed_amount_invoice = 0  # Initialize the variable before the loop
                total_due_amount = 0
                if self.currency_id.name == 'EGP' or not self.currency_id:
                    total_due_amount = account.total_overdue
                else:
                    total_due_amount = self._get_total_due_currency(account)
                # total_due_amount = sum(self.env['account.move'].search([('partner_id', '=', account.id), ('move_type', 'in', ['out_invoice', 'in_refund']), ('payment_state', 'in', [
                #     'not_paid', 'partial', 'in_payment']), ('invoice_date_due', '<', datetime.datetime.today().date())]).mapped('amount_residual'))
                total_due_amount_sales_person += total_due_amount
                data_per_line = {
                    'partner_name': "",
                    'total_initial_balance': 0,
                    'total_sales_before_discount': 0,
                    'total_refund': 0,
                    'Total_sales_updated': 0,
                    'total_payment': 0,
                    'balance': 0,
                    'total_due_amount': 0,
                    'total_safty_checks': 0,
                    'total_collection_checks': 0,
                    'comment': "",
                    'total_sales_before_discount_sales_person': 0,
                    'total_refund_sales_person': 0,
                    'Total_sales_new': 0,
                    'total_payment_sales_person': 0,
                    'balance_sales_person': balance_sales_person,
                    'total_due_amount_sales_person': 0,
                    'total_collection_checks_sales_person': 0,
                    'total_safty_checks_sales_person': 0,
                    'total_purchase_sales_person': 0,
                    'currency_id': 0
                }

                # final_lines=data.filtered(lambda x: x.partner_id.name == account.name).sorted(key=lambda x: x.date)
                final_lines = data.filtered(
                    lambda x: x.partner_id.name == account.name).sorted(key=lambda x: x.date)
                # total_initial_balance=request.env['account.move.line'].sudo().get_initial_balance(account, data[0].date)
                #                         total_initial_balance_sales_person=round((total_initial_balance_sales_person +request.env['account.move.line'].sudo().get_initial_balance(account, data[0].date)),2)
                total_initial_balance = self.env['account.move.line'].sudo(
                ).with_context(curr=self.currency_id).get_initial_balance(account, self.date_start)
                if not total_initial_balance:
                    total_initial_balance = 0
                total_initial_balance_sales_person = round(
                    (total_initial_balance_sales_person + total_initial_balance), 2)

                balance = total_initial_balance
                total_sales_after_discount = 0
                total_sales_before_discount = 0
                discount = 0
                total_refund = 0
                total_payment = 0
                total_debit = 0
                total_credit = 0
                total_safty_checks = 0
                total_collection_checks = 0
                total_customer_allowed_discount = 0
                total_discount = 0
                purchase_total_discount = 0
                old_invoices = 'moves:'
                # total_due_amount = 0
                # <t t-set="final_lines_checks" t-value="request.env['account.move.line'].sudo().search([('partner_id','=',account.id),('move_id.move_type','=','entry'),'|',('account_id.is_collection_account','=',True),('account_id.is_safty_account','=',True)])"/>
                final_lines_checks = self.env['account.move.line'].sudo().search(
                    [('partner_id', '=', account.id), ('move_id.move_type', '=', 'entry'), '|', ('account_id.is_collection_account', '=', True), ('account_id.is_safty_account', '=', True)])
                for line in final_lines_checks:
                    if line.move_id.move_type == 'entry' and line.account_id.is_safty_account == True:
                        total_safty_checks = round(
                            (total_safty_checks - line.credit), 2)
                        total_safty_checks = round(
                            (total_safty_checks + line.debit), 2)
                        total_safty_checks_sales_person = round(
                            (total_safty_checks_sales_person - line.credit), 2)
                        total_safty_checks_sales_person = round(
                            (total_safty_checks_sales_person + line.debit), 2)
                    elif line.move_id.move_type == 'entry' and line.account_id.is_collection_account == True:
                        total_collection_checks = round(
                            (total_collection_checks - line.credit), 2)
                        total_collection_checks = round(
                            (total_collection_checks + line.debit), 2)
                        total_collection_checks_sales_person = round(
                            (total_collection_checks_sales_person + line.debit), 2)
                        total_collection_checks_sales_person = round(
                            (total_collection_checks_sales_person - line.credit), 2)
                for line in final_lines:
                    if line.account_id.customer_allowed_discount == True:
                        total_customer_allowed_discount = round(
                            (total_customer_allowed_discount - line.credit), 2)
                        total_customer_allowed_discount = round(
                            (total_customer_allowed_discount + line.debit), 2)
                        total_customer_allowed_discount_sales_person = round(
                            (total_customer_allowed_discount_sales_person - line.credit), 2)
                        total_customer_allowed_discount_sales_person = round(
                            (total_customer_allowed_discount_sales_person + line.debit), 2)
                    elif line.move_id.move_type == 'entry' and line.account_id.is_safty_account == False and line.account_id.is_collection_account == False and line.account_id.customer_allowed_discount == False and line.move_id.is_customer_discount == False:
                        if line.move_id.is_opening_balance == False:
                            if not self.currency_id or self.currency_id.name == 'EGP':
                                total_payment = round(
                                    (total_payment + (line.credit - line.debit)), 2)
                                total_payment_sales_person = round(
                                    (total_payment_sales_person + (line.credit - line.debit)), 2)
                            else:
                                total_payment = round(
                                    (total_payment + abs(line.amount_currency)), 2)
                                total_payment_sales_person = round(
                                    (total_payment_sales_person + abs(line.amount_currency)), 2)
                        elif line.move_id.is_opening_balance == True:
                            total_initial_balance = total_initial_balance + \
                                (line.debit - line.credit)
                            total_initial_balance_sales_person = total_initial_balance_sales_person + \
                                (line.debit - line.credit)
                        balance = round((balance - line.credit), 2)
                        balance = round(
                            (balance + line.debit + line.x_studio_taxed_amount), 2)
                        # balance_sales_person = round(
                        #     (balance_sales_person - line.credit), 2)
                        # balance_sales_person = round(
                        #     (balance_sales_person + line.debit), 2)
                        total_credit = round((total_credit + line.credit), 2)
                    
                    for invoice_line in line.move_id.invoice_line_ids:
                        if line.move_id.move_type in ['out_refund', 'in_refund']:
                            x_studio_taxed_amount_refund = round(
                                (x_studio_taxed_amount_refund - invoice_line.x_studio_taxed_amount), 2)
                        if line.move_id.move_type in ['in_invoice', 'out_invoice']:
                            x_studio_taxed_amount_invoice = round(
                                (x_studio_taxed_amount_invoice + invoice_line.x_studio_taxed_amount), 2)
                            
                    if line.move_id.invoice_line_ids and line.move_id.move_type in ['out_refund', 'in_refund', 'out_invoice', 'in_invoice'] and line.account_id.is_safty_account == False and line.account_id.is_collection_account == False and line.account_id.customer_allowed_discount == False and line.move_id.name not in old_invoices and line.move_id.is_customer_discount == False:
                        old_invoices = old_invoices + ' , ' + line.move_id.name

                        for inv in line.move_id.invoice_line_ids:
                            if inv.discount > 0 and line.move_id.move_type in ['out_invoice']:
                                discount = round(
                                    discount + (inv.price_unit * ((inv.discount or 0.0) / 100.0) * inv.quantity), 2)
                                total_discount = round(
                                    (total_discount + (inv.price_unit * ((inv.discount or 0.0) / 100.0) * inv.quantity)), 2)
                                total_discount_sales_person = round(
                                    (total_discount_sales_person + (inv.price_unit * ((inv.discount or 0.0) / 100.0) * inv.quantity)), 2)
                            if inv.discount > 0 and line.move_id.move_type in ['in_invoice']:
                                purchase_total_discount = round(
                                    (purchase_total_discount + (inv.price_unit * ((inv.discount or 0.0) / 100.0) * inv.quantity)), 2)
                            if line.move_id.move_type not in ['out_refund', 'in_invoice']:
                                total_debit = round(
                                    (total_debit + inv.price_subtotal), 2)
                                balance = round(
                                    (balance + inv.price_subtotal), 2)
                                balance_sales_person = round(
                                    (balance_sales_person + inv.price_subtotal), 2)
                            else:
                                total_credit = round(
                                    (total_credit + inv.price_subtotal), 2)
                            if line.move_id.move_type in ['out_refund', 'in_refund']:
                                total_refund = round(
                                    (total_refund + inv.price_subtotal), 2)
                                total_refund_sales_person = round(
                                    (total_refund_sales_person + inv.price_subtotal), 2)
                            if line.move_id.move_type in ['in_invoice']:
                                # total_purchase = round(
                                #     (total_purchase + inv.price_subtotal), 2)
                                total_purchase_sales_person = round(
                                    (total_purchase_sales_person + inv.price_subtotal), 2)
                            if line.move_id.move_type in ['out_invoice']:
                                total_sales_after_discount = round(
                                    (total_sales_after_discount + inv.price_subtotal), 2)
                                total_sales_before_discount = round(
                                    (total_sales_before_discount + (inv.quantity * inv.price_unit)), 2)
                                total_sales_before_discount_sales_person = round(
                                    (total_sales_before_discount_sales_person + (inv.quantity * inv.price_unit)), 2)
                                total_sales_after_discount_sales_person = round(
                                    (total_sales_after_discount_sales_person + inv.price_subtotal), 2)


                computed_balance = balance + x_studio_taxed_amount_invoice + x_studio_taxed_amount_refund + total_customer_allowed_discount
                if self.hide_zero_balance and computed_balance == 0:
                        continue
                
                data_per_line = {
                    'partner_name': account.name,
                    'total_initial_balance': total_initial_balance,
                    'total_sales_before_discount': total_sales_before_discount,
                    'total_refund': total_refund,
                    'Total_sales_updated': total_sales_after_discount - total_refund - total_discount - total_customer_allowed_discount,
                    'total_payment': total_payment,
                    'x_studio_taxed_amount': x_studio_taxed_amount,
                    'x_studio_taxed_amount_refund': x_studio_taxed_amount_refund,
                    'x_studio_taxed_amount_invoice': x_studio_taxed_amount_invoice,
                    'balance': total_initial_balance + total_sales_after_discount - total_refund - total_payment - total_customer_allowed_discount,
                    'total_due_amount': total_due_amount,
                    'total_safty_checks': abs(total_safty_checks),
                    'total_collection_checks': abs(total_collection_checks),
                    'comment': html2plaintext(account.comment),
                    'total_sales_before_discount_sales_person': total_sales_before_discount_sales_person,
                    'total_refund_sales_person': total_refund_sales_person,
                    'Total_sales_new': round(total_sales_before_discount_sales_person - total_refund_sales_person),
                    'total_payment_sales_person': total_payment_sales_person,
                    'balance_sales_person': balance_sales_person + total_initial_balance + total_sales_after_discount - total_refund - total_payment - total_customer_allowed_discount,
                    'total_due_amount_sales_person': total_due_amount_sales_person,
                    'total_collection_checks_sales_person': total_collection_checks_sales_person,
                    'total_safty_checks_sales_person': total_safty_checks_sales_person,
                    'total_purchase_sales_person': total_purchase_sales_person,
                    'currency_id': account.currency_id.id,
                    'total_discount': total_discount,
                    'discount': discount,
                    'total_discount_sales_person': total_discount_sales_person,
                    'total_customer_allowed_discount': total_customer_allowed_discount,
                    'purchase_total_discount': purchase_total_discount,

                }
                sales_person_lines.append(data_per_line)
            report_lines.append({
                'sales_person': o.name,
                'lines': sales_person_lines,
            })
        total_data = {
            "date_start": self.date_start,
            "date_end": self.date_end,
            # 'company_id': self.env.user.company_id,
            "lines": report_lines,
        }
        print('LINES')
        print('LINES')
        print(total_data)
        print('LINES')
        print('LINES')
        return self.env.ref('account_statment.action_report_account_statment_total_layout2').report_action(
            self, data=total_data)

# print excel sheet for account statement total

    def get_account_statement_total_report_excel(self):

        result_xlsx = self.account_statement_excel_report()
        result_xlsx_no_Sales = self.partner_without_sales()
        # return True

        attachment_id = self.env['wizard.account.statement.excel.report'].create({
            'namexlsx': 'Account Statement Report.xlsx',
            'reportxlsx': base64.b64encode(result_xlsx),
            'namexlsx_no_sales': 'Account Statement with no sales Report.xlsx',
            'reportxlsx_no_sales': base64.b64encode(result_xlsx_no_Sales)
        })

        return {
            'name': _('Notification'),
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.account.statement.excel.report',
            'res_id': attachment_id.id,
            'data': None,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }  

    def account_statement_excel_report(self):

          
        report_name = 'كشف حساب مبيعات المهندس'

        columns = [
            ('اسم العميل', 20, 'char', 'char'),
            ('الرصيد الافتتاحي', 15, 'char', 'char'),
            
            ('مبيعات', 15, 'char', 'char'),

            ('خصم مسموح به', 15, 'char', 'char'),
            
            ('صافي البيع بعد الخصم', 15, 'char', 'char'),
            ('مرتجعات', 15, 'char', 'char'),

            ('خصومات اخري', 15, 'char', 'char'),
            ('اجمالي السداد', 15, 'char', 'char'),

            ('مشتريات من العملا', 15, 'char', 'char'),
            ('صافي رصيد العميل', 15, 'char', 'char'),

            ('المتأخر', 15, 'char', 'char'),
            ('شيكات ضمان', 15, 'char', 'char'),
            ('شيكات تحت التحصيل', 15, 'char', 'char'),
        ]

        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = self.add_workbook_format(workbook)
        worksheet = workbook.add_worksheet(report_name)


        



        if self.date_start and self.date_end and self.date_start > self.date_end:
            raise UserError("The Start date cannot be greater than the end date.")

        if not self.team_id and not self.user_ids:
            raise UserError("Please At least choose sales team.")
        
        if self.team_id and not self.user_ids:
            moves = self.env['account.move.line'].search([('partner_id.team_id','=',self.team_id.id),'|','|','|',('account_id.account_type','in',('liability_payable', 'asset_receivable')), ('account_id.is_safty_account','=', True), ('account_id.is_collection_account','=', True), ('account_id.customer_allowed_discount','=', True), ('parent_state', '=', 'posted')] + self._date_domain())
            old_invoices = self.env['account.move.line'].search([('date', '<', self.date_start),('partner_id.team_id','=',self.team_id.id),('account_id.account_type','in',('liability_payable', 'asset_receivable')), ('parent_state', '=', 'posted')])


        else:
            moves = self.env['account.move.line'].search([('partner_id.user_id.id','in',self.user_ids.ids),'|','|','|',('account_id.account_type','in',('liability_payable', 'asset_receivable')), ('account_id.is_safty_account','=', True), ('account_id.is_collection_account','=', True), ('account_id.customer_allowed_discount','=', True), ('parent_state', '=', 'posted')] + self._date_domain())
            old_invoices = self.env['account.move.line'].search([('date', '<', self.date_start),('partner_id.user_id.id','in',self.user_ids.ids),('account_id.account_type','in',('liability_payable', 'asset_receivable')), ('parent_state', '=', 'posted')])


        if self.date_start and not self.date_end:
            all_record = moves.filtered(lambda x:x.date >= self.date_start)

        elif not self.date_start and self.date_end:
            all_record = moves.filtered(lambda x:x.date <= self.date_end)
        elif self.date_start and self.date_end:
            all_record = moves.filtered(lambda x:x.date >= self.date_start and x.date <= self.date_end)
        else:
            all_record = moves

        if not all_record:
            raise UserError(_('No Posted Entries'))

        else:
            row = 2
            for sales_person in all_record.mapped(lambda x:x.partner_id.user_id):

                title = '    مبيعات المهندس' +'  '+ str(sales_person.name)
                worksheet.merge_range('A'+str(row)+':F'+str(row+1), title, wbf['title_doc'])

                worksheet.write(row, 8, 'تاريخ الطباعه', wbf['header_orange'])
                worksheet.write(row, 7, str(datetime.datetime.today().strftime('%Y-%m-%d')), wbf['content'])

                row += 4

                col = 0
                for column in columns:
                    column_name = column[0]
                    column_width = column[1]
                    worksheet.set_column(col, col, column_width)
                    worksheet.write(row - 1, col, column_name, wbf['header_orange'])
                    col += 1
                row += 2

                all_record_of_salesperson = all_record.filtered(lambda x:x.partner_id.user_id == sales_person)
                # total customer allowed discount for sales person
                salesperson_total_customer_allowed_discount = sum(all_record_of_salesperson.filtered(lambda x:x.account_id.customer_allowed_discount == True).mapped(lambda x:x.debit - x.credit))
                # total safty check for sales person
                salesperson_total_safty_check = abs(sum(all_record_of_salesperson.filtered(lambda x:x.account_id.is_safty_account == True).mapped(lambda x:x.debit - x.credit)))
                # total collection checks for sales person
                salesperson_total_collection_check = abs(sum(all_record_of_salesperson.filtered(lambda x:x.account_id.is_collection_account == True).mapped(lambda x:x.debit - x.credit)))
                # all records without safty checks and collection checks and customer allowed discount
                records_without_checks_and_allowed_discount = all_record_of_salesperson.filtered(lambda x:x.account_id.customer_allowed_discount == False and x.account_id.is_safty_account == False and x.account_id.is_collection_account == False and x.move_id.is_customer_discount == False)

                # get total refund for sales person
                salesperson_total_refund = abs(sum(records_without_checks_and_allowed_discount.filtered(lambda x:x.move_id.move_type in ['out_refund', 'in_refund']).mapped(lambda x:x.price_subtotal)))
                
                # total purchase for sales person
                salesperson_total_purchase = abs(sum(records_without_checks_and_allowed_discount.filtered(lambda x:x.move_id.move_type in ['in_invoice']).mapped(lambda x:x.price_subtotal)))

                # total sales before discount salesperson
                salesperson_total_sales_before_dis = abs(sum(records_without_checks_and_allowed_discount.filtered(lambda x:x.move_id.move_type in ['out_invoice']).mapped(lambda x:x.move_id.invoice_line_ids).mapped(lambda x:(x.quantity * x.price_unit))))
                
                # total sales after discount salesperson
                salesperson_total_sales_after_dis = abs(sum(records_without_checks_and_allowed_discount.filtered(lambda x:x.move_id.move_type in ['out_invoice']).mapped(lambda x:x.move_id.invoice_line_ids).mapped(lambda x:x.quantity * x.price_unit * ( 1 - x.discount / 100))))
                # total_over due amount
                salesperson_total_over_due_amount = abs(sum(records_without_checks_and_allowed_discount.filtered(lambda x:x.move_id.move_type in ['out_invoice','in_refund'] and x.move_id.payment_state in ['not_paid', 'partial', 'in_payment'] and str(x.move_id.invoice_date_due) < datetime.datetime.today().strftime('%Y-%m-%d')).mapped(lambda x:x.move_id.amount_residual)))
                # salesperson_total_over_due_amount = self._get_total_due_currency(sales_person)
                salesperson_total_discount = salesperson_total_sales_before_dis - salesperson_total_sales_after_dis

                # total payments for sales person
                salesperson_total_payment = abs(sum(records_without_checks_and_allowed_discount.filtered(lambda x:x.move_id.move_type in ['entry'] and x.move_id.is_opening_balance == False).mapped(lambda x:x.credit - x.debit)))
                partners = all_record_of_salesperson.mapped(lambda x:x.partner_id)
                salesperson_total_initial_balance = abs(sum(old_invoices.filtered(lambda x:x.partner_id.user_id == sales_person and x.partner_id in partners).mapped(lambda x:x.credit - x.debit)))
                salesperson_total_initial_balance = salesperson_total_initial_balance + abs(sum(records_without_checks_and_allowed_discount.filtered(lambda x:x.move_id.is_opening_balance == True).mapped(lambda x:x.debit - x.credit)))
                salesperson_total_balance = salesperson_total_initial_balance + salesperson_total_sales_after_dis - salesperson_total_refund - salesperson_total_payment - salesperson_total_purchase - salesperson_total_customer_allowed_discount
                # salesperson_total_balance = salesperson_total_initial_balance + sum(records_without_checks_and_allowed_discount.mapped(lambda x:x.debit - x.credit))



                
                
                for partner in all_record_of_salesperson.mapped(lambda x:x.partner_id):

                    # col_value = partner.name or '0'
                    # wbf_value = wbf['content']
                    worksheet.write(row - 1, 0, partner.name or '0', wbf['content'])
                    # total customer allowed discount for partner
                    total_customer_allowed_discount = sum(all_record_of_salesperson.filtered(lambda x:x.partner_id == partner and x.account_id.customer_allowed_discount == True).mapped(lambda x:x.debit - x.credit))
                    worksheet.write(row - 1, 6, total_customer_allowed_discount, wbf['content'])
                    
                    # total safty checks for partner
                    total_safty_check = abs(sum(all_record_of_salesperson.filtered(lambda x:x.partner_id == partner and x.account_id.is_safty_account == True).mapped(lambda x:x.debit - x.credit)))
                    worksheet.write(row - 1, 11, total_safty_check, wbf['content'])

                    #total collection checks for partner
                    total_collection_check = abs(sum(all_record_of_salesperson.filtered(lambda x:x.partner_id == partner and x.account_id.is_collection_account == True).mapped(lambda x:x.debit - x.credit)))
                    worksheet.write(row - 1, 12, total_collection_check, wbf['content'])

                    # total refund for each partner
                    total_refund = abs(sum(records_without_checks_and_allowed_discount.filtered(lambda x:x.partner_id == partner and x.move_id.move_type in ['out_refund', 'in_refund']).mapped(lambda x:x.price_subtotal)))
                    worksheet.write(row - 1, 5, total_refund, wbf['content'])
                    
                    # total purchase for each partner
                    total_purchase = abs(sum(records_without_checks_and_allowed_discount.filtered(lambda x:x.partner_id == partner and x.move_id.move_type in ['in_invoice']).mapped(lambda x:x.price_subtotal)))
                    worksheet.write(row - 1, 8, total_purchase, wbf['content'])

                    # total sales before discount
                    total_sales_before_dis = abs(sum(records_without_checks_and_allowed_discount.filtered(lambda x:x.partner_id == partner and x.move_id.move_type in ['out_invoice']).mapped(lambda x:x.move_id.invoice_line_ids).mapped(lambda x:x.quantity * x.price_unit)))
                    worksheet.write(row - 1, 2, total_sales_before_dis, wbf['content'])
                    
                    # total sales after discount
                    total_sales_after_dis = abs(sum(records_without_checks_and_allowed_discount.filtered(lambda x:x.partner_id == partner and x.move_id.move_type in ['out_invoice']).mapped(lambda x:x.move_id.invoice_line_ids).mapped(lambda x:x.quantity * x.price_unit * (1-x.discount / 100))))
                    worksheet.write(row - 1, 4, total_sales_after_dis, wbf['content'])
                    
                    total_discount = total_sales_before_dis - total_sales_after_dis
                    worksheet.write(row - 1, 3, total_discount, wbf['content'])

                    # total payment for each partner
                    total_payment = abs(sum(records_without_checks_and_allowed_discount.filtered(lambda x:x.partner_id == partner and x.move_id.move_type in ['entry'] and x.move_id.is_opening_balance == False).mapped(lambda x:x.credit - x.debit)))
                    worksheet.write(row - 1, 7, total_payment, wbf['content'])
                    
                    total_initial_balance = abs(sum(old_invoices.filtered(lambda x:x.partner_id == partner).mapped(lambda x:x.debit - x.credit)))
                    total_initial_balance = total_initial_balance + abs(sum(records_without_checks_and_allowed_discount.filtered(lambda x:x.partner_id == partner and x.move_id.move_type in ['entry'] and x.move_id.is_opening_balance == True).mapped(lambda x:x.debit - x.credit)))

                    # salesperson_total_initial_balance += total_initial_balance
                    worksheet.write(row - 1, 1, total_initial_balance or '0', wbf['content'])
                    
                    total_balance = total_initial_balance + total_sales_after_dis - total_refund - total_payment - total_purchase - total_customer_allowed_discount
                    # total_balance = total_initial_balance + sum(records_without_checks_and_allowed_discount.filtered(lambda x:x.partner_id == partner).mapped(lambda x:x.debit - x.credit))
                    worksheet.write(row - 1, 9, total_balance, wbf['content'])


                    # total over due amout
                    total_over_due_amount = abs(sum(records_without_checks_and_allowed_discount.filtered(lambda x:x.partner_id == partner and x.move_id.move_type in ['out_invoice', 'in_refund'] and x.move_id.payment_state in ['not_paid', 'partial', 'in_payment'] and str(x.move_id.invoice_date_due) < datetime.datetime.today().strftime('%Y-%m-%d')).mapped(lambda x:x.move_id.amount_residual)))
                    worksheet.write(row - 1, 10, total_over_due_amount, wbf['content'])

                    

                    row += 1


                worksheet.merge_range('A'+str(row+1)+':L'+str(row+1), 'الاجمالي', wbf['header_orange'])
                print(salesperson_total_safty_check)
                print(salesperson_total_collection_check)
                row += 2


                worksheet.write(row - 1, 0, 'اجمالي الرصيد الافتتاحي', wbf['header_orange'])
                worksheet.write(row - 1, 1, salesperson_total_initial_balance, wbf['content'])
                row += 1


                worksheet.write(row - 1, 0, 'اجمالي صافي رصيد العملا', wbf['header_orange'])
                worksheet.write(row - 1, 1, salesperson_total_balance, wbf['content'])
                row += 1


                worksheet.write(row - 1, 0, 'اجمالي المتأخر', wbf['header_orange'])
                worksheet.write(row - 1, 1, salesperson_total_over_due_amount, wbf['content'])
                row += 1

                worksheet.write(row - 1, 0, 'اجمالي مبيعات', wbf['header_orange'])
                worksheet.write(row - 1, 1, salesperson_total_sales_before_dis, wbf['content'])
                row += 1

                worksheet.write(row - 1, 0, 'اجمالي خصم مسموح به', wbf['header_orange'])
                worksheet.write(row - 1, 1, salesperson_total_discount, wbf['content'])
                # discount percentage
                discount_percentage = round((salesperson_total_discount/salesperson_total_sales_before_dis)*100,2) if salesperson_total_sales_before_dis != 0 else 0
                worksheet.write(row - 1, 8, 'نسبة الخصم', wbf['header_orange'])
                worksheet.write(row - 1, 9, discount_percentage, wbf['content'])
                row += 1

                worksheet.write(row - 1, 0, 'اجمالي صافي البيع بعد الخصم', wbf['header_orange'])
                worksheet.write(row - 1, 1, salesperson_total_sales_after_dis, wbf['content'])
                row += 1

                worksheet.write(row - 1, 0, 'اجمالي سداد', wbf['header_orange'])
                worksheet.write(row - 1, 1, salesperson_total_payment, wbf['content'])
                # payment percentage
                total = salesperson_total_balance + salesperson_total_payment
                if total==0:
                    salesperson_total_payment_percentage = 0
                else:
                    salesperson_total_payment_percentage = round((salesperson_total_payment/(salesperson_total_balance+salesperson_total_payment))*100,2)
                # salesperson_total_payment_percentage = round((salesperson_total_payment/(salesperson_total_balance+salesperson_total_payment))*100,2) if salesperson_total_payment != 0 and salesperson_total_balance!=0 else 0
                worksheet.write(row - 1, 8, 'نسبة التحصيل', wbf['header_orange'])
                worksheet.write(row - 1, 9, salesperson_total_payment_percentage, wbf['content'])
                row += 1

                worksheet.write(row - 1, 0, 'اجمالي مرتجعات', wbf['header_orange'])
                worksheet.write(row - 1, 1, salesperson_total_refund, wbf['content'])

                # refund percentage
                salesperson_total_refund_percentage = round((salesperson_total_refund/salesperson_total_sales_after_dis)*100,2) if salesperson_total_sales_after_dis != 0 else 0
                worksheet.write(row - 1, 8, 'نسبة المرتجعات', wbf['header_orange'])
                worksheet.write(row - 1, 9, salesperson_total_refund_percentage, wbf['content'])
                row += 1

                worksheet.write(row - 1, 0, 'اجمالي الخصومات الاخري', wbf['header_orange'])
                worksheet.write(row - 1, 1, salesperson_total_customer_allowed_discount, wbf['content'])
                row += 1

                worksheet.write(row - 1, 0, 'اجمالي مشتريات من العملا', wbf['header_orange'])
                worksheet.write(row - 1, 1, salesperson_total_purchase, wbf['content'])
                row += 1

                worksheet.write(row - 1, 0, 'شيكات ضمان', wbf['header_orange'])
                worksheet.write(row - 1, 1, salesperson_total_safty_check, wbf['content'])
                row += 1

                worksheet.write(row - 1, 0, 'شيكات تحت التحصيل', wbf['header_orange'])
                worksheet.write(row - 1, 1, salesperson_total_collection_check, wbf['content'])
                row += 5

                
            row += 8
        workbook.close()

        return fp.getvalue()

    def add_workbook_format(self, workbook):
        colors = {
            'white_orange': '#FFFFDB',
            'orange': '#FFC300',
            'red': '#FF0000',
            'yellow': '#F6FA03',
        }

        wbf = {}
        wbf['header'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': '#FFFFDB', 'font_color': '#000000', 'font_name': 'Georgia'})
        wbf['header'].set_border()

        wbf['header_orange'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': colors['orange'], 'font_color': '#000000',
             'font_name': 'Georgia'})
        wbf['header_orange'].set_border()

        wbf['header_yellow'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': colors['yellow'], 'font_color': '#000000',
             'font_name': 'Georgia'})
        wbf['header_yellow'].set_border()

        wbf['header_no'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': '#FFFFDB', 'font_color': '#000000', 'font_name': 'Georgia'})
        wbf['header_no'].set_border()
        wbf['header_no'].set_align('vcenter')

        wbf['footer'] = workbook.add_format({'align': 'left', 'font_name': 'Georgia'})

        wbf['content_datetime'] = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss', 'font_name': 'Georgia'})
        wbf['content_datetime'].set_left()
        wbf['content_datetime'].set_right()

        wbf['content_date'] = workbook.add_format({'num_format': 'yyyy-mm-dd', 'font_name': 'Georgia'})
        wbf['content_date'].set_left()
        wbf['content_date'].set_right()

        wbf['title_doc'] = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 20,
            'font_name': 'Georgia',
        })

        wbf['company'] = workbook.add_format({'align': 'left', 'font_name': 'Georgia'})
        wbf['company'].set_font_size(11)

        wbf['content'] = workbook.add_format()
        wbf['content'].set_left()
        wbf['content'].set_right()

        wbf['content_float'] = workbook.add_format({'align': 'right', 'num_format': '#,##0.00', 'font_name': 'Georgia'})
        wbf['content_float'].set_right()
        wbf['content_float'].set_left()

        wbf['content_number'] = workbook.add_format({'align': 'right', 'num_format': '#,##0', 'font_name': 'Georgia'})
        wbf['content_number'].set_right()
        wbf['content_number'].set_left()

        wbf['content_percent'] = workbook.add_format({'align': 'right', 'num_format': '0.00%', 'font_name': 'Georgia'})
        wbf['content_percent'].set_right()
        wbf['content_percent'].set_left()

        wbf['total_float'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['white_orange'], 'align': 'right', 'num_format': '#,##0.00',
             'font_name': 'Georgia'})
        wbf['total_float'].set_top()
        wbf['total_float'].set_bottom()
        wbf['total_float'].set_left()
        wbf['total_float'].set_right()

        wbf['total_number'] = workbook.add_format(
            {'align': 'right', 'bg_color': colors['white_orange'], 'bold': 1, 'num_format': '#,##0',
             'font_name': 'Georgia'})
        wbf['total_number'].set_top()
        wbf['total_number'].set_bottom()
        wbf['total_number'].set_left()
        wbf['total_number'].set_right()

        wbf['total'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['white_orange'], 'align': 'center', 'font_name': 'Georgia'})
        wbf['total'].set_left()
        wbf['total'].set_right()
        wbf['total'].set_top()
        wbf['total'].set_bottom()

        wbf['total_float_yellow'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['yellow'], 'align': 'right', 'num_format': '#,##0.00',
             'font_name': 'Georgia'})
        wbf['total_float_yellow'].set_top()
        wbf['total_float_yellow'].set_bottom()
        wbf['total_float_yellow'].set_left()
        wbf['total_float_yellow'].set_right()

        wbf['total_number_yellow'] = workbook.add_format(
            {'align': 'right', 'bg_color': colors['yellow'], 'bold': 1, 'num_format': '#,##0', 'font_name': 'Georgia'})
        wbf['total_number_yellow'].set_top()
        wbf['total_number_yellow'].set_bottom()
        wbf['total_number_yellow'].set_left()
        wbf['total_number_yellow'].set_right()

        wbf['total_yellow'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['yellow'], 'align': 'center', 'font_name': 'Georgia'})
        wbf['total_yellow'].set_left()
        wbf['total_yellow'].set_right()
        wbf['total_yellow'].set_top()
        wbf['total_yellow'].set_bottom()

        wbf['total_float_orange'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['orange'], 'align': 'right', 'num_format': '#,##0.00',
             'font_name': 'Georgia'})
        wbf['total_float_orange'].set_top()
        wbf['total_float_orange'].set_bottom()
        wbf['total_float_orange'].set_left()
        wbf['total_float_orange'].set_right()

        wbf['total_number_orange'] = workbook.add_format(
            {'align': 'right', 'bg_color': colors['orange'], 'bold': 1, 'num_format': '#,##0', 'font_name': 'Georgia'})
        wbf['total_number_orange'].set_top()
        wbf['total_number_orange'].set_bottom()
        wbf['total_number_orange'].set_left()
        wbf['total_number_orange'].set_right()

        wbf['total_orange'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['orange'], 'align': 'center', 'font_name': 'Georgia'})
        wbf['total_orange'].set_left()
        wbf['total_orange'].set_right()
        wbf['total_orange'].set_top()
        wbf['total_orange'].set_bottom()

        wbf['header_detail_space'] = workbook.add_format({'font_name': 'Georgia'})
        wbf['header_detail_space'].set_left()
        wbf['header_detail_space'].set_right()
        wbf['header_detail_space'].set_top()
        wbf['header_detail_space'].set_bottom()

        wbf['header_detail'] = workbook.add_format({'bg_color': '#E0FFC2', 'font_name': 'Georgia'})
        wbf['header_detail'].set_left()
        wbf['header_detail'].set_right()
        wbf['header_detail'].set_top()
        wbf['header_detail'].set_bottom()

        return wbf, workbook

    def partner_without_sales(self):

          
        report_name = 'كشف حساب عملا المهندس '

        columns = [
            ('اسم العميل', 20, 'char', 'char'),
            ('الرصيد الافتتاحي', 15, 'char', 'char'),
            
            # ('مبيعات', 15, 'char', 'char'),

            # ('خصم مسموح به', 15, 'char', 'char'),
            
            # ('صافي البيع بعد الخصم', 15, 'char', 'char'),
            # ('مرتجعات', 15, 'char', 'char'),

            # ('خصومات اخري', 15, 'char', 'char'),
            # ('اجمالي السداد', 15, 'char', 'char'),

            # ('مشتريات من العملا', 15, 'char', 'char'),
            # ('صافي رصيد العميل', 15, 'char', 'char'),

            # ('شيكات ضمان', 15, 'char', 'char'),
            # ('شيكات تحت التحصيل', 15, 'char', 'char'),
        ]

        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = self.add_workbook_format(workbook)
        worksheet = workbook.add_worksheet(report_name)


        



        if self.date_start and self.date_end and self.date_start > self.date_end:
            raise UserError("The Start date cannot be greater than the end date.")
        
        if self.team_id and not self.user_ids:
            moves = self.env['account.move.line'].search([('partner_id.team_id','=',self.team_id.id),'|','|','|',('account_id.account_type','in',('liability_payable', 'asset_receivable')), ('account_id.is_safty_account','=', True), ('account_id.is_collection_account','=', True), ('account_id.customer_allowed_discount','=', True), ('parent_state', '=', 'posted')] + self._date_domain())
            old_invoices = self.env['account.move.line'].search([('date', '<', self.date_start),('partner_id.team_id','=',self.team_id.id),('account_id.account_type','in',('liability_payable', 'asset_receivable')), ('parent_state', '=', 'posted')])


        else:
            moves = self.env['account.move.line'].search([('partner_id.user_id.id','in',self.user_ids.ids),'|','|','|',('account_id.account_type','in',('liability_payable', 'asset_receivable')), ('account_id.is_safty_account','=', True), ('account_id.is_collection_account','=', True), ('account_id.customer_allowed_discount','=', True), ('parent_state', '=', 'posted')] + self._date_domain())
            old_invoices = self.env['account.move.line'].search([('date', '<', self.date_start),('partner_id.user_id.id','in',self.user_ids.ids),('account_id.account_type','in',('liability_payable', 'asset_receivable')), ('parent_state', '=', 'posted')])


        if self.date_start and not self.date_end:
            all_record = moves.filtered(lambda x:x.date >= self.date_start)

        elif not self.date_start and self.date_end:
            all_record = moves.filtered(lambda x:x.date <= self.date_end)
        elif self.date_start and self.date_end:
            all_record = moves.filtered(lambda x:x.date >= self.date_start and x.date <= self.date_end)
        else:
            all_record = moves

        if not all_record:
            raise UserError(_('No Posted Entries'))

        else:
            row = 2

            for sales_person in all_record.mapped(lambda x:x.partner_id.user_id):

                title = '  المهندس' +'  '+ str(sales_person.name)
                worksheet.merge_range('A'+str(row)+':F'+str(row+1), title, wbf['title_doc'])

                worksheet.write(row, 8, 'تاريخ الطباعه', wbf['header_orange'])
                worksheet.write(row, 7, str(datetime.datetime.today().strftime('%Y-%m-%d')), wbf['content'])

                row += 4

                col = 0
                for column in columns:
                    column_name = column[0]
                    column_width = column[1]
                    worksheet.set_column(col, col, column_width)
                    worksheet.write(row - 1, col, column_name, wbf['header_orange'])
                    col += 1
                row += 2

                all_record_of_salesperson = all_record.filtered(lambda x:x.partner_id.user_id == sales_person)
                partners_with_sales = all_record_of_salesperson.mapped(lambda x:x.partner_id)
                # sales_person_partners = self.env['res.partner'].search([('user_id', '=', sales_person)])
                final_partners_moves = old_invoices.filtered(lambda x:x.partner_id.user_id == sales_person and x.partner_id not in partners_with_sales)
                
                salesperson_total_initial_balance = 0





                
                
                for partner in final_partners_moves.mapped(lambda x:x.partner_id):

                    # col_value = partner.name or '0'
                    # wbf_value = wbf['content']
                    worksheet.write(row - 1, 0, partner.name or '0', wbf['content'])
                   
                    total_initial_balance = abs(sum(final_partners_moves.filtered(lambda x:x.partner_id == partner).mapped(lambda x:x.debit - x.credit)))
                    salesperson_total_initial_balance += total_initial_balance
                    worksheet.write(row - 1, 1, total_initial_balance or '0', wbf['content'])
                    
                    # total_balance = total_initial_balance + total_sales_after_dis - total_refund - total_payment - total_purchase
                    # # total_balance = total_initial_balance + sum(records_without_checks_and_allowed_discount.filtered(lambda x:x.partner_id == partner).mapped(lambda x:x.debit - x.credit))
                    # worksheet.write(row - 1, 9, total_balance, wbf['content'])

                    row += 1


                worksheet.merge_range('A'+str(row+1)+':L'+str(row+1), 'الاجمالي', wbf['header_orange'])
                # print(salesperson_total_safty_check)
                # print(salesperson_total_collection_check)
                row += 2


                worksheet.write(row - 1, 0, 'اجمالي الرصيد الافتتاحي', wbf['header_orange'])
                worksheet.write(row - 1, 1, salesperson_total_initial_balance, wbf['content'])
                row += 1

                row += 5

                
            row += 8
        workbook.close()

        return fp.getvalue()
    
    def action_generate_xlsx(self):

        import io
        import base64
        import xlsxwriter

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Statement")

        header_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center',
            'bg_color': '#D9E1F2'
        })

        cell_format = workbook.add_format({
            'border': 1,
            'align': 'center'
        })

        # -------------------------------------------------
        # SAME SOURCE AS PDF (IMPORTANT)
        # -------------------------------------------------
        domain = self._date_domain()

        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))

        lines = self.env['account.move.line'].search(domain)

        partners = lines.mapped('partner_id')

        row = 0

        for partner in partners:

            # =================================================
            # SAME FILTERS AS PDF "data"
            # =================================================
            partner_lines = lines.filtered(lambda line: (
                line.partner_id.id == partner.id
            )).sorted(key=lambda l: l.date)

            if not partner_lines:
                continue

            # -----------------------------
            # HEADER
            # -----------------------------
            sheet.write(row, 0, partner.name, header_format)
            row += 1

            headers = [
                "Date", "Document", "Description",
                "Item", "Qty", "Price",
                "Debit", "Credit", "Balance", "Tax"
            ]

            for col, h in enumerate(headers):
                sheet.write(row, col, h, header_format)

            row += 1

            # =================================================
            # INITIAL BALANCE (same logic as PDF)
            # =================================================
            opening_lines = partner_lines.filtered(
                lambda x: x.move_id.is_opening_balance
            )

            total_initial_balance = sum(
                abs(x.debit - x.credit) for x in opening_lines
            )

            balance = total_initial_balance

            sheet.write(row, 8, total_initial_balance, cell_format)
            row += 1

            # tracking like PDF
            old_invoices = []
            total_debit = 0
            total_credit = 0
            total_sales_before_discount = 0
            total_sales_after_discount = 0
            total_refund = 0
            total_payment = 0
            total_customer_allowed_discount = 0

            # =================================================
            # MAIN LOOP (EXACT PDF CONDITIONS)
            # =================================================
            for line in partner_lines:

                # -------------------------------------------------
                # SKIP CONDITIONS (EXACT PDF FILTERS)
                # -------------------------------------------------
                if (
                    line.account_id.customer_allowed_discount
                    or line.account_id.is_safty_account
                    or line.account_id.is_collection_account
                    or line.move_id.is_customer_discount
                ):
                    continue

                # -------------------------------------------------
                # ENTRY TYPE LOGIC (PDF "entry" block)
                # -------------------------------------------------
                if (
                    line.move_id.move_type == 'entry'
                    and not line.move_id.is_opening_balance
                ):

                    debit = line.debit or 0
                    credit = line.credit or 0

                    # balance logic (same idea as PDF)
                    balance += (line.amount_currency if line.partner_id.property_purchase_currency_id else (debit - credit))

                    total_debit += debit
                    total_credit += credit

                    sheet.write(row, 0, str(line.date), cell_format)
                    sheet.write(row, 1, line.move_id.name or '', cell_format)
                    sheet.write(row, 2, (
                        "شيك" if line.journal_id.type == 'bank'
                        else "قيود عامة" if line.journal_id.type == 'general'
                        else "سداد نقدي"
                    ), cell_format)
                    sheet.write(row, 3, line.name or '', cell_format)
                    sheet.write(row, 4, 0, cell_format)
                    sheet.write(row, 5, 0, cell_format)
                    sheet.write(row, 6, debit, cell_format)
                    sheet.write(row, 7, credit, cell_format)
                    sheet.write(row, 8, balance, cell_format)

                    row += 1

                    continue

                # -------------------------------------------------
                # INVOICE BLOCK (same structure as PDF)
                # -------------------------------------------------
                if (
                    line.move_id.invoice_line_ids
                    and line.move_id.move_type in (
                        'out_refund', 'in_refund',
                        'out_invoice', 'in_invoice'
                    )
                    and not line.move_id.is_customer_discount
                    and line.move_id.name not in old_invoices
                ):

                    old_invoices.append(line.move_id.name)

                    for inv in line.move_id.invoice_line_ids:

                        tax_total = inv.x_studio_taxed_amount or 0

                        price = round(inv.price_unit - ((inv.price_unit * (inv.discount or 0)) / 100), 2)

                        qty = round(inv.quantity, 2)

                        debit = 0
                        credit = 0

                        # same invoice logic split
                        if line.move_id.move_type not in ('out_refund', 'in_invoice'):
                            debit = round(abs(inv.price_total), 2)
                        else:
                            credit = round(inv.price_subtotal + tax_total, 2)

                        # update balance (same logic)
                        if line.move_id.move_type not in ('out_refund', 'in_invoice'):
                            balance += (inv.price_subtotal + tax_total)
                            total_debit += (inv.price_subtotal + tax_total)
                        else:
                            balance -= (inv.price_subtotal + tax_total)
                            total_credit += (inv.price_subtotal + tax_total)

                        # totals
                        if line.move_id.move_type == 'out_invoice':
                            total_sales_after_discount += inv.price_subtotal
                            total_sales_before_discount += (inv.quantity * inv.price_unit)

                        if line.move_id.move_type == 'out_refund':
                            total_refund += (inv.price_subtotal + tax_total)

                        sheet.write(row, 0, str(inv.date), cell_format)
                        sheet.write(row, 1, line.move_id.name or '', cell_format)
                        sheet.write(row, 2, (
                            "مرتجع" if line.move_id.move_type in ('out_refund', 'in_refund')
                            else "فاتورة مشتريات" if line.move_id.move_type == 'in_invoice'
                            else "فاتورة مبيعات"
                        ), cell_format)
                        sheet.write(row, 3, inv.name or '', cell_format)
                        sheet.write(row, 4, qty, cell_format)
                        sheet.write(row, 5, price, cell_format)
                        sheet.write(row, 6, debit, cell_format)
                        sheet.write(row, 7, credit, cell_format)
                        sheet.write(row, 8, balance, cell_format)
                        sheet.write(row, 9, tax_total, cell_format)

                        row += 1

            # =================================================
            # FOOTER TOTALS (mirrors PDF)
            # =================================================
            row += 1

            sheet.write(row, 7, "TOTAL DEBIT", header_format)
            sheet.write(row, 8, total_debit, header_format)
            row += 1

            sheet.write(row, 7, "TOTAL CREDIT", header_format)
            sheet.write(row, 8, total_credit, header_format)
            row += 1

            sheet.write(row, 7, "SALES BEFORE DISCOUNT", header_format)
            sheet.write(row, 8, total_sales_before_discount, header_format)
            row += 1

            sheet.write(row, 7, "REFUNDS", header_format)
            sheet.write(row, 8, total_refund, header_format)
            row += 1

            sheet.write(row, 7, "BALANCE", header_format)
            sheet.write(row, 8, balance, header_format)
            row += 2

        workbook.close()
        output.seek(0)

        file_data = base64.b64encode(output.read())

        self.write({
            'excel_file': file_data,
            'excel_filename': 'account_statement.xlsx'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model={self._name}&id={self.id}&field=excel_file&download=true&filename={self.excel_filename}',
            'target': 'self',
        }