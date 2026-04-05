from odoo import models, fields, _
from odoo.exceptions import UserError


class GeneralLedgerWizard(models.TransientModel):
    _name = "general.ledger.wizard"
    _description = "General Ledger Wizard"

    printed_fields = fields.Many2many('ir.model.fields', string="Fields", help="Choose fields that you want to print", domain=[('model_id.id', '=', 406)])

    def print_general_ledger(self):
        
        # line = self.env['account.move.line'].browse(105433)
        # c = self.printed_fields.name
        # print(line[c])
        # print(self._context.get('active_model'))
        # print(self._context.get('active_ids', []))
        

        data = {
            'model': self._name,
            'ids': self.ids,
            'partner_ids': self._context.get('active_ids'),
            'printed_fields':self.printed_fields.ids
            # 'date_start': self.date_start,
            # 'date_end': self.date_end,
            # 'full_report': full_report,
        }

        return self.env.ref('general_ledger_print_layout.action_report_general_ledger').report_action(self, data=data)
