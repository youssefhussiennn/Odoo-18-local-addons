# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Midilaj (<https://www.cybrosys.com>)
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
import time
from datetime import date, datetime
import pytz
import json
import datetime
import io
from odoo import api, fields, models, _
from odoo.tools import json_default
# from odoo.tools import json_default
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class StockReport(models.TransientModel):
    _name = "wizard.stock.history"
    _description = "Current Stock History"

    warehouse = fields.Many2many('stock.warehouse', 'wh_wiz_rel', 'wh', 'wiz', string='Warehouse', required=True)
    category = fields.Many2many('product.category', 'categ_wiz_rel', 'categ', 'wiz', string='Category')

    # date_start = fields.Date(string="Start Date", required=True, default=fields.Date.context_today)
    # date_end = fields.Date(string="End Date", required=True, default=fields.Date.context_today)

    def export_xls(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'warehouse': self.warehouse.ids,
            'category': self.category.ids,
        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'wizard.stock.history',
                     'options': json.dumps(data, default=json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Current Stock History',
                     },
            'report_type': 'stock_xlsx'
        }

    def get_warehouse(self, data):
        wh = data.warehouse.mapped('id')
        obj = self.env['stock.warehouse'].search([('id', 'in', wh)])
        l1 = []
        l2 = []
        for j in obj:
            l1.append(j.name)
            l2.append(j.id)
        return l1, l2

    def get_lines(self, data, warehouse):
        lines = []
        categ_id = data.mapped('id')
        if categ_id:
            categ_products = self.env['product.product'].search([('categ_id', 'in', categ_id)])
        else:
            categ_products = self.env['product.product'].search([])
        product_ids = tuple([pro_id.id for pro_id in categ_products])
        sale_query = """
               SELECT sum(s_o_l.product_uom_qty) AS product_uom_qty, s_o_l.product_id FROM sale_order_line AS s_o_l
               JOIN sale_order AS s_o ON s_o_l.order_id = s_o.id
               WHERE s_o.state IN ('sale','done')
               AND s_o.warehouse_id = %s
               AND s_o_l.product_id in %s group by s_o_l.product_id"""
        purchase_query = """
               SELECT sum(p_o_l.product_qty) AS product_qty, p_o_l.product_id FROM purchase_order_line AS p_o_l
               JOIN purchase_order AS p_o ON p_o_l.order_id = p_o.id
               INNER JOIN stock_picking_type AS s_p_t ON p_o.picking_type_id = s_p_t.id
               WHERE p_o.state IN ('purchase','done')
               AND s_p_t.warehouse_id = %s AND p_o_l.product_id in %s group by p_o_l.product_id"""
        params = warehouse, product_ids if product_ids else (0, 0)
        self._cr.execute(sale_query, params)
        sol_query_obj = self._cr.dictfetchall()
        self._cr.execute(purchase_query, params)
        pol_query_obj = self._cr.dictfetchall()
        for obj in categ_products:
            sale_value = next((sol['product_uom_qty'] for sol in sol_query_obj if sol['product_id'] == obj.id), 0)
            purchase_value = next((pol['product_qty'] for pol in pol_query_obj if pol['product_id'] == obj.id), 0)
            virtual_available = obj.with_context({'warehouse': warehouse}).virtual_available
            outgoing_qty = obj.with_context({'warehouse': warehouse}).outgoing_qty
            incoming_qty = obj.with_context({'warehouse': warehouse}).incoming_qty
            available_qty = virtual_available + outgoing_qty - incoming_qty
            
            vals = {
                'product_id': obj.id, 
                'sku': obj.default_code,
                'name': obj.name,
                'variant_values': ', '.join(obj.product_template_attribute_value_ids.mapped('name')),
                'usage_rate': obj.usage_rate,
                'composition': obj.composition,
                'category': obj.categ_id.name,
                'parent_category': obj.categ_id.parent_id.name if obj.categ_id.parent_id else '',
                'available': available_qty,
                'virtual': virtual_available,
                'ordered_qty': obj.purchase_order_qty,
                'weight': obj.weight,
            }
            lines.append(vals)
        return lines

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        lines = self.browse(data['ids'])
        d = lines.category
        get_warehouse = self.get_warehouse(lines)
        warehouse_count = len(get_warehouse[0])
        count = warehouse_count + 8
        comp = self.env.user.company_id.name
        sheet = workbook.add_worksheet('Stock Info')

        format0 = workbook.add_format(
            {'font_size': 20, 'align': 'center', 'bold': True, 'bg_color': '#9DE4FF'})  # Light blue
        format1 = workbook.add_format(
            {'font_size': 14, 'align': 'vcenter', 'bold': True, 'bg_color': '#7ADAFF'})  # Aqua Blue
        format11 = workbook.add_format(
            {'font_size': 12, 'align': 'center', 'bold': True, 'bg_color': '#9DE4FF'})  # Light Blue
        format21 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True, 'bg_color': '#C9E6FD'})  # Baby blue
        format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
        format4 = workbook.add_format(
            {'font_size': 12, 'align': 'left', 'bold': True, 'bg_color': '#9DE4FF'})  # Light Blue
        font_size_8 = workbook.add_format({'font_size': 8, 'align': 'center'})
        font_size_8_l = workbook.add_format({'font_size': 8, 'align': 'left'})
        font_size_8_r = workbook.add_format({'font_size': 8, 'align': 'right'})
        red_mark = workbook.add_format({'font_size': 8, 'bg_color': 'red'})
        justify = workbook.add_format({'font_size': 12})
        format3.set_align('center')
        justify.set_align('justify')
        format1.set_align('center')
        red_mark.set_align('center')

        sheet.merge_range(1, 0, 2, 4, 'Product Stock Info', format0)
        sheet.merge_range(3, 0, 3, 4, comp, format11)

        w_house = ', '
        cat = ', '
        c = []
        d1 = d.mapped('id')

        if d1:
            for i in d1:
                c.append(self.env['product.category'].browse(i).name)
            cat = cat.join(c)

        sheet.merge_range(5, 0, 5, 1, 'Warehouse(s) : ', format4)
        w_house = w_house.join(get_warehouse[0])
        sheet.merge_range(5, 2, 5, 2 + warehouse_count, w_house, format4)

        user = self.env['res.users'].browse(self.env.uid)
        tz = pytz.timezone(user.tz if user.tz else 'UTC')
        times = pytz.utc.localize(datetime.datetime.now()).astimezone(tz)

        sheet.merge_range(7, 0, 7, 10, 'Report Date: ' + str(times.strftime("%Y-%m-%d %H:%M %p")),
                          format1)
        sheet.merge_range(8, 0, 8, 6, 'Product Information', format11)

        w_col_no1 = 7

        for i in get_warehouse[0]:
            sheet.write(8, w_col_no1, i, format11)
            w_col_no1 += 1

        sheet.write(9, 0, 'SKU', format21)
        sheet.write(9, 1, 'Parent Category', format21)
        sheet.write(9, 2, 'Category', format21)
        sheet.write(9, 3, 'Name', format21)
        sheet.write(9, 4, 'Composition', format21)
        sheet.write(9, 5, 'Usage Rate', format21)
        sheet.write(9, 6, 'Variant Values', format21)

        p_col_no1 = 7

        for i in get_warehouse[0]:
            sheet.write(9, p_col_no1, 'Available', format21)
            p_col_no1 += 1

        sum_available_col = p_col_no1
        sum_avail_weight_col = p_col_no1 + 1
        weight_col = p_col_no1 + 2
        total_weight_col = p_col_no1 + 3
        # totalweight_col = p_col_no1 + 4

        sheet.write(9, sum_available_col, 'Sum Available', format21)
        sheet.write(9, sum_avail_weight_col, 'Sum Available Weight', format21)
        sheet.write(9, weight_col, 'Ordered Weight', format21)
        sheet.write(9, total_weight_col, 'Total Weight', format21)
        # sheet.write(9, totalweight_col, 'Total Weight', format21)

        prod_row = 10
        prod_col = 0

        product_data = {}

        for i in get_warehouse[1]:
            get_line = self.get_lines(d, i)
            for each in get_line:
                product_key = each['product_id']
                if product_key not in product_data:
                    product_data[product_key] = {
                        'product_id': each['product_id'],
                        'sku': each['sku'],
                        'parent_category': each['parent_category'],
                        'category': each['category'],
                        'name': each['name'],
                        'composition': each['composition'],
                        'usage_rate': each['usage_rate'],
                        'variant_values': each['variant_values'],
                        'sum_available': 0,
                        'ordered_qty': each['ordered_qty'],
                        'weight': each['weight'],
                        'row': prod_row,
                        'total': (each['weight'] * each['available']) + (each['weight'] * each['ordered_qty']),
                        
                    }
                    prod_row += 1

                product_data[product_key]['sum_available'] += each['available']                
                

        for product_key, product_info in product_data.items():
            row = product_info['row']
            sheet.write(row, prod_col, product_info['sku'], font_size_8_l)
            sheet.write(row, prod_col + 1, product_info['parent_category'], font_size_8_l)
            sheet.write(row, prod_col + 2, product_info['category'], font_size_8_l)
            sheet.write(row, prod_col + 3, product_info['name'], font_size_8_r)
            sheet.write(row, prod_col + 4, product_info['composition'], font_size_8_r)
            sheet.write(row, prod_col + 5, product_info['usage_rate'], font_size_8_r)
            sheet.write(row, prod_col + 6, product_info['variant_values'], font_size_8_r)

        prod_col = 7

        for warehouse_id in get_warehouse[1]:
            get_line = self.get_lines(d, warehouse_id)
            product_row_map = {each['product_id']: product_data[each['product_id']]['row'] for each in get_line}
            for each in get_line:
                row = product_row_map[each['product_id']]
                sheet.write(row, prod_col, each['available'], font_size_8)
            prod_col += 1

        for product_key in product_data:
            row = product_data[product_key]['row']
            sheet.write(row, sum_available_col, product_data[product_key]['sum_available'], font_size_8)
            sheet.write(row, sum_avail_weight_col, product_data[product_key]['sum_available'] * product_data[product_key]['weight'], font_size_8)
            sheet.write(row, weight_col, product_data[product_key]['ordered_qty'] * product_data[product_key]['weight'], font_size_8)
            sheet.write(row, total_weight_col, ((product_data[product_key]['sum_available']) + (product_data[product_key]['ordered_qty'])) * product_data[product_key]['weight'], font_size_8)
            # sheet.write(row, total_col, product_data[product_key]['total'], font_size_8)
            # sheet.write(row, totalweight_col, product_data[product_key]['total'] * product_data[product_key]['weight'], font_size_8)
            # sheet.write_formula(row, total_col, '=SUM({}:{})'.format(xlsxwriter.utility.xl_rowcol_to_cell(row, sum_available_col), xlsxwriter.utility.xl_rowcol_to_cell(row, ordered_qty_col)), font_size_8)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
