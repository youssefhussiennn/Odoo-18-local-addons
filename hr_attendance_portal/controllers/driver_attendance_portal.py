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
    """
    Convert a browser local datetime string  →  naive UTC datetime.
    Falls back to datetime.utcnow() on any error.
    """
    try:
        tz       = pytz.timezone(tz_name)
        naive_dt = datetime.strptime(local_datetime_str, '%Y-%m-%d %H:%M:%S')
        local_dt = tz.localize(naive_dt)
        utc_dt   = local_dt.astimezone(pytz.utc)
        return utc_dt.replace(tzinfo=None)          # naive UTC — Odoo standard
    except Exception as e:
        _logger.warning('Driver Portal: tz conversion failed (%s). Using UTC.', e)
        return datetime.utcnow()


def _format_local(utc_dt, tz_name):
    """
    Convert naive UTC datetime  →  formatted strings in driver's local timezone.
    Returns dict with keys: time, date, full, datetime_obj
    """
    try:
        tz       = pytz.timezone(tz_name)
        local_dt = pytz.utc.localize(utc_dt).astimezone(tz)
    except Exception:
        local_dt = utc_dt

    return {
        'time'         : local_dt.strftime('%I:%M %p'),           # 02:30 PM
        'date'         : local_dt.strftime('%A, %d %B %Y'),       # Saturday, 15 June 2026
        'full'         : local_dt.strftime('%d/%m/%Y %I:%M %p'),  # 15/06/2026 02:30 PM
        'datetime_obj' : local_dt,
    }


def _detect_browser(user_agent_str):
    """Extract browser name from User-Agent string."""
    ua = (user_agent_str or '').lower()
    if 'edg' in ua:
        return 'Edge'
    elif 'chrome' in ua and 'safari' in ua:
        return 'Chrome'
    elif 'firefox' in ua:
        return 'Firefox'
    elif 'safari' in ua:
        return 'Safari'
    elif 'opera' in ua or 'opr' in ua:
        return 'Opera'
    return 'Unknown'


def _get_request_meta():
    """Return IP address and browser name from the current HTTP request."""
    ip_address   = request.httprequest.remote_addr or ''
    user_agent   = request.httprequest.user_agent.string or ''
    browser_name = _detect_browser(user_agent)
    return ip_address, browser_name


# ─────────────────────────────────────────────────────────────────────────────
# Controller
# ─────────────────────────────────────────────────────────────────────────────

class DriverAttendancePortal(http.Controller):

    # ── Landing page ─────────────────────────────────────────────────────────
    @http.route('/drivers/attendance', type='http', auth='public', website=True)
    def attendance_home(self, **kwargs):
        return request.render('hr_attendance_portal.portal_main', {})

    # ── Search employee by name or barcode/code ───────────────────────────────
    @http.route('/drivers/attendance/search', type='json', auth='public', csrf=False)
    def search_driver(self, query='', **kwargs):
        query = (query or '').strip()
        if len(query) < 2:
            return {'error': 'Please enter at least 2 characters.'}

        employees = request.env['hr.employee'].sudo().search([
            '|', '|',
            ('name', 'ilike', query),
            ('barcode', '=', query),
            ('pin', '=', query),
            ('active', '=', True),
        ], limit=10)

        return {
            'employees': [
                {
                    'id'         : emp.id,
                    'pin'         : emp.pin or '',
                    'name'       : emp.name,
                    'code'       : emp.barcode or '',
                    'job'        : emp.job_id.name or '',
                    'department' : emp.department_id.name or '',
                }
                for emp in employees
            ]
        }

    # ── Get current attendance status ─────────────────────────────────────────
    @http.route('/drivers/attendance/status', type='json', auth='public', csrf=False)
    def get_status(self, employee_id=None, tz_name='UTC', **kwargs):
        if not employee_id:
            return {'error': 'No employee selected.'}

        employee = request.env['hr.employee'].sudo().browse(int(employee_id))
        if not employee.exists():
            return {'error': 'Employee not found.'}

        open_att = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False),
        ], limit=1, order='check_in desc')

        is_checked_in   = bool(open_att)
        check_in_local  = None
        check_in_full   = None

        if open_att and open_att.check_in:
            fmt            = _format_local(open_att.check_in, tz_name)
            check_in_local = fmt['time']
            check_in_full  = fmt['full']

        return {
            'employee_name'  : employee.name,
            'is_checked_in'  : is_checked_in,
            'attendance_id'  : open_att.id if open_att else None,
            'check_in_time'  : check_in_local,
            'check_in_full'  : check_in_full,
        }

    # ── Check IN ─────────────────────────────────────────────────────────────
    @http.route('/drivers/attendance/checkin', type='json', auth='public', csrf=False)
    def check_in(self, employee_id=None, latitude=None, longitude=None,
                 location_label='', local_datetime=None, tz_name='UTC',
                 tz_offset=0, **kwargs):

        if not employee_id:
            return {'error': 'No employee selected.'}

        employee = request.env['hr.employee'].sudo().browse(int(employee_id))
        if not employee.exists():
            return {'error': 'Employee not found.'}

        # Prevent double check-in
        open_att = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False),
        ], limit=1)
        if open_att:
            return {'error': 'Already checked in. Please check out first.'}

        # Convert browser local time → UTC
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

        # Odoo 18 native kiosk fields (safe — skip if not present)
        att_fields = request.env['hr.attendance'].sudo().fields_get()
        if 'in_mode'       in att_fields: vals['in_mode']       = 'manual'
        if 'in_ip_address' in att_fields: vals['in_ip_address'] = ip_address
        if 'in_browser'    in att_fields: vals['in_browser']    = browser_name

        attendance = request.env['hr.attendance'].sudo().with_context(
            tz=tz_name
        ).create(vals)

        local_display = _format_local(utc_now, tz_name)

        _logger.info(
            'Driver Portal CHECK-IN: employee=%s | utc=%s | local=%s | gps=%s,%s | ip=%s',
            employee.name, utc_now, local_display['full'],
            latitude, longitude, ip_address,
        )

        return {
            'success'       : True,
            'action'        : 'checkin',
            'message'       : f'تم تسجيل الحضور بنجاح',
            'employee_name' : employee.name,
            'attendance_id' : attendance.id,
            'local_time'    : local_display['time'],
            'local_date'    : local_display['date'],
            'local_full'    : local_display['full'],
            'tz_name'       : tz_name,
            'ip'            : ip_address,
            'browser'       : browser_name,
            'latitude'      : float(latitude)  if latitude  else None,
            'longitude'     : float(longitude) if longitude else None,
        }

    # ── Check OUT ─────────────────────────────────────────────────────────────
    @http.route('/drivers/attendance/checkout', type='json', auth='public', csrf=False)
    def check_out(self, employee_id=None, latitude=None, longitude=None,
                  location_label='', local_datetime=None, tz_name='UTC',
                  tz_offset=0, **kwargs):

        if not employee_id:
            return {'error': 'No employee selected.'}

        employee = request.env['hr.employee'].sudo().browse(int(employee_id))
        if not employee.exists():
            return {'error': 'Employee not found.'}

        open_att = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False),
        ], limit=1, order='check_in desc')

        if not open_att:
            return {'error': 'No active check-in found. Please check in first.'}

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

        # Calculate worked hours
        check_in_utc   = open_att.check_in
        worked_seconds = (utc_now - check_in_utc).total_seconds()
        worked_seconds = max(worked_seconds, 0)
        hours          = int(worked_seconds // 3600)
        minutes        = int((worked_seconds % 3600) // 60)

        local_display   = _format_local(utc_now, tz_name)
        checkin_display = _format_local(check_in_utc, tz_name)

        _logger.info(
            'Driver Portal CHECK-OUT: employee=%s | utc=%s | local=%s | worked=%sh%sm | ip=%s',
            employee.name, utc_now, local_display['full'], hours, minutes, ip_address,
        )

        return {
            'success'        : True,
            'action'         : 'checkout',
            'message'        : f'تم تسجيل الانصراف بنجاح',
            'employee_name'  : employee.name,
            'local_time'     : local_display['time'],
            'local_date'     : local_display['date'],
            'local_full'     : local_display['full'],
            'checkin_local'  : checkin_display['full'],
            'checkin_date'   : checkin_display['date'],
            'worked_hours'   : f'{hours}h {minutes}m',
            'worked_h'       : hours,
            'worked_m'       : minutes,
            'tz_name'        : tz_name,
            'ip'             : ip_address,
            'browser'        : browser_name,
            'latitude'       : float(latitude)  if latitude  else None,
            'longitude'      : float(longitude) if longitude else None,
        }