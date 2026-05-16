# -*- coding: utf-8 -*-
{
    'name': "seeds",

    'summary': "Managing seeds and their properties",

    'description': """
This module allows you to manage seeds, including their properties such as type, germination time, and planting instructions. It provides a user-friendly interface to add, edit, and view seed information, making it easier for gardeners and farmers to keep track of their seed inventory and plan their planting schedules effectively.
    """,

    'author': "Youssef Hussien",
    'website': "youssefhussiennn@gmail.com",
    'category': 'Management',
    'version': '18.0.0.1',
    'depends': ['base', 'mail'],

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
}

