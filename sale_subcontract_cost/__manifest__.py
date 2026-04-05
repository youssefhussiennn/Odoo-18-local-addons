{
    'name': 'Sale Subcontract Cost (PO price → SO line)',
    'version': '18.0',
    'summary': 'Store purchase price from subcontract POs on the related sale order line (per-SO cost)',
    'description': 'When a purchase order is created/confirmed for a sale order (subcontract / MTO), write the PO line unit price to the related sale.order.line.purchase_cost so margins can be calculated per order.',
    'category': 'Sales',
    'author': 'Youssef Hussien',
    'website': '',
    'license': 'LGPL-3',
    'depends': ['sale_management', 'purchase'],
    'data': [
        'views/sale_order_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}