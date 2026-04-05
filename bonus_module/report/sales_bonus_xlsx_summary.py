from odoo import api, models, fields
from datetime import datetime

class SalesBonusXlsxSummary(models.AbstractModel):
    _name = 'report.bonus_module.sales_bonus_xlsx_summary'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Sales Bonus Summary Excel Report'

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

        sheet = workbook.add_worksheet('Sales Bonus Summary')

        partner = self.env['res.partner'].browse(data['partner_id'])
        sheet.write(0, 0, 'Partner:', header_style)
        sheet.write(0, 1, partner.name if partner else 'All', content_style)

        # Fetch bonus report records
        bonus_report_records = self.env['account.invoice.report'].browse(data['doc_ids'])

        # Dictionary to store aggregated data by product
        product_totals = {}

        # Aggregate data for each product across multiple invoices
        total_quantity = 0
        total_amount = 0
        total_bonus_sum = 0

        for record in bonus_report_records:
            product_key = (record.product_id.product_tmpl_id.id, record.partner_id.id)  # Unique key based on product and partner

            if product_key not in product_totals:
                product_totals[product_key] = {
                    'partner_name': record.partner_id.name,
                    'product_name': record.product_id.product_tmpl_id.display_name,
                    'quantity': 0,
                    'amount': 0,
                    'bonus': 0,
                    'bonus_percentage': 0
                }

            product_totals[product_key]['quantity'] += record.quantity
            product_totals[product_key]['amount'] += record.price_subtotal
            total_quantity += record.quantity
            total_amount += record.price_subtotal

            # Find the bonus percentage for the product and partner
            found_bonus = False
            for b in data['bonus_values']:
                if b['partner_id'] == record.partner_id.id and b['product_id'] == record.product_id.product_tmpl_id.id:
                    product_totals[product_key]['bonus_percentage'] = b['bonus']
                    found_bonus = True
                    break

            if found_bonus:
                total_bonus = (product_totals[product_key]['bonus_percentage'] / 100) * record.price_subtotal
                product_totals[product_key]['bonus'] += total_bonus
                total_bonus_sum += total_bonus


        sheet.write(3, 0, 'Total Amount', header_style)
        sheet.write(3, 1, total_amount, monetary_format)

        sheet.write(4, 0, 'Total Bonus', header_style)
        sheet.write(4, 1, total_bonus_sum, monetary_format)

        # Headers for summary table
        headers_row = 6
        headers = ['Product', 'Total Quantity', 'Total Amount', 'Bonus %', 'Total Bonus']
        for col_num, header in enumerate(headers):
            sheet.write(headers_row, col_num, header, header_style)

        # Populate summary data in the table
        row = headers_row + 1

        for product_key, totals in product_totals.items():
            sheet.write(row, 0, totals['product_name'], content_style)
            sheet.write(row, 1, totals['quantity'], content_style)
            sheet.write(row, 2, totals['amount'], monetary_format)
            sheet.write(row, 3, totals['bonus_percentage'], monetary_format)
            sheet.write(row, 4, totals['bonus'], monetary_format)
            row += 1
