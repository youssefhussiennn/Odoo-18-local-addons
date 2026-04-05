
from ast import Break
from odoo import fields, models, api, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    price_unit = fields.Float(string='Unit Price', digits=(16,6))
    discount = fields.Float(string='Discount (%)', digits=(16,6), default=0.0)
    price_subtotal = fields.Monetary(string='Subtotal', store=True, readonly=True,
        currency_field='currency_id', digits=(16,6))
    price_total = fields.Monetary(string='Total', store=True, readonly=True,
        currency_field='currency_id', digits=(16,6))
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.depends('order_line.price_total')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                line._compute_amount()
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            currency = order.currency_id or order.partner_id.property_purchase_currency_id or self.env.company.currency_id
            order.update({
                'amount_untaxed': currency.round(amount_untaxed),
                'amount_tax': currency.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })

    amount_untaxed = fields.Monetary(string='Untaxed Amount', digits=(16,6), store=True, readonly=True, compute='_amount_all', tracking=True)
    amount_tax = fields.Monetary(string='Taxes', digits=(16,6), store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', digits=(16,6), store=True, readonly=True, compute='_amount_all')

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    cost = fields.Float(related='product_id.standard_price', digits=(16,6))

    price = fields.Float(string="Price", digits=(16,6))

    percentage_discount_1 = fields.Float(string="Discount", digits=(16,6))
    price_unit = fields.Float(string='Unit Price', required=True, digits=(16,6))
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', store=True, digits=(16,6))
    price_total = fields.Monetary(compute='_compute_amount', string='Total', store=True, digits=(16,6))
    price_tax = fields.Float(compute='_compute_amount', string='Tax', store=True, digits=(16,6))
    

    # percentage_discount_2 = fields.Float(string="Percentage Discount 2")

    # @api.onchange('price_unit')
    # def auto_price(self):
    #     if self.price_unit and not self.price:
    #         self.price = self.product_id.lst_price

    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        for line in self:
            taxes = line.taxes_id.compute_all(
                price_unit=line.price_unit,
                currency=line.currency_id,
                quantity=line.product_qty,
                product=line.product_id,
                partner=line.order_id.partner_id,
                is_refund=False,  # set True if you're doing refunds
            )
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })



    @api.onchange('price', 'percentage_discount_1', 'price_unit')
    def auto_discount(self):
        # discount = 0
        # self.price_unit = self.price
        # if self.price and self.percentage_discount_1:
        #     self.price_unit = self.price - (self.price * (self.percentage_discount_1 / 100))
        # if self.price and self.price_unit and not self.percentage_discount_1:
        #     self.percentage_discount_1 = (1-(self.price_unit / self.price)) * 100
        # if self.percentage_discount_1 and self.price_unit and not self.price:
        #     self.price = (self.price_unit/(100-self.percentage_discount_1))*100
        # if self.price:
        #     self.price_unit = self.price
        # if self.price_unit:
        #     self.price = self.price_unit
        # if self.percentage_discount_1:
        #     self.price_unit = self.price - (self.price * (self.percentage_discount_1 / 100))

        

        if self.percentage_discount_1 and self.percentage_discount_1 != 0.0 and self.price != 0.0:
            self.price_unit = self.price - (self.price * (self.percentage_discount_1 / 100))
            return

        if self.price and self.price_unit and not self.percentage_discount_1:
            self.percentage_discount_1 = (1-(self.price_unit / self.price)) * 100
            return

        if self.percentage_discount_1 and self.price_unit and not self.price:
            self.price = (self.price_unit/(100-self.percentage_discount_1))*100
            return
        elif self.price and self.price != 0.0:
            self.price_unit = self.price
            return
        
        

       




    # @api.onchange('price', 'percentage_discount_2', 'percentage_discount_3')
    # def discount_levels(self):
    #
    #     if self.percentage_discount_2:
    #         self.price_unit =  (self.price_unit * (self.percentage_discount_2 / 100))
    #     if self.percentage_discount_3:
    #         self.price_unit =  (self.price_unit * (self.percentage_discount_3 / 100))


#Discount for tender in tender_vendor