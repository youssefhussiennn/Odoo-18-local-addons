from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_operation_staff = fields.Boolean(
        string='Operations Visits Staff',
        help='Allows this employee to open "My Visits" on the attendance portal '
             '(/drivers/attendance) with their badge code and PIN, and to be '
             'assigned to operation visits.',
    )


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    # Mirrored so users without HR rights can search/filter on it.
    is_operation_staff = fields.Boolean(readonly=True)
