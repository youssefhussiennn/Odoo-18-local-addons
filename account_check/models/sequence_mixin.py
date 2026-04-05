from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import format_date


class SequenceMixin(models.AbstractModel):
    """Mechanism used to have an editable sequence number.

    Be careful of how you use this regarding the prefixes. More info in the
    docstring of _get_last_sequence.
    """

    _inherit = 'sequence.mixin'

    def _constrains_date_sequence(self):
        constraint_date = fields.Date.to_date(self.env['ir.config_parameter'].sudo().get_param(
            'sequence.mixin.constraint_start_date',
            '1970-01-01'
        ))
        # for record in self:
        #     date = fields.Date.to_date(record[record._sequence_date_field])
        #     sequence = record[record._sequence_field]
        #     if sequence and date and date > constraint_date:
        #         format_values = record._get_sequence_format_param(sequence)[1]
        #         if (
        #                 format_values['year'] and format_values['year'] != date.year % 10 ** len(
        #             str(format_values['year']))
        #                 or format_values['month'] and format_values['month'] != date.month
        #         ):
        #             print('#################################3')
        #             print('#################################3')
        #             print('#################################3')
        #             print('#################################3')
        #             print('#################################3')
        #             print('#################################3')
        #             print(sequence)
        #             print('*********************************')
        #             print(format_values)
        #             print('*********************************')
        #
        #             print(format_values['year'])
        #             print('*********************************')
        #             print(date.year % 10 ** len(str(format_values['year'])))
        #             print('*********************************')
        #             print(format_values['month'])
        #             print('*********************************')
        #             print(date.month)
        #             print('*********************************')
        #             raise ValidationError(_(
        #                 "The %(date_field)s (%(date)s) doesn't match the %(sequence_field)s (%(sequence)s).\n"
        #                 "You might want to clear the field %(sequence_field)s before proceeding with the change of the date.",
        #                 date=format_date(self.env, date),
        #                 sequence=sequence,
        #                 date_field=record._fields[record._sequence_date_field]._description_string(self.env),
        #                 sequence_field=record._fields[record._sequence_field]._description_string(self.env),
        #             ))