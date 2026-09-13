from odoo import models, fields, api


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    document_ids = fields.One2many(
        'fleet.vehicle.document', 'vehicle_id', string='Documents'
    )
    document_count = fields.Integer(
        string='Documents', compute='_compute_document_count'
    )

    @api.depends('document_ids')
    def _compute_document_count(self):
        for rec in self:
            rec.document_count = len(rec.document_ids)

    def action_open_vehicle_documents(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Documents',
            'res_model': 'fleet.vehicle.document',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }
