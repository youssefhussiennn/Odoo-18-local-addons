# -*- coding: utf-8 -*-
# from odoo import http


# class BudgetPlan(http.Controller):
#     @http.route('/budget_plan/budget_plan', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/budget_plan/budget_plan/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('budget_plan.listing', {
#             'root': '/budget_plan/budget_plan',
#             'objects': http.request.env['budget_plan.budget_plan'].search([]),
#         })

#     @http.route('/budget_plan/budget_plan/objects/<model("budget_plan.budget_plan"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('budget_plan.object', {
#             'object': obj
#         })

