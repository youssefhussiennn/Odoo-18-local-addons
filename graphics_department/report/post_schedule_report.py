# -*- coding: utf-8 -*-
import calendar
from datetime import timedelta, datetime
from io import BytesIO

import pytz

from odoo import models

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas


NAVY = HexColor('#1e3a5f')
BLUE = HexColor('#3b82f6')
GREY = HexColor('#6b7280')
LIGHT = HexColor('#f8f9fb')
DARK = HexColor('#111827')

PERIOD_LABEL = {'day': 'Daily', 'week': 'Weekly', 'month': 'Monthly'}

STATE_COLOR = {
    'draft': '#3b82f6',
    'posted': '#16a34a',
    'cancelled': '#9ca3af',
}
STATE_LABEL = {
    'draft': 'Scheduled',
    'posted': 'Posted',
    'cancelled': 'Cancelled',
}


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        report = self._get_report(report_ref)
        if report.report_name == 'graphics_department.post_schedule_pdf':
            return self._render_post_schedule(res_ids)
        return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)

    # -- data ------------------------------------------------------------

    def _ps_get_range(self, wizard):
        date_ref = wizard.date_ref
        if wizard.period == 'day':
            return date_ref, date_ref
        if wizard.period == 'week':
            return date_ref, date_ref + timedelta(days=6)
        start = date_ref.replace(day=1)
        last_day = calendar.monthrange(date_ref.year, date_ref.month)[1]
        return start, date_ref.replace(day=last_day)

    def _ps_get_posts(self, start, end):
        tz_name = self.env.user.tz or 'UTC'
        tz = pytz.timezone(tz_name)
        local_start = tz.localize(datetime.combine(start, datetime.min.time()))
        local_end = tz.localize(datetime.combine(end, datetime.max.time()))
        utc_start = local_start.astimezone(pytz.utc).replace(tzinfo=None)
        utc_end = local_end.astimezone(pytz.utc).replace(tzinfo=None)

        domain = [
            ('scheduled_datetime', '>=', utc_start),
            ('scheduled_datetime', '<=', utc_end),
            ('state', '!=', 'cancelled'),
        ]

        def to_local(dt):
            if not dt:
                return dt
            return pytz.utc.localize(dt).astimezone(tz)

        posts = self.env['graphics.scheduled.post'].search(domain)
        by_day = {}
        for rec in posts:
            local_dt = to_local(rec.scheduled_datetime)
            by_day.setdefault(local_dt.date(), []).append({
                'title': rec.title,
                'time': local_dt,
                'content': rec.content or '',
                'state': rec.state,
                'files': len(rec.attachment_ids),
            })
        for d in by_day:
            by_day[d].sort(key=lambda p: p['time'])
        return by_day

    # -- drawing -----------------------------------------------------------

    def _ps_header(self, c, W, H, M, period, d0, d1):
        hh = 30 * mm
        c.setFillColor(NAVY)
        c.rect(0, H - hh, W, hh, fill=1, stroke=0)
        c.setFillColor(BLUE)
        c.rect(0, H - hh, W, 3, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont('Helvetica-Bold', 20)
        c.drawString(M, H - 16 * mm, PERIOD_LABEL[period] + ' Post Schedule')
        c.setFont('Helvetica', 10)
        c.drawString(M, H - 22 * mm, '%s  to  %s' % (d0, d1))

    def _ps_day_header(self, c, W, M, y, d):
        c.setFillColor(NAVY)
        c.setFont('Helvetica-Bold', 13)
        c.drawString(M, y, d.strftime('%A'))
        c.setFont('Helvetica', 9)
        c.setFillColor(GREY)
        c.drawString(
            M + c.stringWidth(d.strftime('%A'), 'Helvetica-Bold', 13) + 6, y,
            '— ' + d.strftime('%d %b %Y')
        )
        c.setLineWidth(1.2)
        c.setStrokeColor(NAVY)
        c.line(M, y - 3, W - M, y - 3)
        return y - 3

    def _ps_card(self, c, W, M, y, p):
        ch = 18 * mm
        col = HexColor(STATE_COLOR.get(p['state'], '#3b82f6'))
        c.setFillColor(LIGHT)
        c.roundRect(M, y - ch, W - 2 * M, ch, 4, fill=1, stroke=0)
        c.setFillColor(col)
        c.roundRect(M, y - ch, 4, ch, 2, fill=1, stroke=0)

        c.setFillColor(NAVY)
        c.setFont('Helvetica-Bold', 12)
        c.drawString(M + 10, y - 8 * mm, p['time'].strftime('%H:%M'))

        bx = M + 28 * mm
        label = STATE_LABEL.get(p['state'], p['state'])
        bw = c.stringWidth(label, 'Helvetica-Bold', 8) + 8
        c.setFillColor(col)
        c.roundRect(bx, y - 7 * mm, bw, 5 * mm, 2, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont('Helvetica-Bold', 8)
        c.drawString(bx + 4, y - 6 * mm + 1, label)

        c.setFillColor(DARK)
        c.setFont('Helvetica-Bold', 12)
        c.drawString(bx, y - 12 * mm, p['title'] or '')

        details = []
        if p['files']:
            details.append('%d attachment(s)' % p['files'])
        if p['content']:
            snippet = p['content'][:70] + ('...' if len(p['content']) > 70 else '')
            details.append(snippet)
        if details:
            c.setFillColor(GREY)
            c.setFont('Helvetica', 8)
            c.drawString(bx, y - 16 * mm, '  |  '.join(details))

        return y - ch - 4 * mm

    # -- entry --------------------------------------------------------------

    def _render_post_schedule(self, res_ids):
        wizard = self.env['graphics.post.schedule.wizard'].browse(res_ids)
        wizard.ensure_one()

        start, end = self._ps_get_range(wizard)
        by_day = self._ps_get_posts(start, end)
        days = sorted(by_day.keys())

        buf = BytesIO()
        W, H = A4
        M = 18 * mm
        c = canvas.Canvas(buf, pagesize=A4)

        self._ps_header(c, W, H, M, wizard.period, start, end)
        y = H - 30 * mm - 14 * mm

        if not days:
            c.setFillColor(GREY)
            c.setFont('Helvetica', 13)
            c.drawCentredString(W / 2, H / 2, 'No posts scheduled in this period')
        else:
            for d in days:
                if y < 40 * mm:
                    c.showPage()
                    self._ps_header(c, W, H, M, wizard.period, start, end)
                    y = H - 30 * mm - 14 * mm
                y = self._ps_day_header(c, W, M, y, d) - 6 * mm
                for p in by_day[d]:
                    if y < 26 * mm:
                        c.showPage()
                        self._ps_header(c, W, H, M, wizard.period, start, end)
                        y = H - 30 * mm - 14 * mm
                    y = self._ps_card(c, W, M, y, p)
                y -= 4 * mm

        c.showPage()
        c.save()
        return buf.getvalue(), 'pdf'
