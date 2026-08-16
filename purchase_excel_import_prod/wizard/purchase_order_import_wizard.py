import base64
import io

from odoo import api, fields, models
from odoo.exceptions import UserError

try:
    from openpyxl import load_workbook
except ImportError:
    load_workbook = None


REQUIRED_HEADERS = [
    'Product',
    'Variant',
    'Quantity',
    'Qty Per Punit',
    'Purchase Unit',
    'Unit Price',
    'Punit Price',
]

VALID_PURCHASE_UNITS = ('Liter', 'KG')


class PurchaseOrderImportWizard(models.TransientModel):
    _name = 'purchase.order.import.wizard'
    _description = 'Import RFQ Lines from Excel'

    order_id = fields.Many2one(
        'purchase.order',
        string='RFQ',
        required=True,
        default=lambda self: self.env.context.get('active_id'),
    )
    excel_file = fields.Binary(string='Excel File', required=True)
    filename = fields.Char(string='Filename')

    def action_import(self):
        self.ensure_one()

        if not load_workbook:
            raise UserError(
                "The 'openpyxl' Python package is not installed on this "
                "server. Ask your admin to run: pip install openpyxl"
            )

        if not self.order_id:
            raise UserError("No RFQ selected to import lines into.")

        try:
            data = base64.b64decode(self.excel_file)
            workbook = load_workbook(io.BytesIO(data), data_only=True)
            sheet = workbook.active
        except Exception as exc:
            raise UserError("Could not read the Excel file: %s" % exc)

        header_row = next(sheet.iter_rows(min_row=1, max_row=1, values_only=True), None)
        if not header_row:
            raise UserError("The Excel sheet appears to be empty.")

        headers = [str(cell).strip() if cell else '' for cell in header_row]

        missing_headers = [h for h in REQUIRED_HEADERS if h not in headers]
        if missing_headers:
            raise UserError(
                "The Excel file is missing these required columns:\n%s\n\n"
                "Expected headers (row 1, exact spelling):\n%s"
                % (', '.join(missing_headers), ', '.join(REQUIRED_HEADERS))
            )

        col = {header: headers.index(header) for header in REQUIRED_HEADERS}

        line_commands = []
        errors = []

        for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            if row is None or all(v in (None, '') for v in row):
                continue  # skip fully blank rows

            product_name = row[col['Product']]
            if not product_name:
                errors.append("Row %s: Product column is empty." % row_num)
                continue
            product_name = str(product_name).strip()

            variant_raw = row[col['Variant']]
            variant_value = str(variant_raw).strip() if variant_raw not in (None, '') else False

            # Match on the TEMPLATE name first (this is what "Product" really
            # is when a product has variants - the variant text like "20gm"
            # is stored separately, not appended to this name).
            candidates = self.env['product.product'].search(
                [('product_tmpl_id.name', '=', product_name)]
            )
            if not candidates:
                errors.append("Row %s: no product found with exact name '%s'." % (row_num, product_name))
                continue

            if variant_value:
                candidates = candidates.filtered(
                    lambda p, v=variant_value: v in p.product_template_attribute_value_ids
                        .mapped('product_attribute_value_id.name')
                )
                if not candidates:
                    errors.append(
                        "Row %s: product '%s' was found, but none of its variants match Variant '%s'."
                        % (row_num, product_name, variant_value)
                    )
                    continue

            if len(candidates) > 1:
                errors.append(
                    "Row %s: product '%s' has %d matching variants - fill in the Variant "
                    "column to pick the right one (e.g. '250ml', '1L', '20gm')."
                    % (row_num, product_name, len(candidates))
                )
                continue

            product = candidates[:1]

            # Purchase Unit is optional. Blank stays blank. If something IS
            # provided, it still has to be 'Liter' or 'KG' because this is an
            # Odoo Selection field - it cannot store arbitrary text, that's
            # a hard database constraint, not a business rule we're choosing.
            purchase_unit_raw = row[col['Purchase Unit']]
            if purchase_unit_raw in (None, ''):
                purchase_unit = False
            else:
                purchase_unit = str(purchase_unit_raw).strip()
                if purchase_unit not in VALID_PURCHASE_UNITS:
                    errors.append(
                        "Row %s: Purchase Unit was '%s' - if you fill this column it must be "
                        "exactly 'Liter' or 'KG'. Leave it empty if it doesn't apply."
                        % (row_num, purchase_unit)
                    )
                    continue

            # Numeric columns are optional too: blank -> 0. Only actual text
            # in a number column is an error, since that truly can't be saved.
            def to_float(value, label):
                if value in (None, ''):
                    return 0.0, None
                try:
                    return float(value), None
                except (TypeError, ValueError):
                    return None, "Row %s: '%s' must be a number (got '%s')." % (row_num, label, value)

            quantity, err1 = to_float(row[col['Quantity']], 'Quantity')
            qty_per_punit, err2 = to_float(row[col['Qty Per Punit']], 'Qty Per Punit')
            unit_price, err3 = to_float(row[col['Unit Price']], 'Unit Price')
            punit_price, err4 = to_float(row[col['Punit Price']], 'Punit Price')

            row_errors = [e for e in (err1, err2, err3, err4) if e]
            if row_errors:
                errors.extend(row_errors)
                continue

            line_commands.append((0, 0, {
                'product_id': product.id,
                'name': product.display_name,
                'product_qty': quantity,
                'product_uom': product.uom_po_id.id or product.uom_id.id,
                'date_planned': fields.Datetime.now(),
                'price_unit': unit_price,
                'x_purchase_qty': qty_per_punit,
                'x_studio_purchase_unit': purchase_unit,
                'x_punite_price': punit_price,
            }))

        if errors:
            raise UserError(
                "Import stopped, nothing was saved. Fix these rows and try again:\n\n%s"
                % '\n'.join(errors)
            )

        if not line_commands:
            raise UserError("No valid product rows were found in the Excel file.")

        # Fresh RFQ workflow: clear any existing lines, then load from Excel.
        self.order_id.order_line = [(5, 0, 0)] + line_commands

        return {'type': 'ir.actions.act_window_close'}
