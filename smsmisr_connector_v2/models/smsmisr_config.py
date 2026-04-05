from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import json

class SmsMisrConfig(models.Model):
    _name = "smsmisr.config"
    _description = "SMSMisr Configuration"
    _rec_name = "sender"

    username = fields.Char(string="Username")
    password = fields.Char(string="Password")
    sender = fields.Char(string="Sender ID")
    api_url = fields.Char(string="API URL", default="https://smsmisr.com/api/SMS/")
    connection_success = fields.Boolean(string="Connection OK", readonly=True)

    @api.model
    def get_solo(self):
        """Always return the single config record, create if missing"""
        rec = self.search([], limit=1)
        if not rec:
            rec = self.create({})
        return rec

    @api.model
    def get_values(self):
        """Load values from ir.config_parameter into the record"""
        IrParam = self.env['ir.config_parameter'].sudo()
        res = super(SmsMisrConfig, self).get_values() if hasattr(super(SmsMisrConfig, self), 'get_values') else {}
        res.update({
            'username': IrParam.get_param('smsmisr.username', default=''),
            'password': IrParam.get_param('smsmisr.password', default=''),
            'sender':   IrParam.get_param('smsmisr.sender', default=''),
            'api_url':  IrParam.get_param('smsmisr.api_url', default='https://smsmisr.com/api/SMS/')
        })
        return res

    @api.model
    def set_values(self):
        """Save values from the record into ir.config_parameter"""
        IrParam = self.env['ir.config_parameter'].sudo()
        IrParam.set_param('smsmisr.username', self.username or '')
        IrParam.set_param('smsmisr.password', self.password or '')
        IrParam.set_param('smsmisr.sender',   self.sender or '')
        IrParam.set_param('smsmisr.api_url',  self.api_url or 'https://smsmisr.com/api/SMS/')
        if hasattr(super(SmsMisrConfig, self), 'set_values'):
            super(SmsMisrConfig, self).set_values()

    def action_test_connection(self):
        """Test the SMSMisr API with a dummy message"""
        if not (self.username and self.password and self.sender):
            raise UserError("Please fill username, password and sender first!")

        payload = {
            "environment": "2",  # Test mode
            "username": self.username,
            "password": self.password,
            "sender": self.sender,
            "mobile": "201100000000",  # Dummy number
            "language": "1",
            "message": "Test Connection"
        }

        try:
            r = requests.post(self.api_url, data=payload, timeout=10)
            if r.status_code != 200:
                self.connection_success = False
                raise UserError(f"API returned status {r.status_code}")

            # Parse response code
            try:
                data = json.loads(r.text)
                code = data.get("code")
                if code in ["1901", "1905"]:  # 1905=invalid mobile, acceptable in test
                    self.connection_success = True
                else:
                    self.connection_success = False
                    raise UserError(f"API returned error code {code}: {data.get('SMSID','')}")
            except Exception:
                self.connection_success = False
                raise UserError(f"Invalid API response: {r.text}")

        except requests.RequestException as e:
            self.connection_success = False
            raise UserError(f"Failed to connect: {str(e)}")
