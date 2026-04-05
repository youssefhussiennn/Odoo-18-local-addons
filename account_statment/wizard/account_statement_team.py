# -*- coding: utf-8 -*-
import time
from odoo import models, fields, api, _, exceptions, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
import datetime
import base64
from datetime import date
from io import BytesIO
import xlsxwriter

class AccountStatementTeamWizard(models.TransientModel):
    _name = 'account.statement.team.wizard'
    
    team_ids = fields.Many2many('crm.team', string="Sales Team")


    date_start = fields.Date(string='Start Date',default=time.strftime('2025-01-01'))
    date_end = fields.Date(string='End Date')



    def get_account_statement_sales_team_report_excel(self):

        result_xlsx = self.final_account_statement_excel_report()
        # return True

        attachment_id = self.env['wizard.account.statement.excel.report'].create({
            'namexlsx': 'Account Statement Report for sales team.xlsx',
            'reportxlsx': base64.encodestring(result_xlsx),
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



    def final_account_statement_excel_report(self):

          
        report_name = 'كشف حساب فريق المبيعات'

        columns = [
            ('اسم المندوب', 20, 'char', 'char'),

            ('الرصيد الافتتاحي', 15, 'char', 'char'),
            
            ('اجمالي مبيعات', 15, 'char', 'char'),
            
            ('اجمالي خصم مسموح به', 15, 'char', 'char'),


            ('صافي البيع بعد الخصم', 15, 'char', 'char'),
            
            ('اجمالي مرتجعات', 15, 'char', 'char'),

            ('اجمالي مشتريات من العملا', 15, 'char', 'char'),
            
            ('صافي البيع', 15, 'char', 'char'),
            
            ('اجمالي السداد', 15, 'char', 'char'),

            ('اجمالي الخصومات الاخري', 15, 'char', 'char'),

            ('رصيد العملاء', 15, 'char', 'char'),

            ('شيكات ضمان', 15, 'char', 'char'),

            ('شيكات تحت التحصيل', 15, 'char', 'char'),

            ('نسبة الخصم', 15, 'char', 'char'),

            ('نسبة التحصيل', 15, 'char', 'char'),

            ('نسبة المرتجعات', 15, 'char', 'char'),



        ]

        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = self.add_workbook_format(workbook)
        worksheet = workbook.add_worksheet(report_name)


        



        if self.date_start and self.date_end and self.date_start > self.date_end:
            raise UserError("The Start date cannot be greater than the end date.")
        
        if self.team_ids:
            moves = self.env['account.move.line'].search([('partner_id.team_id','in',self.team_ids.ids),'|','|','|',('account_id.account_type','in',('liability_payable', 'asset_receivable')), ('account_id.is_safty_account','=', True), ('account_id.is_collection_account','=', True), ('account_id.customer_allowed_discount','=', True), ('parent_state', '=', 'posted')])
            old_invoices = self.env['account.move.line'].search([('date', '<', self.date_start),('partner_id.team_id','in',self.team_ids.ids),('account_id.account_type','in',('liability_payable', 'asset_receivable')), ('parent_state', '=', 'posted')])

        
        # else:
        #     moves = self.env['account.move.line'].search([('partner_id.user_id.id','in',self.user_ids.ids),'|','|','|',('account_id.account_type','in',('liability_payable', 'asset_receivable')), ('account_id.is_safty_account','=', True), ('account_id.is_collection_account','=', True), ('account_id.customer_allowed_discount','=', True), ('parent_state', '=', 'posted')])
        #     old_invoices = self.env['account.move.line'].search([('date', '<', self.date_start),('partner_id.user_id.id','in',self.user_ids.ids),('account_id.account_type','in',('liability_payable', 'asset_receivable')), ('parent_state', '=', 'posted')])

        
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
            for team in all_record.mapped(lambda x:x.partner_id.team_id):

                title = '    مبيعات الفريق' +'  '+ str(team.name)
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


                for sales_person in all_record.mapped(lambda x:x.partner_id.user_id):

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
                    salesperson_total_sales_after_dis = abs(sum(records_without_checks_and_allowed_discount.filtered(lambda x:x.move_id.move_type in ['out_invoice']).mapped(lambda x:x.price_subtotal)))

                    salesperson_total_discount = salesperson_total_sales_before_dis - salesperson_total_sales_after_dis

                    # total payments for sales person
                    # salesperson_total_payment = abs(sum(records_without_checks_and_allowed_discount.filtered(lambda x:x.move_id.move_type in ['entry'] and x.journal_id.type != 'general').mapped(lambda x:x.credit - x.debit)))
                    salesperson_total_payment = abs(sum(records_without_checks_and_allowed_discount.filtered(lambda x:x.move_id.move_type in ['entry'] and x.move_id.is_opening_balance == False).mapped(lambda x:x.credit - x.debit)))
                    partners = all_record_of_salesperson.mapped(lambda x:x.partner_id)
                    salesperson_total_initial_balance = abs(sum(old_invoices.filtered(lambda x:x.partner_id.user_id == sales_person and x.partner_id in partners).mapped(lambda x:x.credit - x.debit)))
                    salesperson_total_initial_balance = salesperson_total_initial_balance + abs(sum(records_without_checks_and_allowed_discount.filtered(lambda x:x.move_id.is_opening_balance == True).mapped(lambda x:x.debit - x.credit)))

                    salesperson_total_balance = salesperson_total_initial_balance + salesperson_total_sales_after_dis - salesperson_total_refund - salesperson_total_payment - salesperson_total_purchase - salesperson_total_customer_allowed_discount
                    # salesperson_total_balance = salesperson_total_initial_balance + sum(records_without_checks_and_allowed_discount.mapped(lambda x:x.debit - x.credit))
                    discount_percentage = round((salesperson_total_discount/salesperson_total_sales_before_dis)*100,2) if salesperson_total_sales_before_dis != 0 else 0
                    total = salesperson_total_balance+salesperson_total_payment
                    if total==0:
                        salesperson_total_payment_percentage = 0
                    else:
                        salesperson_total_payment_percentage = round((salesperson_total_payment/(salesperson_total_balance+salesperson_total_payment))*100,2)
                    salesperson_total_refund_percentage = round((salesperson_total_refund/salesperson_total_sales_after_dis)*100,2) if salesperson_total_sales_after_dis != 0 else 0
                    salesperson_total_final_sale = salesperson_total_sales_after_dis - salesperson_total_refund - salesperson_total_purchase
                    
                    worksheet.write(row - 1, 0, sales_person.name or '0', wbf['content'])
                    worksheet.write(row - 1, 1, salesperson_total_initial_balance, wbf['content'])
                    
                    worksheet.write(row - 1, 2, salesperson_total_sales_before_dis, wbf['content'])

                    worksheet.write(row - 1, 3, salesperson_total_discount, wbf['content'])

                    worksheet.write(row - 1, 4, salesperson_total_sales_after_dis, wbf['content'])
                    
                    worksheet.write(row - 1, 5, salesperson_total_refund, wbf['content'])

                    worksheet.write(row - 1, 6, salesperson_total_purchase, wbf['content'])
                    
                    worksheet.write(row - 1, 7, salesperson_total_final_sale, wbf['content'])
                    
                    worksheet.write(row - 1, 8, salesperson_total_payment, wbf['content'])

                    worksheet.write(row - 1, 9, salesperson_total_customer_allowed_discount, wbf['content'])
                    
                    worksheet.write(row - 1, 10, salesperson_total_balance or '0', wbf['content'])
                    
                    worksheet.write(row - 1, 11, salesperson_total_safty_check, wbf['content'])

                    worksheet.write(row - 1, 12, salesperson_total_collection_check, wbf['content'])

                    worksheet.write(row - 1, 13, discount_percentage, wbf['content'])

                    worksheet.write(row - 1, 14, salesperson_total_payment_percentage, wbf['content'])

                    worksheet.write(row - 1, 15, salesperson_total_refund_percentage, wbf['content'])

                    row += 1


                all_record_of_salesteam = all_record.filtered(lambda x:x.partner_id.team_id == team)
                # total customer allowed discount for sales person
                salesteam_total_customer_allowed_discount = sum(all_record_of_salesteam.filtered(lambda x:x.account_id.customer_allowed_discount == True).mapped(lambda x:x.debit - x.credit))
                # total safty check for sales person
                salesteam_total_safty_check = abs(sum(all_record_of_salesteam.filtered(lambda x:x.account_id.is_safty_account == True).mapped(lambda x:x.debit - x.credit)))
                # total collection checks for sales person
                salesteam_total_collection_check = abs(sum(all_record_of_salesteam.filtered(lambda x:x.account_id.is_collection_account == True).mapped(lambda x:x.debit - x.credit)))
                # all records without safty checks and collection checks and customer allowed discount
                records_without_checks_and_allowed_discount = all_record_of_salesteam.filtered(lambda x:x.account_id.customer_allowed_discount == False and x.account_id.is_safty_account == False and x.account_id.is_collection_account == False)

                # get total refund for sales person
                salesteam_total_refund = abs(sum(records_without_checks_and_allowed_discount.filtered(lambda x:x.move_id.move_type in ['out_refund', 'in_refund']).mapped(lambda x:x.price_subtotal)))
                
                # total purchase for sales person
                salesteam_total_purchase = abs(sum(records_without_checks_and_allowed_discount.filtered(lambda x:x.move_id.move_type in ['in_invoice']).mapped(lambda x:x.price_subtotal)))

                # total sales before discount salesteam
                salesteam_total_sales_before_dis = abs(sum(records_without_checks_and_allowed_discount.filtered(lambda x:x.move_id.move_type in ['out_invoice']).mapped(lambda x:x.move_id.invoice_line_ids).mapped(lambda x:(x.quantity * x.price_unit))))
                
                # total sales after discount salesteam
                salesteam_total_sales_after_dis = abs(sum(records_without_checks_and_allowed_discount.filtered(lambda x:x.move_id.move_type in ['out_invoice']).mapped(lambda x:x.price_subtotal)))

                salesteam_total_discount = salesteam_total_sales_before_dis - salesteam_total_sales_after_dis

                # total payments for sales person
                # salesteam_total_payment = abs(sum(records_without_checks_and_allowed_discount.filtered(lambda x:x.move_id.move_type in ['entry'] and x.journal_id.type != 'general').mapped(lambda x:x.credit - x.debit)))
                salesteam_total_payment = abs(sum(records_without_checks_and_allowed_discount.filtered(lambda x:x.move_id.move_type in ['entry'] and x.move_id.is_opening_balance == False).mapped(lambda x:x.credit - x.debit)))
                partners = all_record_of_salesteam.mapped(lambda x:x.partner_id)
                salesteam_total_initial_balance = abs(sum(old_invoices.filtered(lambda x:x.partner_id.team_id == team and x.partner_id in partners).mapped(lambda x:x.credit - x.debit)))
                salesteam_total_initial_balance = salesteam_total_initial_balance + abs(sum(records_without_checks_and_allowed_discount.filtered(lambda x:x.move_id.is_opening_balance == True).mapped(lambda x:x.debit - x.credit)))

                salesteam_total_balance = salesteam_total_initial_balance + salesteam_total_sales_after_dis - salesteam_total_refund - salesteam_total_payment - salesteam_total_purchase - salesteam_total_customer_allowed_discount
                # salesteam_total_balance = salesteam_total_initial_balance + sum(records_without_checks_and_allowed_discount.mapped(lambda x:x.debit - x.credit))
                discount_percentage = round((salesteam_total_discount/salesteam_total_sales_before_dis)*100,2) if salesteam_total_sales_before_dis != 0 else 0
                team_total = salesteam_total_balance+salesteam_total_payment
                if team_total==0:
                    salesteam_total_payment_percentage = 0
                else:
                    salesteam_total_payment_percentage = round((salesteam_total_payment/(salesteam_total_balance+salesteam_total_payment))*100,2)
                # salesteam_total_payment_percentage = round((salesteam_total_payment/(salesteam_total_balance+salesteam_total_payment))*100,2) if salesteam_total_payment != 0 and salesteam_total_balance!=0 else 0
                salesteam_total_refund_percentage = round((salesteam_total_refund/salesteam_total_sales_after_dis)*100,2) if salesteam_total_sales_after_dis != 0 else 0
                salesteam_final_total_sales = salesteam_total_sales_after_dis - salesteam_total_refund - salesteam_total_purchase

                

                worksheet.merge_range('A'+str(row+1)+':P'+str(row+1), 'الاجمالي', wbf['header_orange'])
                print(salesteam_total_safty_check)
                print(salesteam_total_collection_check)
                row += 2


                worksheet.write(row - 1, 0, 'الرصيد الافتتاحي', wbf['header_orange'])
                worksheet.write(row - 1, 1, salesteam_total_initial_balance, wbf['content'])
                row += 1


                worksheet.write(row - 1, 0, 'رصيد العملاء', wbf['header_orange'])
                worksheet.write(row - 1, 1, salesteam_total_balance, wbf['content'])
                row += 1

                worksheet.write(row - 1, 0, 'اجمالي مبيعات', wbf['header_orange'])
                worksheet.write(row - 1, 1, salesteam_total_sales_before_dis, wbf['content'])
                row += 1

                worksheet.write(row - 1, 0, 'اجمالي خصم مسموح به', wbf['header_orange'])
                worksheet.write(row - 1, 1, salesteam_total_discount, wbf['content'])
                # discount percentage
                worksheet.write(row - 1, 8, 'نسبة الخصم', wbf['header_orange'])
                worksheet.write(row - 1, 9, discount_percentage, wbf['content'])
                row += 1

                worksheet.write(row - 1, 0, 'صافي البيع بعد الخصم', wbf['header_orange'])
                worksheet.write(row - 1, 1, salesteam_total_sales_after_dis, wbf['content'])
                row += 1

                worksheet.write(row - 1, 0, 'اجمالي مرتجعات', wbf['header_orange'])
                worksheet.write(row - 1, 1, salesteam_total_refund, wbf['content'])

                # refund percentage
                worksheet.write(row - 1, 8, 'نسبة المرتجعات', wbf['header_orange'])
                worksheet.write(row - 1, 9, salesteam_total_refund_percentage, wbf['content'])
                row += 1

                worksheet.write(row - 1, 0, 'اجمالي مشتريات من العملا', wbf['header_orange'])
                worksheet.write(row - 1, 1, salesteam_total_purchase, wbf['content'])
                row += 1

                worksheet.write(row - 1, 0, 'صافي البيع', wbf['header_orange'])
                worksheet.write(row - 1, 1, salesteam_final_total_sales, wbf['content'])
                row += 1

                worksheet.write(row - 1, 0, 'اجمالي سداد', wbf['header_orange'])
                worksheet.write(row - 1, 1, salesteam_total_payment, wbf['content'])
                # payment percentage
                worksheet.write(row - 1, 8, 'نسبة التحصيل', wbf['header_orange'])
                worksheet.write(row - 1, 9, salesteam_total_payment_percentage, wbf['content'])
                row += 1

                worksheet.write(row - 1, 0, 'اجمالي الخصومات الاخري', wbf['header_orange'])
                worksheet.write(row - 1, 1, salesteam_total_customer_allowed_discount, wbf['content'])
                row += 1

                worksheet.write(row - 1, 0, 'شيكات ضمان', wbf['header_orange'])
                worksheet.write(row - 1, 1, salesteam_total_safty_check, wbf['content'])
                row += 1

                worksheet.write(row - 1, 0, 'شيكات تحت التحصيل', wbf['header_orange'])
                worksheet.write(row - 1, 1, salesteam_total_collection_check, wbf['content'])
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

