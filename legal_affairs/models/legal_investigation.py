from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import date


class LegalInvestigation(models.Model):
    _name = 'legal.investigation'
    _description = 'Employee Investigation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'investigation_date desc'
    _rec_name = 'name'

    # ── Identity ──────────────────────────────────────────────────────────────
    name = fields.Char(
        string='Reference', readonly=True, copy=False,
        default='New'
    )
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True, tracking=True
    )
    department_id = fields.Many2one(
        'hr.department', string='Department',
        related='employee_id.department_id', store=True
    )
    investigation_date = fields.Date(
        string='Investigation Date', default=fields.Date.today, tracking=True
    )

    # ── Description ───────────────────────────────────────────────────────────
    description = fields.Html(string='Investigation Details')

    # ── Penalty ───────────────────────────────────────────────────────────────
    has_penalty = fields.Boolean(string='Has Penalty?', tracking=True)
    penalty_type = fields.Selection([
        ('warning', 'Warning'),
        ('deduction', 'Salary Deduction'),
        ('termination', 'Termination'),
    ], string='Penalty Type', tracking=True)
    penalty_days = fields.Float(
        string='Deduction Days',
        help='Number of days to deduct from salary'
    )
    penalty_description = fields.Char(string='Penalty Details', tracking=True)

    # ── State ─────────────────────────────────────────────────────────────────
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
    ], string='Status', default='draft', tracking=True)

    hr_notified = fields.Boolean(string='HR Notified', readonly=True)
    payslip_input_id = fields.Many2one(
        'hr.payslip.input', string='Payslip Input', readonly=True
    )

    # ── Constraints ───────────────────────────────────────────────────────────
    @api.constrains('has_penalty', 'penalty_type')
    def _check_penalty_type(self):
        for rec in self:
            if rec.has_penalty and not rec.penalty_type:
                raise ValidationError('Please select a penalty type.')

    @api.constrains('penalty_type', 'penalty_days')
    def _check_penalty_days(self):
        for rec in self:
            if rec.penalty_type == 'deduction' and rec.penalty_days <= 0:
                raise ValidationError(
                    'Deduction days must be greater than zero.'
                )

    # ── ORM ───────────────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'legal.investigation'
                ) or 'New'
        return super().create(vals_list)

    # ── Actions ───────────────────────────────────────────────────────────────
    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_close(self):
        for rec in self:
            if rec.state != 'in_progress':
                raise UserError('Only in-progress investigations can be closed.')
            rec.write({'state': 'closed'})
            if rec.has_penalty:
                rec._apply_penalty()

    def action_reset_draft(self):
        self.write({'state': 'draft', 'hr_notified': False})

    # ── Penalty Logic ─────────────────────────────────────────────────────────
    def _apply_penalty(self):
        self.ensure_one()
        employee = self.employee_id

        if self.penalty_type == 'warning':
            # Post a note on the employee record
            employee.message_post(
                body=(
                    f'⚠️ <b>Warning Penalty</b> issued via investigation '
                    f'<a href="#">{self.name}</a>.<br/>'
                    f'Details: {self.penalty_description or "N/A"}'
                ),
                subject=f'Warning - {self.name}',
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )
            self.hr_notified = True

        elif self.penalty_type == 'deduction':
            self._create_payroll_input()
            self.hr_notified = True

        elif self.penalty_type == 'termination':
            # Post a termination note and notify HR manager via activity
            employee.message_post(
                body=(
                    f'🔴 <b>Termination Penalty</b> issued via investigation '
                    f'<a href="#">{self.name}</a>.<br/>'
                    f'Details: {self.penalty_description or "N/A"}<br/>'
                    f'<b>Action required: Process termination in HR.</b>'
                ),
                subject=f'Termination Notice - {self.name}',
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )
            # Create activity for HR manager
            hr_manager_group = self.env.ref('hr.group_hr_manager')
            hr_managers = hr_manager_group.users
            for manager in hr_managers:
                employee.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=manager.id,
                    summary=f'Termination: {employee.name} — {self.name}',
                    note=(
                        f'Investigation {self.name} has been closed with a '
                        f'Termination penalty. Please process the employee '
                        f'termination accordingly.'
                    ),
                )
            self.hr_notified = True

    def _create_payroll_input(self):
        """Find existing payslip or create a new draft one, then add input."""
        self.ensure_one()
        today = date.today()
        employee = self.employee_id

        # Date range: first and last day of current month
        date_from = today.replace(day=1)
        if today.month == 12:
            date_to = today.replace(day=31)
        else:
            date_to = today.replace(month=today.month + 1, day=1).replace(
                day=1
            ) - __import__('datetime').timedelta(days=1)

        input_type = self.env.ref('legal_affairs.input_type_legal_deduction')

        # Find existing draft payslip for this employee this month
        payslip = self.env['hr.payslip'].search([
            ('employee_id', '=', employee.id),
            ('state', 'in', ['draft', 'verify']),
            ('date_from', '<=', today),
            ('date_to', '>=', today),
        ], limit=1)

        if not payslip:
            # Auto-create a draft payslip for this month
            payslip = self.env['hr.payslip'].create({
                'employee_id': employee.id,
                'date_from': date_from,
                'date_to': date_to,
                'name': f'Payslip {employee.name} - {today.strftime("%B %Y")}',
            })
            payslip.message_post(
                body=(
                    f'📋 Payslip auto-created by Legal Affairs module '
                    f'for investigation {self.name}.'
                )
            )

        # Add the deduction input line
        input_line = self.env['hr.payslip.input'].create({
            'payslip_id': payslip.id,
            'input_type_id': input_type.id,
            'amount': self.penalty_days,
            'name': f'Legal Penalty Deduction — {self.name}',
        })
        self.payslip_input_id = input_line.id

        payslip.message_post(
            body=(
                f'💰 <b>Salary deduction of {self.penalty_days} days</b> '
                f'automatically added from Legal Investigation '
                f'<b>{self.name}</b>.<br/>'
                f'Reason: {self.penalty_description or "N/A"}'
            )
        )
        # Also notify on employee chatter
        employee.message_post(
            body=(
                f'💰 <b>Salary Deduction Penalty Applied</b>: '
                f'{self.penalty_days} days deducted via investigation '
                f'<b>{self.name}</b>.<br/>'
                f'Payslip: <b>{payslip.name}</b> — '
                f'check Payroll to review.'
            ),
            subject=f'Penalty Deduction Applied — {self.name}',
            message_type='comment',
            subtype_xmlid='mail.mt_note',
        )
