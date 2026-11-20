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
            db.add_product('P2', 'New panel', 'Panels', 'Nos', 10)
        self.assertEqual(db.rows("SELECT stock FROM products WHERE sku='P2'")[0]['stock'], 10)
        history = db.rows(db.STOCK_HISTORY)
        self.assertEqual([(row['Movement'], row['Quantity']) for row in history], [('Receipt', 10)])

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
