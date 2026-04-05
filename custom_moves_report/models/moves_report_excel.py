from odoo import models, fields
from datetime import timedelta
import pytz

class MovesReportExcel(models.AbstractModel):
    _name = 'report.custom_moves_report.report_moves_excel'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):

        # Create a worksheet
        sheet = workbook.add_worksheet('Moves Report')

        # Report headers
        sheet.write(0, 0, 'Product Moves Report')
        sheet.write(1, 0, 'Start Date:')
        sheet.write(1, 1, str(data.get('date_start')))
        sheet.write(2, 0, 'End Date:')
        sheet.write(2, 1, str(data.get('date_stop')))

        # Table headers
        sheet.write(4, 0, 'Product')
        if not data.get('to_collapse'):  # Detailed view
            sheet.write(4, 1, 'Date')
            sheet.write(4, 2, 'Operation Type')
            sheet.write(4, 3, 'In')
            sheet.write(4, 4, 'Out')
            sheet.write(4, 5, 'Balance')
            sheet.write(4, 6, 'Partner')
            sheet.write(4, 7, 'Reference')
        else:  # Collapsed view
            sheet.write(4, 1, 'Opening Balance')
            sheet.write(4, 2, 'Total In')
            sheet.write(4, 3, 'Total Out')
            sheet.write(4, 4, 'Final Balance')

        # Variables
        products = self.env['product.product'].browse(data.get('product_ids'))
        location = data.get('location_id')
        date_start = fields.Datetime.from_string(data.get('date_start'))
        date_stop = fields.Datetime.from_string(data.get('date_stop'))

        # Search for relevant stock moves
        domain = [
            '&', '&', 
            ('state', '=', 'done'),
            ('product_id', 'in', data.get('product_ids')),
            ('date', '<=', fields.Datetime.to_string(date_stop)),
            '|',
            ('location_id', '=', location),
            ('location_dest_id', '=', location),
        ]
        all_moves = self.env['stock.move.line'].search(domain, order='date')

        row = 5  # Starting row for data
        grand_total_in = 0
        grand_total_out = 0
        grand_opening_balance = 0
        grand_balance = 0
        
        for product in products:
            total_out = 0
            total_in = 0
            opening_balance = 0
            balance = 0
            moves = all_moves.filtered(lambda r: r.product_id.id == product.id)

            if moves:
                # Opening balance
                balance = sum(
                    -move.qty_done if move.location_id.id == location else move.qty_done
                    for move in moves if move.date <= date_start
                )
                opening_balance = balance

                # Filter moves within the date range
                moves = moves.filtered(lambda r: r.date >= date_start)

                if data.get('to_collapse'):  # Collapsed view
                    for move in moves:
                        if location == move.location_id.id:
                            balance -= move.qty_done
                            total_out += move.qty_done
                        else:
                            balance += move.qty_done
                            total_in += move.qty_done

                    # Write summary row for the product
                    sheet.write(row, 0, product.display_name)
                    sheet.write(row, 1, opening_balance)
                    sheet.write(row, 2, total_in)
                    sheet.write(row, 3, total_out)
                    sheet.write(row, 4, balance)
                    
                    grand_total_in += total_in
                    grand_total_out += total_out
                    grand_opening_balance += opening_balance
                    grand_balance += balance
                    row += 1
                else:  # Detailed view
                    for move in moves:
                        if location == move.location_id.id:
                            in_qty = '--'
                            out_qty = move.qty_done
                            balance -= move.qty_done
                            total_out += move.qty_done
                        else:
                            in_qty = move.qty_done
                            out_qty = '--'
                            balance += move.qty_done
                            total_in += move.qty_done

                        # Write detailed row for the move
                        sheet.write(row, 0, product.display_name)
                        sheet.write(row, 1, fields.Datetime.to_string(move.date))  # Date
                        sheet.write(row, 2, self.substitute(move.picking_type_id.code))  # Operation Type
                        sheet.write(row, 3, in_qty)  # In
                        sheet.write(row, 4, out_qty)  # Out
                        sheet.write(row, 5, balance)  # Balance
                        sheet.write(row, 6, move.picking_id.partner_id.name or 'N/A')  # Partner
                        sheet.write(row, 7, move.reference or 'N/A')  # Reference
                        row += 1

                    # Update grand totals
                    grand_total_in += total_in
                    grand_total_out += total_out
                    grand_opening_balance += opening_balance
                    grand_balance += balance

        # Write the grand totals to the sheet
        if data.get('to_collapse'):
            row += 2
            sheet.write(row, 1, 'Grand Totals:')
            sheet.write(row + 1, 2, 'Total In:')
            sheet.write(row + 1, 3, grand_total_in)
            sheet.write(row + 2, 2, 'Total Out:')
            sheet.write(row + 2, 3, grand_total_out)
            sheet.write(row + 3, 2, 'Final Balance:')
            sheet.write(row + 3, 3, grand_balance)
        else:
            row += 2
            sheet.write(row, 5, 'Grand Opening Balance:')
            sheet.write(row, 6, grand_opening_balance)
            sheet.write(row + 1, 5, 'Grand Total In:')
            sheet.write(row + 1, 6, grand_total_in)
            sheet.write(row + 2, 5, 'Grand Total Out:')
            sheet.write(row + 2, 6, grand_total_out)
            sheet.write(row + 3, 5, 'Grand Final Balance:')
            sheet.write(row + 3, 6, grand_balance)

    @staticmethod
    def substitute(code):
        return code.replace('_', " ").title() if code else code
