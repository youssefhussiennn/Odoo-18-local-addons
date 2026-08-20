from odoo import models, _
# pyrefly: ignore [missing-import]
from odoo.exceptions import UserError


class HelpdeskTicket(models.Model):
    """
    This class extends the 'helpdesk.ticket' model to add custom
    functionalities related to WhatsApp messaging.
    """
    _inherit = 'helpdesk.ticket'

    def action_send_whatsapp(self):
        """ Action for sending a WhatsApp message from the helpdesk
        ticket form.
        """
        self.ensure_one()

        partner = self.partner_id
        mobile = False
        if partner:
            mobile = partner.mobile or partner.phone
        if not mobile:
            # Fallback to the phone number typed directly on the ticket,
            # in case there is no linked partner or the partner has no
            # mobile/phone set.
            mobile = getattr(self, 'partner_phone', False)
        if not mobile:
            raise UserError(_(
                "There is no mobile number available for this ticket. "
                "Please add a mobile number to the customer or the "
                "ticket before sending a WhatsApp message."))

        compose_form_id = self.env.ref(
            'whatsapp_mail_messaging.whatsapp_send_message_view_form').id
        ctx = dict(self.env.context)
        message_template = (
            self.company_id.whatsapp_message if self.company_id else False)
        customer_name = (
            partner.name if partner else getattr(self, 'partner_name', False)
        ) or ''
        ticket_reference = getattr(self, 'ticket_ref', False) or self.id
        default_message = (
                "Hi" + " " + customer_name + ',' + '\n' +
                "This is regarding your support ticket" + ' #' +
                str(ticket_reference) + ' - ' + (self.name or '') + '.' +
                '\n' +
                "Our team is currently working on it and will keep you "
                "updated. Thank you for your patience.")
        message = message_template if message_template else default_message
        ctx.update({
            'default_message': message,
            'default_partner_id': partner.id if partner else False,
            'default_mobile': mobile,
            'default_image_1920': partner.image_1920 if partner else False,
        })
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'whatsapp.send.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
