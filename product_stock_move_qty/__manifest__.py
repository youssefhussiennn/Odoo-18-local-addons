{
    'name': 'Product Stock Move Qty',
    'version': '18.0',
    'author': 'Roaya',
    'license': 'AGPL-3',
    'website': 'http://www.roayadm.com',
    'category': 'Stock Management',
    'summary': 'Show Product Stock Moves Qty for Location/Warehouse',
    'depends': ['stock','base','sale'],
    'data': [
        'views/stock_move_location.xml',
        'views/product_template.xml',
        'views/product_product.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
}