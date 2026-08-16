{
    'name': 'Purchase Excel Import',
    'version': '18.0.1.0.0',
    'summary': 'One-step Excel import for RFQ lines, using the existing Studio fields '
                '(qty/Punit, Purchase Unit, Punit Price).',
    'description': """
PRODUCTION VARIANT.

Unlike the local development version, this build does NOT define
x_purchase_qty, x_studio_purchase_unit, or x_punite_price on
purchase.order.line - those already exist on this database as
Studio fields, and Studio's own view already renders them as
columns in the order line grid.

This module only adds:
- A transient wizard (purchase.order.import.wizard) that reads an
  uploaded .xlsx and creates purchase.order.line records.
- An "Import from Excel" button in the RFQ form header (draft/sent only).

Expected Excel columns (row 1 headers, exact text):
    Product | Quantity | Qty Per Punit | Purchase Unit | Unit Price | Punit Price

- Product is matched by EXACT product name.
- Purchase Unit must be exactly "Liter" or "KG".
- Import clears any existing lines on the RFQ and replaces them with the
  Excel content (intended for use on a freshly created, empty RFQ).
""",
    'category': 'Purchases',
    'depends': ['purchase'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/purchase_order_import_wizard_views.xml',
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
