# -*- coding: utf-8 -*-
# Copyright (c) Abdulrahman Rabie, AlArabia Group All Rights Reserved
from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError


class MrpBom(models.Model):
    _inherit = 'mrp.production'
    def _onchange_product_id(self):
        pass
        # for move in self.move_raw_ids:
        #     if self.product_id == move.product_id:
        #         message = _("The component %s should not be the same as the product to produce.", self.product_id.display_name)
        #         self.move_raw_ids = self.move_raw_ids - move
        #         return {'warning': {'title': _('Warning'), 'message': message}}
        
    def _check_production_lines(self):
        pass
        
class MrpBom(models.Model):
    _inherit = 'mrp.bom'
    
    def _check_bom_lines(self):
        for bom in self:
            for bom_line in bom.bom_line_ids:
                if bom.product_id:
                    same_product = bom.product_id == bom_line.product_id
                else:
                    same_product = bom.product_tmpl_id == bom_line.product_id.product_tmpl_id
                # if same_product:
                #     raise ValidationError(_("BoM line product %s should not be the same as BoM product.") % bom.display_name)
            apply_variants = bom.bom_line_ids.bom_product_template_attribute_value_ids | bom.operation_ids.bom_product_template_attribute_value_ids | bom.byproduct_ids.bom_product_template_attribute_value_ids
            if bom.product_id and apply_variants:
                raise ValidationError(_("You cannot use the 'Apply on Variant' functionality and simultaneously create a BoM for a specific variant."))
            for ptav in apply_variants:
                if ptav.product_tmpl_id != bom.product_tmpl_id:
                    raise ValidationError(_(
                        "The attribute value %(attribute)s set on product %(product)s does not match the BoM product %(bom_product)s.",
                        attribute=ptav.display_name,
                        product=ptav.product_tmpl_id.display_name,
                        bom_product=bom_line.parent_product_tmpl_id.display_name
                    ))
            for byproduct in bom.byproduct_ids:
                if bom.product_id:
                    same_product = bom.product_id == byproduct.product_id
                else:
                    same_product = bom.product_tmpl_id == byproduct.product_id.product_tmpl_id
                if same_product:
                    raise ValidationError(_("By-product %s should not be the same as BoM product.") % bom.display_name)
                if byproduct.cost_share < 0:
                    raise ValidationError(_("By-products cost shares must be positive."))
            if sum(bom.byproduct_ids.mapped('cost_share')) > 100:
                raise ValidationError(_("The total cost share for a BoM's by-products cannot exceed 100."))
