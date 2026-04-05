# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # def fields_view_get(self, cr, uid, view_id=None, view_type='tree', context=None, toolbar=False, submenu=False):
    #     res = super(AccountMoveLine, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type,
    #         context=context, toolbar=toolbar, submenu=submenu)
    #     print(res['fields'])
    #     # if view_type == 'form':
    #     #         doc = etree.XML(res['arch'])
    #     #         for node in doc.xpath("//field[@name='min_date']"):
    #     #                 node.set('readonly', "0")
    #     #                 setup_modifiers(node, res['fields']['min_date'])

    #     #         res['arch'] = etree.tostring(doc)
    #     return res


