"""Tests for Invoice Controller."""
import unittest
import os
import tempfile
from datetime import date
from models.user import User
from models.supplier import Supplier
from models.invoice import Invoice
from models.invoice_item import InvoiceItem
from models.nominal_account import NominalAccount
from models.journal_entry import JournalEntry
from controllers.invoice_controller import InvoiceController


class TestInvoiceController(unittest.TestCase):
    """Test cases for Invoice Controller."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary database for each test
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        
        # Initialize models
        self.user_model = User(db_path=self.temp_db.name)
        self.supplier_model = Supplier(db_path=self.temp_db.name)
        self.invoice_model = Invoice(db_path=self.temp_db.name)
        self.invoice_item_model = InvoiceItem(db_path=self.temp_db.name)
        self.nominal_account_model = NominalAccount(db_path=self.temp_db.name)
        self.journal_entry_model = JournalEntry(db_path=self.temp_db.name)
        
        # Create a test user
        self.user_model.create_user("testuser", "password123")
        success, _, user_id = self.user_model.authenticate("testuser", "password123")
        self.assertTrue(success)
        self.user_id = user_id
        
        # Create required accounts for journal entries
        self._create_test_accounts()
        
        # Create a test supplier
        self.supplier_model.create("SUP001", "Test Supplier", self.user_id)
        suppliers = self.supplier_model.get_all(self.user_id)
        self.supplier_id = suppliers[0]['internal_id']
        
        # Create controller
        self.controller = InvoiceController(
            self.invoice_model,
            self.invoice_item_model,
            self.user_id
        )
    
    def _create_test_accounts(self):
        """Create test nominal accounts."""
        # Trade Creditors
        self.nominal_account_model.create(
            2100, "Trade Creditors", "Liability", "Current Liability", 0.0, False, self.user_id
        )
        # Stock Asset
        self.nominal_account_model.create(
            1500, "Stock", "Asset", "Current Asset", 0.0, False, self.user_id
        )
        # Expense Account
        self.nominal_account_model.create(
            5100, "Expenses", "Expense", "Expenses", 0.0, False, self.user_id
        )
        # VAT Input
        self.nominal_account_model.create(
            1600, "VAT Input", "Asset", "Current Asset", 0.0, False, self.user_id
        )
    
    def tearDown(self):
        """Clean up after tests."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_add_invoice_item_creates_journal_entry(self):
        """Test that adding an invoice item creates journal entries."""
        # Create invoice
        success, _, invoice_id = self.invoice_model.create(
            self.supplier_id, "INV001", "2024-01-01", 20.0, self.user_id
        )
        self.assertTrue(success)
        
        # Add invoice item
        success, message, item_id = self.controller.add_invoice_item(
            invoice_id, None, "ITEM001", "Test Item", 1.0, 100.0, "S", None
        )
        self.assertTrue(success)
        self.assertIsNotNone(item_id)
        
        # Verify item was created
        items = self.invoice_item_model.get_by_invoice(invoice_id)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['description'], "Test Item")
        
        # Verify journal entries were created
        entries = self.journal_entry_model.get_all(self.user_id)
        # Should have at least one entry (net purchase) and possibly VAT entry
        self.assertGreater(len(entries), 0)
        
        # Check for supplier invoice entry
        supplier_entries = [e for e in entries if e.get('transaction_type') == 'Supplier Invoice']
        self.assertGreater(len(supplier_entries), 0)
    
    def test_add_invoice_item_with_vat_creates_vat_entry(self):
        """Test that adding an invoice item with VAT code S creates VAT Input entry."""
        # Create invoice
        success, _, invoice_id = self.invoice_model.create(
            self.supplier_id, "INV002", "2024-01-01", 20.0, self.user_id
        )
        self.assertTrue(success)
        
        # Add invoice item with VAT
        success, _, item_id = self.controller.add_invoice_item(
            invoice_id, None, "ITEM002", "VAT Item", 1.0, 100.0, "S", None
        )
        self.assertTrue(success)
        
        # Verify VAT Input journal entry was created
        entries = self.journal_entry_model.get_all(self.user_id)
        vat_entries = [e for e in entries if e.get('transaction_type') == 'Supplier Invoice VAT']
        self.assertGreater(len(vat_entries), 0)
        
        # Verify VAT amount is correct (20% of 100 = 20)
        vat_entry = vat_entries[0]
        self.assertAlmostEqual(vat_entry['amount'], 20.0, places=2)
    
    def test_add_invoice_item_without_vat_no_vat_entry(self):
        """Test that adding an invoice item with VAT code E doesn't create VAT entry."""
        # Create invoice
        success, _, invoice_id = self.invoice_model.create(
            self.supplier_id, "INV003", "2024-01-01", 20.0, self.user_id
        )
        self.assertTrue(success)
        
        # Add invoice item without VAT (Exempt)
        success, _, item_id = self.controller.add_invoice_item(
            invoice_id, None, "ITEM003", "Exempt Item", 1.0, 100.0, "E", None
        )
        self.assertTrue(success)
        
        # Verify no VAT Input journal entry was created
        entries = self.journal_entry_model.get_all(self.user_id)
        vat_entries = [e for e in entries if e.get('transaction_type') == 'Supplier Invoice VAT']
        self.assertEqual(len(vat_entries), 0)
    
    def test_update_invoice_item_reverses_and_creates_new_entries(self):
        """Test that updating an invoice item reverses old entries and creates new ones."""
        # Create invoice
        success, _, invoice_id = self.invoice_model.create(
            self.supplier_id, "INV004", "2024-01-01", 20.0, self.user_id
        )
        self.assertTrue(success)
        
        # Add invoice item
        success, _, item_id = self.controller.add_invoice_item(
            invoice_id, None, "ITEM004", "Test Item", 1.0, 100.0, "S", None
        )
        self.assertTrue(success)
        
        # Get initial entry count
        initial_entries = self.journal_entry_model.get_all(self.user_id)
        initial_count = len(initial_entries)
        
        # Update invoice item
        success, message = self.controller.update_invoice_item(item_id, 2.0, 150.0)
        self.assertTrue(success)
        
        # Verify item was updated
        items = self.invoice_item_model.get_by_invoice(invoice_id)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['quantity'], 2.0)
        self.assertEqual(items[0]['unit_price'], 150.0)
        
        # Verify reversal entries were created
        entries = self.journal_entry_model.get_all(self.user_id)
        reversal_entries = [e for e in entries if 'Reversal' in e.get('transaction_type', '')]
        self.assertGreater(len(reversal_entries), 0)
        
        # Verify new entries were created
        self.assertGreater(len(entries), initial_count)
    
    def test_delete_invoice_item_reverses_entries(self):
        """Test that deleting an invoice item reverses journal entries."""
        # Create invoice
        success, _, invoice_id = self.invoice_model.create(
            self.supplier_id, "INV005", "2024-01-01", 20.0, self.user_id
        )
        self.assertTrue(success)
        
        # Add invoice item
        success, _, item_id = self.controller.add_invoice_item(
            invoice_id, None, "ITEM005", "Test Item", 1.0, 100.0, "S", None
        )
        self.assertTrue(success)
        
        # Get initial entry count
        initial_entries = self.journal_entry_model.get_all(self.user_id)
        initial_count = len(initial_entries)
        
        # Delete invoice item
        success, message = self.controller.delete_invoice_item(item_id)
        self.assertTrue(success)
        
        # Verify item was deleted
        items = self.invoice_item_model.get_by_invoice(invoice_id)
        self.assertEqual(len(items), 0)
        
        # Verify reversal entries were created
        entries = self.journal_entry_model.get_all(self.user_id)
        reversal_entries = [e for e in entries if 'Reversal' in e.get('transaction_type', '')]
        self.assertGreater(len(reversal_entries), 0)
        self.assertGreater(len(entries), initial_count)
    
    def test_add_invoice_item_preserves_item_data(self):
        """Test that invoice item data is preserved after creation."""
        # Create invoice
        success, _, invoice_id = self.invoice_model.create(
            self.supplier_id, "INV006", "2024-01-01", 20.0, self.user_id
        )
        self.assertTrue(success)
        
        # Add invoice item
        success, _, item_id = self.controller.add_invoice_item(
            invoice_id, None, "ITEM006", "Test Item", 2.0, 50.0, "S", None
        )
        self.assertTrue(success)
        
        # Verify item data is correct
        items = self.invoice_item_model.get_by_invoice(invoice_id)
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item['stock_number'], "ITEM006")
        self.assertEqual(item['description'], "Test Item")
        self.assertEqual(item['quantity'], 2.0)
        self.assertEqual(item['unit_price'], 50.0)
        self.assertEqual(item['line_total'], 100.0)
        self.assertEqual(item['vat_code'], "S")
    
    def test_add_multiple_invoice_items(self):
        """Test adding multiple items to an invoice."""
        # Create invoice
        success, _, invoice_id = self.invoice_model.create(
            self.supplier_id, "INV007", "2024-01-01", 20.0, self.user_id
        )
        self.assertTrue(success)
        
        # Add multiple items
        for i in range(3):
            success, _, item_id = self.controller.add_invoice_item(
                invoice_id, None, f"ITEM{i+1}", f"Item {i+1}", 1.0, 100.0 * (i+1), "S", None
            )
            self.assertTrue(success)
        
        # Verify all items were created
        items = self.invoice_item_model.get_by_invoice(invoice_id)
        self.assertEqual(len(items), 3)
        
        # Verify journal entries were created for each
        entries = self.journal_entry_model.get_all(self.user_id)
        supplier_entries = [e for e in entries if e.get('transaction_type') == 'Supplier Invoice']
        self.assertGreaterEqual(len(supplier_entries), 3)


if __name__ == "__main__":
    unittest.main()

