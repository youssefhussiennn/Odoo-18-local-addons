# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import timedelta, datetime, date
from odoo.exceptions import UserError
from odoo.addons.account.models.company import ResCompany
from odoo.addons.account.models.account_move import AccountMove
from odoo.tools.misc import format_date


def _get_user_fiscal_lock_date(self):
    """Get the fiscal lock date for this company depending on the user"""
    self.ensure_one()
    lock_date = max(self.period_lock_date or date.min, self.fiscalyear_lock_date or date.min)
    if self.user_has_groups('base.group_system'):
        lock_date = self.fiscalyear_lock_date or date.min
    return lock_date

ResCompany._get_user_fiscal_lock_date = _get_user_fiscal_lock_date





def _check_fiscalyear_lock_date(self):
    for move in self:
        lock_date = move.company_id._get_user_fiscal_lock_date()
        if move.date <= lock_date:
            if self.user_has_groups('base.group_system'):
                message = _("You cannot add/modify entries prior to and inclusive of the lock date %s.", format_date(self.env, lock_date))
            else:
                message = _("You cannot add/modify entries prior to and inclusive of the lock date %s. Check the company settings or ask someone with the 'Admin' role", format_date(self.env, lock_date))
            raise UserError(message)
    return True

AccountMove._check_fiscalyear_lock_date = _check_fiscalyear_lock_date