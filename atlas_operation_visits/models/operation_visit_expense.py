from odoo import api, fields, models, _
from odoo.exceptions import UserError

# Business fields locked once the expense is approved.
LOCKED_FIELDS = {'visit_id', 'date', 'line_ids', 'notes'}
# Fields only managers may set (through Approve / Reset to Draft).
APPROVAL_FIELDS = {'state', 'approved_by_id', 'approved_date'}


class OperationVisitExpense(models.Model):
    _name = 'operation.visit.expense'
    _description = 'Operation Visit Expense'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'
    _check_company_auto = True

    name = fields.Char(
        string='Reference', required=True, copy=False, readonly=True,
        default=lambda self: _('New'),
    )
    visit_id = fields.Many2one(
        'operation.visit', string='Visit', required=True, index=True,
        ondelete='restrict', tracking=True,
    )
    partner_id = fields.Many2one(related='visit_id.partner_id', string='Customer', store=True)
    employee_id = fields.Many2one(related='visit_id.employee_id', string='Employee', store=True)
    employee_user_id = fields.Many2one(
        related='visit_id.employee_user_id', string='Employee User', store=True, index=True,
    )
    company_id = fields.Many2one(
        related='visit_id.company_id', string='Company', store=True, index=True,
    )
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency')

    date = fields.Date(
        string='Date', required=True, tracking=True, default=fields.Date.context_today,
    )
    line_ids = fields.One2many(
        'operation.visit.expense.line', 'expense_id', string='Expense Lines', copy=True,
    )
    line_count = fields.Integer(compute='_compute_line_count', string='Items')
    amount_total = fields.Monetary(
        string='Total', compute='_compute_amount_total', store=True,
        currency_field='currency_id', tracking=True,
    )
    notes = fields.Text(string='Notes')
    state = fields.Selection(
        [('draft', 'Draft'), ('approved', 'Approved')],
        string='Status', default='draft', required=True, tracking=True, copy=False,
    )
    approved_by_id = fields.Many2one('res.users', string='Approved By', readonly=True, copy=False)
    approved_date = fields.Datetime(string='Approved On', readonly=True, copy=False)

    @api.depends('line_ids.amount')
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = sum(rec.line_ids.mapped('amount'))

    @api.depends('line_ids')
    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)

    def _is_visit_manager(self):
        return self.env.su or self.env.user.has_group('atlas_operation_visits.group_visit_manager')

    @api.model_create_multi
    def create(self, vals_list):
        is_manager = self._is_visit_manager()
        for vals in vals_list:
            if not is_manager and (
                vals.get('state', 'draft') != 'draft'
                or vals.get('approved_by_id') or vals.get('approved_date')
            ):
                raise UserError(_('Only Operation Visits managers can approve expenses.'))
            if not vals.get('name') or vals['name'] == _('New'):
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('operation.visit.expense') or _('New')
                )
        return super().create(vals_list)

    def write(self, vals):
        if APPROVAL_FIELDS & set(vals) and not self._is_visit_manager():
            raise UserError(_('Only Operation Visits managers can approve or reset expenses.'))
        if (
            not self.env.su
            and LOCKED_FIELDS & set(vals)
            and any(rec.state == 'approved' for rec in self)
        ):
            raise UserError(_('Approved expenses cannot be modified. Reset to Draft first.'))
        return super().write(vals)

    def unlink(self):
        if any(rec.state == 'approved' for rec in self):
            raise UserError(_('Approved expenses cannot be deleted.'))
        return super().unlink()

    def _check_manager(self):
        if not self._is_visit_manager():
            raise UserError(_('Only Operation Visits managers can approve or reset expenses.'))

    def action_approve(self):
        self._check_manager()
        to_approve = self.filtered(lambda r: r.state == 'draft')
        for rec in to_approve:
            if not rec.line_ids:
                raise UserError(_('Expense %s has no lines to approve.', rec.name))
        to_approve.write({
            'state': 'approved',
            'approved_by_id': self.env.user.id,
            'approved_date': fields.Datetime.now(),
        })
        return True

    def action_reset_draft(self):
        self._check_manager()
        self.filtered(lambda r: r.state == 'approved').write({
            'state': 'draft',
            'approved_by_id': False,
            'approved_date': False,
        })
        return True
