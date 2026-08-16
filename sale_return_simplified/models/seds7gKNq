# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SaleReturn(models.Model):
    _name = 'sale.return'
    _description = 'Simplified Sales Return'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    # ── Identity ──────────────────────────────────────────────────────────────
    name = fields.Char(
        string='Reference',
        required=True,
        readonly=True,
        default=lambda self: _('New'),
        copy=False,
        tracking=True,
    )
    state = fields.Selection([
        ('draft',     'Draft'),
        ('done',      'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, copy=False)

    # ── Header ────────────────────────────────────────────────────────────────
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        domain=[('customer_rank', '>', 0)],
        tracking=True,
    )
    return_date = fields.Date(
        string='Return Date',
        required=True,
        default=fields.Date.today,
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        required=True,
        default=lambda self: self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.company.id)], limit=1
        ),
    )
    reason = fields.Text(string='Return Reason')
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
    )

    # ── Product lines (user fills these) ──────────────────────────────────────
    product_line_ids = fields.One2many(
        'sale.return.product.line',
        'return_id',
        string='Products to Return',
    )

    # ── Invoice lines (auto-filled after confirm, read-only) ──────────────────
    invoice_line_ids = fields.One2many(
        'sale.return.invoice.line',
        'return_id',
        string='Invoices Used',
    )

    # ── Smart buttons ─────────────────────────────────────────────────────────
    picking_id = fields.Many2one('stock.picking', string='Return Transfer', copy=False)
    credit_note_ids = fields.Many2many('account.move', string='Credit Notes', copy=False)
    credit_note_count = fields.Integer(compute='_compute_credit_note_count')

    @api.depends('credit_note_ids')
    def _compute_credit_note_count(self):
        for rec in self:
            rec.credit_note_count = len(rec.credit_note_ids)

    # ─────────────────────────────────────────────────────────────────────────
    # ORM
    # ─────────────────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.return') or _('New')
        return super().create(vals_list)

    # ─────────────────────────────────────────────────────────────────────────
    # Actions
    # ─────────────────────────────────────────────────────────────────────────

    def action_confirm(self):
        self.ensure_one()
        self._validate_before_confirm()
        self._process_stock_return()
        self._process_credit_notes()
        self.state = 'done'

    def action_cancel(self):
        self.ensure_one()
        if self.state == 'done':
            raise UserError(_('Cannot cancel a completed return.'))
        self.state = 'cancelled'

    def action_reset_draft(self):
        self.ensure_one()
        if self.state != 'cancelled':
            raise UserError(_('Only cancelled returns can be reset to draft.'))
        self.state = 'draft'

    def action_view_picking(self):
        self.ensure_one()
        return {
            'type':      'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id':    self.picking_id.id,
        }

    def action_view_credit_notes(self):
        self.ensure_one()
        return {
            'type':      'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain':    [('id', 'in', self.credit_note_ids.ids)],
            'context':   {'default_move_type': 'out_refund'},
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Validation
    # ─────────────────────────────────────────────────────────────────────────

    def _validate_before_confirm(self):
        if not self.product_line_ids:
            raise UserError(_('Please add at least one product to return.'))
        for line in self.product_line_ids:
            if line.return_qty <= 0:
                raise ValidationError(_(
                    'Return quantity must be greater than zero for product %s.',
                    line.product_id.name,
                ))

    # ─────────────────────────────────────────────────────────────────────────
    # Stock return — one transfer for all products
    # ─────────────────────────────────────────────────────────────────────────

    def _process_stock_return(self):
        customer_location = self.env.ref('stock.stock_location_customers')
        dest_location     = self.warehouse_id.lot_stock_id

        picking_type = self.env['stock.picking.type'].search([
            ('code',         '=', 'incoming'),
            ('warehouse_id', '=', self.warehouse_id.id),
        ], limit=1)

        if not picking_type:
            raise UserError(_('No incoming operation type found for warehouse %s.', self.warehouse_id.name))

        move_vals = []
        for line in self.product_line_ids:
            move_vals.append((0, 0, {
                'name':             line.product_id.display_name,
                'product_id':       line.product_id.id,
                'product_uom':      line.product_id.uom_id.id,
                'product_uom_qty':  line.return_qty,
                'location_id':      customer_location.id,
                'location_dest_id': dest_location.id,
            }))

        picking = self.env['stock.picking'].create({
            'picking_type_id':  picking_type.id,
            'partner_id':       self.partner_id.id,
            'location_id':      customer_location.id,
            'location_dest_id': dest_location.id,
            'origin':           self.name,
            'move_ids':         move_vals,
        })

        picking.action_confirm()
        picking.action_assign()

        for move in picking.move_ids:
            if move.move_line_ids:
                for move_line in move.move_line_ids:
                    move_line.quantity = move.product_uom_qty
            else:
                move.write({'quantity': move.product_uom_qty})

        picking._action_done()
        self.picking_id = picking.id

    # ─────────────────────────────────────────────────────────────────────────
    # Credit notes — auto distribute newest → oldest per product
    # ─────────────────────────────────────────────────────────────────────────

    def _process_credit_notes(self):
        credit_notes      = self.env['account.move']
        invoice_line_log  = []  # rows for the read-only invoice lines tab

        for product_line in self.product_line_ids:
            remaining_qty = product_line.return_qty

            # Fetch posted invoice lines for this customer + product, newest first
            inv_lines = self.env['account.move.line'].search([
                ('move_id.partner_id', '=', self.partner_id.id),
                ('move_id.move_type', '=', 'out_invoice'),
                ('move_id.state',     '=', 'posted'),
                ('product_id',        '=', product_line.product_id.id),
                ('quantity',          '>',  0),
            ], order='move_id desc')

            if not inv_lines:
                raise UserError(_(
                    'No posted invoices found for customer %s with product %s.',
                    self.partner_id.name, product_line.product_id.name,
                ))

            for inv_line in inv_lines:
                if remaining_qty <= 0:
                    break

                qty_from_this = min(remaining_qty, inv_line.quantity)
                remaining_qty -= qty_from_this

                # Create credit note for this invoice line
                credit_note = self.env['account.move'].create({
                    'move_type':    'out_refund',
                    'partner_id':   self.partner_id.id,
                    'invoice_date': self.return_date,
                    'ref':          _('Return: %s / %s', self.name, inv_line.move_id.name),
                    'invoice_origin': self.name,
                    'invoice_line_ids': [(0, 0, {
                        'product_id': product_line.product_id.id,
                        'quantity':   qty_from_this,
                        'price_unit': inv_line.price_unit,
                        'name': '%s - %s' % (product_line.product_id.display_name, self.reason or self.name),
                    })],
                })
                credit_note.action_post()
                self._reconcile_credit_note(credit_note, inv_line.move_id)
                credit_notes |= credit_note

                # Log for the invoice lines tab
                invoice_line_log.append({
                    'return_id':      self.id,
                    'product_id':     product_line.product_id.id,
                    'invoice_id':     inv_line.move_id.id,
                    'invoice_date':   inv_line.move_id.invoice_date,
                    'return_qty':     qty_from_this,
                    'price_unit':     inv_line.price_unit,
                    'credit_note_id': credit_note.id,
                })

            if remaining_qty > 0:
                raise UserError(_(
                    'Not enough invoiced quantity to cover the return for product %s. '
                    'Missing %.2f %s.',
                    product_line.product_id.name,
                    remaining_qty,
                    product_line.product_id.uom_id.name,
                ))

        self.credit_note_ids = [(6, 0, credit_notes.ids)]

        # Write the read-only invoice breakdown
        if invoice_line_log:
            self.env['sale.return.invoice.line'].create(invoice_line_log)

    def _reconcile_credit_note(self, credit_note, invoice):
        reconcilable_credit = credit_note.line_ids.filtered(
            lambda l: l.account_id.account_type == 'asset_receivable' and not l.reconciled
        )
        reconcilable_invoice = invoice.line_ids.filtered(
            lambda l: l.account_id.account_type == 'asset_receivable' and not l.reconciled
        )
        if reconcilable_credit and reconcilable_invoice:
            (reconcilable_credit | reconcilable_invoice).reconcile()
