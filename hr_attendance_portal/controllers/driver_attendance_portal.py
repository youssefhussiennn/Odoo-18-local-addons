# -*- coding: utf-8 -*-
import pytz
import logging
from datetime import datetime

from odoo import http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _parse_local_to_utc(local_datetime_str, tz_name):
    try:
        tz       = pytz.timezone(tz_name)
        naive_dt = datetime.strptime(local_datetime_str, '%Y-%m-%d %H:%M:%S')
        local_dt = tz.localize(naive_dt)
        utc_dt   = local_dt.astimezone(pytz.utc)
        return utc_dt.replace(tzinfo=None)
    except Exception as e:
        _logger.warning('Driver Portal: tz conversion failed (%s). Using UTC.', e)
        return datetime.utcnow()


def _format_local(utc_dt, tz_name):
    try:
        tz       = pytz.timezone(tz_name)
        local_dt = pytz.utc.localize(utc_dt).astimezone(tz)
    except Exception:
        local_dt = utc_dt
    return {
        'time' : local_dt.strftime('%I:%M %p'),
        'date' : local_dt.strftime('%A, %d %B %Y'),
        'full' : local_dt.strftime('%d/%m/%Y %I:%M %p'),
    }


def _detect_browser(user_agent_str):
    ua = (user_agent_str or '').lower()
    if 'edg'    in ua: return 'Edge'
    if 'chrome' in ua and 'safari' in ua: return 'Chrome'
    if 'firefox' in ua: return 'Firefox'
    if 'safari'  in ua: return 'Safari'
    return 'Unknown'


def _get_request_meta():
    ip_address = request.httprequest.remote_addr or ''
    user_agent = request.httprequest.user_agent.string or ''
    return ip_address, _detect_browser(user_agent)


def _verify_employee(code, pin):
    """
    Verify employee by Badge ID (barcode) + PIN.
    Returns employee record or None.
    """
    code = (code or '').strip()
    pin  = (pin or '').strip()
    if not code or not pin:
        return None

    employee = request.env['hr.employee'].sudo().search([
        ('barcode', '=', code),
        ('active', '=', True),
    ], limit=1)

    if not employee:
        return None

    if (employee.pin or '') != pin:
        return None

    return employee


# ─────────────────────────────────────────────────────────────────────────────
# Controller
# ─────────────────────────────────────────────────────────────────────────────

class DriverAttendancePortal(http.Controller):

    # ── Landing page (login form) ───────────────────────────────────────────
    @http.route('/drivers/attendance', type='http', auth='public', website=True)
    def attendance_home(self, **kwargs):
        return request.render('hr_attendance_portal.portal_main', {})

    # ── Verify login (code + PIN) ───────────────────────────────────────────
    @http.route('/drivers/attendance/login', type='json', auth='public', csrf=False)
    def login(self, code=None, pin=None, **kwargs):
        employee = _verify_employee(code, pin)
        if not employee:
            return {'error': 'كود الموظف أو الرقم السري غير صحيح / Invalid code or PIN'}

        return {
            'success'       : True,
            'employee_id'   : employee.id,
            'employee_name' : employee.name,
            'employee_code' : employee.barcode or '',
        }

    # ── Get current status — requires code+pin again for safety ────────────
    @http.route('/drivers/attendance/status', type='json', auth='public', csrf=False)
    def get_status(self, code=None, pin=None, tz_name='UTC', **kwargs):
        employee = _verify_employee(code, pin)
        if not employee:
            return {'error': 'كود الموظف أو الرقم السري غير صحيح / Invalid code or PIN'}

        open_att = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_out',   '=', False),
        ], limit=1, order='check_in desc')

        is_checked_in = bool(open_att)
        check_in_full = None
        if open_att and open_att.check_in:
            fmt           = _format_local(open_att.check_in, tz_name)
            check_in_full = fmt['full']

        return {
            'success'       : True,
            'employee_id'   : employee.id,
            'employee_name' : employee.name,
            'is_checked_in' : is_checked_in,
            'check_in_full' : check_in_full,
        }

    # ── Check IN ─────────────────────────────────────────────────────────────
    @http.route('/drivers/attendance/checkin', type='json', auth='public', csrf=False)
    def check_in(self, code=None, pin=None, latitude=None, longitude=None,
                 location_label='', local_datetime=None, tz_name='UTC',
                 tz_offset=0, **kwargs):

        employee = _verify_employee(code, pin)
        if not employee:
            return {'error': 'كود الموظف أو الرقم السري غير صحيح / Invalid code or PIN'}

        open_att = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_out',   '=', False),
        ], limit=1)
        if open_att:
            return {'error': 'أنت مسجل الحضور بالفعل / Already checked in'}

        utc_now = _parse_local_to_utc(local_datetime, tz_name) \
                  if local_datetime else datetime.utcnow()

        ip_address, browser_name = _get_request_meta()

        vals = {
            'employee_id'        : employee.id,
            'check_in'           : utc_now,
            'check_in_latitude'  : float(latitude)  if latitude  else 0.0,
            'check_in_longitude' : float(longitude) if longitude else 0.0,
            'check_in_location'  : location_label or '',
            'portal_entry'       : True,
            'portal_tz'          : tz_name,
        }

        att_fields = request.env['hr.attendance'].sudo().fields_get()
        if 'in_mode'       in att_fields: vals['in_mode']       = 'manual'
        if 'in_ip_address' in att_fields: vals['in_ip_address'] = ip_address
        if 'in_browser'    in att_fields: vals['in_browser']    = browser_name

        attendance = request.env['hr.attendance'].sudo().with_context(
            tz=tz_name
        ).create(vals)

        local_display = _format_local(utc_now, tz_name)

        _logger.info(
            'Driver Portal CHECK-IN: employee=%s | utc=%s | ip=%s',
            employee.name, utc_now, ip_address,
        )

        return {
            'success'       : True,
            'action'        : 'checkin',
            'message'       : 'تم تسجيل الحضور بنجاح / Checked in successfully',
            'employee_name' : employee.name,
            'attendance_id' : attendance.id,
            'local_time'    : local_display['time'],
            'local_date'    : local_display['date'],
            'local_full'    : local_display['full'],
            'tz_name'       : tz_name,
            'latitude'      : float(latitude)  if latitude  else None,
            'longitude'     : float(longitude) if longitude else None,
        }

    # ── Check OUT ─────────────────────────────────────────────────────────────
    @http.route('/drivers/attendance/checkout', type='json', auth='public', csrf=False)
    def check_out(self, code=None, pin=None, latitude=None, longitude=None,
                  location_label='', local_datetime=None, tz_name='UTC',
                  tz_offset=0, **kwargs):

        employee = _verify_employee(code, pin)
        if not employee:
            return {'error': 'كود الموظف أو الرقم السري غير صحيح / Invalid code or PIN'}

        open_att = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_out',   '=', False),
        ], limit=1, order='check_in desc')

        if not open_att:
            return {'error': 'لا يوجد تسجيل حضور مفتوح / No open check-in found'}

        utc_now = _parse_local_to_utc(local_datetime, tz_name) \
                  if local_datetime else datetime.utcnow()

        ip_address, browser_name = _get_request_meta()

        vals = {
            'check_out'           : utc_now,
            'check_out_latitude'  : float(latitude)  if latitude  else 0.0,
            'check_out_longitude' : float(longitude) if longitude else 0.0,
            'check_out_location'  : location_label or '',
        }

        att_fields = request.env['hr.attendance'].sudo().fields_get()
        if 'out_mode'       in att_fields: vals['out_mode']       = 'manual'
        if 'out_ip_address' in att_fields: vals['out_ip_address'] = ip_address
        if 'out_browser'    in att_fields: vals['out_browser']    = browser_name

        open_att.sudo().with_context(tz=tz_name).write(vals)

        check_in_utc   = open_att.check_in
        worked_seconds = max((utc_now - check_in_utc).total_seconds(), 0)
        hours          = int(worked_seconds // 3600)
        minutes        = int((worked_seconds % 3600) // 60)

        local_display   = _format_local(utc_now, tz_name)
        checkin_display = _format_local(check_in_utc, tz_name)

        _logger.info(
            'Driver Portal CHECK-OUT: employee=%s | worked=%sh%sm | ip=%s',
            employee.name, hours, minutes, ip_address,
        )

        return {
            'success'       : True,
            'action'        : 'checkout',
            'message'       : 'تم تسجيل الانصراف بنجاح / Checked out successfully',
            'employee_name' : employee.name,
            'local_time'    : local_display['time'],
            'local_date'    : local_display['date'],
            'local_full'    : local_display['full'],
            'checkin_local' : checkin_display['full'],
            'worked_hours'  : f'{hours}h {minutes}m',
            'tz_name'       : tz_name,
            'latitude'      : float(latitude)  if latitude  else None,
            'longitude'     : float(longitude) if longitude else None,
        }