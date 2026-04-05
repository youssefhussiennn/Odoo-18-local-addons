import logging
import requests
from odoo import models
from odoo.exceptions import UserError
import json

_logger = logging.getLogger(__name__)

SMSMISR_CODES = {
    "1901": "Success",
    "1902": "Invalid Request",
    "1903": "Invalid username/password",
    "1904": "Invalid sender",
    "1905": "Invalid mobile",
    "1906": "Insufficient Credit",
    "1907": "Server updating",
    "1908": "Invalid DelayUntil format",
    "1909": "Invalid Message",
    "1910": "Invalid Language",
    "1911": "Text too long",
    "1912": "Invalid Environment",
}

class SMSMisrService(models.AbstractModel):
    _name = 'smsmisr.service'
    _description = 'SMSMisr API Service'

    def _get_cfg(self):
        cfg = self.env['smsmisr.config'].sudo().get_solo()
        return {
            'username': cfg.username,
            'password': cfg.password,
            'sender': cfg.sender,
            'url': cfg.api_url or 'https://smsmisr.com/api/SMS/'
        }

    def send_sms(self, mobile, message, language=1, environment=2, delay_until=None):
        cfg = self._get_cfg()
        if not (cfg['username'] and cfg['password'] and cfg['sender']):
            raise UserError('SMSMisr credentials not configured.')

        payload = {
            "environment": str(environment),
            "username": cfg['username'],
            "password": cfg['password'],
            "sender": cfg['sender'],
            "mobile": mobile,
            "language": str(language),
            "message": message,
        }

        if delay_until:
            payload["DelayUntil"] = delay_until

        try:
            response = requests.post(cfg['url'], data=payload, timeout=20)
            _logger.info("SMSMisr send: payload=%s status=%s", payload, response.status_code)

            result = {
                'success': False,
                'status_code': response.status_code,
                'response_text': response.text,
                'error': None,
                'message_id': None,
            }

            # Parse response JSON
            try:
                data = json.loads(response.text)
                code = data.get("code")
                result['message_id'] = data.get("SMSID")
                result['success'] = code == "1901"
                if code != "1901":
                    result['error'] = SMSMISR_CODES.get(code, f"Unknown error code {code}")
            except Exception as e:
                result['error'] = f"Invalid response format: {response.text}"

            return result

        except Exception as e:
            _logger.exception("Failed to send SMS")
            return {'success': False, 'error': str(e)}
