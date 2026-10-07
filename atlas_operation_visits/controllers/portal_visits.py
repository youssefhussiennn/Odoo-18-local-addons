# -*- coding: utf-8 -*-
"""'My Visits' pages on the driver attendance portal.

Operations employees have no Odoo users. They log in on /drivers/attendance with
badge code + PIN (hr_attendance_portal); when the employee is flagged
"Operations Visits Staff", the login also stores their id in the HTTP session
for SESSION_TTL seconds. Every visits route reads the employee from the session
only, and every record is re-checked against that employee in the model.
"""
import logging
import time
from datetime import timedelta
from urllib.parse import quote_plus

import pytz

from odoo import fields, http
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
from odoo.tools import format_amount

from odoo.addons.hr_attendance_portal.controllers.driver_attendance_portal import (
    DriverAttendancePortal,
)

_logger = logging.getLogger(__name__)

SESSION_KEY = 'atlas_visit_portal'
FLASH_KEY = 'atlas_visit_portal_flash'
SESSION_TTL = 12 * 3600          # seconds
MAX_FILE_SIZE = 10 * 1024 * 1024  # bytes per file
DEFAULT_TZ = 'Africa/Cairo'
DONE_DAYS = 7                    # finished visits kept on the list

TYPE_LABELS = {
    'follow_up': 'متابعة · Follow Up',
    'return': 'مرتجع · Return',
    'collection': 'تحصيل · Collection',
}
STATE_LABELS = {
    'scheduled': 'مجدولة · Scheduled',
    'in_progress': 'جارية · In Progress',
    'done': 'منتهية · Done',
}
EXPENSE_STATE_LABELS = {
    'draft': 'قيد المراجعة · Pending',
    'approved': 'معتمد · Approved',
}
CATEGORY_LABELS = [
    ('transportation', 'مواصلات · Transportation'),
    ('fuel', 'بنزين · Fuel'),
    ('parking', 'انتظار · Parking'),
    ('accommodation', 'إقامة · Accommodation'),
    ('other', 'أخرى · Other'),
]


class DriverAttendancePortalVisits(DriverAttendancePortal):

    @http.route()
    def login(self, code=None, pin=None, **kwargs):
        res = super().login(code=code, pin=pin, **kwargs)
        # Any login attempt on this device ends the previous visits session.
        request.session.pop(SESSION_KEY, None)
        if isinstance(res, dict) and res.get('success'):
            employee = request.env['hr.employee'].sudo().browse(res['employee_id'])
            if employee.is_operation_staff:
                request.session[SESSION_KEY] = {
                    'employee_id': employee.id,
                    'ts': int(time.time()),
                }
                res['visits_url'] = '/drivers/visits'
        return res


class OperationVisitPortal(http.Controller):

    # ------------------------------------------------------------------ helpers
    def _employee(self):
        data = request.session.get(SESSION_KEY)
        if not data:
            return None
        if int(time.time()) - int(data.get('ts') or 0) > SESSION_TTL:
            request.session.pop(SESSION_KEY, None)
            return None
        employee = request.env['hr.employee'].sudo().browse(data.get('employee_id')).exists()
        if not employee or not employee.active or not employee.is_operation_staff:
            request.session.pop(SESSION_KEY, None)
            return None
        return employee

    def _visit(self, employee, visit_id):
        visit = request.env['operation.visit'].sudo().browse(int(visit_id)).exists()
        if not visit or visit.employee_id != employee:
            return None
        return visit

    def _flash(self, kind, message):
        request.session[FLASH_KEY] = [kind, message]

    def _login_redirect(self):
        return request.redirect('/drivers/attendance')

    def _read_files(self, field_name):
        files = []
        for storage in request.httprequest.files.getlist(field_name):
            if not storage or not storage.filename:
                continue
            data = storage.read()
            if not data:
                continue
            if len(data) > MAX_FILE_SIZE:
                raise UserError(
                    f'الملف "{storage.filename}" أكبر من 10 ميجا / '
                    f'File "{storage.filename}" is larger than 10 MB'
                )
            files.append((storage.filename, data))
        return files

    def _run(self, visit_id, func, ok_message=None):
        """Run a visit action for the logged-in employee and redirect back."""
        employee = self._employee()
        if not employee:
            return self._login_redirect()
        visit = self._visit(employee, visit_id)
        if not visit:
            self._flash('err', 'الزيارة غير موجودة / Visit not found')
            return request.redirect('/drivers/visits')
        try:
            with request.env.cr.savepoint():
                func(employee, visit)
        except (UserError, ValidationError) as e:
            self._flash('err', str(e))
        except Exception:
            _logger.exception('Visits portal: action failed on visit %s', visit.id)
            self._flash('err', 'حدث خطأ، حاول مرة أخرى / Something went wrong, please try again')
        else:
            if ok_message:
                self._flash('ok', ok_message)
        return request.redirect(f'/drivers/visits/{visit.id}')

    def _base_values(self, employee):
        tz = pytz.timezone(employee.tz or DEFAULT_TZ)

        def fmt_dt(value):
            if not value:
                return ''
            return pytz.utc.localize(value).astimezone(tz).strftime('%d/%m/%Y %I:%M %p')

        def fmt_date(value):
            return value.strftime('%d/%m/%Y') if value else ''

        def fmt_money(amount, currency):
            return format_amount(request.env, amount or 0.0, currency)

        return {
            'employee': employee,
            'flash': request.session.pop(FLASH_KEY, None),
            'today': fields.Date.context_today(employee.with_context(tz=tz.zone)),
            'type_labels': TYPE_LABELS,
            'state_labels': STATE_LABELS,
            'expense_state_labels': EXPENSE_STATE_LABELS,
            'category_labels': CATEGORY_LABELS,
            'category_dict': dict(CATEGORY_LABELS),
            'fmt_dt': fmt_dt,
            'fmt_date': fmt_date,
            'fmt_money': fmt_money,
        }

    # ------------------------------------------------------------------ pages
    @http.route('/drivers/visits', type='http', auth='public', methods=['GET'], sitemap=False)
    def visits_list(self, **kw):
        employee = self._employee()
        if not employee:
            return self._login_redirect()
        Visit = request.env['operation.visit'].sudo()
        domain = [('employee_id', '=', employee.id)]
        values = self._base_values(employee)
        values.update({
            'page_title': 'زياراتي · My Visits',
            'in_progress': Visit.search(domain + [('state', '=', 'in_progress')],
                                        order='start_datetime asc, id asc'),
            'scheduled': Visit.search(domain + [('state', '=', 'scheduled')],
                                      order='visit_date asc, id asc'),
            'done_recent': Visit.search(
                domain + [
                    ('state', '=', 'done'),
                    ('done_datetime', '>=', fields.Datetime.now() - timedelta(days=DONE_DAYS)),
                ],
                order='done_datetime desc', limit=30,
            ),
        })
        return request.render('atlas_operation_visits.portal_visits_list', values)

    @http.route('/drivers/visits/<int:visit_id>', type='http', auth='public', methods=['GET'], sitemap=False)
    def visit_detail(self, visit_id, **kw):
        employee = self._employee()
        if not employee:
            return self._login_redirect()
        visit = self._visit(employee, visit_id)
        if not visit:
            self._flash('err', 'الزيارة غير موجودة / Visit not found')
            return request.redirect('/drivers/visits')
        partner = visit.partner_id
        address = ', '.join(filter(None, [
            partner.street, partner.street2, partner.city,
            partner.state_id.name, partner.country_id.name,
        ]))
        if partner.partner_latitude and partner.partner_longitude:
            customer_map = (f'https://www.google.com/maps?q='
                            f'{partner.partner_latitude},{partner.partner_longitude}')
        elif address:
            customer_map = f'https://www.google.com/maps/search/?api=1&query={quote_plus(address)}'
        else:
            customer_map = False
        values = self._base_values(employee)
        values.update({
            'page_title': visit.name,
            'visit': visit,
            'partner': partner,
            'customer_map': customer_map,
            'customer_address': address,
            'expense_lines': visit.expense_ids.line_ids.sorted(lambda l: (l.date, l.id), reverse=True),
            'expense_total': sum(visit.expense_ids.mapped('amount_total')),
        })
        return request.render('atlas_operation_visits.portal_visit_detail', values)

    # ------------------------------------------------------------------ actions
    @http.route('/drivers/visits/<int:visit_id>/start', type='http', auth='public',
                methods=['POST'], sitemap=False)
    def visit_start(self, visit_id, latitude=None, longitude=None, accuracy=None, **kw):
        return self._run(
            visit_id,
            lambda emp, visit: visit.portal_start(emp, latitude, longitude, accuracy),
            'تم بدء الزيارة وتسجيل الموقع / Visit started and location saved',
        )

    @http.route('/drivers/visits/<int:visit_id>/save', type='http', auth='public',
                methods=['POST'], sitemap=False)
    def visit_save(self, visit_id, employee_notes=None, collected_money=None, action=None, **kw):
        finish = action == 'done'

        def _do(emp, visit):
            visit.portal_update(
                emp, employee_notes=employee_notes, collected_money=collected_money,
                files=self._read_files('attachments'),
            )
            if finish:
                visit.portal_done(emp)

        return self._run(
            visit_id, _do,
            'تم إنهاء الزيارة / Visit finished' if finish else 'تم الحفظ / Saved',
        )

    @http.route('/drivers/visits/<int:visit_id>/expense/add', type='http', auth='public',
                methods=['POST'], sitemap=False)
    def expense_add(self, visit_id, category=None, amount=None, description=None, **kw):
        def _do(emp, visit):
            files = self._read_files('receipt')
            visit.portal_add_expense(emp, category, amount, description,
                                     receipt=files[0] if files else None)

        return self._run(visit_id, _do, 'تم إضافة المصروف / Expense added')

    @http.route('/drivers/visits/<int:visit_id>/expense/<int:line_id>/delete', type='http',
                auth='public', methods=['POST'], sitemap=False)
    def expense_delete(self, visit_id, line_id, **kw):
        return self._run(
            visit_id,
            lambda emp, visit: visit.portal_remove_expense_line(emp, line_id),
            'تم حذف المصروف / Expense removed',
        )

    @http.route('/drivers/visits/logout', type='http', auth='public',
                methods=['GET', 'POST'], csrf=False, sitemap=False)
    def visits_logout(self, **kw):
        request.session.pop(SESSION_KEY, None)
        request.session.pop(FLASH_KEY, None)
        return self._login_redirect()
