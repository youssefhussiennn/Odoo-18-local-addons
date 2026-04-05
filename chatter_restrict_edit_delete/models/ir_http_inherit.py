from odoo import api, http, models

class Http(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        res = super().session_info()
        user = self.env.user
        res.update({"show_btn": not user.has_group('chatter_restrict_edit_delete.chatter_restrict_edit_delete_group_user'), })
        return res
