# -*- coding: utf-8 -*-
{
    'name': "Hide Cost",

    'summary': """
        Hide Cost""",

    'author': "Roaya",
    'website': "http://www.roayadm.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Extra Tools',
    'version': '18.0',

    # any module necessary for this one to work correctly
    'depends': ['product','stock','stock_account','sale','sale_margin','product_margin'],

    # always loaded
    'data': [
        'security/security.xml',
        'views/views.xml',
        #'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo/demo.xml',
    ],
}
