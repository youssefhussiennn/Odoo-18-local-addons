from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase, tagged


def line(product='Widget', qty=10, unit_price=2.5, unit='KG'):
    return {'product': product, 'qty': qty, 'unit': unit, 'unitPrice': unit_price}


@tagged('post_install', '-at_install')
class TestEgctApi(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.api = cls.env['egct.api']
        group_user = cls.env.ref('european_group_control_tower.group_egct_user')
        cls.user = cls.env['res.users'].create({
            'name': 'Control Tower User', 'login': 'egct_user', 'email': 'egct_user@example.com',
            'groups_id': [(6, 0, [group_user.id])],
        })

    # -- helpers ---------------------------------------------------------
    def _make_po(self, number='P100', lines=None, **extra):
        res = self.api.save_po(dict({'id': '', 'poNumber': number, 'currency': 'USD',
                                     'lines': lines if lines is not None else [line()]}, **extra))
        return self.env['egct.po'].browse(int(res['id']))

    def _dataset(self):
        """A client-shaped dataset like the one built by the JS importer from an Excel file."""
        return {
            'suppliers': [{'id': 's-acme', 'company': 'ACME  Ltd', 'country': 'Spain'}],
            'pos': [
                {'id': 'po-P1', 'poNumber': 'p1', 'poDate': '2026-01-05', 'supplierId': 's-acme', 'rep': 'Mona',
                 'category': 'Fertilizer', 'currency': 'EUR', 'notes': '',
                 'lines': [line('A', 100, 2), line('B', 50, 1)]},
                {'id': 'po-P2', 'poNumber': 'P2', 'poDate': '', 'supplierId': '', 'rep': '', 'category': '',
                 'currency': 'USD', 'notes': '', 'lines': []},
            ],
            'shipments': [
                {'id': 'sh-P1', 'poId': 'po-P1', 'stage': 'At Sea', 'bl': 'BL1', 'eta': '2026-03-01', 'etd': '2026-02-01',
                 'customs': 'Not Started', 'acid': '123', 'notes': ''},
                {'id': 'sh-P2', 'poId': 'po-P2', 'stage': 'Booked', 'customs': 'Not Started'},
            ],
            'payments': [
                {'id': 'pay-P1', 'poId': 'po-P1', 'invoice': 'INV1', 'total': 250, 'paid': 100, 'dueDate': '2026-04-01'},
                {'id': 'pay-P2', 'poId': 'po-P2', 'total': 0, 'paid': 0},
            ],
            'documents': [
                {'id': 'doc-P1-bl', 'poId': 'po-P1', 'type': 'Bill of Lading', 'status': 'Received', 'reference': 'BL1'},
                {'id': 'doc-P1-acid', 'poId': 'po-P1', 'type': 'ACID', 'status': 'Received', 'reference': '123'},
            ],
        }

    # -- tests -----------------------------------------------------------
    def test_empty_dataset_shape(self):
        res = self.api.bootstrap()
        self.assertEqual(set(res['data']), {'suppliers', 'pos', 'shipments', 'payments', 'documents', 'activity'})
        self.assertTrue(res['user']['isManager'])  # test runs as superuser

    def test_po_creation_creates_shipment_and_payment(self):
        po = self._make_po('p100', [line(qty=10, unit_price=2.5), line('Other', 4, 1)])
        self.assertEqual(po.name, 'P100')
        self.assertAlmostEqual(po.total_amount, 29.0)
        self.assertEqual(po.shipment_ids.stage, 'PO Issued')
        self.assertAlmostEqual(po.payment_ids.total, 29.0)
        data = self.api.get_dataset()
        self.assertEqual(data['pos'][0]['id'], str(po.id))
        self.assertEqual(data['shipments'][0]['poId'], str(po.id))
        self.assertEqual(len(data['pos'][0]['lines']), 2)

    def test_po_update_keeps_synced_payment_in_step(self):
        po = self._make_po('P101', [line(qty=10, unit_price=2)])
        self.api.save_po({'id': str(po.id), 'poNumber': 'P101', 'currency': 'USD', 'lines': [line(qty=20, unit_price=2)]})
        self.assertAlmostEqual(po.payment_ids.total, 40.0)
        # once the payment total was edited by hand it is no longer synchronised
        po.payment_ids.total = 999.0
        self.api.save_po({'id': str(po.id), 'poNumber': 'P101', 'currency': 'USD', 'lines': [line(qty=1, unit_price=1)]})
        self.assertAlmostEqual(po.payment_ids.total, 999.0)
        self.assertAlmostEqual(po.total_amount, 1.0)

    def test_po_number_must_be_unique_and_present(self):
        self._make_po('P102')
        with self.assertRaises(UserError):
            self._make_po('p102')
        with self.assertRaises(UserError):
            self.api.save_po({'id': '', 'poNumber': '  ', 'lines': []})

    def test_delete_po_cascades(self):
        po = self._make_po('P103')
        self.api.save_record('documents', {'id': '', 'poId': str(po.id), 'type': 'Packing List', 'status': 'Received'}, 'document')
        self.api.delete_po(str(po.id))
        self.assertFalse(po.exists())
        for model in ('egct.shipment', 'egct.payment', 'egct.document'):
            self.assertFalse(self.env[model].search_count([]))

    def test_shipment_acid_creates_acid_document_and_one_shipment_per_po(self):
        po = self._make_po('P104')
        ship = po.shipment_ids
        res = self.api.save_record('shipments', {'id': str(ship.id), 'poId': str(po.id), 'stage': 'Booked', 'acid': '777'}, 'shipment')
        self.assertEqual(ship.stage, 'Booked')
        doc = po.document_ids.filtered(lambda d: d.type == 'ACID')
        self.assertEqual((doc.status, doc.reference), ('Received', '777'))
        self.assertTrue(any(s['acid'] == '777' for s in res['data']['shipments']))
        with self.assertRaises(UserError):
            self.api.save_record('shipments', {'id': '', 'poId': str(po.id), 'stage': 'Booked'}, 'shipment')

    def test_payment_status_is_computed(self):
        po = self._make_po('P105', [line(qty=10, unit_price=10)])
        pay = po.payment_ids
        self.assertEqual((pay.status, pay.remaining), ('Unpaid', 100.0))
        self.api.save_record('payments', {'id': str(pay.id), 'poId': str(po.id), 'total': 100, 'paid': 40}, 'payment')
        self.assertEqual((pay.status, pay.remaining), ('Partial', 60.0))
        self.api.save_record('payments', {'id': str(pay.id), 'poId': str(po.id), 'total': 100, 'paid': 100}, 'payment')
        self.assertEqual((pay.status, pay.remaining), ('Paid', 0.0))

    def test_supplier_with_orders_cannot_be_deleted(self):
        res = self.api.save_record('suppliers', {'id': '', 'company': 'Delta Co'}, 'supplier')
        sid = res['data']['suppliers'][0]['id']
        self._make_po('P106', supplierId=sid)
        with self.assertRaises(UserError):
            self.api.remove_record('suppliers', sid, 'supplier Delta Co')

    def test_import_merge_creates_then_updates_by_natural_key(self):
        self.api.import_dataset(self._dataset(), 'merge', 'test import')
        po = self.env['egct.po'].search([('name', '=', 'P1')])
        self.assertEqual(len(po), 1)
        self.assertEqual(po.supplier_id.name, 'ACME  Ltd')
        self.assertEqual(len(po.line_ids), 2)
        self.assertAlmostEqual(po.total_amount, 250.0)
        self.assertEqual(po.shipment_ids.stage, 'At Sea')
        self.assertEqual(po.payment_ids.status, 'Partial')
        self.assertEqual(len(po.document_ids), 2)

        # second import: the supplier is matched by normalised name, empty incoming values never erase data
        ds = self._dataset()
        ds['suppliers'][0]['company'] = 'acme ltd'
        ds['pos'][0].update({'lines': [], 'rep': ''})
        ds['shipments'][0].update({'stage': 'Arrived Port', 'bl': ''})
        self.api.import_dataset(ds, 'merge', 'second')
        self.assertEqual(self.env['egct.supplier'].search_count([]), 1)
        self.assertEqual(self.env['egct.po'].search_count([]), 2)
        self.assertEqual(len(po.line_ids), 2)
        self.assertEqual(po.rep, 'Mona')
        self.assertEqual(po.shipment_ids.stage, 'Arrived Port')
        self.assertEqual(po.shipment_ids.bl, 'BL1')
        self.assertEqual(len(po.document_ids), 2)

    def test_import_replace_needs_manager(self):
        self._make_po('OLD1')
        with self.assertRaises(AccessError):
            self.api.with_user(self.user).import_dataset(self._dataset(), 'replace', 'nope')
        self.assertTrue(self.env['egct.po'].search([('name', '=', 'OLD1')]))
        self.api.import_dataset(self._dataset(), 'replace', 'ok')
        self.assertFalse(self.env['egct.po'].search([('name', '=', 'OLD1')]))
        self.assertEqual(self.env['egct.po'].search_count([]), 2)
        # clearing everything is the same call with an empty dataset
        self.api.import_dataset({}, 'replace', 'clear')
        self.assertEqual(self.env['egct.po'].search_count([]), 0)
        self.assertEqual(self.env['egct.supplier'].search_count([]), 0)

    def test_plain_user_can_work_but_not_without_group(self):
        res = self.api.with_user(self.user).save_po({'id': '', 'poNumber': 'U1', 'currency': 'USD', 'lines': [line()]})
        self.assertTrue(res['id'])
        outsider = self.env['res.users'].create({'name': 'Outsider', 'login': 'egct_out', 'email': 'out@example.com'})
        with self.assertRaises(AccessError):
            self.api.with_user(outsider).bootstrap()

    def test_import_acid_updates_existing_and_creates_stubs(self):
        po = self._make_po('P107')
        res = self.api.import_acid([['p107', '555'], ['NEW9', '999'], ['', 'x'], ['EMPTY', '']])
        self.assertEqual(res['count'], 2)
        self.assertEqual(po.shipment_ids.acid, '555')
        self.assertEqual(po.document_ids.filtered(lambda d: d.type == 'ACID').reference, '555')
        stub = self.env['egct.po'].search([('name', '=', 'NEW9')])
        self.assertEqual(stub.shipment_ids.acid, '999')
        self.assertEqual(stub.payment_ids.total, 0.0)

    def test_activity_is_logged_and_limited(self):
        self._make_po('P108')
        acts = self.api.get_dataset()['activity']
        self.assertEqual(acts[0]['text'], 'Created PO P108')
        self.assertTrue(acts[0]['ts'].endswith('Z'))
