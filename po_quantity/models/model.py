from odoo import _,api,models,fields
from odoo.exceptions import UserError, ValidationError

class POQuantity(models.Model):
    _inherit='purchase.order.line'

    @api.constrains('product_qty')
    def _check_quantity(self):
        
        for rec in self:
            if rec.product_qty < 0 :
                raise ValidationError(_("The Quantity Can't be Less Than ZERO!"))
