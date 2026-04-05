from odoo import models
from odoo.tools import SQL


class PartnerLedgerCustomHandler(models.AbstractModel):
    _inherit = 'account.partner.ledger.report.handler'

    def _get_aml_values(self, options, partner_ids, offset=0, limit=None):
        rslt = {partner_id: [] for partner_id in partner_ids}

        partner_ids_wo_none = [x for x in partner_ids if x]
        directly_linked_aml_partner_clauses = []
        indirectly_linked_aml_partner_clause = SQL('aml_with_partner.partner_id IS NOT NULL')

        if None in partner_ids:
            directly_linked_aml_partner_clauses.append(SQL('account_move_line.partner_id IS NULL'))
        if partner_ids_wo_none:
            directly_linked_aml_partner_clauses.append(
                SQL('account_move_line.partner_id IN %s', tuple(partner_ids_wo_none))
            )
            indirectly_linked_aml_partner_clause = SQL(
                'aml_with_partner.partner_id IN %s', tuple(partner_ids_wo_none)
            )

        directly_linked_aml_partner_clause = SQL(
            '(%s)', SQL(' OR ').join(directly_linked_aml_partner_clauses)
        )

        queries = []
        journal_name = self.env['account.journal']._field_to_sql('journal', 'name')
        report = self.env.ref('account_reports.partner_ledger_report')

        for column_group_key, group_options in report._split_options_per_column_group(options).items():
            query = report._get_report_query(group_options, 'strict_range')

            account_alias = query.left_join(
                lhs_alias='account_move_line',
                lhs_column='account_id',
                rhs_table='account_account',
                rhs_column='id',
                link='account_id',
            )

            account_code = self.env['account.account']._field_to_sql(account_alias, 'code', query)
            account_name = self.env['account.account']._field_to_sql(account_alias, 'name')

            # -------------------------------
            # Directly linked AMLs
            # -------------------------------
            queries.append(SQL(
                '''
                SELECT
                    account_move_line.id,
                    account_move_line.x_studio_vessel                      AS x_studio_vessel,
                    account_move_line.date_maturity,
                    account_move_line.name,
                    account_move_line.ref,
                    account_move_line.company_id,
                    account_move_line.account_id,
                    account_move_line.payment_id,
                    account_move_line.partner_id,
                    account_move_line.currency_id,
                    account_move_line.amount_currency,
                    account_move_line.matching_number,
                    COALESCE(account_move_line.invoice_date, account_move_line.date) AS invoice_date,
                    %(debit_select)s                                 AS debit,
                    %(credit_select)s                                AS credit,
                    %(balance_select)s                               AS amount,
                    %(balance_select)s                               AS balance,
                    account_move.name                                AS move_name,
                    account_move.move_type                           AS move_type,
                    %(account_code)s                                 AS account_code,
                    %(account_name)s                                 AS account_name,
                    journal.code                                     AS journal_code,
                    %(journal_name)s                                 AS journal_name,
                    %(column_group_key)s                             AS column_group_key,
                    'directly_linked_aml'                            AS key,
                    0                                                 AS partial_id
                FROM %(table_references)s
                JOIN account_move ON account_move.id = account_move_line.move_id
                %(currency_table_join)s
                LEFT JOIN account_journal journal ON journal.id = account_move_line.journal_id
                WHERE %(search_condition)s
                  AND %(directly_linked_aml_partner_clause)s
                ORDER BY account_move_line.date, account_move_line.id
                ''',
                debit_select=report._currency_table_apply_rate(SQL("account_move_line.debit")),
                credit_select=report._currency_table_apply_rate(SQL("account_move_line.credit")),
                balance_select=report._currency_table_apply_rate(SQL("account_move_line.balance")),
                account_code=account_code,
                account_name=account_name,
                journal_name=journal_name,
                column_group_key=column_group_key,
                table_references=query.from_clause,
                currency_table_join=report._currency_table_aml_join(group_options),
                search_condition=query.where_clause,
                directly_linked_aml_partner_clause=directly_linked_aml_partner_clause,
            ))

            # -------------------------------
            # Indirectly linked AMLs
            # -------------------------------
            queries.append(SQL(
                '''
                SELECT
                    account_move_line.id,
                    account_move_line.x_studio_vessel                      AS x_studio_vessel,
                    account_move_line.date_maturity,
                    account_move_line.name,
                    account_move_line.ref,
                    account_move_line.company_id,
                    account_move_line.account_id,
                    account_move_line.payment_id,
                    aml_with_partner.partner_id,
                    account_move_line.currency_id,
                    account_move_line.amount_currency,
                    account_move_line.matching_number,
                    COALESCE(account_move_line.invoice_date, account_move_line.date) AS invoice_date,
                    %(debit_select)s                                 AS debit,
                    %(credit_select)s                                AS credit,
                    %(balance_select)s                               AS amount,
                    %(balance_select)s                               AS balance,
                    account_move.name                                AS move_name,
                    account_move.move_type                           AS move_type,
                    %(account_code)s                                 AS account_code,
                    %(account_name)s                                 AS account_name,
                    journal.code                                     AS journal_code,
                    %(journal_name)s                                 AS journal_name,
                    %(column_group_key)s                             AS column_group_key,
                    'indirectly_linked_aml'                          AS key,
                    partial.id                                       AS partial_id
                FROM %(table_references)s
                %(currency_table_join)s,
                    account_partial_reconcile partial,
                    account_move,
                    account_move_line aml_with_partner,
                    account_journal journal
                WHERE
                    (account_move_line.id = partial.debit_move_id
                     OR account_move_line.id = partial.credit_move_id)
                    AND account_move_line.partner_id IS NULL
                    AND account_move.id = account_move_line.move_id
                    AND (aml_with_partner.id = partial.debit_move_id
                         OR aml_with_partner.id = partial.credit_move_id)
                    AND %(indirectly_linked_aml_partner_clause)s
                    AND journal.id = account_move_line.journal_id
                    AND %(account_alias)s.id = account_move_line.account_id
                    AND %(search_condition)s
                    AND partial.max_date BETWEEN %(date_from)s AND %(date_to)s
                ORDER BY account_move_line.date, account_move_line.id
                ''',
                debit_select=report._currency_table_apply_rate(
                    SQL("CASE WHEN aml_with_partner.balance > 0 THEN 0 ELSE partial.amount END")
                ),
                credit_select=report._currency_table_apply_rate(
                    SQL("CASE WHEN aml_with_partner.balance < 0 THEN 0 ELSE partial.amount END")
                ),
                balance_select=report._currency_table_apply_rate(
                    SQL("-SIGN(aml_with_partner.balance) * partial.amount")
                ),
                account_code=account_code,
                account_name=account_name,
                journal_name=journal_name,
                column_group_key=column_group_key,
                table_references=query.from_clause,
                currency_table_join=report._currency_table_aml_join(group_options),
                indirectly_linked_aml_partner_clause=indirectly_linked_aml_partner_clause,
                account_alias=SQL.identifier(account_alias),
                search_condition=query.where_clause,
                date_from=group_options['date']['date_from'],
                date_to=group_options['date']['date_to'],
            ))

        query = SQL(" UNION ALL ").join(SQL("(%s)", q) for q in queries)

        if offset:
            query = SQL('%s OFFSET %s', query, offset)
        if limit:
            query = SQL('%s LIMIT %s', query, limit)

        self._cr.execute(query)

        for aml in self._cr.dictfetchall():
            if aml['key'] == 'indirectly_linked_aml':
                if aml['partner_id'] in rslt:
                    rslt[aml['partner_id']].append(aml)
                if None in rslt:
                    rslt[None].append({
                        **aml,
                        'debit': aml['credit'],
                        'credit': aml['debit'],
                        'amount': aml['credit'] - aml['debit'],
                        'balance': -aml['balance'],
                    })
            else:
                rslt[aml['partner_id']].append(aml)

        return rslt
