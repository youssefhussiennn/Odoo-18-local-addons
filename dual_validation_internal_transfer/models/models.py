# -*- coding: utf-8 -*-

from odoo import models, fields, api,_

from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError

class PickingTypeEdit(models.Model):
    _inherit='stock.picking'


    state = fields.Selection(selection_add=[('approved','approved'),('done', ),])

    validate_flag = fields.Boolean(related='picking_type_id.need_approve', string="Need Approve", store=True)
    customs_approval = fields.Boolean(string="Customs Approval", default=False)
  
        
    def button_validate(self):
        
        if self.validate_flag == True and self.customs_approval == False:
            if self.env.user == self.picking_type_id.responsible:
                self.customs_approval = True
                self.state='approved'
                return super(PickingTypeEdit, self).button_validate()
            else:
                raise UserError(_("You cann't validate wait for another user to validate."))
        else:
            # if self.env.user in self.picking_type_id.user_ids:

            return super(PickingTypeEdit, self).button_validate()
                
                