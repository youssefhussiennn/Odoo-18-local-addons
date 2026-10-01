# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models, tools
from .location_stock_sql import VARIANT_LOCATION_SQL


class ProductPivotReport(models.Model):
    """ Model for generating pivot view for product variants based on product
     locations"""
    _name = 'stock.location.product.variant'
    _description = "Product Variant Location Report"
    _auto = False

    product_id = fields.Many2one('product.product', string="Product",
                                 help='Name of the product')
    location_id = fields.Many2one('stock.location', string='Location',
                                  help='Choose the location')
    on_hand_qty = fields.Float(string='On Hand Quantity',
                                 help='On hand quantity of the product')
    qty_incoming = fields.Float(string='Incoming Quantity',
                                  help='Incoming quantity of the product')
    qty_outgoing = fields.Float(string='Outgoing Quantity',
                                  help='Outgoing quantity of the product')
    forecast_qty = fields.Float(string='Forecast Quantity',
                                  help='Forecasted quantity of the product')

    def init(self):
        """Initialize the view. Drops the existing view if it exists and
        creates a new view with the following columns for the Product variant
        model"""
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""CREATE OR REPLACE VIEW %s AS (
        SELECT row_number() OVER () AS id, base.*
          FROM (%s) base)""" % (self._table, VARIANT_LOCATION_SQL))
