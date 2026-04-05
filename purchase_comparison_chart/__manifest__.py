# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Purchase Comparison Chart',
    'version': '18.0',
    'category': 'Purchase',
    'author': 'PPTS [India] Pvt.Ltd.',
    'description': """
    Purchase Comparison Chart
    """,
    'license': 'LGPL-3',
    'summary': 'Purchase Comparison Chart',
    'depends': ['purchase', 'purchase_requisition', 'purchase_last_price_info'],
    'website': 'https://www.pptssolutions.com',
    'data': [
        # 'security/base_groups.xml',
        'security/ir.model.access.csv',
        'views/inherit_purchase_requisition_view.xml',
        # 'views/bid_templates.xml',
        'views/inherit_purchase_requisition_view.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 105,
    'qweb': [
        'static/src/xml/assets.xml',
    ],
    'installable': True,
    'auto_install': False,
}
