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
"""Shared SQL for the stock-by-location reports.

product.template / product.product qty_incoming / qty_outgoing are NOT stored
columns, so they cannot be selected in raw SQL. Instead, the quantities are
computed per (variant, internal location) from stock_quant and pending
stock_move records:
  * incoming: pending moves entering the location from outside internal stock
  * outgoing: pending moves leaving the location to outside internal stock
"""

PENDING_STATES = "('waiting', 'confirmed', 'assigned', 'partially_available')"

# One row per (product_id [variant], location_id) with float quantities.
VARIANT_LOCATION_SQL = """
    WITH quant AS (
        SELECT sq.product_id, sq.location_id, SUM(sq.quantity) AS qty
          FROM stock_quant sq
          JOIN stock_location sl ON sl.id = sq.location_id
         WHERE sl.usage = 'internal'
         GROUP BY sq.product_id, sq.location_id
    ), incoming AS (
        SELECT sm.product_id, sm.location_dest_id AS location_id,
               SUM(sm.product_qty) AS qty
          FROM stock_move sm
          JOIN stock_location src ON src.id = sm.location_id
          JOIN stock_location dst ON dst.id = sm.location_dest_id
         WHERE sm.state IN %(states)s
           AND dst.usage = 'internal' AND src.usage != 'internal'
         GROUP BY sm.product_id, sm.location_dest_id
    ), outgoing AS (
        SELECT sm.product_id, sm.location_id AS location_id,
               SUM(sm.product_qty) AS qty
          FROM stock_move sm
          JOIN stock_location src ON src.id = sm.location_id
          JOIN stock_location dst ON dst.id = sm.location_dest_id
         WHERE sm.state IN %(states)s
           AND src.usage = 'internal' AND dst.usage != 'internal'
         GROUP BY sm.product_id, sm.location_id
    ), keys AS (
        SELECT product_id, location_id FROM quant
        UNION SELECT product_id, location_id FROM incoming
        UNION SELECT product_id, location_id FROM outgoing
    )
    SELECT k.product_id,
           k.location_id,
           COALESCE(q.qty, 0)::float AS on_hand_qty,
           COALESCE(i.qty, 0)::float AS qty_incoming,
           COALESCE(o.qty, 0)::float AS qty_outgoing,
           (COALESCE(q.qty, 0) + COALESCE(i.qty, 0)
            - COALESCE(o.qty, 0))::float AS forecast_qty
      FROM keys k
      LEFT JOIN quant q ON q.product_id = k.product_id
                       AND q.location_id = k.location_id
      LEFT JOIN incoming i ON i.product_id = k.product_id
                          AND i.location_id = k.location_id
      LEFT JOIN outgoing o ON o.product_id = k.product_id
                          AND o.location_id = k.location_id
""".replace('%(states)s', PENDING_STATES)
