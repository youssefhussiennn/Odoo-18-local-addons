# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from . import translation_util

_logger = logging.getLogger(__name__)


class PesticideTranslationCache(models.Model):
    _name = "pesticide.translation.cache"
    _description = "ICAMA Translation Cache (zh <-> en)"
    _rec_name = "source_text"

    source_text = fields.Char(required=True, index=True)
    source_lang = fields.Selection(
        [("zh", "Chinese"), ("en", "English")], required=True
    )
    target_lang = fields.Selection(
        [("zh", "Chinese"), ("en", "English")], required=True
    )
    target_text = fields.Char(required=True)
    provider = fields.Selection(
        [("lara", "Lara"), ("google", "Google (fallback)")],
        string="Translated Via",
        readonly=True,
        help="Which engine produced this translation. If you're "
        "expecting Lara but see 'Google (fallback)' here, check that "
        "your Lara Access Key ID/Secret are configured and the "
        "lara-sdk Python package is installed on the server (or check "
        "the server log for the actual error). Delete the row to have "
        "it re-translated with whichever provider is configured next "
        "time it's needed.",
    )

    _sql_constraints = [
        (
            "translation_uniq",
            "unique(source_text, source_lang, target_lang)",
            "This text is already cached for this language pair.",
        ),
    ]

    def _lara_config(self):
        """Read the Lara settings configured under Settings > General
        Settings > ICAMA Pesticide Search. Returns
        (access_key_id, access_key_secret, require)."""
        ICP = self.env["ir.config_parameter"].sudo()
        access_key_id = ICP.get_param("pesticide_icama_search.lara_access_key_id")
        access_key_secret = ICP.get_param(
            "pesticide_icama_search.lara_access_key_secret"
        )
        require = ICP.get_param("pesticide_icama_search.require_lara")
        return access_key_id, access_key_secret, str(require) == "True"

    @api.model
    def translate(self, text, source_lang="zh", target_lang="en"):
        """Translate a single string. Convenience wrapper around
        translate_many for one-off calls (e.g. a single search
        criterion) - see translate_many for the actual lookup order."""
        text = (text or "").strip()
        if not text:
            return text
        return self.translate_many([text], source_lang, target_lang)[0]

    @api.model
    def translate_many(self, texts, source_lang="zh", target_lang="en"):
        """
        Translate a list of strings. Order of lookup, cheapest and most
        reliable first:
          1. static regulatory dictionary (instant, no DB/network)
          2. this cache table (instant, looked up once before)
          3. ONE Lara batch call covering every remaining miss at once
             (if Access Key ID/Secret are configured in Settings)
          4. Google's free endpoint, one string at a time, for
             anything Lara couldn't handle or if no credentials are set

        Every distinct string is therefore sent to a translator at
        most once, ever - no matter how many times the same category /
        dosage form / holder name shows up across thousands of ICAMA
        records, and results from a whole results page are translated
        in a single request rather than one call per field per record.
        """
        cleaned = [(t or "").strip() for t in texts]
        result = {}
        misses = []

        for text in cleaned:
            if not text or source_lang == target_lang:
                result[text] = text
                continue
            if text in result:
                continue

            static_hit = translation_util.static_lookup(
                text, source_lang, target_lang
            )
            if static_hit:
                result[text] = static_hit
                continue

            cached = self.search(
                [
                    ("source_text", "=", text),
                    ("source_lang", "=", source_lang),
                    ("target_lang", "=", target_lang),
                ],
                limit=1,
            )
            if cached:
                result[text] = cached.target_text
                continue

            misses.append(text)

        if misses:
            self._resolve_misses(misses, source_lang, target_lang, result)

        return [result.get(t, t) for t in cleaned]

    def _resolve_misses(self, misses, source_lang, target_lang, result):
        """Fill `result` (dict, mutated in place) for every string in
        `misses` via a live translator, and persist each one to the
        cache (with its provider) so it's never looked up again."""
        access_key_id, access_key_secret, require_lara = self._lara_config()
        to_cache = {}  # text -> (translation, provider)

        remaining = list(misses)
        if access_key_id and access_key_secret:
            for start in range(0, len(remaining), translation_util.LARA_BATCH_SIZE):
                chunk = remaining[start : start + translation_util.LARA_BATCH_SIZE]
                errors = []
                translated = translation_util.lara_translate_batch(
                    chunk,
                    source_lang,
                    target_lang,
                    access_key_id,
                    access_key_secret,
                    errors=errors,
                )
                if translated:
                    for src, tgt in zip(chunk, translated):
                        result[src] = tgt
                        to_cache[src] = (tgt, "lara")
                elif require_lara:
                    # "Require Lara" is on in Settings - fail loudly
                    # with the real reason instead of silently
                    # degrading to Google.
                    raise UserError(
                        _(
                            "Lara translation failed and 'Require "
                            "Lara' is enabled in Settings, so this "
                            "isn't falling back to Google. Reason: %s"
                        )
                        % (errors[-1] if errors else _("unknown error"))
                    )
                else:
                    _logger.warning(
                        "Lara batch translation failed for %d "
                        "string(s) - falling back to Google for these. "
                        "%s",
                        len(chunk),
                        errors[-1] if errors else "",
                    )
                # If the batch failed (and require_lara is off), those
                # texts stay unresolved here and fall through to Google.
            remaining = [t for t in remaining if t not in result]
        elif require_lara:
            raise UserError(
                _(
                    "'Require Lara' is enabled in Settings, but Lara "
                    "Access Key ID/Secret aren't both configured "
                    "(Settings > General Settings > ICAMA Pesticide "
                    "Search)."
                )
            )
        else:
            _logger.info(
                "No Lara Access Key ID/Secret configured (Settings > "
                "General Settings > ICAMA Pesticide Search) - using "
                "Google Translate for %d string(s).",
                len(remaining),
            )

        # Fallback (no Lara credentials configured, or its batch call
        # failed for some texts): Google's free endpoint, one string
        # at a time.
        for text in remaining:
            translated = translation_util.google_translate_single(
                text, source_lang, target_lang
            )
            if translated:
                result[text] = translated
                to_cache[text] = (translated, "google")
            else:
                # Translation unavailable anywhere - fall back to the
                # original rather than blocking the sync.
                result[text] = text

        for source_text, (target_text, provider) in to_cache.items():
            try:
                self.create(
                    {
                        "source_text": source_text,
                        "source_lang": source_lang,
                        "target_lang": target_lang,
                        "target_text": target_text,
                        "provider": provider,
                    }
                )
            except Exception:  # noqa: BLE001 - concurrent insert, ignore
                self.env.cr.rollback()
