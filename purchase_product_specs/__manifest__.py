# -*- coding: utf-8 -*-
{
    'name': 'Purchase Product Specifications',
    'version': '18.0.1.0.0',
    'category': 'Purchase',
    'summary': 'Add product specification fields to Purchase RFQ lines and Purchase Agreement lines',
    'description': """
        This module extends two standard Odoo models with read-only product
        specification fields that auto-fill from product.template whenever a
        product is selected on the line:

        Models extended:
          • purchase.order.line   → shown in Purchase RFQ / Purchase Order
          • purchase.requisition.line → shown in Purchase Agreements

        Fields added (all related to product.template):
          • Product Sub-category  (x_studio_many2one_field_BoGZB)
          • Suggested Additions   (x_studio_suggested_additions)
          • Composition           (composition — from product_new_fields)
          • Formulation           (x_studio_formulation)
          • Color                 (x_studio_color)
          • P_UOM                 (x_studio_p_uom — Selection: كجم / لتر)
    """,
    'author': 'Custom',
    'depends': [
        'purchase',               # purchase.order.line model
        'purchase_requisition',   # purchase.requisition.line model
        'product_new_fields',     # adds composition field to product.template
    ],
    'data': [
        'views/purchase_order_line_views.xml',
        'views/purchase_requisition_line_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
