# -*- coding: utf-8 -*-
{
    'name': "Inventory Report Add Measures",

    'summary': """
        Inventory report Add Measures ( total, tax)""",


    'author': "Roaya",
    'website': "https://www.roayadm.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Stock',
    'version': '18.0',

    'license': 'OPL-1',
    # any module necessary for this one to work correctly
    'depends': ['stock_account','stock'],

    # always loaded
    'data': [
        'report/inventory_report.xml',
    ],

}