# -*- coding: utf-8 -*-

from odoo import models, fields, api,_

from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError
from datetime import date

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    new_sequence_id = fields.Many2one(
        'ir.sequence', 'Validation Sequence',
        check_company=True, copy=False)
    

class PickingTypeEdit(models.Model):
    _inherit='stock.picking'

    num_sequence = fields.Char(string='Serial Number')
    num_sequence_whom = fields.Many2one(string='serial created by whom',comodel_name='res.users')
    num_sequence_when = fields.Datetime(string='serial created when')
    
    

    
    # def write(self, values):
    #     if self.state == 'done':
    #          if self.picking_type_id.new_sequence_id:
    #             values['num_sequence'] = self.picking_type_id.new_sequence_id.number_next_actual
    #             self.picking_type_id.new_sequence_id.next_by_id()
    
    #     result = super(PickingTypeEdit, self).write(values)
    
    #     return result

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf(self, res_ids=None, data=None):
        if self.model == 'stock.picking' and res_ids:
            print('lllllllllllllllllllllllllllllllll')
            picking_reports = self.env.ref('stock.action_report_picking')
            delivery_reports = self.env.ref('inventory_print_layout.action_report_delivery_layout')
            if self == picking_reports or self == delivery_reports:
                pickings = self.env['stock.picking'].browse(res_ids)
                for rec in pickings:
                    if rec.picking_type_id.new_sequence_id and not rec.num_sequence:

                        next = rec.picking_type_id.new_sequence_id.next_by_id()
                        print('next')
                        print(next)
                        # if int(next) == 1:
                        rec.write({'num_sequence': next})
                        if not rec.num_sequence_whom:
                            rec.write({'num_sequence_whom':self.env.user.id})
                            rec.write({'num_sequence_when':date.today()})
                        # else:
                            # rec.write({'num_sequence': next})
                            # if not rec.num_sequence_whom:
                            #     rec.write({'num_sequence_whom':self.env.user.id})
                            #     rec.write({'num_sequence_when':date.today()})


        return super()._render_qweb_pdf(res_ids=res_ids, data=data)
    


           
                         