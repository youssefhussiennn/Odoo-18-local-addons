# -*- coding: utf-8 -*-

from odoo import _, api, fields, models

class ProductTemplate(models.Model):
    _inherit = "product.template"

    def stock_move_location_action_product_tmpl(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("product_stock_move_qty.stock_move_location_action_product_tmpl_moves")
        action['domain'] = [('product_id.product_tmpl_id', 'in', self.ids)]
        return action

class ProductProduct(models.Model):
    _inherit = "product.product"

    def stock_move_location_action_product_tmpl(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("product_stock_move_qty.stock_move_location_action_product_tmpl_moves")
        action['domain'] = [('product_id.id', 'in', self.ids)]
        return action