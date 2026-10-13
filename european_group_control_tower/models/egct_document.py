from odoo import fields, models

DOC_TYPES = [(t, t) for t in (
    'Proforma Invoice', 'Commercial Invoice', 'Packing List', 'Bill of Lading', 'Certificate of Origin',
    'Certificate of Analysis', 'Insurance', 'ACID', 'Customs', 'Other',
)]
DOC_STATUSES = [(s, s) for s in ('Missing', 'Pending', 'Received', 'Expired')]


class EgctDocument(models.Model):
    _name = 'egct.document'
    _description = 'Control Tower Document'
    _rec_name = 'po_id'
    _order = 'po_id, id'

    po_id = fields.Many2one('egct.po', string='Purchase Order', required=True, ondelete='cascade', index=True)
    type = fields.Selection(DOC_TYPES, string='Document Type', required=True, default='Commercial Invoice')
    status = fields.Selection(DOC_STATUSES, required=True, default='Received')
    reference = fields.Char('Reference / Number')
    url = fields.Char('Document URL')
    expiry = fields.Date('Expiry Date')
    notes = fields.Text()
