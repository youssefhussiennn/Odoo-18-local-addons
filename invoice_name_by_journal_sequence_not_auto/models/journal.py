# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountJournal(models.AbstractModel):
    _inherit = 'account.journal'

    sequence_id = fields.Many2one('ir.sequence', string='Entry Sequence',
                                  help="This field contains the information related to the numbering of the journal entries of this journal.",
                                  required=True, copy=False)
    refund_sequence_id = fields.Many2one('ir.sequence', string='Credit Note Entry Sequence',
                                         help="This field contains the information related to the numbering of the credit note entries of this journal.",
                                         copy=False)
    sequence_number_next = fields.Integer(string='Next Number',
                                          help='The next sequence number will be used for the next invoice.',
                                          compute='_compute_seq_number_next',
                                          inverse='_inverse_seq_number_next')
    refund_sequence_number_next = fields.Integer(string='Credit Notes Next Number',
                                                 help='The next sequence number will be used for the next credit note.',
                                                 compute='_compute_refund_seq_number_next',
                                                 inverse='_inverse_refund_seq_number_next')

    # do not depend on 'sequence_id.date_range_ids', because
    # sequence_id._get_current_sequence() may invalidate it!
    @api.depends('sequence_id.use_date_range', 'sequence_id.number_next_actual')
    def _compute_seq_number_next(self):
        '''Compute 'sequence_number_next' according to the current sequence in use,
        an ir.sequence or an ir.sequence.date_range.
        '''
        for journal in self:
            if journal.sequence_id:
                sequence = journal.sequence_id._get_current_sequence()
                journal.sequence_number_next = sequence.number_next_actual
            else:
                journal.sequence_number_next = 1

    def _inverse_seq_number_next(self):
        '''Inverse 'sequence_number_next' to edit the current sequence next number.
        '''
        for journal in self:
            if journal.sequence_id and journal.sequence_number_next:
                sequence = journal.sequence_id._get_current_sequence()
                sequence.sudo().number_next = journal.sequence_number_next

    # do not depend on 'refund_sequence_id.date_range_ids', because
    # refund_sequence_id._get_current_sequence() may invalidate it!
    @api.depends('refund_sequence_id.use_date_range', 'refund_sequence_id.number_next_actual')
    def _compute_refund_seq_number_next(self):
        '''Compute 'sequence_number_next' according to the current sequence in use,
        an ir.sequence or an ir.sequence.date_range.
        '''
        for journal in self:
            if journal.refund_sequence_id and journal.refund_sequence:
                sequence = journal.refund_sequence_id._get_current_sequence()
                journal.refund_sequence_number_next = sequence.number_next_actual
            else:
                journal.refund_sequence_number_next = 1

    def _inverse_refund_seq_number_next(self):
        '''Inverse 'refund_sequence_number_next' to edit the current sequence next number.
        '''
        for journal in self:
            if journal.refund_sequence_id and journal.refund_sequence and journal.refund_sequence_number_next:
                sequence = journal.refund_sequence_id._get_current_sequence()
                sequence.sudo().number_next = journal.refund_sequence_number_next

    @api.model
    def _get_sequence_prefix(self, code, refund=False):
        prefix = code.upper()
        if refund:
            prefix = 'R' + prefix
        return prefix + '/%(range_year)s/'

    @api.model
    def _create_sequence(self, vals, refund=False):
        """ Create new no_gap entry sequence for every new Journal"""
        prefix = self._get_sequence_prefix(vals['code'], refund)
        seq_name = refund and vals['code'] + _(': Refund') or vals['code']
        seq = {
            'name': _('%s Sequence') % seq_name,
            'implementation': 'no_gap',
            'prefix': prefix,
            'padding': 4,
            'number_increment': 1,
            'use_date_range': False,
        }
        if 'company_id' in vals:
            seq['company_id'] = vals['company_id']
        seq = self.env['ir.sequence'].create(seq)
        seq_date_range = seq._get_current_sequence()
        seq_date_range.number_next = refund and vals.get('refund_sequence_number_next', 1) or vals.get(
            'sequence_number_next', 1)
        return seq

    @api.model
    def create(self, vals):
        # If no code provided, loop to find next available journal code
        if 'code' not in vals:
            raise UserError(_("Cannot generate an unused journal code. Please fill the 'Shortcode' field."))

        # We just need to create the relevant sequences according to the chosen options
        if not vals.get('sequence_id'):
            vals.update({'sequence_id': self.sudo()._create_sequence(vals).id})
        if vals.get('type') in ('sale', 'purchase') and vals.get('refund_sequence') and not vals.get(
                'refund_sequence_id'):
            vals.update({'refund_sequence_id': self.sudo()._create_sequence(vals, refund=True).id})

        journal = super(AccountJournal, self.with_context(mail_create_nolog=True)).create(vals)
        return journal

    def write(self, vals):
        print(vals)
        if not self.sequence_id and 'code' in vals:
            vals.update({'sequence_id': self.sudo()._create_sequence_write(vals).id})
        if not self.refund_sequence_id and 'code' in vals:
            vals.update({'refund_sequence_id': self.sudo()._create_sequence_write(vals, refund=True).id})
            
        return super(AccountJournal, self).write(vals)

    @api.model
    def _create_sequence_write(self, vals, refund=False):
        """ Create new no_gap entry sequence for every new Journal"""
        prefix = vals['code'].upper()
        if refund:
            prefix = 'R' + prefix
        prefix = prefix + '/%(range_year)s/'
        seq_name = refund and vals['code'] + _(': Refund') or vals['code']
        seq = {
            'name': _('%s Sequence') % seq_name,
            'implementation': 'no_gap',
            'prefix': prefix,
            'padding': 4,
            'number_increment': 1,
            'use_date_range': False,
        }
        seq = self.env['ir.sequence'].create(seq)
        return seq