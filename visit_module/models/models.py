from odoo import models, fields

class Visit(models.Model):
    _name = 'visit'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'Visit'

    contact_name = fields.Many2many('res.partner', string='Partners' , tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency')
    date = fields.Date(string='Date' , tracking=True)
    description = fields.Text(string='Description' )
    finished_time = fields.Datetime(string='Finished Time' , tracking=True)
    kind = fields.Char(string='تنشيط.متابعة')
    user_id = fields.Many2one('res.users', string='Users' , tracking=True)
    memo = fields.Char(string='Internal Note' , tracking=True)
    new_customer = fields.Char(string='New Customer' , tracking=True)
    partner_email = fields.Char(string='Email')
    partner_id = fields.Many2one('res.partner', string='Contact' , tracking=True)
    partner_phone = fields.Char(string='Phone' , tracking=True)
    product_ids = fields.Many2many('product.template', string='Product' , tracking=True)
    quotation_ids = fields.Many2many('sale.order', string='Qutation' , tracking=True)
    request = fields.Char(string='طلب')
    start_time = fields.Datetime(string='Start Time', tracking=True)
    responsible_id = fields.Many2one('res.users', string='Responsible',readonly=True, default=lambda self: self.env.user)
    value = fields.Float(string='Value', tracking=True)
