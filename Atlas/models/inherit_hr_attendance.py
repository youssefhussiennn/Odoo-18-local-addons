# -*- coding: utf-8 -*-
from odoo import models, fields


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    # ── GPS Check-In ──────────────────────────────────────────────────────────
    check_in_latitude   = fields.Float(
        string='Check-In Latitude',
        digits=(10, 7),
    )
    check_in_longitude  = fields.Float(
        string='Check-In Longitude',
        digits=(10, 7),
    )
    check_in_location   = fields.Char(
        string='Check-In Location',
    )

    # ── GPS Check-Out ─────────────────────────────────────────────────────────
    check_out_latitude  = fields.Float(
        string='Check-Out Latitude',
        digits=(10, 7),
    )
    check_out_longitude = fields.Float(
        string='Check-Out Longitude',
        digits=(10, 7),
    )
    check_out_location  = fields.Char(
        string='Check-Out Location',
    )

    # ── Portal Meta ───────────────────────────────────────────────────────────
    portal_entry        = fields.Boolean(
        string='Via Driver Portal',
        default=False,
    )
    portal_tz           = fields.Char(
        string='Driver Timezone',
    )