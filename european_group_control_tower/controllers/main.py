import os

from odoo import http
from odoo.http import request
from odoo.tools import file_path

BUNDLE = 'european_group_control_tower/static/dist/egct.iife.js'


class ControlTowerController(http.Controller):
    """Thin JSON-RPC layer; every operation runs as the logged-in user (no sudo) so Odoo ACLs apply."""

    @property
    def _api(self):
        return request.env['egct.api']

    @http.route('/egct/info', type='json', auth='user')
    def info(self):
        """Tells the OWL client action which front-end bundle to load (versioned by file mtime for cache busting)."""
        try:
            version = int(os.path.getmtime(file_path(BUNDLE)))
        except (OSError, FileNotFoundError):
            version = 0
        return {'bundleUrl': f'/{BUNDLE}?v={version}'}

    @http.route('/egct/bootstrap', type='json', auth='user')
    def bootstrap(self):
        return self._api.bootstrap()

    @http.route('/egct/save', type='json', auth='user')
    def save(self, coll, rec, label=''):
        return self._api.save_record(coll, rec, label)

    @http.route('/egct/remove', type='json', auth='user')
    def remove(self, coll, id, label=''):
        return self._api.remove_record(coll, id, label)

    @http.route('/egct/po/save', type='json', auth='user')
    def po_save(self, po):
        return self._api.save_po(po)

    @http.route('/egct/po/delete', type='json', auth='user')
    def po_delete(self, id):
        return self._api.delete_po(id)

    @http.route('/egct/import', type='json', auth='user')
    def import_dataset(self, dataset, mode='merge', label=''):
        return self._api.import_dataset(dataset, mode, label)

    @http.route('/egct/import_acid', type='json', auth='user')
    def import_acid(self, items):
        return self._api.import_acid(items)
