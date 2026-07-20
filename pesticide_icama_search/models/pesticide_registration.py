# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PesticideRegistration(models.Model):
    _name = "pesticide.registration"
    _description = "ICAMA Pesticide Registration Record"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    registration_no = fields.Char(
        string="Registration No. (登记证号)", required=True, index=True
    )
    name = fields.Char(string="Pesticide Name (农药名称)", index=True)
    category = fields.Char(string="Category (农药类别)", index=True)
    dosage_form = fields.Char(string="Dosage Form (剂型)", index=True)
    total_content = fields.Char(string="Total Content (总含量)")
    valid_until = fields.Char(string="Valid Until (有效期至)")
    holder = fields.Char(string="Registration Holder (登记证持有人)")
    active_ingredient = fields.Char(
        string="Active Ingredient (有效成分)", index=True
    )
    detail_ref = fields.Char(string="Detail Reference ID")

    # English translations, filled in at sync time (see
    # pesticide_search_term._run_search). Kept as separate stored
    # fields rather than computed on the fly so translation only ever
    # happens once per value, not on every view load.
    name_en = fields.Char(string="Pesticide Name (EN)", index=True, readonly=True)
    category_en = fields.Char(string="Category (EN)", index=True, readonly=True)
    dosage_form_en = fields.Char(
        string="Dosage Form (EN)", index=True, readonly=True
    )
    holder_en = fields.Char(string="Registration Holder (EN)", readonly=True)
    active_ingredient_en = fields.Char(
        string="Active Ingredient (EN)", index=True, readonly=True
    )

    # Internal links, auto-matched by English name (see
    # _link_rd_and_vendor below). Left blank when no match exists -
    # this never creates x_r_d / x_contact_vendor records on its own.
    x_r_d_id = fields.Many2one(
        "x_r_d",
        string="R&D Product",
        help="Auto-matched from Pesticide Name (EN) against the R&D "
        "product's Name field (exact match, case-insensitive).",
    )
    x_contact_vendor_id = fields.Many2one(
        "x_contact_vendor",
        string="Vendor",
        help="Auto-matched from Registration Holder (EN) against the "
        "vendor's Name field (exact match, case-insensitive).",
    )

    search_term_id = fields.Many2one(
        "pesticide.search.term",
        string="Found Via Search Term",
        ondelete="set null",
    )
    last_synced = fields.Datetime(string="Last Synced", readonly=True)

    _sql_constraints = [
        (
            "registration_no_uniq",
            "unique(registration_no)",
            "A registration with this Registration No. already exists.",
        )
    ]

    def action_open_source_page(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": (
                "https://www.icama.cn/BasicdataSystem/pesticideRegistration/"
                "tagview.do?pdno=%s" % (self.registration_no or "")
            ),
            "target": "new",
        }

    def _link_rd_and_vendor(self):
        """
        Match this recordset's English name/holder against x_r_d.x_name
        and x_contact_vendor.x_name (exact match, case-insensitive) and
        set the many2one links where found. Never creates x_r_d /
        x_contact_vendor records - leaves the link blank if there's no
        existing match.

        Batched: one read per target model for the whole recordset,
        not one search per registration. sudo() is used for the lookup
        since x_r_d / x_contact_vendor may have their own access
        groups that shouldn't block this internal linking step.
        """
        to_process = self.filtered(lambda r: r.name_en or r.holder_en)
        if not to_process:
            return

        wanted_names = {
            r.name_en.strip().lower() for r in to_process if r.name_en
        }
        wanted_holders = {
            r.holder_en.strip().lower() for r in to_process if r.holder_en
        }

        Rd = self.env["x_r_d"].sudo()
        Vendor = self.env["x_contact_vendor"].sudo()

        rd_map = {}
        if wanted_names:
            for rec in Rd.search_read([("x_name", "!=", False)], ["x_name"]):
                key = (rec["x_name"] or "").strip().lower()
                if key in wanted_names and key not in rd_map:
                    rd_map[key] = rec["id"]

        vendor_map = {}
        if wanted_holders:
            for rec in Vendor.search_read(
                [("x_name", "!=", False)], ["x_name"]
            ):
                key = (rec["x_name"] or "").strip().lower()
                if key in wanted_holders and key not in vendor_map:
                    vendor_map[key] = rec["id"]

        for reg in to_process:
            vals = {}
            if reg.name_en:
                rd_id = rd_map.get(reg.name_en.strip().lower())
                if rd_id and reg.x_r_d_id.id != rd_id:
                    vals["x_r_d_id"] = rd_id
            if reg.holder_en:
                vendor_id = vendor_map.get(reg.holder_en.strip().lower())
                if vendor_id and reg.x_contact_vendor_id.id != vendor_id:
                    vals["x_contact_vendor_id"] = vendor_id
            if vals:
                reg.write(vals)

    def action_link_rd_and_vendor(self):
        """
        Manual/bulk entry point for the same matching logic used by the
        automated action - callable from the form button or the Action
        (⚙) menu on the list view for on-demand re-linking, e.g. after
        adding new x_r_d / x_contact_vendor records.
        """
        self._link_rd_and_vendor()
        matched_rd = len(self.filtered("x_r_d_id"))
        matched_vendor = len(self.filtered("x_contact_vendor_id"))
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("R&D / Vendor Linking Complete"),
                "message": _("%s/%s linked to an R&D product, %s/%s linked to a vendor.")
                % (matched_rd, len(self), matched_vendor, len(self)),
                "sticky": False,
                "type": "success",
            },
        }

    def action_retranslate(self):
        """
        Force these registrations' English fields to be re-translated
        with whichever provider is CURRENTLY configured in Settings,
        ignoring any previously cached translation.

        This matters because the cache is checked before any live
        translator runs: once a string is cached (e.g. by the Google
        fallback, before Lara credentials were set), it keeps winning
        forever - adding credentials later doesn't retroactively fix
        already-cached strings, or the name_en/holder_en already
        written onto these records. This action clears exactly the
        cache entries these records depend on, then re-translates them,
        so it's the fix to run after configuring/changing the Lara
        credentials if existing data still looks wrong.
        """
        Cache = self.env["pesticide.translation.cache"]

        zh_texts = []
        for reg in self:
            for val in (
                reg.name,
                reg.category,
                reg.dosage_form,
                reg.holder,
                reg.active_ingredient,
            ):
                if val:
                    zh_texts.append(val)
        unique_zh = list(dict.fromkeys(zh_texts))

        en_lookup = {}
        if unique_zh:
            Cache.search(
                [
                    ("source_text", "in", unique_zh),
                    ("source_lang", "=", "zh"),
                    ("target_lang", "=", "en"),
                ]
            ).unlink()
            translated = Cache.translate_many(unique_zh, "zh", "en")
            en_lookup = dict(zip(unique_zh, translated))

        for reg in self:
            reg.write(
                {
                    "name_en": en_lookup.get(reg.name, reg.name),
                    "category_en": en_lookup.get(reg.category, reg.category),
                    "dosage_form_en": en_lookup.get(
                        reg.dosage_form, reg.dosage_form
                    ),
                    "holder_en": en_lookup.get(reg.holder, reg.holder),
                    "active_ingredient_en": en_lookup.get(
                        reg.active_ingredient, reg.active_ingredient
                    ),
                }
            )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Re-translation Complete"),
                "message": _(
                    "%s record(s) re-translated using the currently "
                    "configured provider."
                )
                % len(self),
                "sticky": False,
                "type": "success",
            },
        }
