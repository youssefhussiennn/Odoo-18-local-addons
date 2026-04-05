# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools import date_utils
import json
import io
import datetime
import uuid
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

class CustomerSalesReportWizard(models.TransientModel):
    _name = "wizard.customer.sales.report"
    _description = "Customer Sales Report"

    customer_ids = fields.Many2many(
        'res.partner',
        string='Customers',
        domain=[('customer_rank', '>', 0)],
        required=False,
        context={'default_customer_rank': 1, 'create': False},
        options={'no_create': True, 'no_create_edit': True}
    )

    salesperson_ids = fields.Many2many(
        'res.users',
        string='Sales Persons',
        required=False,
        context={'create': False},
        options={'no_create': True, 'no_create_edit': True}
    )

    category_ids = fields.Many2many(
        'product.category',
        string='Product Categories',
        context={'create': False},
        options={'no_create': True, 'no_create_edit': True}
    )
    product_id = fields.Many2one('product.product', string='Product')
    sku = fields.Char(string='SKU')
    qty_sale = fields.Float(string='Qty (Sales Order)')
    qty_contract = fields.Float(string='Qty (Contract)')
    session_id = fields.Char(string='Session ID', index=True)
    
    date_start = fields.Date(string="Start Date", required=True, default=fields.Date.context_today)
    date_end = fields.Date(string="End Date", required=True, default=fields.Date.context_today)

    def export_xls(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'customers': self.customer_ids.ids,
            'salespersons': self.salesperson_ids.ids,
            'categories': self.category_ids.ids,
            'date_start': self.date_start.isoformat(),
            'date_end': self.date_end.isoformat(),
        }
        return {
            'type': 'ir.actions.report',
            'data': {
                'model': self._name,
                'options': json.dumps(data, default=date_utils.json_default),
                'output_format': 'xlsx',
                'report_name': 'Customer Sales Report',
            },
            'report_type': 'custom_xlsx',
        }

    def get_sales_lines(self, customer, category_ids, start_date, end_date, salesperson_ids):
        Product = self.env['product.product']
        Contract = self.env['contract.contract']
        SaleOrder = self.env['sale.order']

        # Get all products in the selected categories
        product_domain = [('categ_id', 'in', category_ids)]
        products = Product.search(product_domain)

        product_map = {
            product.id: {
                'product': product.name,
                'variant': ', '.join(product.product_template_variant_value_ids.mapped('name')),
                'sku': product.default_code,
                'category': product.categ_id.name,
                'qty_contract': 0,
                'qty_sale': 0,
                'price_unit': 0,
                'subtotal': 0.0,
            }
            for product in products
        }

        # Get relevant contracts for the customer
        contracts = Contract.search([
            ('partner_id', '=', customer.id),
            ('date_start', '<=', end_date),
            ('date_end', '>=', start_date),
        ])

        # Aggregate contract quantities
        for contract in contracts:
            for c_line in contract.contract_line_fixed_ids:
                prod_id = c_line.product_id.id
                if prod_id in product_map:
                    product_map[prod_id]['qty_contract'] += c_line.quantity
                    product_map[prod_id]['price_unit'] = c_line.price_unit

        # Get sale orders in the range
        sale_domain = [
            ('partner_id', '=', customer.id),
            ('state', 'in', ['sale', 'done']),
            ('date_order', '>=', start_date),
            ('date_order', '<=', end_date),
        ]
        if salesperson_ids:
            sale_domain.append(('user_id', 'in', salesperson_ids))

        sale_orders = SaleOrder.search(sale_domain)
        sale_lines = sale_orders.mapped('order_line')

        # Aggregate sale quantities
        for line in sale_lines:
            prod_id = line.product_id.id
            if prod_id in product_map:
                product_map[prod_id]['qty_sale'] += line.product_uom_qty
                product_map[prod_id]['subtotal'] += line.price_subtotal
                if not product_map[prod_id]['price_unit']:
                    product_map[prod_id]['price_unit'] = line.price_unit

        return list(product_map.values())

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Customer Sales')

        format_header = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
        format_cell = workbook.add_format({'border': 1})

        headers = ['Customer', 'Category', 'Product SKU', 'Product Name', 'Variant',
                'Qty (Sales)', 'Qty (Contract)']
        for col, header in enumerate(headers):
            sheet.write(0, col, header, format_header)

        row = 1
        customer_ids = data.get('customers', [])
        salesperson_ids = data.get('salespersons', [])
        category_ids = data['categories']
        date_start = fields.Date.from_string(data['date_start'])
        date_end = fields.Date.from_string(data['date_end'])

        customers = self.env['res.partner'].browse(customer_ids)

        # If no customers were selected, fetch from salespeople’s records
        if not customers and salesperson_ids:
            # Customers from sales
            sale_customers = self.env['sale.order'].search([
                ('user_id', 'in', salesperson_ids),
                ('state', 'in', ['sale', 'done']),
                ('date_order', '>=', date_start),
                ('date_order', '<=', date_end),
            ]).mapped('partner_id')

            # Customers from contracts
            contract_customers = self.env['contract.contract'].search([
                ('user_id', 'in', salesperson_ids),
                ('date_start', '<=', date_end),
                ('date_end', '>=', date_start),
            ]).mapped('partner_id')

            customers = (sale_customers | contract_customers).filtered(lambda c: c.customer_rank > 0).sorted(key=lambda c: c.id)

        # Loop through each customer and write data
        for customer in customers:
            lines = self.get_sales_lines(customer, category_ids, date_start, date_end, salesperson_ids)
            for line in lines:
                sheet.write(row, 0, customer.name, format_cell)
                sheet.write(row, 1, line['category'], format_cell)
                sheet.write(row, 2, line['sku'], format_cell)
                sheet.write(row, 3, line['product'], format_cell)
                sheet.write(row, 4, line['variant'], format_cell)
                sheet.write(row, 5, line['qty_sale'], format_cell)
                sheet.write(row, 6, line['qty_contract'], format_cell)
                # sheet.write(row, 7, line['price_unit'], format_cell)
                # sheet.write(row, 8, line['subtotal'], format_cell)
                row += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
        
    def action_show_report_lines(self):
        self.ensure_one()
        session_id = str(uuid.uuid4())
        
        ReportLine = self.env['wizard.customer.sales.report']
        ReportLine.search([('session_id', '=', session_id)]).unlink()  # Clear old lines

        customer_ids = self.customer_ids
        if not customer_ids and self.salesperson_ids:
            sale_customers = self.env['sale.order'].search([
                ('user_id', 'in', self.salesperson_ids.ids),
                ('state', 'in', ['sale', 'done']),
                ('date_order', '>=', self.date_start),
                ('date_order', '<=', self.date_end),
            ]).mapped('partner_id')

            contract_customers = self.env['contract.contract'].search([
                ('user_id', 'in', self.salesperson_ids.ids),
                ('date_start', '<=', self.date_end),
                ('date_end', '>=', self.date_start),
            ]).mapped('partner_id')

            customer_ids = (sale_customers | contract_customers).filtered(lambda c: c.customer_rank > 0)

        for customer in customer_ids:
            lines = self.get_sales_lines(
                customer=customer,
                category_ids=self.category_ids.ids,
                start_date=self.date_start,
                end_date=self.date_end,
                salesperson_ids=self.salesperson_ids.ids
            )
            for line in lines:
                ReportLine.create({
                    'customer_ids': [(6, 0, [customer.id])],
                    'product_id': self.env['product.product'].search([('default_code', '=', line['sku'])], limit=1).id,
                    'category_ids': [(6, 0, [self.env['product.category'].search([('name', '=', line['category'])], limit=1).id])],
                    'sku': line['sku'],
                    'qty_sale': line['qty_sale'],
                    'qty_contract': line['qty_contract'],
                    'session_id': session_id,
                })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Customer Sales Report Lines'),
            'res_model': 'wizard.customer.sales.report',
            'view_mode': 'list',
            'domain': [('session_id', '=', session_id)],
            'target': 'current',
        }
