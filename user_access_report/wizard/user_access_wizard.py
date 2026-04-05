from odoo import api, fields, models
import csv
import base64
from io import StringIO

class UserAccessWizard(models.TransientModel):
    _name = "user.access.wizard"
    _description = "Wizard: Export User Access"

    user_ids = fields.Many2many("res.users", string="Users", required=True)
    model_ids = fields.Many2many("ir.model", string="Models", required=True)
    file_data = fields.Binary("CSV File", readonly=True)
    file_name = fields.Char("Filename", readonly=True)

    def action_export(self):
        header = [
            "User",
            "User Login",
            "Model (technical)",
            "Model (name)",
            "Read",
            "Write",
            "Create",
            "Delete",
            "Group sources",
        ]
        rows = []
        for user in self.user_ids:
            groups = user.groups_id
            for mdl in self.model_ids:
                # aggregate permissions from all groups
                perms = {"read": False, "write": False, "create": False, "unlink": False}
                src_groups = []
                for g in groups:
                    access_recs = self.env["ir.model.access"].sudo().search([
                        ("group_id", "=", g.id),
                        ("model_id", "=", mdl.id),
                    ])
                    for acc in access_recs:
                        for p in perms:
                            perms[p] = perms[p] or bool(getattr(acc, f"perm_{p}"))
                        if any([acc.perm_read, acc.perm_write, acc.perm_create, acc.perm_unlink]):
                            src_groups.append(g.name)
                rows.append([
                    user.name,
                    user.login,
                    mdl.model,
                    mdl.name,
                    "Y" if perms["read"] else "-",
                    "Y" if perms["write"] else "-",
                    "Y" if perms["create"] else "-",
                    "Y" if perms["unlink"] else "-",
                    ", ".join(sorted(set(src_groups))) or "(none)",
                ])
        # create CSV in memory
        csv_buffer = StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(header)
        writer.writerows(rows)
        csv_value = base64.b64encode(csv_buffer.getvalue().encode())
        csv_buffer.close()

        self.write({
            "file_data": csv_value,
            "file_name": "Users Access Report.csv",
        })

        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }