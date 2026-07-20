# -*- coding: utf-8 -*-
from odoo import _, fields, models

from . import translation_util


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pesticide_lara_access_key_id = fields.Char(
        string="Lara Access Key ID",
        config_parameter="pesticide_icama_search.lara_access_key_id",
        help="From Lara Translate (laratranslate.com) > API credentials. "
        "Used together with the Access Key Secret to translate ICAMA "
        "pesticide/vendor names between Chinese and English, one batch "
        "call per sync instead of one call per record. Requires the "
        "'lara-sdk' Python package to be installed on the Odoo server "
        "(pip install lara-sdk). Leave blank to fall back to the free "
        "Google Translate endpoint instead.",
    )
    pesticide_lara_access_key_secret = fields.Char(
        string="Lara Access Key Secret",
        config_parameter="pesticide_icama_search.lara_access_key_secret",
        help="Paired with the Access Key ID above. Lara only shows this "
        "once when the credentials are created - store it somewhere "
        "safe, it can't be retrieved again if lost.",
    )
    pesticide_require_lara = fields.Boolean(
        string="Require Lara (no silent fallback)",
        config_parameter="pesticide_icama_search.require_lara",
        help="If enabled, a failed Lara call raises an error instead "
        "of quietly falling back to Google. Turn this on once your "
        "connection to Lara is confirmed working, so any future "
        "failure is loud and visible rather than silently degrading "
        "translation quality again.",
    )

    def action_test_lara_connection(self):
        """Send one real test request with whatever's currently typed
        in the form (even if not saved yet) and show the actual
        result/error - so a failure is diagnosable immediately instead
        of only showing up as a silent Google fallback later."""
        ok, message = translation_util.test_lara_connection(
            self.pesticide_lara_access_key_id,
            self.pesticide_lara_access_key_secret,
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Lara Connection Test"),
                "message": message,
                "sticky": True,
                "type": "success" if ok else "danger",
            },
        }
