# -*- coding: utf-8 -*-

from odoo import models, api


class AccountReport(models.Model):
    _inherit = 'account.report'

    def _init_options_partner(self, options, previous_options):
        """Extend partner filter initialization to add salesperson filter."""
        super()._init_options_partner(options, previous_options)

        if not self.filter_partner:
            return

        # Add salesperson filter data to options
        previous_salesperson_ids = previous_options.get('salesperson_ids') or []
        selected_salesperson_ids = [int(sp) for sp in previous_salesperson_ids]
        selected_salespersons = (
            self.env['res.users'].search([('id', 'in', selected_salesperson_ids)])
            if selected_salesperson_ids
            else self.env['res.users']
        )
        options['salesperson_ids'] = selected_salespersons.ids
        options['selected_salesperson_names'] = selected_salespersons.mapped('display_name')

    @api.model
    def _get_options_partner_domain(self, options):
        """Extend partner domain to filter by salesperson."""
        domain = super()._get_options_partner_domain(options)

        if options.get('salesperson_ids'):
            salesperson_ids = [int(sp) for sp in options['salesperson_ids']]
            domain.append(('partner_id.user_id', 'in', salesperson_ids))

        return domain
