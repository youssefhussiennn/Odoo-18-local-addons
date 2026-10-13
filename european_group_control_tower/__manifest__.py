{
    "name": "European Group Control Tower",
    "version": "18.0.1.0.0",
    "category": "Inventory/Purchase",
    "summary": "Purchase orders, shipments, tracking, payments and documents on one control tower.",
    "description": """
European Group | Control Tower
===============================
Purchase Orders -> Shipments -> Tracking -> Payments -> Documents -> Customs -> Warehouse -> Reports.

* Single-page control tower UI (React) embedded in Odoo as a client action.
* All data is stored in Odoo models (egct.*) and secured by Odoo access groups.
* Excel / CSV import with column mapping, XLSX / CSV export, printable reports.
""",
    "author": "European Group",
    "license": "LGPL-3",
    "depends": ["base", "web"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/egct_views.xml",
        "views/menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "european_group_control_tower/static/src/js/**/*",
            "european_group_control_tower/static/src/scss/**/*",
        ],
    },
    "application": True,
    "installable": True,
    "auto_install": False,
}
