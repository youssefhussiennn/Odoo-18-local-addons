# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, models
from odoo.tools import groupby
from ..models.location_stock_sql import VARIANT_LOCATION_SQL


class StockLocationReport(models.AbstractModel):
    """To generate report based on query and get report values"""
    _name = "report.stock_analysis_by_location_report.report_stock_location"

    @api.model
    def _get_report_values(self, docids, data=None):
        """ To get the report values based on the user giving conditions """
        value = self.query_data(data['report_type'], data['product_id'],
                                data['product_variant_id'])
        grouped_data = {}
        for product_id, group in (
                groupby(value, key=lambda x: x['product'])):
            grouped_data[product_id] = list(group)
        return {
            'grouped_data': grouped_data,
            'var': value
        }

    def query_data(self, report_type, product_id, product_variant_id):
        """ To fetch values from database using query """
        name = """COALESCE(pt.name->>%(lang)s, pt.name->>'en_US')"""
        params = {'lang': self.env.lang or 'en_US'}
        where = ""
        if report_type == 'product':
            if product_id:
                where = "WHERE pt.id = %(product_id)s"
                params['product_id'] = product_id
        elif product_variant_id:
            where = "WHERE pp.id = %(product_variant_id)s"
            params['product_variant_id'] = product_variant_id
        query = """
            SELECT %s AS product,
                   sl.complete_name AS location,
                   SUM(base.on_hand_qty) AS on_hand_qty,
                   SUM(base.qty_incoming) AS qty_incoming,
                   SUM(base.qty_outgoing) AS qty_outgoing,
                   SUM(base.forecast_qty) AS forecast_qty
              FROM (%s) base
              JOIN product_product pp ON pp.id = base.product_id
              JOIN product_template pt ON pt.id = pp.product_tmpl_id
              JOIN stock_location sl ON sl.id = base.location_id
              %s
             GROUP BY pt.id, sl.id
             ORDER BY product, location
        """ % (name, VARIANT_LOCATION_SQL, where)
        self.env.cr.execute(query, params)
        return self.env.cr.dictfetchall()
