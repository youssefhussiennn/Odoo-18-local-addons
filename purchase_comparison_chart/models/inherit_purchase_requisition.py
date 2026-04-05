from odoo import models, fields, api, _
from urllib.parse import urljoin
# from odoo.tools import slugify
from odoo.exceptions import UserError
import xlwt
import base64
from datetime import datetime
import platform


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('requisition_id'):
                purchase_ids = self.env['purchase.order'].search([('requisition_id', '=', vals.get('requisition_id'))])
                for po_id in purchase_ids:
                    if vals.get('partner_id') == po_id.partner_id.id:
                        raise UserError(_('RFQ is available for this purchase agreement for the same vendor'))
        return super(PurchaseOrder, self).create(vals_list)

    def write(self, vals):
        if self.requisition_id:
            if vals.get('partner_id') or vals.get('requisition_id'):
                purchase_ids = self.env['purchase.order'].search([('requisition_id', '=', vals.get('requisition_id'))])
                for po_id in purchase_ids:
                    if vals.get('partner_id') == po_id.partner_id.id:
                        raise UserError(_('RFQ is available for this purchase agreement for the same vendor'))
            return super(PurchaseOrder, self).write(vals)


class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    print_url = fields.Char("Print link", compute="_compute_url")

    def _compute_url(self):
        """ Computes a public URL for the purchase comparison """
        base_url = '/' if self.env.context.get('relative_url') else self.env['ir.config_parameter'].get_param(
            'web.base.url')
        # for record in self:
        #     record.print_url = urljoin(base_url, "purchase_comparison_chart/purchase_comparison/%s" % (slugify(record)))

    def show_terms_condition(self, value1, value2):
        if value1 and value2:
            va = str(value1).strip()
            terms_condition = self.env['purchase.order'].search(
                [('requisition_id', '=', self.id), ('partner_id', '=', int(va))])
            if terms_condition:
                return terms_condition.notes
            else:
                return None

    def purchase_comparison(self):
        """ Open the website page with the purchase comparison form """
        self.ensure_one()
        if self.order_count == 0:
            raise UserError(_('No RFQ available for the Purchase agreement. Please add some RFQ to compare'))
        return {
            'type': 'ir.actions.act_url',
            'name': "Purchase Comparison Chart",
            'target': 'self',
            'url': self.with_context(relative_url=True).print_url
        }

    def print_xl(self):
        purchase_orders = self.env['purchase.order'].search([('requisition_id', '=', self.id)])
        for rec in purchase_orders:
            for line in rec.order_line:
                price_subtotal = line.price_subtotal
                

            style2 = xlwt.easyxf('font: name Times New Roman bold on;align: horiz center;', num_format_str='#,##0')
            style0 = xlwt.easyxf('font: name Times New Roman bold on;align: horiz center, wrap on;', num_format_str='#,##0.00')
            style3 = xlwt.easyxf('font: name Times New Roman bold on; align: horiz center, wrap on, rotation 90;', num_format_str='#,##0.00')
            style1 = xlwt.easyxf('font: name Times New Roman, bold on, height 250; ''pattern: pattern solid, fore_colour light_green; ''align: horiz center, wrap on;', num_format_str='#,##0.00')

            workbook = xlwt.Workbook()
            sheet = workbook.add_sheet(self.name)
            sheet.write_merge(2, 2, 0, 4, 'PURCHASE  COMPARISON', style1) 
            sheet.write(3, 1, 'PRC No', style0)  
            sheet.write(3, 2, self.name, style0)  
            sheet.write(4, 1, 'Date', style0)  
            sheet.write(4, 2, self.date_start.strftime('%m-%d-%Y'), style0)

            sheet.write(8, 0, 'Internal Reference', style1) 
            sheet.write_merge(8, 8, 1, 3, 'Product', style1) 
            sheet.write(8, 4, 'Package', style1)  
            sheet.write(8, 5, 'QTY', style1)  
            sheet.write(8, 6, 'Unit', style1)  
            sheet.write(8, 7, 'Description', style1)  
            sheet.write(8, 8, 'Qty On Hand', style1)  
            sheet.write(8, 9, 'Forcasted Qty', style1)  
            sheet.write(8, 10, 'Average', style1)   
            sheet.write(8, 11, 'Available Qty', style1)  
            sheet.write(8, 12, 'Last Purchase Price', style1)  

            # Add partner's name and payment term
            partner_names = [rec.partner_id.name for rec in purchase_orders]
            payment_terms = [rec.payment_term_id for rec in purchase_orders]
            # Write partner names
            for i, partner_name in enumerate(partner_names):
                sheet.write(7, 13 + i, partner_name, style3) 

        

            # Write product prices for each partner
            for j, line in enumerate(self.line_ids):
                price_unit = line.price_unit
                purchase_qty = line.purchase_qty_punit
                composition = line.composition
                purchase_unit = line.purchase_unit
                qty_on_hand = line.qty_on_hand_punit
                product_id = line.product_id  
                last_purchase_price  = line.last_purchase_price_punit 
                forcasted  = line.forcasted 
                available  = line.forcasted + line.qty_on_hand_punit
                internal_reference = line.product_id.default_code
                form = line.form

                # Fetch the product variant details
                if product_id:
                    product_record = self.env['product.product'].browse(product_id.id)
                    variant_name = product_record.product_template_variant_value_ids.mapped('name')
                else:
                    variant_name = ""

                row_index = 9 + j  
                sheet.write(row_index, 0, internal_reference, style0)  
                sheet.write_merge(row_index, row_index, 1, 3, product_id.name, style0)  
                sheet.write(row_index, 4, ', '.join(variant_name), style0)  
                sheet.write(row_index, 5, purchase_qty, style0)  
                sheet.write(row_index, 6, purchase_unit, style0) 
                sheet.write(row_index, 7, composition, style0)  
                sheet.write(row_index, 8, qty_on_hand, style0)  
                sheet.write(row_index, 9, forcasted, style0)  
                sheet.write(row_index, 11, form, style0)  
                sheet.write(row_index, 12, last_purchase_price, style0)  


                # Collect prices for calculating the average
                prices = []
                for i, order in enumerate(purchase_orders):
                    # Filter order lines to match the current product
                    matching_order_lines = order.order_line.filtered(lambda ol: ol.product_id.id == product_id.id)

                    if matching_order_lines:
                        partner_price = matching_order_lines[0].price_punit  # Get the first match
                        try:
                            price = float(partner_price)
                            if price > 0:
                                prices.append(price)
                                sheet.write(row_index, 13 + i, partner_price, style0)
                            else:
                                # Write an empty cell if the price is 0.0
                                sheet.write(row_index, 13 + i, '', style0)
                        except ValueError:
                            # Handle the case where partner_price cannot be converted to float
                            pass

                # Calculate and write the average price
                valid_prices = [price for price in prices if price > 0]
                if valid_prices:
                    average_price = sum(valid_prices) / len(valid_prices)
                    sheet.write(row_index, 10, average_price, style0)

            #write payment terms
            payment_terms = [rec.payment_term_id for rec in purchase_orders]
            # payment_terms_start_row = row_index + 2 
            for i, payment_term in enumerate(payment_terms):
                sheet.write(8, 13 + i, payment_term.name if payment_term else "", style0)

        ams_time = datetime.now()
        date = ams_time.strftime('%m-%d-%Y %H.%M.%S')

        if platform.system() == 'Linux':
            filename = ('/tmp/Purchase Comparison Chart-' + str(datetime.today().date()) + '.xls')
        else:
            filename = ('Purchase Comparison Chart-' + str(datetime.today().date()) + '.xls')

        workbook.save(filename)
        fp = open(filename, "rb")
        file_data = fp.read()
        out = base64.b64encode(file_data)
        attach_id = self.env['report.wizard'].create({'attachment': out,
                                                    'attach_name': 'Purchase Comparison Chart.xls'})
        fp.close()

        return {
            'type': 'ir.actions.act_window',
            'name': ('Report'),
            'res_model': 'report.wizard',
            'res_id': attach_id.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }



class PaymentWizard(models.TransientModel):
    _name = 'report.wizard'
    _description = 'Report Details'

    attachment = fields.Binary('Excel Report File', nodrop=True, readonly=True)
    attach_name = fields.Char('Attachment Name')
