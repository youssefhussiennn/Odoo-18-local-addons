# -*- coding: utf-8 -*-
import datetime
from itertools import chain

from dateutil.relativedelta import relativedelta

from odoo import models, fields, _
from odoo.exceptions import UserError
from odoo.tools import SQL


class AgedPartnerBalanceCustomHandler(models.AbstractModel):
    """
    Replaces Odoo's stock aging buckets - which are ALWAYS evenly spaced
    (one `aging_interval`, e.g. 30/30/30/30/Older) - with fixed, unevenly
    spaced buckets: 1-30, 31-90, 91-150, 151-365, Older.

    Odoo's own filter for "30/60/90 Days" (`options['aging_interval']`) has
    no concept of variable-width buckets, so there's no clean way to get
    this via configuration - the date-boundary math has to be overridden.

    _CUMULATIVE_DAYS is the single source of truth for the bucket edges:
    both the report's data engine and its "click a cell to see the
    invoices" audit action read from it, so they can never drift out of
    sync with each other (the stock code hardcodes 30 days separately in
    both places, which is a latent bug if you ever change the interval
    filter and forget the audit action still assumes 30).

    _CUMULATIVE_DAYS[0] is always 0. Each subsequent value is the
    cumulative day-count at which that bucket ends. The number of entries
    after the leading 0 must equal the number of dated columns
    (period1..period4) defined on the Aged Receivable / Aged Payable
    reports - 4, by default in stock Odoo 18.
    """
    _inherit = 'account.aged.partner.balance.report.handler'

    _CUMULATIVE_DAYS = [0, 30, 90, 150, 365]  # -> buckets: 1-30, 31-90, 91-150, 151-365, then Older

    # ------------------------------------------------------------------
    # Column labels ("1 - 30", "31 - 90", ...)
    # ------------------------------------------------------------------
    def _custom_options_initializer(self, report, options, previous_options):
        super()._custom_options_initializer(report, options, previous_options=previous_options)

        # Toggle state, persisted per user/session the same way as
        # aging_based_on / aging_interval above. Defaults to ON.
        options['custom_periods_enabled'] = (
            True if previous_options is None
            else previous_options.get('custom_periods_enabled', True)
        )

        if not options['custom_periods_enabled']:
            return  # leave the stock interval-based labels super() already set

        custom_labels = []
        prev = 0
        for end_day in self._CUMULATIVE_DAYS[1:]:
            custom_labels.append(f'{prev + 1} - {end_day}')
            prev = end_day

        for column in options['columns']:
            if column['expression_label'].startswith('period'):
                period_number = int(column['expression_label'].replace('period', '')) - 1
                if 0 <= period_number < len(custom_labels):
                    column['name'] = custom_labels[period_number]

    # ------------------------------------------------------------------
    # Core data engine - copied from account_reports, only the `periods`
    # construction block differs from stock (marked below). Everything
    # after it is untouched and operates generically on `periods` /
    # `len(periods)`, so it doesn't need to know the boundaries are custom.
    # ------------------------------------------------------------------
    def _aged_partner_report_custom_engine_common(self, options, internal_type, current_groupby, next_groupby, offset=0, limit=None):
        report = self.env['account.report'].browse(options['report_id'])
        report._check_groupby_fields((next_groupby.split(',') if next_groupby else []) + ([current_groupby] if current_groupby else []))

        def minus_days(date_obj, days):
            return fields.Date.to_string(date_obj - relativedelta(days=days))

        aging_date_field = SQL.identifier('invoice_date') if options['aging_based_on'] == 'base_on_invoice_date' else SQL.identifier('date_maturity')
        date_to = fields.Date.from_string(options['date']['date_to'])
        nb_periods = len([column for column in options['columns'] if column['expression_label'].startswith('period')]) - 1

        if options.get('custom_periods_enabled', True):
            # --- CUSTOM: variable-width buckets instead of options['aging_interval'] ---
            bounds = self._CUMULATIVE_DAYS[1:]  # e.g. [30, 90, 150, 365]
            if nb_periods != len(bounds) + 1:
                raise UserError(_(
                    "Aged Report Custom Periods: the report defines %(actual)s dated "
                    "period columns, but this module's _CUMULATIVE_DAYS expects "
                    "%(expected)s (one per custom bucket + Older). Check the "
                    "aged_receivable_report/aged_payable_report column definitions, "
                    "or adjust _CUMULATIVE_DAYS to match.",
                    actual=nb_periods, expected=len(bounds) + 1,
                ))

            periods = [(False, fields.Date.to_string(date_to))]  # period0: Not Due
            prev_end = 0
            for end_day in bounds:
                start_date = minus_days(date_to, prev_end + 1)
                end_date = minus_days(date_to, end_day)
                periods.append((start_date, end_date))
                prev_end = end_day
            periods.append((minus_days(date_to, prev_end + 1), False))  # Older, open-ended
            # --- END CUSTOM ---
        else:
            # --- STOCK: original evenly-spaced aging_interval logic ---
            interval = options['aging_interval']
            periods = [(False, fields.Date.to_string(date_to))]
            for i in range(nb_periods):
                start_date = minus_days(date_to, (interval * i) + 1)
                end_date = minus_days(date_to, interval * (i + 1)) if i < nb_periods - 1 else False
                periods.append((start_date, end_date))
            # --- END STOCK ---

        def build_result_dict(report, query_res_lines):
            rslt = {f'period{i}': 0 for i in range(len(periods))}

            for query_res in query_res_lines:
                for i in range(len(periods)):
                    period_key = f'period{i}'
                    rslt[period_key] += query_res[period_key]

            if current_groupby == 'id':
                query_res = query_res_lines[0]  # We're grouping by id, so there is only 1 element in query_res_lines anyway
                currency = self.env['res.currency'].browse(query_res['currency_id'][0]) if len(query_res['currency_id']) == 1 else None
                rslt.update({
                    'invoice_date': query_res['invoice_date'][0] if len(query_res['invoice_date']) == 1 else None,
                    'due_date': query_res['due_date'][0] if len(query_res['due_date']) == 1 else None,
                    'amount_currency': query_res['amount_currency'],
                    'currency_id': query_res['currency_id'][0] if len(query_res['currency_id']) == 1 else None,
                    'currency': currency.display_name if currency else None,
                    'account_name': query_res['account_name'][0] if len(query_res['account_name']) == 1 else None,
                    'total': None,
                    'has_sublines': query_res['aml_count'] > 0,
                    'partner_id': query_res['partner_id'][0] if query_res['partner_id'] else None,
                })
            else:
                rslt.update({
                    'invoice_date': None,
                    'due_date': None,
                    'amount_currency': None,
                    'currency_id': None,
                    'currency': None,
                    'account_name': None,
                    'total': sum(rslt[f'period{i}'] for i in range(len(periods))),
                    'has_sublines': False,
                })

            return rslt

        # Build period table
        period_table_format = ('(VALUES %s)' % ','.join("(%s, %s, %s)" for period in periods))
        params = list(chain.from_iterable(
            (period[0] or None, period[1] or None, i)
            for i, period in enumerate(periods)
        ))
        period_table = SQL(period_table_format, *params)

        # Build query
        query = report._get_report_query(options, 'strict_range', domain=[('account_id.account_type', '=', internal_type)])
        account_alias = query.left_join(lhs_alias='account_move_line', lhs_column='account_id', rhs_table='account_account', rhs_column='id', link='account_id')
        account_code = self.env['account.account']._field_to_sql(account_alias, 'code', query)

        always_present_groupby = SQL("period_table.period_index")
        if current_groupby:
            select_from_groupby = SQL("%s AS grouping_key,", SQL.identifier("account_move_line", current_groupby))
            groupby_clause = SQL("%s, %s", SQL.identifier("account_move_line", current_groupby), always_present_groupby)
        else:
            select_from_groupby = SQL()
            groupby_clause = always_present_groupby
        multiplicator = -1 if internal_type == 'liability_payable' else 1
        select_period_query = SQL(',').join(
            SQL("""
                CASE WHEN period_table.period_index = %(period_index)s
                THEN %(multiplicator)s * SUM(%(balance_select)s)
                ELSE 0 END AS %(column_name)s
                """,
                period_index=i,
                multiplicator=multiplicator,
                column_name=SQL.identifier(f"period{i}"),
                balance_select=report._currency_table_apply_rate(SQL(
                    "account_move_line.balance - COALESCE(part_debit.amount, 0) + COALESCE(part_credit.amount, 0)"
                )),
            )
            for i in range(len(periods))
        )

        tail_query = report._get_engine_query_tail(offset, limit)
        query = SQL(
            """
            WITH period_table(date_start, date_stop, period_index) AS (%(period_table)s)

            SELECT
                %(select_from_groupby)s
                %(multiplicator)s * (
                    SUM(account_move_line.amount_currency)
                    - COALESCE(SUM(part_debit.debit_amount_currency), 0)
                    + COALESCE(SUM(part_credit.credit_amount_currency), 0)
                ) AS amount_currency,
                ARRAY_AGG(DISTINCT account_move_line.partner_id) AS partner_id,
                ARRAY_AGG(account_move_line.payment_id) AS payment_id,
                ARRAY_AGG(DISTINCT move.invoice_date) AS invoice_date,
                ARRAY_AGG(DISTINCT COALESCE(account_move_line.%(aging_date_field)s, account_move_line.date)) AS report_date,
                ARRAY_AGG(DISTINCT %(account_code)s) AS account_name,
                ARRAY_AGG(DISTINCT COALESCE(account_move_line.%(aging_date_field)s, account_move_line.date)) AS due_date,
                ARRAY_AGG(DISTINCT account_move_line.currency_id) AS currency_id,
                COUNT(account_move_line.id) AS aml_count,
                ARRAY_AGG(%(account_code)s) AS account_code,
                %(select_period_query)s

            FROM %(table_references)s

            JOIN account_journal journal ON journal.id = account_move_line.journal_id
            JOIN account_move move ON move.id = account_move_line.move_id
            %(currency_table_join)s

            LEFT JOIN LATERAL (
                SELECT
                    SUM(part.amount) AS amount,
                    SUM(part.debit_amount_currency) AS debit_amount_currency,
                    part.debit_move_id
                FROM account_partial_reconcile part
                WHERE part.max_date <= %(date_to)s AND part.debit_move_id = account_move_line.id
                GROUP BY part.debit_move_id
            ) part_debit ON TRUE

            LEFT JOIN LATERAL (
                SELECT
                    SUM(part.amount) AS amount,
                    SUM(part.credit_amount_currency) AS credit_amount_currency,
                    part.credit_move_id
                FROM account_partial_reconcile part
                WHERE part.max_date <= %(date_to)s AND part.credit_move_id = account_move_line.id
                GROUP BY part.credit_move_id
            ) part_credit ON TRUE

            JOIN period_table ON
                (
                    period_table.date_start IS NULL
                    OR COALESCE(account_move_line.%(aging_date_field)s, account_move_line.date) <= DATE(period_table.date_start)
                )
                AND
                (
                    period_table.date_stop IS NULL
                    OR COALESCE(account_move_line.%(aging_date_field)s, account_move_line.date) >= DATE(period_table.date_stop)
                )

            WHERE %(search_condition)s

            GROUP BY %(groupby_clause)s

            HAVING
                ROUND(SUM(%(having_debit)s), %(currency_precision)s) != 0
                OR ROUND(SUM(%(having_credit)s), %(currency_precision)s) != 0
            %(tail_query)s
            """,
            account_code=account_code,
            period_table=period_table,
            select_from_groupby=select_from_groupby,
            select_period_query=select_period_query,
            multiplicator=multiplicator,
            aging_date_field=aging_date_field,
            table_references=query.from_clause,
            currency_table_join=report._currency_table_aml_join(options),
            date_to=date_to,
            search_condition=query.where_clause,
            groupby_clause=groupby_clause,
            having_debit=report._currency_table_apply_rate(SQL("CASE WHEN account_move_line.balance > 0  THEN account_move_line.balance else 0 END - COALESCE(part_debit.amount, 0)")),
            having_credit=report._currency_table_apply_rate(SQL("CASE WHEN account_move_line.balance < 0  THEN -account_move_line.balance else 0 END - COALESCE(part_credit.amount, 0)")),
            currency_precision=self.env.company.currency_id.decimal_places,
            tail_query=tail_query,
        )

        self._cr.execute(query)
        query_res_lines = self._cr.dictfetchall()

        if not current_groupby:
            return build_result_dict(report, query_res_lines)
        else:
            rslt = []

            all_res_per_grouping_key = {}
            for query_res in query_res_lines:
                grouping_key = query_res['grouping_key']
                all_res_per_grouping_key.setdefault(grouping_key, []).append(query_res)

            for grouping_key, query_res_lines in all_res_per_grouping_key.items():
                rslt.append((grouping_key, build_result_dict(report, query_res_lines)))

            return rslt

    # ------------------------------------------------------------------
    # Audit / drill-down domain when a cell is clicked. Stock Odoo
    # hardcodes 30-day buckets here regardless of aging_interval - it
    # must be kept in sync with the buckets above or the invoices shown
    # won't match the cell that was clicked.
    # ------------------------------------------------------------------
    def _build_domain_from_period(self, options, period):
        if period == "total" or not period[-1].isdigit():
            return []

        period_number = int(period[-1])
        options_date_to = datetime.datetime.strptime(options['date']['date_to'], '%Y-%m-%d')

        if period_number == 0:
            return [('date_maturity', '>=', options['date']['date_to'])]

        if not options.get('custom_periods_enabled', True):
            # --- STOCK: original hardcoded-30-day formula ---
            period_end = options_date_to - datetime.timedelta(30 * (period_number - 1) + 1)
            period_start = options_date_to - datetime.timedelta(30 * period_number)
            if period_number == 5:
                return [('date_maturity', '<=', period_end)]
            return [('date_maturity', '>=', period_start), ('date_maturity', '<=', period_end)]

        bounds = self._CUMULATIVE_DAYS  # [0, 30, 90, 150, 365]

        if 1 <= period_number < len(bounds):
            days_before = bounds[period_number - 1]
            days_after = bounds[period_number]
            period_start = options_date_to - datetime.timedelta(days=days_after)
            period_end = options_date_to - datetime.timedelta(days=days_before + 1)
            return [('date_maturity', '>=', period_start), ('date_maturity', '<=', period_end)]

        # Older: anything past the last defined boundary
        period_end = options_date_to - datetime.timedelta(days=bounds[-1] + 1)
        return [('date_maturity', '<=', period_end)]
