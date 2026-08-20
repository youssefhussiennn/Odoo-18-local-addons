import re

from odoo import api, fields, models, _
# pyrefly: ignore [missing-import]
from odoo.exceptions import UserError

# Egypt's international dialing/country code, used to auto-correct mobile
# numbers before a WhatsApp message is sent. Change this if you operate in
# a different country.
COUNTRY_CODE = '20'
# Expected length of a local Egyptian mobile number without the leading 0
# and without the country code, e.g. '1012345678'.
NATIONAL_NUMBER_LENGTH = 10


class WhatsappSendMessage(models.TransientModel):
    """ Wizard for sending whatsapp message."""
    _name = 'whatsapp.send.message'
    _description = 'Whatsapp Send Message'

    partner_id = fields.Many2one('res.partner',
                                 string="Recipient",
                                 help="Partner")
    mobile = fields.Char(string="Contact Number",
                         required=True,
                         help="Contact number of Partner")
    message = fields.Text(string="Message",
                          required=True,
                          help="Message to send")
    image_1920 = fields.Binary(string='Image', help="Image of Partner")

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """ Function for fetching the mobile number and image of partner."""
        self.mobile = self.partner_id.mobile or self.partner_id.phone
        self.image_1920 = self.partner_id.image_1920

    @api.model
    def _format_whatsapp_number(self, mobile):
        """ Validate a mobile number and return it formatted with the
        country code required by WhatsApp (e.g. '201012345678').

        Accepted input formats (spaces, dashes, parentheses are ignored):
        - 11 digits starting with 0, e.g. 01012345678
        - 10 digits without the leading 0, e.g. 1012345678
        - Already containing the country code, e.g. 201012345678 or
          +201012345678 or 00201012345678

        Raises a UserError if the number does not match any of the above.
        """
        if not mobile:
            raise UserError(_(
                "Please enter a mobile number before sending the "
                "WhatsApp message."))

        # Keep digits only.
        digits = re.sub(r'\D', '', mobile)

        # Strip an international dialing prefix (00) if present.
        if digits.startswith('00'):
            digits = digits[2:]

        if digits.startswith(COUNTRY_CODE):
            national_number = digits[len(COUNTRY_CODE):]
        elif digits.startswith('0'):
            # Local format, e.g. 01012345678 (11 digits including the 0).
            national_number = digits[1:]
        else:
            # No country code and no leading 0, e.g. 1012345678.
            national_number = digits

        if len(national_number) != NATIONAL_NUMBER_LENGTH:
            raise UserError(_(
                "The mobile number '%s' is not valid. It should have 11 "
                "digits starting with 0 (e.g. 01012345678) or 10 digits "
                "without the leading 0 (e.g. 1012345678).") % mobile)

        return COUNTRY_CODE + national_number

    def send_message(self):
        """ This function redirects to the whatsapp web with required
        parameters.
        """
        if not self.message or not self.mobile:
            raise UserError(_(
                "Please enter both a message and a mobile number before "
                "sending the WhatsApp message."))

        formatted_mobile = self._format_whatsapp_number(self.mobile)

        message_string = ''
        message = self.message.split(' ')
        for msg in message:
            message_string = message_string + msg + '%20'
        message_string = message_string[:(len(message_string) - 3)]
        message_post_content = message_string
        if self.partner_id:
            self.partner_id.message_post(body=message_post_content)
        return {
            'type': 'ir.actions.act_url',
            'url': "https://api.whatsapp.com/send?phone=" +
                   formatted_mobile + "&text=" + message_string,
            'target': 'new',
            'res_id': self.id,
        }
