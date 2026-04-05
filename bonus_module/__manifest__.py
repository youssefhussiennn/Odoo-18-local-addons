# -*- coding: utf-8 -*-
{
    'name': "Bonus",

    'summary': """To Create Sales bonus for partners""",

    'description': """Allows to create sales bonus based on Product""",

    'author': "Youssef",
    'website': "",

    'category': 'Uncategorized',
    'version': '18.0',

    # any module necessary for this one to work correctly
    'depends': ['sale_management', 'account', 'report_xlsx'],

    # always loaded
    'data': [

        'security/ir.model.access.csv',
        'report/sales_bonus_reports.xml',
        'report/sales_bonus_templates.xml', 
        'wizard/sales_bonus_report_views.xml',
        'views/sales_bonus_views.xml',
        'views/sales_bonus_menus.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}

