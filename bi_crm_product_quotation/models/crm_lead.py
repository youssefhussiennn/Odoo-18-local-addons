# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class crm_lead(models.Model):
    _inherit = 'crm.lead'

    lead_product_ids = fields.One2many(
        'lead.line', 'lead_line_id', string='Products', copy=True)
    crm_count = fields.Integer(
        string="Quotation", compute="get_quotation_count")
    is_crm_quotation = fields.Boolean('Is CRM Quotation')
    sales_count = fields.Integer(
        string="Sales Count")
    description = fields.Html(
        string='Internal Notes',
        default="""<p><strong>1. Scope of Work</strong></p>
    <p>2. Documents Required from Client<br/>1-<br/>2-<br/>3-<br/>4-</p>
    <p>3. Deliverables</p>
    <p>4. Estimated Completion Time<br/>1-<br/>2-<br/>3-<br/>• Delivery time: ( ) working days from receiving clients’ confirmation.</p>
    <p>5. Costs and Payment Terms</p>
    <p>Total Cost & Payment Schedule:<br/>
    We ensure competitive pricing while maintaining high service standards<br/>
    <strong>Total Cost: $</strong></p>
    <p>6. Terms & Conditions</p>
    <ul>
    <li>The quoted price is valid for 30 days from the date of this offer.</li>
    <li>Any additional work beyond the agreed scope will be subject to a separate quotation.</li>
    <li>The final plans are based on the accuracy of provided and collected vessel data.</li>
    <li>All deliverables will comply with relevant maritime regulations.</li>
    <li>Any regulatory approvals or classifications are the responsibility of the vessel owner/operator.</li>
    </ul>
    <p>Best Regards;</p>"""
    )
    def action_quotations_view(self):
        order_line = []
        for record in self.lead_product_ids:
            order_line.append((0, 0, {
                'product_id': record.product_id.id,
                'name': record.name,
                # 'product_uom_qty': record.product_uom_quantity,
                # 'price_unit': record.price_unit,
                # 'tax_id': [(6, 0, record.tax_id.ids)],
            }))
        if self.partner_id:
            self.write({'sales_count': 1}) 
            for record in self.lead_product_ids:
                if record.product_id and record.name:
                    sale_create_obj = self.env['sale.order'].create({
                        'partner_id': self.partner_id.id,
                        'person_in_charge': self.user_id.id,
                        'opportunity_id': self.id,
                        'state': "draft",
                        'order_line': order_line,
                        'note': self.description,
                        'vessel_id': self.vessel_id.id if self.vessel_id else False,
                        
                    })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Quotation Created'),
                        'message': _('Quotation %s has been successfully created.') % sale_create_obj.name,
                        'sticky': False,
                        'type': 'success',
                    },
                }
            else:
                raise UserError('Enter the "Product" and "Description".')
        else:
            raise UserError('Please select the "Customer".')

    def open_quotation_from_view_action(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "sale.action_quotations_with_onboarding")
        action['domain'] = [
            ('partner_id', '=', self.partner_id.id), ('opportunity_id', '=', self.id)]
        return action

    def get_quotation_count(self):
        count = self.env['sale.order'].search_count(
            [('partner_id', '=', self.partner_id.id), ('opportunity_id', '=', self.id)])
        self.crm_count = count
