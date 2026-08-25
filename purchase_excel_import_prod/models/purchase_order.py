import base64
import io

from odoo import _, models
from odoo.exceptions import UserError

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
except ImportError:
    Workbook = None


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def action_export_lines_excel(self):
        """Export this RFQ's order lines to an .xlsx file for reporting/sharing.

        Columns mirror what's shown on screen: full product name (with
        variant), quantity, qty/Punit, both unit prices, purchase unit,
        and the line amount.
        """
        self.ensure_one()

        if not Workbook:
            raise UserError(_(
                "The 'openpyxl' Python package is not installed on this server. "
                "Ask your admin to run: pip install openpyxl"
            ))

        if not self.order_line:
            raise UserError(_("This RFQ has no lines to export."))

        # Columns match the IMPORT format exactly, so an exported file can be
        # edited and re-imported without reformatting:
        #   Product | Variant | Quantity | Qty Per Punit | Purchase Unit | Punit Price
        headers = [
            'Product',
            'Variant',
            'Quantity',
            'Qty Per Punit',
            'Purchase Unit',
            'Punit Price',
        ]

        wb = Workbook()
        ws = wb.active
        ws.title = 'RFQ Lines'
        ws.append(headers)

        # Header styling
        for c in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=c)
            cell.font = Font(bold=True, color='FFFFFF')
            cell.fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
            cell.alignment = Alignment(horizontal='center')

        for line in self.order_line:
            product = line.product_id
            # Template name goes in Product; the variant attribute value(s)
            # go in Variant - mirroring how the import splits them back apart.
            template_name = product.product_tmpl_id.name or ''
            variant_values = product.product_template_attribute_value_ids.mapped(
                'product_attribute_value_id.name'
            )
            variant_text = ', '.join(variant_values) if variant_values else ''

            ws.append([
                template_name,
                variant_text,
                line.product_qty,
                line.x_purchase_qty,
                line.x_studio_purchase_unit or '',
                line.x_punite_price,
            ])

        # Reasonable column widths
        widths = [30, 14, 12, 14, 14, 12]
        for i, width in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(i)].width = width

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        file_data = base64.b64encode(buffer.read())
        buffer.close()

        filename = '%s_lines.xlsx' % (self.name or 'RFQ').replace('/', '_')

        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': file_data,
            'res_model': 'purchase.order',
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
