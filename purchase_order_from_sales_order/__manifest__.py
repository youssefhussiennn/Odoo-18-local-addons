# -*- coding: utf-8 -*-
###################################################################################
#
#    Abblez Technologies and Robotics LLP.
#
#    Copyright (C) 2023-TODAY Abblez Technologies and Robotics  (<https://www.abbleztechnologies.com>).
#    Author: Abblez Technologies and Robotics LLP
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
###################################################################################

{
    'name': 'Purchase Order from Sales order lines',
    'version': '1.0',
    'summary': 'Create purchase order from  Sale order lines based on Vendor selection',
    'author': 'Abblez Technologies and Robotics',
    'description': """Create purchase order from  Sale order lines based on Vendor selection""",
    'category':'sales',
    'company': 'Abblez Technologies and Robotics LLP',
    'maintainer': 'Abblez Technologies and Robotics LLP',
    'website': "https://www.abbleztechnologies.com",
    'version': '18.0',
    'depends': ['base', 'product', 'sale_management', 'purchase'],
    'assets': {
        'web.assets_frontend': [

        ],
    },
    'data': [
        'views/sale_order_inherit_views.xml'
    ],
    'licenSe': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
    'images': ['static/description/banner.png'],
    }
