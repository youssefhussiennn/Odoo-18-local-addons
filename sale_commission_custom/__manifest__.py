# -*- coding: utf-8 -*-
{
    'name': "sale_commission_custom",

    'summary': """
        Sale Commission""",

    'description': """
        Sale Commission
    """,

    'author': "Roaya",
    'website': "https://www.roayadm.com",
    'category': 'Sales',
    'version': '1.0',
    'license': 'OPL-1',
    'depends': ['sale_management', 'account'],

    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/sale_commission.xml',
        'views/sale_order.xml',
        'views/account_move.xml',
        'views/invoice_report.xml',
    ],
}
