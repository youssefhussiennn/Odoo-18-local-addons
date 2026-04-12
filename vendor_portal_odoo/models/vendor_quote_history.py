# -*- coding: utf-8 -*-

from odoo import fields, models


class VendorQuoteHistory(models.Model):
    """Vendor Quotation History"""
    _name = 'vendor.quote.history'
    _description = "Vendor Quotation History"
    _rec_name = 'vendor_id'

    vendor_id = fields.Many2one('res.partner',
                                domain="[('is_registered', '=', True)]",
                                string="Vendor",
                                help="Select Vendor")
    quoted_price = fields.Monetary(currency_field='currency_id',
                                   help="Quoted Price")
    discount = fields.Float(help="Discount")
    
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  help="Currency",
                                  required=True,
                                  default=lambda
                                      self: self.env.user.company_id.currency_id)
    estimate_date = fields.Date(string="Estimate date", help="Estimated Date")
    note = fields.Text(string="Note", help="Additional Note")
    order_id = fields.Many2one('purchase.order', help="Quote ID")
