# -*- coding: utf-8 -*-
{
    'name': "SO Smart Buttons",

    'summary': "Adds smart buttons to sale order form view",

    'description': """
        Adds smart buttons to sale order form view
""",

    'author': "Odoo Developers",
    'website': "",

    'category': 'Operations/sales',
    'version': '18.0',

    'application': False,
    'installable': True,
    'auto_install': False,

    'depends': ['base','mail','sale'],

    'data': [

        'views/sales_order_view.xml',

    ],
}
