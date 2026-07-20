# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

from . import icama_client
from . import translation_util

_logger = logging.getLogger(__name__)


class PesticideSearchTerm(models.Model):
    _name = "pesticide.search.term"
    _description = "ICAMA Pesticide Saved Search"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(string="Search Label", required=True)
    active = fields.Boolean(default=True)

    pesticide_name = fields.Char(string="Pesticide Name (农药名称)")
    category = fields.Char(string="Category (农药类别)")
    dosage_form = fields.Char(string="Dosage Form (剂型)")
    registration_no = fields.Char(string="Registration No. (登记证号)")
    holder = fields.Char(string="Registration Holder (登记证持有人)")
    active_ingredient = fields.Char(string="Active Ingredient (有效成分)")

    fuzzy_match = fields.Boolean(
        string="Fuzzy Match",
        default=True,
        help="If enabled, partial matches are returned (e.g. searching "
        "'噻虫' will also match '噻虫嗪'). If disabled, only exact matches "
        "are returned.",
    )

    result_ids = fields.One2many(
        "pesticide.registration", "search_term_id", string="Results"
    )
    result_count = fields.Integer(compute="_compute_result_count")

    last_run = fields.Datetime(string="Last Run", readonly=True)
    last_run_state = fields.Selection(
        [("done", "Done"), ("error", "Error")],
        string="Last Run Status",
        readonly=True,
    )
    last_run_message = fields.Char(string="Last Run Message", readonly=True)

    @api.depends("result_ids")
    def _compute_result_count(self):
        for term in self:
            term.result_count = len(term.result_ids)

    def _check_has_criteria(self):
        for term in self:
            if not any(
                [
                    term.pesticide_name,
                    term.category,
                    term.dosage_form,
                    term.registration_no,
                    term.holder,
                    term.active_ingredient,
                ]
            ):
                raise UserError(
                    _(
                        "Search term '%s' has no criteria set (name, "
                        "category, dosage form, registration no., "
                        "holder or active ingredient). Please fill in "
                        "at least one field."
                    )
                    % term.name
                )

    def _zh_criteria(self, term, cache):
        """
        ICAMA's own search form only understands Chinese terms. If the
        user typed criteria in English, translate them to Chinese
        before sending them to the site (Chinese input passes through
        unchanged) - in a single batch call covering all of this
        term's criteria fields at once, not one call per field.
        """
        fields_map = {
            "pesticide_name": term.pesticide_name,
            "category": term.category,
            "dosage_form": term.dosage_form,
            "holder": term.holder,
            "active_ingredient": term.active_ingredient,
        }
        to_translate = [
            v
            for v in fields_map.values()
            if v and not translation_util.contains_chinese(v)
        ]
        translated = {}
        if to_translate:
            results = cache.translate_many(to_translate, "en", "zh")
            translated = dict(zip(to_translate, results))

        def zh_value(value):
            value = (value or "").strip()
            if not value or translation_util.contains_chinese(value):
                return value
            return translated.get(value, value)

        return {k: zh_value(v) for k, v in fields_map.items()}

    def _run_search(self):
        """Run the ICAMA search for each term in self and upsert results."""
        Registration = self.env["pesticide.registration"]
        Cache = self.env["pesticide.translation.cache"]

        try:
            session = icama_client.new_session()
        except icama_client.ICAMAClientError as exc:
            # Can't even establish a session - mark every term as failed
            # rather than trying (and failing) one-by-one.
            for term in self:
                term.write(
                    {
                        "last_run": fields.Datetime.now(),
                        "last_run_state": "error",
                        "last_run_message": str(exc)[:250],
                    }
                )
            self.env.cr.commit()
            return True

        for term in self:
            try:
                zh_criteria = self._zh_criteria(term, Cache)
                records = icama_client.search(
                    name=zh_criteria["pesticide_name"],
                    category=zh_criteria["category"],
                    dosage_form=zh_criteria["dosage_form"],
                    registration_no=term.registration_no or "",
                    holder=zh_criteria["holder"],
                    active_ingredient=zh_criteria["active_ingredient"],
                    fuzzy=term.fuzzy_match,
                    session=session,
                )

                # Translate every zh value across the whole results page
                # in one pass, de-duplicated first, so a 100-row page
                # with only 10-20 distinct names/holders only pays for
                # 10-20 Lara calls (or cache hits after the first sync),
                # not 500 (5 fields x 100 rows).
                zh_texts = []
                for record in records:
                    for key in (
                        "name",
                        "category",
                        "dosage_form",
                        "holder",
                        "active_ingredient",
                    ):
                        val = record.get(key)
                        if val:
                            zh_texts.append(val)
                en_lookup = {}
                if zh_texts:
                    unique_zh = list(dict.fromkeys(zh_texts))
                    translated = Cache.translate_many(unique_zh, "zh", "en")
                    en_lookup = dict(zip(unique_zh, translated))

                now = fields.Datetime.now()
                created, updated = 0, 0
                for record in records:
                    reg_no = record.get("registration_no")
                    if not reg_no:
                        continue
                    vals = {
                        "registration_no": reg_no,
                        "name": record.get("name"),
                        "category": record.get("category"),
                        "dosage_form": record.get("dosage_form"),
                        "total_content": record.get("total_content"),
                        "valid_until": record.get("valid_until"),
                        "holder": record.get("holder"),
                        "active_ingredient": record.get("active_ingredient"),
                        "detail_ref": record.get("detail_ref"),
                        "search_term_id": term.id,
                        "last_synced": now,
                        "name_en": en_lookup.get(record.get("name"), record.get("name")),
                        "category_en": en_lookup.get(
                            record.get("category"), record.get("category")
                        ),
                        "dosage_form_en": en_lookup.get(
                            record.get("dosage_form"), record.get("dosage_form")
                        ),
                        "holder_en": en_lookup.get(
                            record.get("holder"), record.get("holder")
                        ),
                        "active_ingredient_en": en_lookup.get(
                            record.get("active_ingredient"),
                            record.get("active_ingredient"),
                        ),
                    }
                    existing = Registration.search(
                        [("registration_no", "=", reg_no)], limit=1
                    )
                    if existing:
                        existing.write(vals)
                        updated += 1
                    else:
                        Registration.create(vals)
                        created += 1

                term.write(
                    {
                        "last_run": now,
                        "last_run_state": "done",
                        "last_run_message": _(
                            "%s found (%s new, %s updated)"
                        )
                        % (len(records), created, updated),
                    }
                )
                # Commit per term so one bad term doesn't roll back
                # progress already made on others during a cron run.
                self.env.cr.commit()
            except Exception as exc:  # noqa: BLE001
                _logger.exception(
                    "ICAMA search failed for search term '%s'", term.name
                )
                term.write(
                    {
                        "last_run": fields.Datetime.now(),
                        "last_run_state": "error",
                        "last_run_message": str(exc)[:250],
                    }
                )
                self.env.cr.commit()
        return True

    def action_search_now(self):
        self._check_has_criteria()
        self._run_search()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("ICAMA Search Complete"),
                "message": "\n".join(
                    "%s: %s" % (t.name, t.last_run_message) for t in self
                ),
                "sticky": False,
                "type": "success"
                if all(t.last_run_state == "done" for t in self)
                else "warning",
            },
        }

    @api.model
    def _cron_run_all_searches(self):
        """Called by the scheduled action. Refreshes all active searches."""
        terms = self.search([("active", "=", True)])
        if not terms:
            return
        terms._run_search()
