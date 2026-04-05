from odoo import models


class AccountReportXlsx(models.AbstractModel):
    _name = 'report.kb_account_reports.report_account_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        domain = [('date', '<=', data['end_date']), ('date', '>=', data['start_date']), ('account_id', '=', data['account_id'])]
        if data['state'] == 'draft':
            state = 'Unposted'
            domain.append(('parent_state', '=', 'draft'))
        elif data['state'] == 'posted':
            state = 'Posted'
            domain.append(('parent_state', '=', 'posted'))
        else:
            state = 'All'
        move_line_ids = self.env['account.move.line'].search(domain, order='date asc, move_id DESC')
        
        domain = [ ('date', '<', data['start_date']), ('account_id', '=', data['account_id'])]
        if data['state'] == 'draft':
            state = 'Unposted'
            domain.append(('parent_state', '=', 'draft'))
        elif data['state'] == 'posted':
            state = 'Posted'
            domain.append(('parent_state', '=', 'posted'))
        else:
            state = 'All'
        move_balance = self.env['account.move.line'].search(domain)
        
        
        header_merge_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter',
                                                   'font_size': 10, 'bg_color': '#D3D3D3', 'border': 1})
        
        header_merge_format_currency = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter',
                                                   'font_size': 10, 'bg_color': '#ADD8E6', 'border': 1}) #light blue
        
        header_data_format = workbook.add_format({'align': 'center', 'valign': 'vcenter',
                                                  'font_size': 10, 'border': 1})

        monetary_format = workbook.add_format({'num_format': '$#,##0.00','align': 'center', 'valign': 'vcenter',
                                                  'font_size': 10, 'border': 1})  
        for line in move_line_ids:
            currency_symbol = line.currency_id.symbol
            
            monetary_format_line = workbook.add_format({'num_format': currency_symbol + '#,##0.00', 'align': 'center', 'valign': 'vcenter',
                                                      'font_size': 10, 'border': 1})

        worksheet = workbook.add_worksheet()
        worksheet.set_column('A:B', 18)
        worksheet.set_column('C:H', 12)
        worksheet.write(2, 0, 'Date From', header_merge_format)
        worksheet.write(3, 0, data.get('start_date'), header_data_format)
        worksheet.write(2, 1, 'Date To', header_merge_format)
        worksheet.write(3, 1, data.get('end_date'), header_data_format)
        worksheet.write(2, 2, 'Status', header_merge_format)
        worksheet.write(3, 2, state, header_data_format)
        worksheet.write(2, 3, 'Account', header_merge_format)
        worksheet.write(2, 5, 'Initial Balance', header_merge_format) 
        worksheet.write(2, 6, 'Closing Balance', header_merge_format)
        worksheet.write(2, 8, 'Initial Balance Currency', header_merge_format_currency) #Currency
        worksheet.write(2, 9, 'Closing Balance Currency', header_merge_format_currency) #Currency
        worksheet.write(3, 3, data.get('account_name'), header_data_format)

        worksheet.write(5, 0, 'Date', header_merge_format)
        worksheet.write(5, 1, 'Label', header_merge_format)
        worksheet.merge_range(5, 2, 5, 3, "Partner", header_merge_format)
        worksheet.write(5, 4, 'Sales Person', header_merge_format)  # Sales Person column
        worksheet.write(5, 5, 'Debit', header_merge_format)
        worksheet.write(5, 6, 'Credit', header_merge_format)
        worksheet.write(5, 7, 'Balance', header_merge_format) 

        worksheet.write(5, 8, 'Debit Currency', header_merge_format_currency)  #Currency
        worksheet.write(5, 9, 'Credit Currency', header_merge_format_currency) #Currency
        worksheet.write(5, 10, 'Balance Currency', header_merge_format_currency)  #Currency
        rows = 5
        
        balance = 0
        # balance_currency_initial = 0
        balance_currency = 0

        for x in move_balance:
            debit_currency = x.amount_currency if x.amount_currency > 0 else 0
            credit_currency = -x.amount_currency if x.amount_currency < 0 else 0
            balance = x.debit - x.credit + balance
            # balance_currency_initial = debit_currency - credit_currency + balance_currency_initial
            balance_currency = debit_currency - credit_currency + balance_currency

        worksheet.write(3, 5, balance, monetary_format_line)  # Display initial balance at the top
        worksheet.write(3, 8, balance_currency, monetary_format_line)  # Display initial balance Currency at the top
        rows += 1
        for line in move_line_ids:
            debit_currency = line.amount_currency if line.amount_currency > 0 else 0
            credit_currency = -line.amount_currency if line.amount_currency < 0 else 0
            print(type(line.date))
            worksheet.write(rows, 0, str(line.date.strftime("%d-%m-%Y")), header_data_format)
            worksheet.write(rows, 1, line.name, header_data_format)  # Label
            worksheet.merge_range(rows, 2, rows, 3, line.partner_id.name if line.partner_id else "", header_data_format) # Partner
            worksheet.write(rows, 4, line.partner_id.user_id.name if line.partner_id.user_id else "", header_data_format)  # Placeholder for Sales Person
            worksheet.write(rows, 5, line.debit, monetary_format_line)
            worksheet.write(rows, 6, line.credit, monetary_format_line)

            worksheet.write(rows, 8, debit_currency, monetary_format_line) #Currency
            worksheet.write(rows, 9, credit_currency, monetary_format_line) #Currency

            balance = line.debit - line.credit + balance
            balance_currency = debit_currency - credit_currency + balance_currency
            
            worksheet.write(rows, 7, balance, monetary_format) 
            worksheet.write(rows, 10, balance_currency, monetary_format)  
            rows += 1

        worksheet.write(3, 6, balance, monetary_format_line)  # Display closing balance at the top
        worksheet.write(3, 9, balance_currency, monetary_format_line)  # Display closing balance Currency at the top
        workbook.close()