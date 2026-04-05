# -*- coding: utf-8 -*-
{
    'name': "close_create_and_edit_of_partner_in_each_app",

    'summary': """
        close create and edit of partner in each app sale, purchase, etc""",

    'description': """
        close create and edit of partner in each app sale, purchase, etc
    """,

    'author': "Roaya",
    'website': "https://www.roayadm.com",
    'category': 'Extra Tools',
    'license': 'OPL-1',
    'version': '18.0',
    'depends': ['sale', 'purchase', 'stock', 'account'],

    'data': [
        'views/sale_order.xml',
        'views/purchase_order.xml',
        'views/inventory.xml',
        'views/payment.xml',
        'views/account_move.xml',
    ],
}
