import tempfile
import unittest
from pathlib import Path
import database as db

class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original = db.DB_PATH
        db.DB_PATH = Path(self.temp.name) / 'test.db'
        db.init()
        self.pid = db.execute("INSERT INTO products(sku,name,category,variant,unit,cost,price,minimum) VALUES('P1','Panel','Panels','TOPCon','Nos',100,120,2)")

    def tearDown(self):
        db.DB_PATH = self.original
        self.temp.cleanup()

    def test_receipt_issue_and_returns(self):
        for kind, quantity in [('Receipt',10),('Issue',4),('Customer return',1),('Supplier return',2)]:
            db.move(self.pid,kind,quantity,100,None,None,'TEST','')
        self.assertEqual(db.rows('SELECT stock FROM products')[0]['stock'],5)
        self.assertEqual(len(db.rows('SELECT * FROM movements')),4)

    def test_overdraw_does_not_change_stock_or_ledger(self):
        db.move(self.pid,'Receipt',3,100,None,None,'OPEN','')
        with self.assertRaises(ValueError):
            db.move(self.pid,'Issue',4,100,None,None,'OUT','')
        self.assertEqual(db.rows('SELECT stock FROM products')[0]['stock'],3)
        self.assertEqual(len(db.rows('SELECT * FROM movements')),1)

    def test_invalid_reference_and_quantity(self):
        for quantity, reference in [(0,'REF'),(1,' ')]:
            with self.assertRaises(ValueError):
                db.move(self.pid,'Receipt',quantity,100,None,None,reference,'')

    def test_dashboard_totals_keep_units_separate_and_count_returns(self):
        cable_id = db.execute("INSERT INTO products(sku,name,category,variant,unit,cost,price,minimum) VALUES('C1','Cable','Cables','AC','Metres',0,0,0)")
        for kind, quantity in [('Receipt', 10), ('Issue', 4), ('Customer return', 1), ('Supplier return', 2)]:
            db.move(self.pid, kind, quantity, 0, None, None, 'TEST', '')
        db.move(cable_id, 'Receipt', 50, 0, None, None, 'CABLE-OPEN', '')

        products, _, totals, _ = db.inventory_snapshot()
        per_sku = {p['sku']: (p['stock_in'], p['stock_out'], p['stock']) for p in products}
        self.assertEqual(per_sku, {'P1': (11, 6, 5), 'C1': (50, 0, 50)})
        self.assertEqual(totals, [
            {'Unit': 'Metres', 'Stock in': 50, 'Stock out': 0, 'On hand': 50},
            {'Unit': 'Nos', 'Stock in': 11, 'Stock out': 6, 'On hand': 5},
        ])

    def test_stock_history_shows_dispatch_destination(self):
        db.move(self.pid, 'Receipt', 10, 0, None, None, 'Receive stock', '')
        db.move(self.pid, 'Issue', 4, 0, None, None, 'Send stock', '', destination='Job Site A')
        history = db.rows(db.STOCK_HISTORY)
        self.assertEqual(history[0]['Sent to'], 'Job Site A')
        self.assertEqual(history[0]['Quantity'], 4)
        self.assertIsNone(history[1]['Sent to'])
        self.assertEqual(db.dispatch_history(), [history[0]])
        self.assertEqual(db.rows('SELECT stock FROM products')[0]['stock'], 6)

    def test_add_product_records_first_delivery_once(self):
        db.add_product('P2', 'New panel', 'Panels', 'Nos', 10)
        with self.assertRaises(db.IntegrityError):
            db.add_product('P2', 'Different panel', 'Panels', 'Nos', 10)
        self.assertEqual(db.rows("SELECT stock FROM products WHERE sku='P2'")[0]['stock'], 10)
        history = db.rows(db.STOCK_HISTORY)
        self.assertEqual([(row['Movement'], row['Quantity']) for row in history], [('Receipt', 10)])

    def test_add_same_product_records_a_delivery_on_the_existing_row(self):
        for name, category in [('Waaree panel', 'Panels'), ('Solar inverter', 'Inverters')]:
            with self.subTest(category=category):
                self.assertTrue(db.add_product(category, name, category, 'Nos', 17, source='Supplier A'))
                self.assertFalse(db.add_product(category + '-NEW', '  ' + name.upper().replace(' ', '   '),
                                                category, 'Nos', 6, source='Supplier B'))
                with self.assertRaises(ValueError):
                    db.add_product(category + '-OTHER', name, category, 'Kg', 2)
                products = [p for p in db.overview_products() if p['name'] == name]
                self.assertEqual([(p['sku'], p['stock'], p['latest_received']) for p in products],
                                 [(category, 23, 6)])
                receipts = [r for r in db.receipt_history() if r['Product'] == name]
                self.assertEqual([(r['Quantity'], r['Received from']) for r in receipts],
                                 [(6, 'Supplier B'), (17, 'Supplier A')])

    def test_repeated_deliveries_show_latest_quantity_and_dispatch_only_reduces_stock(self):
        db.add_product('W1', 'Waaree panel', 'Panels', 'Nos', 17, source='Waaree')
        product = next(p for p in db.overview_products() if p['sku'] == 'W1')
        self.assertEqual((product['stock'], product['latest_received']), (17, 17))

        for quantity, expected_stock in [(6, 23), (2, 25)]:
            db.move(product['id'], 'Receipt', quantity, 0, None, None, 'Receive stock', '', source='Distributor')
            current = next(p for p in db.overview_products() if p['sku'] == 'W1')
            self.assertEqual((current['stock'], current['latest_received']), (expected_stock, quantity))
            self.assertEqual(current['stock_before_receipt'], expected_stock - quantity)

        db.move(product['id'], 'Issue', 4, 0, None, None, 'Send stock', '', destination='Job Site A')
        current = next(p for p in db.overview_products() if p['sku'] == 'W1')
        self.assertEqual((current['stock'], current['latest_received']), (21, 2))
        self.assertEqual(current['stock_before_receipt'], 23)
        self.assertEqual([(r['Quantity'], r['Received from']) for r in db.receipt_history()],
                         [(2, 'Distributor'), (6, 'Distributor'), (17, 'Waaree')])
        self.assertEqual(db.dispatch_history()[0]['Sent to'], 'Job Site A')

    def test_edit_stock_and_last_received_independently(self):
        db.move(self.pid, 'Receipt', 10, 0, None, None, 'Receive stock', '', source='Supplier')
        db.move(self.pid, 'Issue', 4, 0, None, None, 'Send stock', '', destination='Site')
        before = db.overview_products()[0]
        db.edit_product(before, 'Panel', 'Panels', 5, 12)
        updated = db.overview_products()[0]
        self.assertEqual((updated['stock'], updated['latest_received']), (5, 12))
        self.assertEqual((updated['stock_in'], updated['stock_out']), (12, 7))
        self.assertEqual([(r['Quantity'], r['Received from']) for r in db.receipt_history()], [(12, 'Supplier')])
        self.assertEqual([r['Quantity'] for r in db.dispatch_history()], [4])
        with self.assertRaises(ValueError):
            db.edit_product(before, 'Panel', 'Panels', 8, 10)
        db.edit_product(updated, 'Panel', 'Panels', 5, 0)
        corrected = db.overview_products()[0]
        self.assertEqual((corrected['stock'], corrected['latest_received']), (5, 0))
        self.assertEqual(db.receipt_history()[0]['Quantity'], 0)
        db.edit_product(corrected, 'Panel', 'Panels', 0, 0)
        self.assertEqual(db.overview_products()[0]['stock'], 0)

    def test_legacy_database_keeps_receipts_and_accepts_zero_corrections(self):
        db.DB_PATH = Path(self.temp.name) / 'legacy.db'
        legacy_schema = db.SCHEMA.replace(
            "CONSTRAINT movements_receipt_quantity_check\n"
            "              CHECK(quantity>0 OR (quantity=0 AND kind IN ('Receipt', 'Customer return')))",
            'CHECK(quantity>0)',
        )
        with db.connect() as connection:
            connection.executescript(legacy_schema)
        db.add_product('OLD', 'Existing panel', 'Panels', 'Nos', 8, source='Supplier')
        db.init()
        product = db.overview_products()[0]
        db.edit_product(product, 'Existing panel', 'Panels', 8, 0)
        self.assertEqual([(r['Quantity'], r['Received from']) for r in db.receipt_history()], [(0, 'Supplier')])

    def test_merge_duplicates_preserves_current_balance_and_movement_history(self):
        db.move(self.pid, 'Receipt', 36, 0, None, None, 'Receive stock', '', source='Supplier A')
        db.move(self.pid, 'Issue', 15, 0, None, None, 'Send stock', '', destination='Job Site A')
        duplicate_id = db.execute(
            "INSERT INTO products(sku,name,category,variant,unit,cost,price,minimum) "
            "VALUES('P2','  PANEL  ','Panels','TOPCon','Nos',100,120,2)"
        )
        db.move(duplicate_id, 'Receipt', 36, 0, None, None, 'Receive stock', '', source='Supplier B')
        products = db.overview_products()
        db.merge_duplicate_products(products)
        self.assertEqual([(p['id'], p['stock'], p['latest_received']) for p in db.overview_products()],
                         [(self.pid, 57, 36)])
        self.assertEqual([m['Received from'] for m in db.receipt_history()], ['Supplier B', 'Supplier A'])
        self.assertEqual(db.dispatch_history()[0]['Sent to'], 'Job Site A')
        with self.assertRaises(ValueError):
            db.merge_duplicate_products(products)

    def test_delete_mistaken_product_removes_only_its_first_delivery(self):
        db.add_product('NEW', 'Mistaken entry', 'Panels', 'Nos', 8)
        pid = db.rows("SELECT id FROM products WHERE sku='NEW'")[0]['id']
        db.delete_mistaken_product(pid, 'NEW')
        self.assertEqual([product['sku'] for product in db.overview_products()], ['P1'])
        self.assertEqual(db.rows(db.STOCK_HISTORY), [])

    def test_delete_mistaken_product_preserves_later_movements(self):
        db.add_product('NEW', 'Active product', 'Panels', 'Nos', 8)
        pid = db.rows("SELECT id FROM products WHERE sku='NEW'")[0]['id']
        db.move(pid, 'Issue', 2, 0, None, None, 'Send stock', '', destination='Job Site A')
        with self.assertRaises(ValueError):
            db.delete_mistaken_product(pid, 'NEW')
        self.assertEqual(db.rows("SELECT stock FROM products WHERE sku='NEW'")[0]['stock'], 6)
        self.assertEqual(len(db.rows(db.STOCK_HISTORY)), 2)

if __name__ == '__main__':
    unittest.main()
