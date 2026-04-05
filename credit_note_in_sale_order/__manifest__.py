# -*- coding: utf-8 -*-
{
    'name': "credit_note_in_sale_order",

    'summary': """
        create credit note when product invoicing policy (delivery) and sale order line less than 0
    """,

    'description': """
        create credit note when product invoicing policy (delivery) and sale order line less than 0
    """,

    'author': "Roaya",
    'website': "https://www.roayadm.com",
    'category': 'Sale',
    'license': 'OPL-1',
    'version': '18.0',

    'depends': ['sale_stock', 'sale', 'stock'],

    'data': [
        'views/views.xml',
    ],
}
