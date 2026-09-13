# -*- coding: utf-8 -*-
import calendar
import os
from datetime import timedelta, datetime
from io import BytesIO

import pytz

from odoo import models

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display


# --- Arabic helpers ---------------------------------------------------------

_FONT_NAME = 'Amiri'
_FONT_REGISTERED = False
_RESHAPER = arabic_reshaper.ArabicReshaper(
    configuration={'delete_harakat': False, 'support_ligatures': True}
)


def _ensure_font():
    global _FONT_REGISTERED
    if not _FONT_REGISTERED:
        font_path = os.path.join(
            os.path.dirname(__file__), '..', 'static', 'src', 'fonts',
            'Amiri-Regular.ttf'
        )
        pdfmetrics.registerFont(TTFont(_FONT_NAME, font_path))
        _FONT_REGISTERED = True


def ar(text):
    return get_display(_RESHAPER.reshape(text or ''))


def _has_arabic(text):
    if not text:
        return False
    return any('\u0600' <= ch <= '\u06FF' or '\uFB50' <= ch <= '\uFEFF'
               for ch in text)


def draw_smart(c, x, y, text, size, latin_font='Helvetica-Bold',
               right=False, width_only=False):
    """Draw text that may contain Arabic. Arabic -> reshape + Amiri font;
    otherwise the given Latin font. Returns the drawn string width."""
    text = text or ''
    if _has_arabic(text):
        shaped = ar(text)
        font = _FONT_NAME
    else:
        shaped = text
        font = latin_font
    w = c.stringWidth(shaped, font, size)
    if width_only:
        return w
    c.setFont(font, size)
    if right:
        c.drawRightString(x, y, shaped)
    else:
        c.drawString(x, y, shaped)
    return w


WEEKDAY_AR = {
    0: 'الإثنين', 1: 'الثلاثاء', 2: 'الأربعاء', 3: 'الخميس',
    4: 'الجمعة', 5: 'السبت', 6: 'الأحد',
}
MONTH_AR = {
    1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل', 5: 'مايو', 6: 'يونيو',
    7: 'يوليو', 8: 'أغسطس', 9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر',
}
TYPE_INFO = {
    'Meeting': {'ar': 'اجتماع', 'color': '#2563eb'},
    'Travel': {'ar': 'سفر', 'color': '#16a34a'},
    'Conference': {'ar': 'مؤتمر', 'color': '#9333ea'},
}
PERIOD_INFO = {
    'day': {'en': 'Daily', 'ar': 'اليومي'},
    'week': {'en': 'Weekly', 'ar': 'الأسبوعي'},
    'month': {'en': 'Monthly', 'ar': 'الشهري'},
}

NAVY = HexColor('#1e3a5f')
BLUE = HexColor('#3b82f6')
GREY = HexColor('#6b7280')
LIGHT = HexColor('#f8f9fb')
DARK = HexColor('#111827')


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        # Intercept ONLY our timetable report; everything else is untouched.
        report = self._get_report(report_ref)
        if report.report_name == 'secretary_meetings.timetable_pdf':
            return self._render_secretary_timetable(res_ids)
        return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)

    # -- data ----------------------------------------------------------------

    def _st_get_range(self, wizard):
        date_ref = wizard.date_ref
        if wizard.period == 'day':
            return date_ref, date_ref
        if wizard.period == 'week':
            return date_ref, date_ref + timedelta(days=6)
        start = date_ref.replace(day=1)
        last_day = calendar.monthrange(date_ref.year, date_ref.month)[1]
        return start, date_ref.replace(day=last_day)

    def _st_get_events(self, start, end):
        tz_name = self.env.user.tz or 'UTC'
        tz = pytz.timezone(tz_name)
        local_start = tz.localize(datetime.combine(start, datetime.min.time()))
        local_end = tz.localize(datetime.combine(end, datetime.max.time()))
        utc_start = local_start.astimezone(pytz.utc).replace(tzinfo=None)
        utc_end = local_end.astimezone(pytz.utc).replace(tzinfo=None)

        domain = [
            ('start_datetime', '>=', utc_start),
            ('start_datetime', '<=', utc_end),
            ('state', '!=', 'cancelled'),
        ]

        def to_local(dt):
            if not dt:
                return dt
            return pytz.utc.localize(dt).astimezone(tz)

        events = []
        for rec in self.env['owner.meeting'].search(domain):
            events.append({'type': 'Meeting', 'title': rec.title,
                           'start': to_local(rec.start_datetime),
                           'stop': to_local(rec.stop_datetime),
                           'place': rec.location or ''})
        for rec in self.env['owner.travel'].search(domain):
            events.append({'type': 'Travel', 'title': rec.title,
                           'start': to_local(rec.start_datetime),
                           'stop': to_local(rec.stop_datetime),
                           'place': rec.destination or ''})
        for rec in self.env['owner.conference'].search(domain):
            events.append({'type': 'Conference', 'title': rec.title,
                           'start': to_local(rec.start_datetime),
                           'stop': to_local(rec.stop_datetime),
                           'place': rec.location or ''})
        events.sort(key=lambda e: e['start'])

        by_day = {}
        for e in events:
            by_day.setdefault(e['start'].date(), []).append(e)
        return by_day

    # -- drawing -------------------------------------------------------------

    def _st_header(self, c, W, H, M, period, d0, d1):
        hh = 34 * mm
        c.setFillColor(NAVY)
        c.rect(0, H - hh, W, hh, fill=1, stroke=0)
        c.setFillColor(BLUE)
        c.rect(0, H - hh, W, 3, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont('Helvetica-Bold', 20)
        c.drawString(M, H - 18 * mm, PERIOD_INFO[period]['en'] + ' Timetable')
        c.setFont('Helvetica', 10)
        c.drawString(M, H - 24 * mm, '%s  to  %s' % (d0, d1))
        c.setFont(_FONT_NAME, 20)
        c.drawRightString(W - M, H - 18 * mm,
                          ar('جدول المواعيد %s' % PERIOD_INFO[period]['ar']))

    def _st_legend(self, c, W, M, y):
        x = M
        for t in ['Meeting', 'Travel', 'Conference']:
            col = HexColor(TYPE_INFO[t]['color'])
            c.setFillColor(col)
            c.circle(x + 2, y + 3, 3, fill=1, stroke=0)
            c.setFillColor(DARK)
            c.setFont('Helvetica', 9)
            label = '%s / ' % t
            c.drawString(x + 8, y, label)
            wlab = c.stringWidth(label, 'Helvetica', 9)
            c.setFont(_FONT_NAME, 10)
            arw = ar(TYPE_INFO[t]['ar'])
            c.drawString(x + 8 + wlab, y - 1, arw)
            x += 8 + wlab + c.stringWidth(arw, _FONT_NAME, 10) + 16

    def _st_day_header(self, c, W, M, y, d):
        c.setFillColor(NAVY)
        c.setFont('Helvetica-Bold', 13)
        en = d.strftime('%A')
        c.drawString(M, y, en)
        c.setFont('Helvetica', 9)
        c.setFillColor(GREY)
        c.drawString(M + c.stringWidth(en, 'Helvetica-Bold', 13) + 6, y,
                     '— ' + d.strftime('%d %b %Y'))
        c.setFillColor(NAVY)
        c.setFont(_FONT_NAME, 13)
        c.drawRightString(W - M, y,
                          ar('%s  %d %s %d' % (WEEKDAY_AR[d.weekday()], d.day,
                                               MONTH_AR[d.month], d.year)))
        c.setLineWidth(1.2)
        c.setStrokeColor(NAVY)
        c.line(M, y - 3, W - M, y - 3)
        return y - 3

    def _st_card(self, c, W, M, y, e):
        ch = 20 * mm
        col = HexColor(TYPE_INFO[e['type']]['color'])
        c.setFillColor(LIGHT)
        c.roundRect(M, y - ch, W - 2 * M, ch, 4, fill=1, stroke=0)
        c.setFillColor(col)
        c.roundRect(M, y - ch, 4, ch, 2, fill=1, stroke=0)

        c.setFillColor(NAVY)
        c.setFont('Helvetica-Bold', 12)
        c.drawString(M + 10, y - 9 * mm,
                     '%s - %s' % (e['start'].strftime('%H:%M'),
                                  e['stop'].strftime('%H:%M')))

        bx = M + 42 * mm
        bw = c.stringWidth(e['type'], 'Helvetica-Bold', 8) + 8
        c.setFillColor(col)
        c.roundRect(bx, y - 8 * mm, bw, 5 * mm, 2, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont('Helvetica-Bold', 8)
        c.drawString(bx + 4, y - 7 * mm + 1, e['type'])

        c.setFillColor(DARK)
        draw_smart(c, bx, y - 13 * mm, e['title'] or '', 12,
                   latin_font='Helvetica-Bold')

        if e['place']:
            c.setFillColor(GREY)
            if _has_arabic(e['place']):
                c.setFont('Helvetica', 9)
                c.drawString(bx, y - 17 * mm, 'Location: ')
                lw = c.stringWidth('Location: ', 'Helvetica', 9)
                draw_smart(c, bx + lw, y - 17 * mm, e['place'], 9,
                           latin_font='Helvetica')
            else:
                c.setFont('Helvetica', 9)
                c.drawString(bx, y - 17 * mm, 'Location: ' + e['place'])

        arw = ar(TYPE_INFO[e['type']]['ar'])
        aw = c.stringWidth(arw, _FONT_NAME, 11) + 10
        c.setFillColor(col)
        c.roundRect(W - M - aw - 6, y - 8 * mm, aw, 6 * mm, 2, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont(_FONT_NAME, 11)
        c.drawRightString(W - M - 11, y - 7 * mm, arw)

        return y - ch - 4 * mm

    # -- entry ---------------------------------------------------------------

    def _render_secretary_timetable(self, res_ids):
        _ensure_font()
        wizard = self.env['secretary.timetable.wizard'].browse(res_ids)
        wizard.ensure_one()

        start, end = self._st_get_range(wizard)
        by_day = self._st_get_events(start, end)
        days = sorted(by_day.keys())

        buf = BytesIO()
        W, H = A4
        M = 18 * mm
        c = canvas.Canvas(buf, pagesize=A4)

        self._st_header(c, W, H, M, wizard.period, start, end)
        y = H - 34 * mm - 12 * mm
        self._st_legend(c, W, M, y)
        y -= 12 * mm

        if not days:
            c.setFillColor(GREY)
            c.setFont('Helvetica', 13)
            c.drawCentredString(W / 2, H / 2, 'No events scheduled in this period')
            c.setFont(_FONT_NAME, 13)
            c.drawCentredString(W / 2, H / 2 - 8 * mm,
                                ar('لا توجد مواعيد خلال هذه الفترة'))
        else:
            for d in days:
                if y < 45 * mm:
                    c.showPage()
                    self._st_header(c, W, H, M, wizard.period, start, end)
                    y = H - 34 * mm - 14 * mm
                y = self._st_day_header(c, W, M, y, d) - 6 * mm
                for e in sorted(by_day[d], key=lambda x: x['start']):
                    if y < 30 * mm:
                        c.showPage()
                        self._st_header(c, W, H, M, wizard.period, start, end)
                        y = H - 34 * mm - 14 * mm
                    y = self._st_card(c, W, M, y, e)
                y -= 4 * mm

        c.showPage()
        c.save()
        return buf.getvalue(), 'pdf'
