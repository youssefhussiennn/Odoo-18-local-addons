from odoo import fields, models


class SalesBonusReport(models.TransientModel):
    """Creating sales bonus report model."""
    _name = 'sales.bonus.report'
    _description = 'Sales Bonus Report'

    sales_person_id = fields.Many2one('res.users', string='Sales Person',
                                      help="Sales person")
    partner_id = fields.Many2one('res.partner', string='Partner',
                                      help="Partner")
    start_date = fields.Date(string='Start Date', help="Start date")
    end_date = fields.Date(string='End Date', help="End date")

    def action_print_report(self):
        """To create a report for sale bonus for a sales person"""
        data = {
            'sales_person_id': self.sales_person_id.name,
            'partner_id': self.partner_id.name,
            'start_date': self.start_date,
            'end_date': self.end_date,
        }
        return self.env.ref(
            'bonus_module.sales_bonus_report_action'
        ).report_action(self, data=data)

    def action_print_xlsx_report(self):
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'partner_id': self.partner_id.id if self.partner_id else False
        }

        domain = [('commission_type', '!=', 'بونص عملاء')]   ## Just add it for Euro server
        # domain = []

        if data['partner_id']:
            domain.append(('partner_id', '=', data['partner_id']))

        if data['start_date']:
            domain.append(('invoice_date', '>=', data['start_date']))

        if data['end_date']:
            domain.append(('invoice_date', '<=', data['end_date']))

        # Filter bonuses within configuration date range
        bonus_config_domain = [
            '|',
            '&',
            ('date_start', '<=', self.end_date),
            ('date_end', '>=', self.start_date),
            '&',
            ('date_start', '<=', self.end_date),
            ('date_end', '>=', self.start_date)
        ]

        applicable_bonuses = self.env['sales.bonus'].search(bonus_config_domain)

        if not applicable_bonuses:
            domain.append(('id', '=', False))
        else:
            applicable_partners = applicable_bonuses.mapped('partner_id.id')
            applicable_products = applicable_bonuses.mapped('product_based_ids.product_id.id')

            if applicable_partners:
                domain.append(('partner_id', 'in', applicable_partners))

            if applicable_products:
                domain.append(('product_id.product_tmpl_id', 'in', applicable_products))

        doc_ids = self.env['account.invoice.report'].search(domain).ids
        bonus_values = self._get_bonus_values(doc_ids)

        data.update({
            'doc_ids': doc_ids,
            'bonus_values': bonus_values if bonus_values else [],
        })

        return self.env.ref('bonus_module.action_sales_bonus_xlsx').report_action(self, data=data)

    def action_print_xlsx_report_new(self):
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'partner_id': self.partner_id.id if self.partner_id else False
        }

        domain = [('commission_type', '!=', 'بونص عملاء')]   ## Just add it for Euro server
        # domain = []

        if data['partner_id']:
            domain.append(('partner_id', '=', data['partner_id']))

        if data['start_date']:
            domain.append(('invoice_date', '>=', data['start_date']))

        if data['end_date']:
            domain.append(('invoice_date', '<=', data['end_date']))

        bonus_config_domain = [
            '|',
            '&',
            ('date_start', '<=', self.end_date),
            ('date_end', '>=', self.start_date),
            '&',
            ('date_start', '<=', self.end_date),
            ('date_end', '>=', self.start_date)
        ]

        applicable_bonuses = self.env['sales.bonus'].search(bonus_config_domain)
        applicable_partners = applicable_bonuses.mapped('partner_id.id')
        applicable_products = applicable_bonuses.mapped('product_based_ids.product_id.id')

        if applicable_partners:
            domain.append(('partner_id', 'in', applicable_partners))

        if applicable_products:
            domain.append(('product_id.product_tmpl_id', 'in', applicable_products))

        doc_ids = self.env['account.invoice.report'].search(domain).ids
        bonus_values = self._get_bonus_values(doc_ids)

        data.update({
            'doc_ids': doc_ids,
            'bonus_values': bonus_values if bonus_values else [],
        })

        return self.env.ref('bonus_module.action_sales_bonus_xlsx_summary').report_action(self, data=data)

    def _get_bonus_values(self, doc_ids):
        """Get bonus values for the specified document IDs."""
        bonus_values = []

        for doc_id in doc_ids:
            invoice = self.env['account.invoice.report'].browse(doc_id)
            partner_id = invoice.partner_id.id
            invoice_date = invoice.invoice_date

            # IMPORTANT: use template instead of variant
            product_ids = invoice.mapped('product_id.product_tmpl_id.id')

            applicable_bonuses = self.env['sales.bonus'].search([
                ('partner_id', '=', partner_id),
                ('product_based_ids.product_id', 'in', product_ids),
                ('date_start', '<=', invoice_date),
                ('date_end', '>=', invoice_date)
            ])

            for bonus_record in applicable_bonuses:
                for product_line in bonus_record.product_based_ids:

                    for template in product_line.product_id:
                        if template.id in product_ids:
                            bonus_values.append({
                                'partner_id': partner_id,
                                'product_id': template.id,
                                'bonus': product_line.bonus,
                                'invoice_date': invoice_date,
                                'date_start': bonus_record.date_start,
                                'date_end': bonus_record.date_end
                            })

        return bonus_values