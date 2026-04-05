# -*- coding: utf-8 -*-
{
    'name': "Vendor Development",

    'summary': "Manage vendor details, contacts, and meeting points easily",

    'description': """
        Full-featured vendor management app.
        - Store vendor company info
        - Track multiple contact persons
        - Plan and organize meeting points
        """,

    'author': "Youssef Hussien",

    'category': 'Operations/Vendor Management',
    'version': '18.0',
    'images': ['static/description/dev_vendor.png'],
    'application': True,
    'installable': True,
    'auto_install': False,

    'depends': ['base','mail'],

    'data': [
        'security/ir.model.access.csv',  
        'views/develop_vendor_views.xml',
        'views/vendor_tag_views.xml'
    ],
    
}
