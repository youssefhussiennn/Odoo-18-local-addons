import base64

from odoo import api, fields, models, _
from odoo.tools.mimetypes import guess_mimetype
from odoo.exceptions import UserError, ValidationError


class OperationVisitExpenseLine(models.Model):
    _name = 'operation.visit.expense.line'
    _description = 'Operation Visit Expense Line'
    _order = 'expense_id, sequence, id'

    expense_id = fields.Many2one(
        'operation.visit.expense', string='Expense', required=True,
        ondelete='cascade', index=True,
    )
    sequence = fields.Integer(default=10)
    category = fields.Selection(
        [
            ('transportation', 'Transportation'),
            ('fuel', 'Fuel'),
            ('parking', 'Parking'),
            ('accommodation', 'Accommodation'),
            ('other', 'Other'),
        ],
        string='Category', required=True,
    )
    description = fields.Char(string='Description')
    amount = fields.Monetary(string='Amount', required=True, currency_field='currency_id')
    receipt = fields.Binary(string='Receipt', attachment=True, copy=False)
    receipt_filename = fields.Char(string='Receipt File Name', copy=False)

    # Stored for reporting / rules
    visit_id = fields.Many2one(related='expense_id.visit_id', string='Visit', store=True, index=True)
    employee_id = fields.Many2one(related='expense_id.employee_id', string='Employee', store=True)
    partner_id = fields.Many2one(related='expense_id.partner_id', string='Customer', store=True)
    date = fields.Date(related='expense_id.date', string='Date', store=True)
    state = fields.Selection(related='expense_id.state', string='Status', store=True)
    company_id = fields.Many2one(related='expense_id.company_id', string='Company', store=True, index=True)
    currency_id = fields.Many2one(related='expense_id.currency_id', string='Currency')

    @api.constrains('amount')
    def _check_amount(self):
        for line in self:
            if line.amount <= 0:
                raise ValidationError(_('Expense amounts must be greater than zero.'))

    @api.constrains('category', 'description')
    def _check_description(self):
        for line in self:
            if line.category == 'other' and not line.description:
                raise ValidationError(_('Please write a description for "Other" expenses.'))

    def _check_editable(self, expenses):
        # Only server-side code running as superuser (e.g. migrations) may bypass the lock;
        # a context key would be settable by any RPC caller.
        if self.env.su:
            return
        if any(exp.state == 'approved' for exp in expenses):
            raise UserError(_('Lines of approved expenses cannot be changed. Reset to Draft first.'))

    @api.model_create_multi
    def create(self, vals_list):
        expense_ids = {vals.get('expense_id') for vals in vals_list if vals.get('expense_id')}
        self._check_editable(self.env['operation.visit.expense'].browse(list(expense_ids)))
        return super().create(vals_list)

    def write(self, vals):
        self._check_editable(self.mapped('expense_id'))
        return super().write(vals)

    def unlink(self):
        self._check_editable(self.mapped('expense_id'))
        return super().unlink()

    def report_receipt_is_image(self):
        """Used by the visit PDF report to embed receipt photos (not PDFs)."""
        self.ensure_one()
        if not self.receipt:
            return False
        try:
            data = base64.b64decode(self.receipt)
        except (TypeError, ValueError):
            return False
        return guess_mimetype(data).startswith('image/')
