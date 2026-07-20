{
    "name": "ICAMA Pesticide Registration Search",
    "version": "18.0.1.0.0",
    "summary": "Search and sync China ICAMA pesticide registration data by name, category or dosage form, in Chinese or English",
    "description": """
ICAMA Pesticide Registration Search
====================================

Lets you define saved search terms (pesticide name / category / dosage form /
registration number) and periodically pulls matching records from the public
ICAMA pesticide registration query system (https://www.icama.cn) via a
scheduled cron job. Results are stored locally as Pesticide Registration
records that you can search, filter and report on inside Odoo.

Search criteria and results work in Chinese or English: type either
language into a saved search, and every record is stored with both its
original Chinese fields and English translations. Translation is done
with a static dictionary for ICAMA's fixed regulatory vocabulary
(category / dosage form), plus calls to the Lara Translate API (via
its official Python SDK - configure your credentials under Settings)
for free-text fields (name / holder), with a no-configuration Google
Translate fallback if no credentials are set or the 'lara-sdk' Python
package (pip install lara-sdk) isn't installed on the server.

Each synced record is also auto-linked (by exact, case-insensitive English
name match) to your x_r_d and x_contact_vendor records, so ICAMA data
connects straight into your existing R&D product / vendor master data. No
new records are created by this link - it only connects to what already
exists, and can be re-run any time from the Action menu.

Features
--------
* Saved search terms with name / category / dosage form / registration no.
* Search criteria and results in Chinese or English
* Auto-link to internal R&D product and vendor records by English name
* Manual "Search Now" button for on-demand sync
* Scheduled cron job to refresh all active search terms automatically
* Deduplicated storage keyed on registration number
* Error/status tracking per search term
""",
    "category": "Manufacturing/Quality",
    "author": "Custom Development",
    "license": "LGPL-3",
    "depends": ["base", "mail", "base_automation"],
    "external_dependencies": {
        "python": ["requests", "lxml"],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/pesticide_registration_views.xml",
        "views/pesticide_search_term_views.xml",
        "views/pesticide_translation_cache_views.xml",
        "views/res_config_settings_views.xml",
        "views/menu_views.xml",
        "data/ir_cron_data.xml",
        "data/automated_action_data.xml",
    ],
    "installable": True,
    "application": True,
}
