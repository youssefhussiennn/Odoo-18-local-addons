from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    custom_linked_move_id = fields.Many2one(
        comodel_name='account.move',
        string='Linked Journal Entry',
        readonly=True,
        copy=False,
        help="Automatically generated custom journal entry when this payment is posted."
    )

    # action_post is no longer needed since we create the entry on button click instead.
        
    def _create_custom_linked_journal_entry(self):
        """
        Generate a secondary Journal Entry mapping fields from the payment.
        """
        for payment in self:
            
            
            journal = payment.journal_id
            
            # Determine correct AR/AP accounts based on payment direction
            journal = payment.journal_id
            if payment.partner_id:
                if payment.payment_type == 'inbound':
                    debit_account_id = journal.default_account_id.id
                    credit_account_id = payment.partner_id.property_account_receivable_id.id
                if payment.payment_type == 'outbound':
                    credit_account_id = journal.default_account_id.id
                    debit_account_id = payment.partner_id.property_account_payable_id.id
            if payment.payment_type == 'inbound':
                credit_account_id = payment.destination_account_id.id
                debit_account_id = journal.default_account_id.id
                
            if payment.payment_type == 'outbound':
                debit_account_id = payment.destination_account_id.id
                credit_account_id = journal.default_account_id.id
                
                  
                if not debit_account_id or not credit_account_id:
                    raise UserError(_("Could not find appropriate accounts to create the journal entry. Make sure the partner has AR/AP accounts set."))


            currency = payment.currency_id
            company_currency = payment.company_id.currency_id
            
            if currency == company_currency:
                amount_company = payment.amount
                amount_currency = payment.amount
            else:
                amount_company = currency._convert(
                    payment.amount, company_currency, payment.company_id, payment.date
                )
                amount_currency = payment.amount

            # Lines configuration (Debit & Credit)
            line_ids = [
                (0, 0, {
                    'name': payment.memo or _('Custom Entry for %s') % payment.name,
                    'account_id': debit_account_id,
                    'partner_id': payment.partner_id.id,
                    'debit': amount_company,
                    'credit': 0.0,
                    'currency_id': currency.id,
                    'amount_currency': amount_currency,
                }),
                (0, 0, {
                    'name': payment.memo or _('Custom Entry for %s') % payment.name,
                    'account_id': credit_account_id,
                    'partner_id': payment.partner_id.id,
                    'debit': 0.0,
                    'credit': amount_company,
                    'currency_id': currency.id,
                    'amount_currency': -amount_currency,
                }),
            ]

            move_vals = {
                'move_type': 'entry',
                'date': payment.date,
                'journal_id': payment.journal_id.id,
                'ref': payment.memo or _('Linked to: %s') % payment.name,
                'line_ids': line_ids,
            }

            try:
                # Create the secondary journal entry
                new_move = self.env['account.move'].create(move_vals)
                
                # Link the newly created move to the payment record
                payment.custom_linked_move_id = new_move.id
                
                # Optional: Uncomment if the linked move should also be posted automatically
                # new_move.action_post()
            except Exception as e:
                raise UserError(_("An error occurred while generating the custom journal entry: %s") % str(e))

    def button_open_journal_entry(self):
        """
        Override Journal Entry button:
        - If Odoo default entry exists → open it
        - Else → create and open custom draft entry
        """
        self.ensure_one()

        # ✅ Case 1: Standard Odoo entry already exists → open it
        if self.move_id:
            return {
                'name': _('Posted Journal Entry'),
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': self.move_id.id,
                'target': 'current',
            }

        # ✅ Case 2: No standard entry → use custom logic
        if not self.custom_linked_move_id:
            self._create_custom_linked_journal_entry()

        return {
            'name': _('Custom Draft Entry'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.custom_linked_move_id.id,
            'target': 'current',
        }