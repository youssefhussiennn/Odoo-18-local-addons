from odoo import fields, models,api,_

class MessageInherited(models.Model):
    _inherit='mail.message'

    def _message_format(self, fnames, format_reply=True, legacy=False):
        vals_list = super()._message_format(fnames=fnames, format_reply=format_reply, legacy=legacy)
        for vals in vals_list:
            vals.update({
                'showbtn': False if self.env.user.has_group('chatter_restrict_edit_delete.chatter_restrict_edit_delete_group_user') else True
            })
        return vals_list

