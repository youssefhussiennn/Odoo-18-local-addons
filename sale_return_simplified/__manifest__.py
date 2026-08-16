# -*- coding: utf-8 -*-
{
    'name': 'Simplified Sales Return',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'One-form sales return: stock reversal + credit note + reconciliation',
    'depends': ['sale_management', 'account', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_return_views.xml',
        'views/sale_return_menu.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
