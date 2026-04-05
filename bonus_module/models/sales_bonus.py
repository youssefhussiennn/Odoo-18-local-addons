
from odoo import fields, models, api
from odoo.exceptions import ValidationError

class SalesBonus(models.Model):
    """Creating sales Bonus model."""
    _name = "sales.bonus"
    _description = "Sales Bonus"

    name = fields.Char(string="Bonus Name", help="Name of the Bonus")
    partner_id = fields.Many2many('res.partner', string='Partner',
                                        help="Partner")
    bonus_type = fields.Selection(
        string="Bonus Type",
        selection=[('product_based', 'Product Based'),], help="Type of Bonus")
    
    std_bonus_perc = fields.Float(string='Standard Bonus Percentage',
                                       help="Standard Bonus type")
    product_based_ids = fields.One2many(
        "product.based.sales.bonus", 'sale_bonus_id',
        string='Sales Bonus Exceptions',
        help="Product based sales Bonus", copy=True)
    date = fields.Date(string="Date", help="Date")
    description = fields.Char(string="Description", help="Description")
    bonus_amount = fields.Float(string="Bonus Amount",
                                     help="Bonus amount")
    sale_order_id = fields.Many2one('sale.order', help="Sale order",
                                    string='Sale Order')
    date_start = fields.Date(string="Start Date")
    date_end = fields.Date(string="End Date")
    

class ProductBasedSalesBonus(models.Model):
    """Creating product based sales Bonus model."""
    _name = "product.based.sales.bonus"
    _description = " Product Based Sales Bonus"

    sale_bonus_id = fields.Many2one("sales.bonus",
                                         help="Sales Bonus",
                                         string='Sale Bonus')
    product_id = fields.Many2many('product.template', string='Product',
                                 help="Product", copy=True)
    # product_category_id = fields.Many2one(
    #     related='product_id.categ_id', 
    #     string='Product Category', 
    #     store=True, 
    #     help="Category of the Product")
    
    bonus = fields.Float(string='Bonus %', help="Bonus %", copy=True)