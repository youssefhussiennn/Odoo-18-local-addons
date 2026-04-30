from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    analytic_account_ids = fields.Many2many(
        "account.analytic.account",
        compute="_compute_analytic_accounts",
        store=True,
    )

    primary_analytic_id = fields.Many2one(
        "account.analytic.account",
        compute="_compute_primary_analytic",
        store=True,
    )

    # -----------------------------
    # SAFE PARSING FUNCTION
    # -----------------------------
    def _parse_analytic_keys(self, keys):
        ids = []
        for k in keys:
            if not k:
                continue

            # handle "16,22"
            if isinstance(k, str) and "," in k:
                parts = [p.strip() for p in k.split(",")]
                for p in parts:
                    if p.isdigit():
                        ids.append(int(p))
            else:
                if str(k).strip().isdigit():
                    ids.append(int(k))

        return list(set(ids))  # remove duplicates

    # -----------------------------
    # COMPUTE MANY2MANY
    # -----------------------------
    @api.depends("analytic_distribution")
    def _compute_analytic_accounts(self):
        for line in self:
            dist = line.analytic_distribution or {}
            ids = self._parse_analytic_keys(dist.keys())

            line.analytic_account_ids = [(6, 0, ids)] if ids else [(5, 0, 0)]

    # -----------------------------
    # PRIMARY ANALYTIC (SAFE)
    # -----------------------------
    @api.depends("analytic_distribution")
    def _compute_primary_analytic(self):
        for line in self:
            dist = line.analytic_distribution or {}

            if not dist:
                line.primary_analytic_id = False
                continue

            try:
                main_key = max(dist.items(), key=lambda x: x[1])[0]

                # handle "16,22"
                if isinstance(main_key, str) and "," in main_key:
                    main_key = main_key.split(",")[0].strip()

                line.primary_analytic_id = int(main_key)
            except Exception:
                line.primary_analytic_id = False