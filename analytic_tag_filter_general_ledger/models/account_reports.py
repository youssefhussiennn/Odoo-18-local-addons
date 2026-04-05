# -*- coding: utf-8 -*-

from odoo import models, api


class AccountReport(models.Model):
    _inherit = 'account.report'

    # -----------------------------
    # INIT OPTIONS
    # -----------------------------
    def _init_options_analytic_tag(self, options, previous_options):
        """Initialize analytic tag filter in report options."""

        previous_tag_ids = previous_options.get('analytic_tag_ids') or []
        selected_tag_ids = [int(tag) for tag in previous_tag_ids]

        selected_tags = self.env['account.analytic.tag'].browse(selected_tag_ids)

        options['analytic_tag_ids'] = selected_tags.ids
        options['selected_analytic_tag_names'] = selected_tags.mapped('name')

    def _init_options(self, options, previous_options=None):
        super()._init_options(options, previous_options)
        self._init_options_analytic_tag(options, previous_options or {})

    # -----------------------------
    # DOMAIN FILTER
    # -----------------------------
    @api.model
    def _get_options_domain(self, options, date_scope=None):
        domain = super()._get_options_domain(options, date_scope)

        if options.get('analytic_tag_ids'):
            tag_ids = [int(tag) for tag in options['analytic_tag_ids']]
            domain.append(('analytic_tag_ids', 'in', tag_ids))

        return domain