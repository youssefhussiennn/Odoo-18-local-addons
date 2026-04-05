from odoo import models, _
from odoo.tools import SQL
from collections import defaultdict


class PartnerLedgerAmountCurrencyHandler(models.AbstractModel):
    _inherit = 'account.partner.ledger.report.handler'

    # ------------------------------------------------------------
    # 1. ADD COLUMN
    # ------------------------------------------------------------
    def _custom_options_initializer(self, report, options, previous_options=None):
        super()._custom_options_initializer(report, options, previous_options)

        if not any(col.get('expression_label') == 'amount_currency' for col in options['columns']):
            options['columns'].append({
                'name': _('Amount Currency'),
                'expression_label': 'amount_currency',
                'class': 'monetary',
                'figure_type': 'monetary',
            })

    # ------------------------------------------------------------
    # 2. SQL (FIXED DATE RANGE)
    # ------------------------------------------------------------
    def _get_query_sums(self, options):
        queries = []
        report = self.env.ref('account_reports.partner_ledger_report')

        for column_group_key, column_group_options in report._split_options_per_column_group(options).items():
            # 🔥 FIX: use strict_range instead of from_beginning
            query = report._get_report_query(column_group_options, 'strict_range')

            queries.append(SQL(
                """
                SELECT
                    account_move_line.partner_id AS groupby,
                    %(column_group_key)s AS column_group_key,

                    SUM(%(debit_select)s) AS debit,
                    SUM(%(credit_select)s) AS credit,
                    SUM(%(balance_select)s) AS amount,
                    SUM(%(balance_select)s) AS balance,
                    SUM(account_move_line.amount_currency) AS amount_currency

                FROM %(table_references)s
                %(currency_table_join)s
                WHERE %(search_condition)s
                GROUP BY account_move_line.partner_id
                """,
                column_group_key=column_group_key,
                debit_select=report._currency_table_apply_rate(SQL("account_move_line.debit")),
                credit_select=report._currency_table_apply_rate(SQL("account_move_line.credit")),
                balance_select=report._currency_table_apply_rate(SQL("account_move_line.balance")),
                table_references=query.from_clause,
                currency_table_join=report._currency_table_aml_join(column_group_options),
                search_condition=query.where_clause,
            ))

        return SQL(' UNION ALL ').join(queries)

    # ------------------------------------------------------------
    # 3. AGGREGATION
    # ------------------------------------------------------------
    def _query_partners(self, options):

        groupby_partners = {}

        def assign_sum(row):
            groupby_partners.setdefault(row['groupby'], defaultdict(lambda: defaultdict(float)))
            group = groupby_partners[row['groupby']][row['column_group_key']]

            for field in ['debit', 'credit', 'amount', 'balance', 'amount_currency']:
                group[field] += row.get(field, 0.0)

        # MAIN QUERY
        query = self._get_query_sums(options)
        self._cr.execute(query)

        for row in self._cr.dictfetchall():
            assign_sum(row)

        # RECONCILIATION (DO NOT TOUCH amount_currency)
        query = self._get_sums_without_partner(options)
        self._cr.execute(query)

        for row in self._cr.dictfetchall():
            if row['groupby'] not in groupby_partners:
                continue

            group = groupby_partners[row['groupby']][row['column_group_key']]

            group['debit'] += row.get('debit', 0.0)
            group['credit'] += row.get('credit', 0.0)
            group['amount'] += row.get('amount', 0.0)
            group['balance'] += row.get('balance', 0.0)

        # FETCH PARTNERS
        partners = self.env['res.partner'].with_context(active_test=False).browse(
            list(groupby_partners.keys())
        ) if groupby_partners else []

        return [(partner, groupby_partners.get(partner.id, {})) for partner in partners]

    # ------------------------------------------------------------
    # 4. BUILD LINES
    # ------------------------------------------------------------
    def _build_partner_lines(self, report, options, level_shift=0):
        lines = []

        totals_by_column_group = {
            column_group_key: {
                field: 0.0
                for field in ['debit', 'credit', 'amount', 'balance', 'amount_currency']
            }
            for column_group_key in options['column_groups']
        }

        partners_results = self._query_partners(options)

        for partner, results in partners_results:
            partner_values = defaultdict(dict)

            for column_group_key in options['column_groups']:
                sums = results.get(column_group_key, {})

                for field in totals_by_column_group[column_group_key]:
                    value = sums.get(field, 0.0)
                    partner_values[column_group_key][field] = value
                    totals_by_column_group[column_group_key][field] += value

            lines.append(self._get_report_line_partners(
                options, partner, partner_values, level_shift=level_shift
            ))

        return lines, totals_by_column_group