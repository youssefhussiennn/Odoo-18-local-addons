import base64

from markupsafe import Markup

from odoo import Command, api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import format_amount
from odoo.tools.mimetypes import guess_mimetype

# Fields only the workflow actions (start / done / reset) may change.
WORKFLOW_FIELDS = {
    'state', 'start_datetime', 'done_datetime', 'balance_at_visit',
    'location', 'latitude', 'longitude', 'location_accuracy',
}
# Planning fields: editable by non-managers only while the visit is scheduled.
PLANNING_FIELDS = {
    'name', 'visit_date', 'visit_type', 'partner_id', 'employee_id', 'user_id', 'company_id',
}
# Arabic-Indic / Persian digits and separators typed on Arabic phone keyboards.
_DIGITS_MAP = str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹٫٬', '01234567890123456789.,')
PORTAL_FILE_TYPES = ('image/', 'application/pdf')
PORTAL_NOTRACK_CTX = {'mail_notrack': True, 'mail_create_nolog': True, 'tracking_disable': True}


def _business_fields(vals):
    """Ignore technical mail/activity fields written by the chatter."""
    return {
        f for f in vals
        if not f.startswith(('message_', 'activity_', 'website_message'))
    }


class OperationVisit(models.Model):
    _name = 'operation.visit'
    _description = 'Operation Visit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'visit_date desc, id desc'
    _check_company_auto = True
    _rec_names_search = ['name', 'partner_id.name']

    name = fields.Char(string='Visit Name', required=True, tracking=True)
    visit_date = fields.Date(
        string='Visit Date', required=True, tracking=True,
        default=fields.Date.context_today,
    )
    visit_type = fields.Selection(
        [
            ('follow_up', 'Follow Up'),
            ('return', 'Return'),
            ('collection', 'Collection'),
        ],
        string='Visit Type', required=True, default='follow_up', tracking=True,
    )
    partner_id = fields.Many2one(
        'res.partner', string='Customer', required=True, tracking=True, index=True,
        check_company=True,
    )
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True, tracking=True,
        index=True, check_company=True,
        domain="[('is_operation_staff', '=', True)]",
        help='Operations employee who will perform the visit '
             '(employees with "Operations Visits Staff" checked).',
    )
    employee_user_id = fields.Many2one(
        related='employee_id.user_id', string='Employee User', store=True, index=True,
    )
    user_id = fields.Many2one(
        'res.users', string='Assigned By', tracking=True, index=True,
        default=lambda self: self.env.user,
    )
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, index=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency')

    partner_balance = fields.Monetary(
        string='Customer Balance', currency_field='currency_id',
        compute='_compute_partner_balance',
        help='Live balance of the customer: receivable minus payable (posted entries only).',
    )
    balance_at_visit = fields.Monetary(
        string='Balance at Visit', currency_field='currency_id',
        readonly=True, copy=False,
        help='Snapshot of the customer balance when the visit was marked as done.',
    )
    collected_money = fields.Char(string='Collected Money', tracking=True, copy=False)
    notes = fields.Html(string='Notes', help='Instructions from the manager to the employee.')
    employee_notes = fields.Text(
        string='Visit Report', copy=False,
        help='What happened during the visit, written by the employee (also from the portal).',
    )
    attachment_ids = fields.Many2many(
        'ir.attachment', 'operation_visit_ir_attachment_rel',
        'visit_id', 'attachment_id', string='Attachments', copy=False,
    )

    # Location captured when the visit starts
    location = fields.Char(string='Location', readonly=True, copy=False)
    latitude = fields.Float(string='Latitude', digits=(10, 7), readonly=True, copy=False)
    longitude = fields.Float(string='Longitude', digits=(10, 7), readonly=True, copy=False)
    location_accuracy = fields.Float(string='Accuracy (m)', digits=(10, 1), readonly=True, copy=False)
    location_url = fields.Char(string='Map', compute='_compute_location_url')
    start_datetime = fields.Datetime(string='Started At', readonly=True, copy=False)
    done_datetime = fields.Datetime(string='Finished At', readonly=True, copy=False)

    expense_ids = fields.One2many('operation.visit.expense', 'visit_id', string='Expenses')
    expense_count = fields.Integer(compute='_compute_expense_stats', string='Expense Count')
    expense_total = fields.Monetary(
        compute='_compute_expense_stats', string='Total Expenses', currency_field='currency_id',
    )

    state = fields.Selection(
        [
            ('scheduled', 'Scheduled'),
            ('in_progress', 'In Progress'),
            ('done', 'Done'),
        ],
        string='Status', default='scheduled', required=True, tracking=True, copy=False,
    )

    # -------------------------------------------------------------------------
    # Computes / onchanges
    # -------------------------------------------------------------------------
    @api.depends('partner_id', 'company_id')
    def _compute_partner_balance(self):
        self.partner_balance = 0.0
        # Batch per company: one credit/debit query per company instead of per row.
        for company, recs in self.filtered('partner_id').grouped('company_id').items():
            # sudo: credit/debit are restricted to accounting groups
            partners = recs.partner_id.commercial_partner_id.sudo().with_company(company)
            balances = {p.id: p.credit - p.debit for p in partners}
            for rec in recs:
                rec.partner_balance = balances.get(rec.partner_id.commercial_partner_id.id, 0.0)

    @api.depends('expense_ids.amount_total')
    def _compute_expense_stats(self):
        for rec in self:
            rec.expense_count = len(rec.expense_ids)
            rec.expense_total = sum(rec.expense_ids.mapped('amount_total'))

    @api.depends('latitude', 'longitude', 'location')
    def _compute_location_url(self):
        for rec in self:
            rec.location_url = (
                f'https://www.google.com/maps?q={rec.latitude},{rec.longitude}'
                if rec.location else False
            )

    @api.onchange('visit_type')
    def _onchange_visit_type(self):
        if self.visit_type != 'collection':
            self.collected_money = False

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        emp = self.employee_id
        if emp and not emp.user_id and not (emp.barcode and emp.pin):
            return {'warning': {
                'title': _('Employee cannot log in'),
                'message': _(
                    '%s has no Badge ID and/or PIN, so they cannot open "My Visits" '
                    'on the attendance portal. Set them in the employee HR Settings tab.',
                    emp.name,
                ),
            }}

    # -------------------------------------------------------------------------
    # CRUD
    # -------------------------------------------------------------------------
    def _is_visit_manager(self):
        return self.env.su or self.env.user.has_group('atlas_operation_visits.group_visit_manager')

    @api.model_create_multi
    def create(self, vals_list):
        if not self._is_visit_manager():
            for vals in vals_list:
                if WORKFLOW_FIELDS & set(vals):
                    raise UserError(_('Visit status and location can only be set by the visit workflow.'))
        records = super().create(vals_list)
        records._link_attachments()
        return records

    def write(self, vals):
        if not self._is_visit_manager():
            changed = _business_fields(vals)
            if WORKFLOW_FIELDS & changed:
                raise UserError(_('Visit status and location can only be changed with the visit buttons.'))
            for rec in self:
                if rec.state == 'done' and changed:
                    raise UserError(_('Visit %s is done and can no longer be modified.', rec.name))
                if rec.state != 'scheduled' and PLANNING_FIELDS & changed:
                    raise UserError(_('Visit %s has already started; its planning cannot be changed.', rec.name))
        res = super().write(vals)
        if 'attachment_ids' in vals:
            self._link_attachments()
        return res

    def _link_attachments(self):
        """Bind files uploaded through the form to the visit so they also show in the chatter."""
        for rec in self:
            orphans = rec.attachment_ids.filtered(
                lambda a: not a.res_id
                and a.res_model in (False, rec._name)
                and (self.env.su or a.create_uid == self.env.user)
            )
            if orphans:
                orphans.sudo().write({'res_model': rec._name, 'res_id': rec.id})

    # -------------------------------------------------------------------------
    # Shared workflow helpers
    # -------------------------------------------------------------------------
    @api.model
    def _parse_location(self, latitude, longitude, accuracy=None):
        if latitude in (None, '', False) or longitude in (None, '', False):
            raise UserError(_('Location is required to start the visit. / يجب تفعيل الموقع لبدء الزيارة'))
        try:
            lat, lng = float(latitude), float(longitude)
            acc = float(accuracy or 0.0)
        except (TypeError, ValueError):
            raise ValidationError(_('Invalid location received from the browser. / موقع غير صالح'))
        if not (-90 <= lat <= 90 and -180 <= lng <= 180) or (lat == 0 and lng == 0):
            raise ValidationError(_('Invalid location received from the browser. / موقع غير صالح'))
        return lat, lng, acc

    def _start_vals(self, lat, lng, acc):
        return {
            'state': 'in_progress',
            'start_datetime': fields.Datetime.now(),
            'latitude': lat,
            'longitude': lng,
            'location_accuracy': acc,
            'location': f'{lat:.6f}, {lng:.6f}',
        }

    def _start_message(self):
        return Markup('%s <a href="%s" target="_blank">%s</a>') % (
            _('Visit started at location:'), self.location_url, self.location,
        )

    def _check_done_allowed(self):
        for rec in self:
            if rec.state != 'in_progress':
                raise UserError(_('Visit %s must be In Progress before marking it as Done.', rec.name))
            if rec.visit_type == 'collection' and not rec.collected_money:
                raise UserError(_(
                    'Please enter the collected money for visit %s. / يرجى إدخال المبلغ المحصل',
                    rec.name,
                ))

    def _done_vals(self):
        return {
            'state': 'done',
            'done_datetime': fields.Datetime.now(),
            'balance_at_visit': self.partner_balance,
        }

    # -------------------------------------------------------------------------
    # Backend actions
    # -------------------------------------------------------------------------
    def action_view_expenses(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Expenses'),
            'res_model': 'operation.visit.expense',
            'view_mode': 'list,form',
            'domain': [('visit_id', '=', self.id)],
            'context': {'default_visit_id': self.id},
        }

    def _check_can_act(self):
        if self._is_visit_manager():
            return
        for rec in self:
            if rec.employee_user_id != self.env.user:
                raise UserError(_('Only the assigned employee can update visit %s.', rec.name))

    def action_start(self, latitude=None, longitude=None, accuracy=None):
        """Called from the backend JS button with the browser GPS position."""
        self.ensure_one()
        self._check_can_act()
        if self.state != 'scheduled':
            raise UserError(_('Only scheduled visits can be started.'))
        lat, lng, acc = self._parse_location(latitude, longitude, accuracy)
        # sudo: workflow fields are protected against direct writes by employees
        self.sudo().write(self._start_vals(lat, lng, acc))
        self.message_post(body=self._start_message())
        return True

    def action_done(self):
        self._check_can_act()
        self._check_done_allowed()
        for rec in self:
            rec.sudo().write(rec._done_vals())
        return True

    def action_reset_scheduled(self):
        if not self._is_visit_manager():
            raise UserError(_('Only Operation Visits managers can reset visits.'))
        self.write({
            'state': 'scheduled',
            'start_datetime': False,
            'done_datetime': False,
            'balance_at_visit': 0.0,
            'location': False,
            'latitude': 0.0,
            'longitude': 0.0,
            'location_accuracy': 0.0,
        })
        return True

    # -------------------------------------------------------------------------
    # Attendance portal (employees without Odoo users)
    # Called by the controller in sudo; every method re-checks the employee.
    # -------------------------------------------------------------------------
    def _portal_check(self, employee):
        self.ensure_one()
        if not employee or not employee.is_operation_staff or self.employee_id != employee:
            raise UserError(_('This visit is not assigned to you. / هذه الزيارة غير مخصصة لك'))

    def _portal_post(self, employee, body, attachment_ids=None):
        self.message_post(
            body=body,
            author_id=employee.work_contact_id.id or False,
            message_type='comment',
            subtype_xmlid='mail.mt_note',
            attachment_ids=attachment_ids or [],
        )

    @api.model
    def _portal_check_file(self, name, data):
        mimetype = guess_mimetype(data)
        if not mimetype.startswith(PORTAL_FILE_TYPES):
            raise UserError(_(
                'File "%s" is not allowed. Upload photos or PDF only. / '
                'مسموح بالصور أو ملفات PDF فقط', name,
            ))

    @api.model
    def _portal_parse_amount(self, amount):
        text = str(amount or '').translate(_DIGITS_MAP).replace(',', '').strip()
        try:
            value = float(text)
        except ValueError:
            raise UserError(_('Please enter a valid amount. / يرجى إدخال مبلغ صحيح'))
        if value <= 0:
            raise UserError(_('Amount must be greater than zero. / المبلغ يجب أن يكون أكبر من صفر'))
        return value

    def portal_start(self, employee, latitude, longitude, accuracy=None):
        self._portal_check(employee)
        if self.state != 'scheduled':
            raise UserError(_('This visit has already started. / تم بدء هذه الزيارة بالفعل'))
        lat, lng, acc = self._parse_location(latitude, longitude, accuracy)
        self.with_context(**PORTAL_NOTRACK_CTX).write(self._start_vals(lat, lng, acc))
        self._portal_post(employee, self._start_message())

    def portal_update(self, employee, employee_notes=None, collected_money=None, files=None):
        self._portal_check(employee)
        if self.state == 'done':
            raise UserError(_('This visit is done and can no longer be changed. / الزيارة منتهية'))
        vals = {}
        if employee_notes is not None:
            notes = employee_notes.strip()
            if notes != (self.employee_notes or ''):
                vals['employee_notes'] = notes or False
        if (
            collected_money is not None
            and self.visit_type == 'collection'
            and self.state == 'in_progress'
        ):
            money = collected_money.strip()
            if money != (self.collected_money or ''):
                vals['collected_money'] = money or False
        if vals:
            self.with_context(**PORTAL_NOTRACK_CTX).write(vals)
        if 'collected_money' in vals:
            self._portal_post(employee, _('Collected money: %s', vals['collected_money'] or '-'))
        if files:
            for name, data in files:
                self._portal_check_file(name, data)
            attachments = self.env['ir.attachment'].create([{
                'name': name,
                'raw': data,
                'res_model': self._name,
                'res_id': self.id,
            } for name, data in files])
            self.with_context(**PORTAL_NOTRACK_CTX).write({
                'attachment_ids': [Command.link(a.id) for a in attachments],
            })
            self._portal_post(
                employee, _('%s file(s) uploaded from the portal.', len(attachments)),
                attachment_ids=attachments.ids,
            )

    def portal_done(self, employee):
        self._portal_check(employee)
        self._check_done_allowed()
        self.with_context(**PORTAL_NOTRACK_CTX).write(self._done_vals())
        body = _('Visit finished.')
        if self.visit_type == 'collection':
            body = _('Visit finished. Collected money: %s', self.collected_money)
        self._portal_post(employee, body)

    def portal_add_expense(self, employee, category, amount, description=None, receipt=None):
        self._portal_check(employee)
        Line = self.env['operation.visit.expense.line']
        categories = dict(Line._fields['category'].selection)
        if category not in categories:
            raise UserError(_('Please choose the expense type. / يرجى اختيار نوع المصروف'))
        value = self._portal_parse_amount(amount)
        description = (description or '').strip()
        if category == 'other' and not description:
            raise UserError(_('Please write a description for "Other". / يرجى كتابة وصف للمصروف'))
        expense = self.expense_ids.filtered(lambda e: e.state == 'draft').sorted('id')[-1:]
        if not expense:
            expense = self.env['operation.visit.expense'].with_context(**PORTAL_NOTRACK_CTX).create({
                'visit_id': self.id,
                'date': fields.Date.context_today(self.with_context(tz=employee.tz or 'Africa/Cairo')),
            })
        vals = {
            'expense_id': expense.id,
            'category': category,
            'amount': value,
            'description': description or False,
        }
        if receipt:
            name, data = receipt
            self._portal_check_file(name, data)
            vals.update(receipt=base64.b64encode(data), receipt_filename=name)
        Line.with_context(**PORTAL_NOTRACK_CTX).create(vals)
        self._portal_post(employee, _(
            'Expense added (%(ref)s): %(category)s %(amount)s%(desc)s',
            ref=expense.name, category=categories[category],
            amount=format_amount(self.env, value, self.currency_id),
            desc=f' — {description}' if description else '',
        ))

    def portal_remove_expense_line(self, employee, line_id):
        self._portal_check(employee)
        line = self.env['operation.visit.expense.line'].browse(int(line_id)).exists()
        if not line or line.expense_id.visit_id != self:
            raise UserError(_('Expense line not found. / المصروف غير موجود'))
        expense = line.expense_id
        if expense.state != 'draft':
            raise UserError(_('Approved expenses cannot be changed. / لا يمكن تعديل مصروف معتمد'))
        line.unlink()
        if not expense.line_ids:
            expense.unlink()
