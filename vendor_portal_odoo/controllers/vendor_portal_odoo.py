# -*- coding: utf-8 -*-

from collections import OrderedDict
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import pager as portal_pager, CustomerPortal


class RFQCustomerPortal(CustomerPortal):

    # -----------------------------
    # HOME COUNTER
    # -----------------------------
    def _prepare_home_portal_values(self, counters):
            values = super()._prepare_home_portal_values(counters)

            partner = request.env.user.partner_id

            if 'my_rfq_count' in counters:
                values['my_rfq_count'] = request.env['purchase.order'].sudo().search_count([
                    ('partner_id', '=', partner.id),
                    ('state', 'in', ['sent', 'to approve', 'purchase'])
                ])

            return values

    # -----------------------------
    # RFQ LIST PAGE
    # -----------------------------
    @http.route([
        '/my/vendor_rfqs',
        '/my/vendor_rfqs/page/<int:page>'
    ], type='http', auth="user", website=True)
    def portal_my_vendor_rfqs(self, page=1, date_begin=None,
                              date_end=None, sortby=None, filterby=None, **kw):

        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        PurchaseOrder = request.env['purchase.order'].sudo()

        domain = [
            ('partner_id', '=', partner.id),
            ('state', 'in', ['sent', 'to approve'])
        ]

        # -----------------------------
        # Date filter
        # -----------------------------
        if date_begin and date_end:
            domain += [
                ('create_date', '>', date_begin),
                ('create_date', '<=', date_end)
            ]

        # -----------------------------
        # Sorting
        # -----------------------------
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Reference'), 'order': 'name asc'},
        }

        sortby = sortby or 'date'
        order = searchbar_sortings[sortby]['order']

        # -----------------------------
        # Filters
        # -----------------------------
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'rfq': {'label': _('RFQs'), 'domain': [('state', '=', 'sent')]},
            # 'purchase': {'label': _('Purchase Orders'), 'domain': [('state', '=', 'purchase')]},
        }

        filterby = filterby or 'all'
        domain += searchbar_filters[filterby]['domain']

        # -----------------------------
        # Count
        # -----------------------------
        total = PurchaseOrder.search_count(domain)

        # -----------------------------
        # Pager
        # -----------------------------
        pager = portal_pager(
            url="/my/vendor_rfqs",
            url_args={
                'date_begin': date_begin,
                'date_end': date_end,
                'sortby': sortby,
                'filterby': filterby
            },
            total=total,
            page=page,
            step=self._items_per_page
        )

        # -----------------------------
        # Records
        # -----------------------------
        orders = PurchaseOrder.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )

        values.update({
            'orders': orders,
            'page_name': 'vendor_rfq',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'default_url': '/my/vendor_rfqs',
        })

        return request.render("vendor_portal_odoo.portal_my_rfq", values)

    # -----------------------------
    # RFQ DETAIL PAGE (CRASH-PROOF)
    # -----------------------------
    @http.route([
        '/my/vendor_rfq/<int:order_id>'
    ], type='http', auth="user", website=True)
    def portal_my_vendor_rfq(self, order_id, access_token=None, **kw):

        # SAFE FETCH (NO BROKEN MIXINS)
        order = request.env['purchase.order'].sudo().browse(order_id)

        if not order.exists():
            return request.not_found()

        # SECURITY CHECK (portal-safe)
        if order.partner_id != request.env.user.partner_id:
            return request.not_found()

        # SAFE QUOTE FETCH
        vendor_quote = request.env['vendor.quote.history'].sudo().search([
            ('order_id', '=', order.id),
            ('vendor_id', '=', request.env.user.partner_id.id)
        ], limit=1)


        # SAFE VALUES ONLY (NO INTERNAL ODOO MIXINS)
        values = {
            'page_name': 'vendor_rfq',
            'order': order,
            'order_lines': order.order_line,
            'vendor_quote': vendor_quote,
            'quoted_price': vendor_quote.quoted_price if vendor_quote else 0.0,
            'discount': vendor_quote.discount if vendor_quote else 0.0,
        }

        return request.render(
            "vendor_portal_odoo.portal_my_vendor_rfq",
            values
        )

    # -----------------------------
    # SUBMIT QUOTE (SAFE)
    # -----------------------------
    @http.route([
        '/quote/details'
    ], type='http', auth="user", website=True, csrf=False)
    def quote_details(self, **post):

        order_id = int(post.get('rfq_id') or 0)
        price = float(post.get('price') or 0.0)
        discount = float(post.get('discount') or 0.0)
        delivery_date = post.get('delivery_date')
        note = post.get('additional_note')

        order = request.env['purchase.order'].sudo().browse(order_id)

        if not order.exists():
            return request.not_found()

        if order.partner_id != request.env.user.partner_id:
            return request.not_found()
        
        for line in order.order_line:
            line.sudo().write({
                'price_unit': price,
                'discount': discount,
            })
            
        request.env['vendor.quote.history'].sudo().create({
            'order_id': order.id,
            'vendor_id': request.env.user.partner_id.id,
            'quoted_price': price,
            'discount': discount,
            'estimate_date': delivery_date,
            'note': note,
        })

        return request.redirect(f'/my/vendor_rfq/{order.id}')
    
    @http.route(['/quote/update_price'], type='http', auth="user", website=True, csrf=True)
    def update_price(self, **post):

        line_id = int(post.get('line_id'))
        price = float(post.get('price') or 0.0)
        discount = float(post.get('discount') or 0.0)
        order_id = int(post.get('order_id'))

        line = request.env['purchase.order.line'].sudo().browse(line_id)

        if not line.exists():
            return request.not_found()

        # security check (VERY IMPORTANT)
        if line.order_id.partner_id != request.env.user.partner_id:
            return request.not_found()

        line.write({
            'price_unit': price,
            'discount' : discount,
        })

        return request.redirect(f'/my/vendor_rfq/{order_id}')