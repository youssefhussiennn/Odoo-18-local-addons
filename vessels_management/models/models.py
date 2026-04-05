from odoo import models, fields, api, _

from odoo.exceptions import ValidationError

class VesselsManagement(models.Model):
    _name = 'vessels_management.vessels_management'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'Vessels Management'

    # --- Basic Info ---
    name = fields.Char(string="Vessel Name", required=True, tracking=True)
    imo_no = fields.Char(string="IMO No", tracking=True)
    call_sign = fields.Char(string="Call Sign", tracking=True)
    mmsi_no = fields.Char(string="MMSI No", tracking=True)
    official_no = fields.Char(string="Official Number", tracking=True)
    vessel_type_ids = fields.Many2many(
    'vessels_management.vessel_type',
    'vessel_vessel_type_rel',  # 👈 shorter table name
    'vessel_id',
    'type_id',
    string="Vessel Types",
)
    
    flag = fields.Char(string="Flag", tracking=True)
    port_of_registry = fields.Char(string="Port of Registry", tracking=True)

    # --- Build Info ---
    built_yyyymm = fields.Char(string="Built YYYYMM (e.g. 190001)")
    mat_of_hull = fields.Char(string="Material of Hull")
    builder = fields.Char(string="Builder")
    yard_no = fields.Char(string="Yard No")
    dt_keel_laid = fields.Date(string="Date Keel Laid")

    # --- Measurements ---
    gt_itc69 = fields.Float(string="GT (ITC 69)")
    nt_itc69 = fields.Float(string="NT (ITC 69)")
    dead_weight_tonnage = fields.Float(string="Dead Weight Tonnage")
    summer_draught_m = fields.Float(string="Summer Draught (m)")
    depth_mld_m = fields.Float(string="Depth MLD (m)")
    breadth_ext_m = fields.Float(string="Breadth EXT (m)")
    breadth_mld_m = fields.Float(string="Breadth MLD (m)")
    length_oa_m = fields.Float(string="Length OA (m)")
    length_bp_m = fields.Float(string="Length BP (m)")
    speed = fields.Float(string="Speed (knots)")
    displacement_tonnes = fields.Float(string="Displacement (Tonnes)")

    # --- Capacity & Structure ---
    no_of_holds = fields.Integer(string="No of Holds")
    no_of_passenger = fields.Integer(string="No of Passenger")
    no_of_crew = fields.Integer(string="No of Crew")
    no_of_propulsion_units = fields.Integer(string="No of Propulsion Units")
    no_of_decks_in_cargo_area = fields.Integer(string="No of Decks in Cargo Area")

    # --- Ownership ---
    vessel_owner_id = fields.Many2one('res.partner', string="Beneficiery Owner", tracking=True)
    vessel_manager_id = fields.Many2one('res.partner', string="ISM Manager", tracking=True)
    vessel_registered_id = fields.Many2one('res.partner', string="Registered Owner", tracking=True)
    vessel_billing_contact = fields.Many2one('res.partner', string="Billing Contact", tracking=True)

    # --- Classification ---
    current_class = fields.Char(string="Current Class")
    status = fields.Selection([
        ('active', 'Active'),
        ('draft', 'In-active'),
        ('under_maintenance', 'Under Maintenance')], string="Status", default='active', tracking=True)
    
    _sql_constraints = [
        # Optional: ensure lowercase unique enforcement at DB level (but we’ll handle in Python below)
    ]

    @api.constrains('imo_no')
    def _check_unique_imo_no(self):
        for record in self:
            if not record.imo_no:
                continue  # Skip if blank

            # Case-insensitive match, ignoring 'N/A'
            if record.imo_no.strip().upper() == 'N/A':
                continue

            # Search for duplicates (case-insensitive)
            duplicate = self.search([
                ('imo_no', '=ilike', record.imo_no),
                ('id', '!=', record.id)
            ], limit=1)

            if duplicate:
                raise ValidationError(
                    _("The IMO number '%s' already exists for vessel '%s'. Only 'N/A' can be duplicated.")
                    % (record.imo_no, duplicate.name)
                )
    
    def action_inactive(self):
        self.write({'status': 'draft'})

    def action_active(self):
        self.write({'status': 'active'})

    def action_under_maintenance(self):
        self.write({'status': 'under_maintenance'})
        
        
    sale_order_count = fields.Integer(compute='compute_count_sales')
    # vessels_managed_count = fields.Integer(compute='compute_count_vessels_managed')

        
    def compute_count_sales(self):
        for record in self:
            record.sale_order_count = self.env['sale.order'].search_count([
                ('vessel_id', '=', record.id)
            ])
            
    def action_view_sale_orders(self):
        """Smart button action to view sale orders linked to this vessel"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sales Orders',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('vessel_id', '=', self.id)],
            'context': {'default_vessel_id': self.id},
        }
        
        
class VesselType(models.Model):
    _name = 'vessels_management.vessel_type'
    _description = 'Vessel Type'
    _rec_name = 'name'

    name = fields.Char(string="Vessel Type", required=True)
    color = fields.Integer(string="Color Index")
    
        
class ResPartner(models.Model):
    _inherit = 'res.partner'

    vessels_count = fields.Integer(compute='compute_count_vessels')
    # vessels_managed_count = fields.Integer(compute='compute_count_vessels_managed')

        
    def compute_count_vessels(self):
        for record in self:
            domain = [
                ('vessel_owner_id', '=', record.id),
            ]
            record.vessels_count = self.env['vessels_management.vessels_management'].search_count(domain)
            
    def action_view_vessels(self):
        """Smart button to show vessels owned by this partner"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vessels',
            'res_model': 'vessels_management.vessels_management',
            'view_mode': 'list,form',
            'domain': [('vessel_owner_id', '=', self.id)],
            'context': {'default_vessel_owner_id': self.id,'create': False},
        }
        
        
        
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    vessel_id = fields.Many2one(
        'vessels_management.vessels_management',
        string="Vessel",
        # domain="[('vessel_owner_id', '=', partner_id)]",
        help="Select the vessel owned by this customer."
    )

    # @api.onchange('partner_id')
    # def _onchange_partner_id(self):
    #     """Filter vessels by selected customer."""
    #     for order in self:
    #         if not order.partner_id:
    #             order.vessel_id = False
    #         else:
    #             # Reset vessel if it doesn't belong to new partner
    #             if order.vessel_id and order.vessel_id.vessel_owner_id != order.partner_id:
    #                 order.vessel_id = False
                    
    def action_create_project(self):
        self.ensure_one()

        if not self.show_create_project_button:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'danger',
                    'message': _("The project couldn't be created because the order must be confirmed or already has a project."),
                }
            }

        # 🔧 Base context from Odoo core
        sorted_line = self.order_line.sorted('sequence')
        default_sale_line = next((
            sol for sol in sorted_line
            if sol.product_id.type == 'service' and not sol.is_downpayment
        ), self.env['sale.order.line'])

        # 📦 Get original action
        action = super().action_create_project()

        # 🧠 Inject the vessel into the project creation wizard
        ctx = dict(action.get('context', {}))
        ctx.update({
            'default_sale_order_id': self.id,
            'default_sale_line_id': default_sale_line.id,
            'default_partner_id': self.partner_id.id,
            'default_user_ids': [self.env.uid],
            'default_allow_billable': 1,
            'hide_allow_billable': True,
            'default_company_id': self.company_id.id,
            'generate_milestone': default_sale_line.product_id.service_policy == 'delivered_milestones',
        })

        # ⚓ Add the vessel to context
        if self.vessel_id:
            ctx['default_vessel_id'] = self.vessel_id.id

        action['context'] = ctx
        return action
    
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def _timesheet_service_generation(self):
        res = super()._timesheet_service_generation()

        for line in self:
            # If a project was created automatically from this line
            if line.product_id.service_tracking == 'task_in_project' and line.order_id.vessel_id:
                project = line.project_id
                if project:
                    project.vessel_id = line.order_id.vessel_id.id

        return res

class ProjectProject(models.Model):
    _inherit = 'project.project'

    vessel_id = fields.Many2one('vessels_management.vessels_management', string='Vessel')
    
class ProjectTask(models.Model):
    _inherit = 'project.task'

    vessel_id = fields.Many2one(
        'vessels_management.vessels_management',
        string="Vessel",
        related='project_id.vessel_id',
        store=True,
        readonly=False,
        help="Vessel linked to this task, inherited from the project."
    )

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    vessel_id = fields.Many2one(
        'vessels_management.vessels_management',
        string="Vessel",
#         domain="[('vessel_owner_id', '=', partner_id)]",
        help="Select the vessel owned by this customer."
    )

#     @api.onchange('partner_id')
#     def _onchange_partner_id(self):
#         """Filter vessels by selected customer."""
#         for lead in self:
#             if not lead.partner_id:
#                 lead.vessel_id = False
#             else:
#                 # Reset vessel if it doesn't belong to new partner
#                 if lead.vessel_id and lead.vessel_id.vessel_owner_id != lead.partner_id:
#                     lead.vessel_id = False
