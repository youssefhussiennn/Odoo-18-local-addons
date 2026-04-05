import logging

from odoo import models, fields, api
from odoo import tools

_logger = logging.getLogger(__name__)

class StockMoveLocation(models.Model):

        _name = "stock.move.location"
        _description = "Location Moves"
        _auto = False
        _order = "date asc"

        id = fields.Char(
                string='id',
                size=16,
                readonly=True
        )
        description = fields.Char(
                string='Description',
                readonly=True
        )
        location_id = fields.Many2one(
                comodel_name='stock.location',
                string='Location',
                readonly=True
        )
        location_name_to = fields.Char(
                string='Location To',
                readonly=True
        )
        location_name_from = fields.Char(
                string='Location From',
                readonly=True
        )
        product_id = fields.Many2one(
                comodel_name='product.product',
                string='Product',
                readonly=True
        )
        product_tmpl_id = fields.Many2one(
                related='product_id.product_tmpl_id',
                comodel_name='product.template',
                string='Product Template'
        )
        categ_id = fields.Many2one(
                comodel_name="product.category",
                string='Category',
                readonly=True
        )
        product_uom_id = fields.Many2one(
                'uom.uom',
                string='Product Unit of Measure',
                required=True,
        )

        uom_id = fields.Many2one(
                related='product_id.uom_id',
                comodel_name="uom.uom",
                string="UoM",
                readonly = True
        )
        date = fields.Datetime(
                string='Date Planned',
                readonly=True
        )
        picking_id = fields.Many2one(
                comodel_name='stock.picking',
                string='Packing',
                readonly=True
        )
        company_id = fields.Many2one(
                comodel_name='res.company',
                string='Company',
                readonly=True
        )
        warehouse_id = fields.Many2one(
                comodel_name='stock.warehouse',
                string='Warehouse',
                readonly=True
        )
        qty_on_hand = fields.Float(
                string='Quantity On Hand',
                digits=(16,4),
                readonly=True
        )
        qty_add = fields.Float(
                string='In',
                digits=(16,4),
                readonly=True,
                compute='_compute_field_qty'
        )
        qty_ded = fields.Float(
                string='Out',
                digits=(16,4),
                readonly=True,
                compute='_compute_field_qty'
        )
        qty_current = fields.Float(
                string='Balance',
                digits=(16,4),
                readonly=True,
                compute='_compute_field'
        )
        move_type = fields.Char(
                string='Move Type',
                readonly=True
        )
        partner_id = fields.Many2one(
                comodel_name='res.partner',
                string='Vendor/Customer',
                readonly=True
        )

        @api.depends('qty_on_hand')
        def _compute_field(self):
                locations=[]
                products=[]
                
                stockobj = self.env['stock.move.location']

                for record in self:
                        if record.location_id in locations and record.product_id in products:
                                stockobjsearch = stockobj.search([('location_id.id', '=', record.location_id.id),('product_id.id', '=', record.product_id.id),('date', '<', record.date)])
                                lastqty = record.qty_on_hand
                                for stockobjsearchline in stockobjsearch: lastqty += stockobjsearchline.qty_on_hand
                                record.qty_current = lastqty
                        else:
                                locations.append(record.location_id)
                                products.append(record.product_id)
                                record.qty_current = record.qty_on_hand

        @api.depends('qty_on_hand')
        def _compute_field_qty(self):
                for record in self:
                        record.qty_ded = 0
                        record.qty_add = 0
                        if record.qty_on_hand > 0:
                                record.qty_add = record.qty_on_hand
                        elif record.qty_on_hand < 0:
                                record.qty_ded = abs(record.qty_on_hand)
                                
        def _view_internal_add(self):
                
                view_str = """
                select sml.id ,
                sl.id as location_id, sml.product_id, sml.product_uom_id, sm.warehouse_id,vendor.id as partner_id,
                sml.reference as description,
                case when sml.state ='done' 
                        then 
                                case when uom.uom_type = 'reference' then round(sm.product_qty, 4) 
                                        when uom.uom_type = 'bigger' then round(sm.product_qty*(1/uom.factor), 4)
                                        when uom.uom_type = 'smaller' then round(sm.product_qty*uom.factor, 4)
                                        else 0
                                end
                        else 0 end as qty_on_hand,
                sml.date,
                sml.picking_id,sl.company_id,
                sll.complete_name as location_name_from ,
                sl.complete_name as location_name_to,
                pr.categ_id as categ_id,
                /*to_char(sm.location_id ,'999')  as location_name_from,*/

                spt.code as move_type
                from
                stock_move_line sml
				
	        INNER join stock_move sm ON sm.id = sml.move_id
                
                left join stock_location sll ON sml.location_id=sll.id
                left join stock_location sl ON
                        sml.location_dest_id = sl.id
                left join stock_picking sp ON
                        sp.id = sml.picking_id
                left join res_partner vendor ON sp.partner_id = vendor.id
                left join stock_picking_type spt ON
                        sp.picking_type_id = spt.id
	        left join product_product pp on 
                        sml.product_id = pp.id
                left join product_template pr ON
		        pp.product_tmpl_id = pr.id
		left join uom_uom uom ON
		        sml.product_uom_id = uom.id
			
                where sl.usage='internal'
                and sml.state != 'cancel'
                and sml.company_id = sl.company_id
                and sm.product_qty != 0
                and sml.state ='done'
                
                """
                return view_str

        def _view_internal_deduct(self):
                view_str = """
                
                select -sml.id ,
                sl.id as location_id ,sml.product_id, sml.product_uom_id, sm.warehouse_id,vendor.id as partner_id,
                sml.reference as description,
                case when sml.state ='done' 
                        then 
                                case when uom.uom_type = 'reference' then round(-sm.product_qty, 4) 
                                        when uom.uom_type = 'bigger' then round(-sm.product_qty*(1/uom.factor), 4)
                                        when uom.uom_type = 'smaller' then round(-sm.product_qty*uom.factor, 4)
                                        else 0
                                end
                        else 0 end as qty_on_hand,
                sml.date,
                sml.picking_id,sl.company_id,
                
                /*to_char(sm.location_dest_id,'999') as location_name_to,*/
                sl.complete_name as location_name_from,
				sll.complete_name as location_name_to,
                pr.categ_id as categ_id,
                spt.code as move_type
                from
                stock_move_line sml
		inner join stock_move sm ON sm.id = sml.move_id
        
                left join stock_location sll ON sml.location_dest_id=sll.id
                left join stock_location sl ON
                        sml.location_id = sl.id
                left join stock_picking sp ON
                        sp.id = sml.picking_id
                left join res_partner vendor ON  sp.partner_id = vendor.id
                left join stock_picking_type spt ON
                        sp.picking_type_id = spt.id
		left join product_product pp on 
                        sml.product_id = pp.id
                left join product_template pr ON
		        pp.product_tmpl_id = pr.id
		left join uom_uom uom ON
		        sml.product_uom_id = uom.id
			
                where sl.usage='internal'
                and sml.state != 'cancel'
                and sml.company_id = sl.company_id
                and sm.product_qty != 0
                and sml.state ='done' 
                """
                # and sl.company_id = %s

                return view_str

        def init(self):
                tools.drop_view_if_exists(self.env.cr, self._table)
                sql ="""CREATE or REPLACE VIEW %s as (
                %s
                union all
                %s
                )""" % (self._table,
                        self._view_internal_add(),
                        self._view_internal_deduct()
                        )
                self.env.cr.execute(sql)

        @api.model
        def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
                
                res = super(StockMoveLocation, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

                for line in res:
                        if '__domain' in line:
                                lines = self.search(line['__domain'])
                                total_qty = sum(lines.mapped('qty_add')) - sum(lines.mapped('qty_ded'))
                                total_qty_add = sum(lines.mapped('qty_add'))
                                total_qty_ded = sum(lines.mapped('qty_ded'))
                                line['qty_current'] = total_qty
                                line['qty_add'] = total_qty_add
                                line['qty_ded'] = total_qty_ded
                
                return res
        
