from odoo import http
from odoo.http import request

class SmsMisrController(http.Controller):
    @http.route('/smsmisr/dlr', type='http', auth='public', methods=['POST', 'GET'], csrf=False)
    def dlr(self, **post):
        message_id = post.get('messageid') or post.get('id') or post.get('msgid') or post.get('message_id')
        status = post.get('status') or post.get('stat') or post.get('delivery')
        mobile = post.get('mobile') or post.get('phone') or post.get('msisdn')

        if not message_id:
            return 'Missing message id', 400

        msgs = request.env['smsmisr.message'].sudo().search([('external_id','=', message_id)], limit=1)
        if not msgs:
            return 'Not found', 200

        if status and status.lower() in ('delivered', 'delivery', 'deliv', 'dlr', 'ok', 'success'):
            msgs.sudo().write({'status': 'sent', 'response': str(post)})
        else:
            msgs.sudo().write({'status': 'failed', 'response': str(post)})
        return 'OK'
