# -*- coding: utf-8 -*-

from collections import defaultdict

from odoo import models, api, _, SUPERUSER_ID
from odoo.addons import stock

# Remove action_assign after backorder creation

def _create_backorder(self):
    """ This method is called when the user chose to create a backorder. It will create a new
    picking, the backorder, and move the stock.moves that are not `done` or `cancel` into it.
    """
    backorders = self.env['stock.picking']
    bo_to_assign = self.env['stock.picking']
    for picking in self:
        moves_to_backorder = picking.move_line_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
        if moves_to_backorder:
            backorder_picking = picking.copy({
                'name': '/',
                'move_lines': [],
                'move_line_ids': [],
                'backorder_id': picking.id
            })
            picking.message_post(
                body=_('The backorder <a href=# data-oe-model=stock.picking data-oe-id=%d>%s</a> has been created.') % (
                    backorder_picking.id, backorder_picking.name))
            moves_to_backorder.write({'picking_id': backorder_picking.id})
            moves_to_backorder.move_line_ids.package_level_id.write({'picking_id':backorder_picking.id})
            moves_to_backorder.mapped('move_line_ids').write({'picking_id': backorder_picking.id})
            backorders |= backorder_picking
            if backorder_picking.picking_type_id.reservation_method == 'at_confirm':
                bo_to_assign |= backorder_picking
    if bo_to_assign:
        bo_to_assign.action_assign()
    #Unreserve qty from backorders 
    elif backorders:
        backorders.do_unreserve()
        backorders.move_lines.write({
            'state':'draft'
        })

    return backorders



stock.models.stock_picking.Picking._create_backorder = _create_backorder

