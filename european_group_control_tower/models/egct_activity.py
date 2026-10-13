from odoo import fields, models


class EgctActivity(models.Model):
    _name = 'egct.activity'
    _description = 'Control Tower Activity Log'
    _order = 'id desc'

    text = fields.Char(required=True)
    kind = fields.Char(default='update', index=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, ondelete='set null')
