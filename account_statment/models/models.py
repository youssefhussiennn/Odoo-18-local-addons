# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools.misc import formatLang, format_date, get_lang

from markupsafe import Markup, escape


class MonetaryConverter(models.AbstractModel):
    """ ``monetary`` converter, has a mandatory option
    ``display_currency`` only if field is not of type Monetary.
    Otherwise, if we are in presence of a monetary field, the field definition must
    have a currency_field attribute set.

    The currency is used for formatting *and rounding* of the float value. It
    is assumed that the linked res_currency has a non-empty rounding value and
    res.currency's ``round`` method is used to perform rounding.

    .. note:: the monetary converter internally adds the qweb context to its
              options mapping, so that the context is available to callees.
              It's set under the ``_values`` key.
    """
    _inherit = 'ir.qweb.field.monetary'

    @api.model
    def value_to_html(self, value, options):
        display_currency = options['display_currency']

        # check if display_currency is int then convert it to currency object
        if isinstance(display_currency, int):
            display_currency = self.env['res.currency'].browse(
                display_currency)

        if not isinstance(value, (int, float)):
            raise ValueError(
                _("The value send to monetary field is not a number."))

        # lang.format mandates a sprintf-style format. These formats are non-
        # minimal (they have a default fixed precision instead), and
        # lang.format will not set one by default. currency.round will not
        # provide one either. So we need to generate a precision value
        # (integer > 0) from the currency's rounding (a float generally < 1.0).
        fmt = "%.{0}f".format(display_currency.decimal_places)

        if options.get('from_currency'):
            date = options.get('date') or fields.Date.today()
            company_id = options.get('company_id')
            if company_id:
                company = self.env['res.company'].browse(company_id)
            else:
                company = self.env.company
            value = options['from_currency']._convert(
                value, display_currency, company, date)

        lang = self.user_lang()
        formatted_amount = lang.format(fmt, display_currency.round(value),
                                       grouping=True).replace(r' ', '\N{NO-BREAK SPACE}').replace(r'-', '-\N{ZERO WIDTH NO-BREAK SPACE}')

        pre = post = ''
        if display_currency.position == 'before':
            pre = '{symbol}\N{NO-BREAK SPACE}'.format(
                symbol=display_currency.symbol or '')
        else:
            post = '\N{NO-BREAK SPACE}{symbol}'.format(
                symbol=display_currency.symbol or '')

        if options.get('label_price') and lang.decimal_point in formatted_amount:
            sep = lang.decimal_point
            integer_part, decimal_part = formatted_amount.split(sep)
            integer_part += sep
            return Markup('{pre}<span class="oe_currency_value">{0}</span><span class="oe_currency_value" style="font-size:0.5em">{1}</span>{post}').format(integer_part, decimal_part, pre=pre, post=post)

        return Markup('{pre}<span class="oe_currency_value">{0}</span>{post}').format(formatted_amount, pre=pre, post=post)


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_opening_balance = fields.Boolean(string="Opening Balance")
    is_customer_discount = fields.Boolean(string="Customer Discount")

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _check_payable_receivable(self):
        # Do nothing – effectively disabling the constraint
        pass

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    x_studio_tax_value = fields.Float(string="Tax Value", related='tax_ids.amount')
    x_studio_taxed_amount = fields.Monetary(string="Taxed Amount", compute="_compute_x_studio_taxed_amount")

    @api.depends('price_total', 'price_subtotal')
    def _compute_x_studio_taxed_amount(self):
        for record in self:
            # Same tax amount shown on the invoice line itself: the
            # difference between the tax-included and untaxed totals,
            # both already computed by Odoo's own tax engine.
            record.x_studio_taxed_amount = record.price_total - record.price_subtotal
    # account_type = fields.Many2one(string="Account Type", related='account_id.user_type_id', readonly=True, store=True)
    # balance = fields.Monetary(string="Balance", related='partner_id.total_due')
    # move_type = fields.Selection(string="Move Type", related='move_id.move_type')

    def get_initial_balance(self, partner, date):
        # company = self.env.user.company_id.id
        moves = self.env['account.move.line'].search([('date', '<', date), ('partner_id', '=', partner.id), (
            'account_id.account_type', 'in', ('asset_receivable', 'liability_payable')), ('parent_state', '=', 'posted')])
        balance = 0
        forign = False
        if self._context.get('curr', False):
            if self._context.get('curr', False).name == 'EGP':
                forign = False
            else:
                forign = True
        if not forign:
            for move in moves:
                balance = balance + move.debit
                balance = balance - move.credit
        else:
            for move in moves:
                balance = balance + move.amount_currency
                # balance = balance - move.credit

        # convert this code to be sql query for performance
        # query = """
        #     SELECT SUM(debit) - SUM(credit) as balance
        #     FROM account_move_line
        #     WHERE date < %s AND partner_id = %s AND account_id IN (SELECT id FROM account_account WHERE user_type_id IN (SELECT id FROM account_account_type WHERE name IN ('Receivable', 'المدين', 'Payable', 'الدائن'))) AND parent_state = 'posted'
        # """
        return balance

    exclude_from_report = fields.Boolean(string="Exclude From Report")


class AccountAccount(models.Model):
    _inherit = 'account.account'

    is_safty_account = fields.Boolean('Safty Account')
    is_collection_account = fields.Boolean('Collection Account')
    customer_allowed_discount = fields.Boolean('Customer Allowed Discount')
