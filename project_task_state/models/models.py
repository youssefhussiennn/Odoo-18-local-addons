# -*- coding: utf-8 -*-
from odoo import models, fields

class ProjectTask(models.Model):
    _inherit = "project.task"

    state = fields.Selection(
        selection_add=[
            ("on_going", "On Going"),
            ("submitted", "Submitted"),
        ],
        ondelete={
            "on_going": "set default",
            "submitted": "set default",
        },
    )
