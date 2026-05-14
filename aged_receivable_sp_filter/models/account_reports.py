# -*- coding: utf-8 -*-

from odoo import models, api


class AccountReport(models.Model):
    _inherit = 'account.report'

    def _init_options_partner(self, options, previous_options):
        """Extend partner filter initialization to add salesperson + account filters."""
        super()._init_options_partner(options, previous_options)

        if not self.filter_partner:
            return

        # =====================================================
        # Salesperson Filter
        # =====================================================

        previous_salesperson_ids = previous_options.get('salesperson_ids') or []

        selected_salesperson_ids = [int(sp) for sp in previous_salesperson_ids]

        selected_salespersons = (
            self.env['res.users'].search([('id', 'in', selected_salesperson_ids)])
            if selected_salesperson_ids
            else self.env['res.users']
        )

        options['salesperson_ids'] = selected_salespersons.ids
        options['selected_salesperson_names'] = selected_salespersons.mapped('display_name')

        # =====================================================
        # Account Filter
        # =====================================================

        previous_account_ids = previous_options.get('account_ids') or []

        selected_account_ids = [int(acc) for acc in previous_account_ids]

        selected_accounts = (
            self.env['account.account'].search([('id', 'in', selected_account_ids)])
            if selected_account_ids
            else self.env['account.account']
        )

        options['account_ids'] = selected_accounts.ids
        options['selected_account_names'] = selected_accounts.mapped('display_name')

    @api.model
    def _get_options_partner_domain(self, options):
        """Extend partner domain to filter by salesperson + account."""
        domain = super()._get_options_partner_domain(options)

        # =====================================================
        # Salesperson Filter
        # =====================================================

        if options.get('salesperson_ids'):
            salesperson_ids = [int(sp) for sp in options['salesperson_ids']]
            domain.append(('partner_id.user_id', 'in', salesperson_ids))

        # =====================================================
        # Account Filter
        # =====================================================

        if options.get('account_ids'):
            account_ids = [int(acc) for acc in options['account_ids']]
            domain.append(('account_id', 'in', account_ids))

        return domain