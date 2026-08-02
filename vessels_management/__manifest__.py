# -*- coding: utf-8 -*-
{
    'name': "vessels_management",

    'summary': "Create and manage vessels",

    'description': """
vessels_management module allows users to create and manage vessels, including details such as name, type, capacity, and status. and link them to the projects.
    """,

    'author': "Youssef Hussien",
    'website': "",
    'images': ['static/description/img.png'],
    'category': 'Managment',
    'version': '18.0',
    'depends': ['base','project','mail','contacts','sale_management','sale_project','crm'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/res.partner.xml',
        'views/sale.order.xml',
        'views/project.project.xml',
        'views/project.task.xml',
        'views/crm_lead.xml',
    ],
    'installable': True,
    'application': True,
}

