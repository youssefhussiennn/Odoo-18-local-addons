from odoo import api, models, fields


class SalesBonusReportAbstract(models.AbstractModel):
    """To create report for sales bonus"""
    _name = 'report.bonus_module.report_sales_bonus'
    _description = 'Sales Bonus Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """To get values for the report for sales bonus for a partner"""

        
        bonus_values = []
        sale_bonus_report = []
        

        
        if docids:
            sale_bonus_report = self.env['account.invoice.report'].browse(docids)
        else:
            
            domain = []
            if data:
                if data.get('partner_id'):
                    domain.append(('partner_id', '=', data['partner_id']))
                if data.get('start_date'):
                    domain.append(('invoice_date', '>=', data['start_date']))
                if data.get('end_date'):
                    domain.append(('invoice_date', '<=', data['end_date']))
            
            
            sale_bonus_report = self.env['account.invoice.report'].search(domain)
        
        
        for invoice in sale_bonus_report:
            
            partner_id = invoice.partner_id.id
            product_ids = invoice.mapped('product_id.product_tmpl_id.id') 

            
            sales_bonus = self.env['sales.bonus'].search([
                ('partner_id', '=', partner_id),
                ('product_based_ids.product_id', 'in', product_ids)  
            ])
            
            
            for bonus_record in sales_bonus:
                for product_line in bonus_record.product_based_ids:
                   
                    for product in product_line.product_id.product_tmpl_id:
                        if product.id in product_ids:
                            bonus_values.append({
                                'partner_id': partner_id,
                                'product_id': product.id,
                                'bonus': product_line.bonus
                            })
                       

        
        return {
            'doc_ids': docids,
            'doc_model': 'account.invoice.report',
            'docs': sale_bonus_report,
            'data': data,
            'bonus_values': bonus_values 
        }
