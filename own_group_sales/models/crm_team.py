# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    parent_team = fields.Many2one('crm.team', string='Parent Team')

    
    # @api.onchange('parent_team')
    # def _onchange_rparent_team(self):
    #     child_teams = self.search([('parent_team', '=', self._origin.id)])

    #     if self.parent_team:
    #         if self.parent_team in child_teams:
    #             raise UserError(_("You can't choose subteam team as parent."))

    #         if self.parent_team.id == self._origin.id:
    #             raise UserError(_("You can't choose the same team as parent."))

    