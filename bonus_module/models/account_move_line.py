from odoo import fields, models, api

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    bonus = fields.Char(string="Bonus", compute="_compute_bonus", store=True)
    bonus_amount = fields.Float(string="Bonus Amount", compute="_compute_bonus_amount", store=True)
    
    
    @api.depends('move_id.sales_bonus', 'product_id.product_tmpl_id')
    def _compute_bonus(self):
        for rec in self:
            # Initialize the bonus field to 0
            rec.bonus = '0'

            # Get the related sales.order record from the Many2one field (sales_bonus)
            sales_order = rec.move_id.sales_bonus

            if sales_order:
                # Variable to accumulate the bonus if there are multiple matches
                total_bonus = 0

                # Iterate over the product_based_ids (One2many field linking to product.based.sales.bonus)
                for product_based_bonus in sales_order.product_based_ids:
                    # Check if the product_id in the account.move.line matches the product_id in product.based.sales.bonus
                    if rec.product_id.product_tmpl_id in product_based_bonus.product_id:
                        # If a match is found, accumulate the bonus
                        total_bonus += product_based_bonus.bonus

                # If at least one match was found, assign the total bonus
                if total_bonus > 0:
                    rec.bonus = str(total_bonus)
                else:
                    # No matching product found, the bonus remains 0
                    rec.bonus = '0'
                    
    @api.depends('bonus', 'price_subtotal')
    def _compute_bonus_amount(self):
        for rec in self:
            try:
                bonus_percentage = float(rec.bonus) / 100 if rec.bonus else 0
                rec.bonus_amount = bonus_percentage * rec.price_subtotal if rec.price_subtotal else 0
            except ValueError:
                rec.bonus_amount = 0