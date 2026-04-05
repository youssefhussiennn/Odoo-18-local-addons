from odoo import models, fields, api, _

class ProductProduct(models.Model):
    _inherit = "product.product"
    
    # composition = fields.Char(
    #     string="Composition" 
    # ) #add incase the server doesnt have the composition field
    
    purchase_unit = fields.Selection(
        selection=[("liter", "Liter"), ("kg", "KG")],
        string="Purchase Unit",
    )
    form = fields.Char(
        string="Form"
    )
    
class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    
    type = fields.Selection(
        selection=[("Local", "Local"), ("Global", "Global")],
        string="Type",
    )
    
    
class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"
    
    price_punit = fields.Float(
        string="Price/Unit"
    )

class RequsitionLine(models.Model):
    _inherit = "purchase.requisition.line"


    purchase_qty_punit = fields.Float(
        string="Qty/Unit",
        compute="_compute_purchase_qty_punit",
        
    )
    composition = fields.Char(
        related="product_id.composition",
        string="Composition"
    )
    form = fields.Char(
        related="product_id.form",
        string="Form"
    )
    weight = fields.Float(
        related="product_id.weight",
        string="Weight"
    )
    
    purchase_unit = fields.Char(
        related="product_id.uom_po_id.name",
        string="Purchase Unit"
    )
    qty_on_hand = fields.Float(
        related="product_id.qty_available",
        string="Qty on Hand"
    )
    qty_on_hand_punit = fields.Float(
        string="Qty on Hand/Unit",
        compute="_compute_qty_on_hand_punit",
        
    )
    
    last_purchase_price = fields.Float(
        related="product_id.last_purchase_price",
        string="Last Purchase Price"
    )
    
    last_purchase_price_punit = fields.Float(
        string="Last Purchase Price / Unit",
        compute="_compute_last_purchase_price_punit",
        
    )
    
    forcasted = fields.Float(
        related="product_id.virtual_available",
        string="Forcasted"
    )
    
    @api.depends("product_qty", "weight")
    def _compute_purchase_qty_punit(self):
        for line in self:
            line.purchase_qty_punit = (line.product_qty * line.weight) if line.weight else 0.0

    @api.depends("qty_on_hand", "weight")
    def _compute_qty_on_hand_punit(self):
        for line in self:
            line.qty_on_hand_punit = (line.qty_on_hand * line.weight) if line.weight else 0.0

    @api.depends("last_purchase_price", "weight")
    def _compute_last_purchase_price_punit(self):
        for line in self:
            line.last_purchase_price_punit = (line.last_purchase_price / line.weight) if line.weight else 0.0
