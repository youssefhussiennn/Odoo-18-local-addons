from odoo import models, fields, api, _, exceptions, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
import datetime
import base64
from datetime import date
from io import BytesIO
import xlsxwriter

class WizardGeneralLedgerInformationExcelReport(models.TransientModel):
    _name = 'wizard.account.statement.excel.report'
    _description = 'wizard Account Statement Xlsx report'
  
    namexlsx = fields.Char('File Name', size=64)
    reportxlsx = fields.Binary('Prepared File', readonly=True)

    namexlsx_no_sales = fields.Char('Excel File Name ', size=64)
    reportxlsx_no_sales = fields.Binary('Prepared Excel File', readonly=True)