from odoo import fields, models

STAGES = [
    ('PO Issued', 'PO Issued'),
    ('Booked', 'Booked'),
    ('At Sea', 'At Sea'),
    ('Arrived Port', 'Arrived Port'),
    ('Customs Cleared', 'Customs Cleared'),
    ('In Inventory', 'In Inventory'),
]
CUSTOMS = [
    ('Not Started', 'Not Started'),
    ('In Progress', 'In Progress'),
    ('Held', 'Held'),
    ('Cleared', 'Cleared'),
]


class EgctShipment(models.Model):
    _name = 'egct.shipment'
    _description = 'Control Tower Shipment'
    _rec_name = 'po_id'
    _order = 'id'
    _sql_constraints = [('po_uniq', 'unique(po_id)', 'A purchase order can only have one shipment.')]

    po_id = fields.Many2one('egct.po', string='Purchase Order', required=True, ondelete='cascade', index=True)
    stage = fields.Selection(STAGES, required=True, default='PO Issued', index=True)
    bl = fields.Char('BL Number')
    booking = fields.Char('Booking No.')
    container = fields.Char()
    tracking_number = fields.Char('Tracking Number')
    tracking_url = fields.Char('Tracking URL')
    carrier = fields.Char('Carrier / Shipping Line')
    vessel = fields.Char()
    voyage = fields.Char()
    etd = fields.Date('ETD')
    eta = fields.Date('ETA')
    actual_arrival = fields.Date('Actual Arrival')
    location = fields.Char('Current Location')
    destination = fields.Char('Destination Port')
    registration = fields.Char()
    customs = fields.Selection(CUSTOMS, required=True, default='Not Started')
    acid = fields.Char('ACID Number')
    notes = fields.Text()
