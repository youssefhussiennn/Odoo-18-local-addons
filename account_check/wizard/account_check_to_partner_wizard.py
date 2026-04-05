from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class AccountToPartnerCheckWizard(models.TransientModel):
    _name = 'account.to.partner.wizard'
    _description = 'Account To Partner Check Wizard'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner')

    account_id = fields.Many2one(
        comodel_name='account.account',
        string='Account')

    date = fields.Date(
        default=fields.Date.context_today,
        required=True,
    )

    check_id = fields.Many2one(comodel_name='account.check')

    @api.model
    def validate_sell_check(self, check):
        debit_line_diff_vals = {}
        if not check.journal_id.default_account_id:
            raise UserError(
                _('You must selected default debit account on this check Journal.'))

        if check.type == 'third_check':
            if check.state != 'handed':
                raise UserError(
                    _('The selected checks must be in Handed state.'))

        type = 'delivered'
        credit_account = check.journal_id.holding_check_account_id
        debit_account = self.account_id
        name = _('Check "%s" Paid to vendor') % (check.name)

        debit_line_vals = {
            'name': name,
            'account_id': debit_account.id,
            'debit': check.amount,
            'amount_currency': check.amount_currency,
            'partner_id': self.partner_id.id or False
        }
        credit_line_vals = {
            'name': name,
            'account_id': credit_account.id,
            'credit': check.amount,
            'amount_currency': check.amount_currency,
            'partner_id': check.partner_id.id or False
        }

        lines = [(0, False, debit_line_vals), (0, False, credit_line_vals)]

        move_vals = {
            # 'name': name,
            'journal_id': check.journal_id.id,
            'date': self.date,
            'ref': name,
            'move_check_id': check.id,
            'partner_id': check.partner_id.id,
            'line_ids': lines
        }
        return {
            'type': type,
            'move_vals': move_vals,
        }
 
    def action_confirm(self):
        for check in self.env['account.check'].browse(self._context.get('active_ids', [])):

            # validate check and get move vals
            vals = self.validate_sell_check(check)
            type = vals.get('type', {})
            move_vals = vals.get('move_vals')
            move = self.env['account.move'].with_context({}).create(move_vals)
            move.post()
            check.write({'state': type})

            # add operation with move ref
            check._add_operation(type, move, partner=check.partner_id, date=self.date)

            if check.safety_check: 
                # if self.action_type == 'inbank':
                #     account_id = vals.get('account_id')
                #     check.write({'depostin_sefty_account_id': account_id.id})
                # if self.action_type == 'bank_debit':
                name = _('Check "%s" Registered "%s"') % (check.name, "Safty" if check.safety_check else "")
                debit_account = check.journal_id.safty_check_account_id
                if not debit_account:
                    raise ValidationError('Please Check the journal Safty account')
                credit_account = check.partner_id.property_account_receivable_id
                if not credit_account:
                    raise ValidationError('Please Check the partner or partner revceivable account')

                debit_line_vals = {
                    'name': name,
                    'account_id': debit_account.id,
                    'debit': check.amount,
                    'amount_currency': check.amount_currency,
                    'partner_id': check.partner_id and check.partner_id.id or False
                }
                credit_line_vals = {
                    'name': name,
                    'account_id': credit_account.id,
                    'credit': check.amount,
                    'amount_currency': check.amount_currency,
                    'partner_id': check.partner_id and check.partner_id.id or False
                }
                move_vals = {
                    # 'name': name,
                    'journal_id': check.journal_id.id,
                    'date': self.date,
                    'ref': name,
                    'partner_id': check.partner_id.id,
                    'move_check_id': check.id,
                    'line_ids': [
                        (0, False, debit_line_vals),
                        (0, False, credit_line_vals)]
                }
                move = self.env['account.move'].with_context({}).create(move_vals)
                move._post()

                return True
        return True
