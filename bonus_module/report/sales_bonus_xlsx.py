from odoo import api, models, fields
from datetime import datetime

class SalesBonusXlsx(models.AbstractModel):
    _name = 'report.bonus_module.sales_bonus_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Sales Bonus Excel Report'

    def generate_xlsx_report(self, workbook, data, partners):


        date_format = workbook.add_format({'num_format': 'dd-mm-yyyy'})

        monetary_format = workbook.add_format({'num_format': '#,##0'})

        header_style = workbook.add_format({
            'font_size': 10,
            'align': 'center',
            'bold': True,
            'bg_color': '#D3D3D3',
            'border': 1
        })

        content_style = workbook.add_format({
            'font_size': 10,
            'align': 'left',
            'border': 1
        })

        sheet = workbook.add_worksheet('Sales Bonus Report')

        partner = self.env['res.partner'].browse(data['partner_id'])
        sheet.write(0, 0, 'Partner:', header_style)
        sheet.write(0, 1, partner.name, content_style)

        bonus_report_records = self.env['account.invoice.report'].browse(data['doc_ids'])

        total_quantity = 0
        total_amount = 0
        total_bonus_sum = 0

        for record in bonus_report_records:
            
            total_quantity += record.quantity
            total_amount += record.price_subtotal

            found_bonus = False
            bonus_value = 0
            for b in data['bonus_values']:
                if b['partner_id'] == record.partner_id.id and b['product_id'] == record.product_id.product_tmpl_id.id:
                    bonus_value = b['bonus']
                    found_bonus = True
                    break

            if found_bonus:
                total_bonus = (bonus_value / 100) * record.price_subtotal
                total_bonus_sum += total_bonus

        totals_row = 2
        
        sheet.write(totals_row, 5, total_amount, monetary_format)
        sheet.write(totals_row, 7, total_bonus_sum, monetary_format)
        

        headers_row = 4

        headers = [
            'Date', 'Invoice', 'Product Category', 
            'Product', 'Quantity', 'Amount', 'Bonus %', 'Total Bonus'
        ]
        for col_num, header in enumerate(headers):
            sheet.write(headers_row, col_num, header, header_style)


        data_start_row = headers_row + 1
        row = data_start_row

        for record in bonus_report_records:
            sheet.write(row, 0, record.invoice_date, date_format)
            sheet.write(row, 1, record.move_id.name, content_style)
            sheet.write(row, 2, record.product_categ_id.name, content_style)
            sheet.write(row, 3, record.product_id.display_name, content_style)
            sheet.write(row, 4, record.quantity, content_style)
            sheet.write(row, 5, record.price_subtotal, monetary_format)

            found_bonus = False
            for b in data['bonus_values']:

                if b['partner_id'] == record.partner_id.id and b['product_id'] == record.product_id.product_tmpl_id.id:
                    
                    date_start = fields.Datetime.from_string(b['date_start'])
                    date_end = fields.Datetime.from_string(b['date_end'])
                    invoice_date = fields.Datetime.from_string(record.invoice_date)

                    # Check if the invoice date is within the bonus date range
                    if date_start <= invoice_date <= date_end:
                        sheet.write(row, 6, b['bonus'], content_style)
                        bonus_value = b['bonus']
                        found_bonus = True
                        break

            if not found_bonus:
                sheet.write(row, 6, 'N/A', content_style)

            if found_bonus:
                total_bonus = (bonus_value / 100) * record.price_subtotal
                sheet.write(row, 7, total_bonus, monetary_format)
            
            row += 1
