from odoo import models, fields, api

class SmsMisrMessage(models.Model):
    _name = "smsmisr.message"
    _description = "SMS Messages"

    name = fields.Char("Subject")
    mobile = fields.Char("Mobile Number", required=True)
    message = fields.Text("Message Body", required=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ], default='draft', index=True)
    external_id = fields.Char("External ID")
    response = fields.Text("Last Response")

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = (vals.get('message') or '')[:40]
        return super(SmsMisrMessage, self).create(vals)

    def action_queue(self):
        for rec in self:
            rec.status = 'queued'

    def action_send_now(self):
        svc = self.env['smsmisr.service']
        for rec in self:
            res = svc.send_sms(rec.mobile, rec.message)
            if res.get('success'):
                rec.status = 'sent'
                rec.external_id = res.get('message_id') or res.get('external_id') or False
                rec.response = str(res.get('response_text'))
            else:
                rec.status = 'failed'
                rec.response = str(res.get('error') or res.get('response_text'))
