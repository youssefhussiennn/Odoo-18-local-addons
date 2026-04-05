# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountAsset(models.Model):
    _inherit = 'account.asset'
    def open_asset(self, view_mode):
        asset_type = self.asset_type if len(self) == 1 else self[0].asset_type
        views = [v for v in self._get_views(asset_type) if v[1] in view_mode]
        ctx = dict(self._context,
                asset_type=asset_type,
                default_asset_type=asset_type)
        ctx.pop('default_move_type', None)
        action = {
            'name': _('Asset'),
            'view_mode': ','.join(view_mode),
            'type': 'ir.actions.act_window',
            'res_id': self.id if 'tree' not in view_mode else False,
            'res_model': 'account.asset',
            'views': views,
            'domain': [('id', 'in', self.ids)],
            'context': ctx
        }
        if asset_type == 'sale':
            action['name'] = _('Deferred Revenue')
        elif asset_type == 'expense':
            action['name'] = _('Deferred Expense')

        return action

