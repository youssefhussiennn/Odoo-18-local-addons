# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    require_company_location = fields.Boolean(
        string='Must Check In From Company Location',
        default=False,
        help='If enabled, this employee can only check in/out from within the '
             'company location radius. Leave unchecked for drivers and field '
             'staff who work off-site.',
    )


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    # GPS Check-In
    check_in_latitude = fields.Float(string='Check-In Latitude', digits=(10, 7))
    check_in_longitude = fields.Float(string='Check-In Longitude', digits=(10, 7))
    check_in_location = fields.Char(string='Check-In Location')

    # GPS Check-Out
    check_out_latitude = fields.Float(string='Check-Out Latitude', digits=(10, 7))
    check_out_longitude = fields.Float(string='Check-Out Longitude', digits=(10, 7))
    check_out_location = fields.Char(string='Check-Out Location')

    # Portal Meta
    portal_entry = fields.Boolean(string='Via Driver Portal', default=False)
    portal_tz = fields.Char(string='Driver Timezone')

    # Mission (مأمورية)
    is_mission = fields.Boolean(
        string='Mission (مأمورية)',
        default=False,
        help='Checked when the employee registered attendance as a mission '
             '(off-site work), bypassing the company location geofence.',
    )

    # Maps Links (computed)
    check_in_maps_url = fields.Char(string='Check-In Maps Link', compute='_compute_maps_urls')
    check_out_maps_url = fields.Char(string='Check-Out Maps Link', compute='_compute_maps_urls')

    @api.depends('check_in_latitude', 'check_in_longitude',
                 'check_out_latitude', 'check_out_longitude')
    def _compute_maps_urls(self):
        for rec in self:
            if rec.check_in_latitude and rec.check_in_longitude:
                rec.check_in_maps_url = (
                    f'https://www.google.com/maps?q={rec.check_in_latitude},{rec.check_in_longitude}'
                )
            else:
                rec.check_in_maps_url = False

            if rec.check_out_latitude and rec.check_out_longitude:
                rec.check_out_maps_url = (
                    f'https://www.google.com/maps?q={rec.check_out_latitude},{rec.check_out_longitude}'
                )
            else:
                rec.check_out_maps_url = False