"""Tests for Sales Controller."""
import unittest
import os
import tempfile
from datetime import date
from models.user import User
from models.customer import Customer
from models.sales_invoice import SalesInvoice
from models.sales_invoice_item import SalesInvoiceItem
from models.nominal_account import NominalAccount
from models.journal_entry import JournalEntry
from models.product import Product
from models.service import Service
from models.vehicle import Vehicle
from models.customer_payment import CustomerPayment
from models.customer_payment_allocation import CustomerPaymentAllocation
from controllers.sales_controller import SalesController


class TestSalesController(unittest.TestCase):
    """Test cases for Sales Controller."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary database for each test
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        
        # Initialize models
        self.user_model = User(db_path=self.temp_db.name)
        self.customer_model = Customer(db_path=self.temp_db.name)
        self.sales_invoice_model = SalesInvoice(db_path=self.temp_db.name)
        self.sales_invoice_item_model = SalesInvoiceItem(db_path=self.temp_db.name)
        self.nominal_account_model = NominalAccount(db_path=self.temp_db.name)
        self.journal_entry_model = JournalEntry(db_path=self.temp_db.name)
        
        # Create a test user
        self.user_model.create_user("testuser", "password123")
        success, _, user_id = self.user_model.authenticate("testuser", "password123")
        self.assertTrue(success)
        self.user_id = user_id
        
        # Create required accounts for journal entries
        self._create_test_accounts()
        
        # Create a test customer
        self.customer_model.create("CUST001", "Test Customer", self.user_id)
        customers = self.customer_model.get_all(self.user_id)
        self.customer_id = customers[0]['internal_id']
        
        # Create controller (we'll need to mock the view)
        from unittest.mock import MagicMock
        
        mock_view = MagicMock()
        mock_view.selected_document_id = None
        mock_view.show_success_dialog = MagicMock()
        mock_view.show_error_dialog = MagicMock()
        
        self.controller = SalesController(
            mock_view,
            self.sales_invoice_model,
            self.sales_invoice_item_model,
            CustomerPayment(db_path=self.temp_db.name),  # customer_payment_model
            CustomerPaymentAllocation(db_path=self.temp_db.name),  # customer_payment_allocation_model
            self.customer_model,
            Product(db_path=self.temp_db.name),  # product_model
            Service(db_path=self.temp_db.name),  # service_model
            Vehicle(db_path=self.temp_db.name),  # vehicle_model
            self.user_id
        )
    
    def _create_test_accounts(self):
        """Create test nominal accounts."""
        # Trade Debtors
        self.nominal_account_model.create(
            1400, "Trade Debtors", "Asset", "Current Asset", 0.0, False, self.user_id
        )
        # Sales
        self.nominal_account_model.create(
            4000, "Sales", "Income", "Turnover", 0.0, False, self.user_id
        )
        # VAT Output
        self.nominal_account_model.create(
            2200, "VAT Output", "Liability", "Current Liability", 0.0, False, self.user_id
        )
        # Cost of Sales
        self.nominal_account_model.create(
            5000, "Cost of Sales", "Expense", "Cost of Sales", 0.0, False, self.user_id
        )
        # Stock Asset
        self.nominal_account_model.create(
            1500, "Stock", "Asset", "Current Asset", 0.0, False, self.user_id
        )
    
    def tearDown(self):
        """Clean up after tests."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_add_sales_invoice_item_creates_journal_entry(self):
        """Test that adding a sales invoice item creates journal entries."""
        # Create sales invoice
        success, _, invoice_id = self.sales_invoice_model.create(
            self.customer_id, "2024-01-01", "invoice", "", self.user_id
        )
        self.assertTrue(success)
        
        # Add sales invoice item
        success, message, item_id = self.controller.handle_add_item(
            invoice_id, None, None, "ITEM001", "Test Item", 1.0, 100.0, "S"
        )
        self.assertTrue(success)
        self.assertIsNotNone(item_id)
        
        # Verify item was created
        items = self.sales_invoice_item_model.get_by_sales_invoice(invoice_id)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['description'], "Test Item")
        
        # Verify journal entries were created
        entries = self.journal_entry_model.get_all(self.user_id)
        # Should have at least one entry (net sales) and possibly VAT entry
        self.assertGreater(len(entries), 0)
        
        # Check for sales invoice entry
        sales_entries = [e for e in entries if e.get('transaction_type') == 'Sales Invoice']
        self.assertGreater(len(sales_entries), 0)
    
    def test_add_sales_invoice_item_with_vat_creates_vat_entry(self):
        """Test that adding a sales invoice item with VAT code S creates VAT Output entry."""
        # Create sales invoice
        success, _, invoice_id = self.sales_invoice_model.create(
            self.customer_id, "2024-01-01", "invoice", "", self.user_id
        )
        self.assertTrue(success)
        
        # Add sales invoice item with VAT
        success, _, item_id = self.controller.handle_add_item(
            invoice_id, None, None, "ITEM002", "VAT Item", 1.0, 100.0, "S"
        )
        self.assertTrue(success)
        
        # Verify VAT Output journal entry was created
        entries = self.journal_entry_model.get_all(self.user_id)
        vat_entries = [e for e in entries if e.get('transaction_type') == 'Sales Invoice VAT']
        self.assertGreater(len(vat_entries), 0)
        
        # Verify VAT amount is correct (20% of 100 = 20)
        vat_entry = vat_entries[0]
        self.assertAlmostEqual(vat_entry['amount'], 20.0, places=2)
    
    def test_add_sales_invoice_item_preserves_item_data(self):
        """Test that sales invoice item data is preserved after creation."""
        # Create sales invoice
        success, _, invoice_id = self.sales_invoice_model.create(
            self.customer_id, "2024-01-01", "invoice", "", self.user_id
        )
        self.assertTrue(success)
        
        # Add sales invoice item
        success, _, item_id = self.controller.handle_add_item(
            invoice_id, None, None, "ITEM003", "Test Item", 2.0, 50.0, "S"
        )
        self.assertTrue(success)
        
        # Verify item data is correct
        items = self.sales_invoice_item_model.get_by_sales_invoice(invoice_id)
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item['stock_number'], "ITEM003")
        self.assertEqual(item['description'], "Test Item")
        self.assertEqual(item['quantity'], 2.0)
        self.assertEqual(item['unit_price'], 50.0)
        self.assertEqual(item['line_total'], 100.0)
        self.assertEqual(item['vat_code'], "S")
    
    def test_update_sales_invoice_item_reverses_and_creates_new_entries(self):
        """Test that updating a sales invoice item reverses old entries and creates new ones."""
        # Create sales invoice
        success, _, invoice_id = self.sales_invoice_model.create(
            self.customer_id, "2024-01-01", "invoice", "", self.user_id
        )
        self.assertTrue(success)
        
        # Add sales invoice item
        success, _, item_id = self.controller.handle_add_item(
            invoice_id, None, None, "ITEM004", "Test Item", 1.0, 100.0, "S"
        )
        self.assertTrue(success)
        
        # Get initial entry count
        initial_entries = self.journal_entry_model.get_all(self.user_id)
        initial_count = len(initial_entries)
        
        # Update sales invoice item
        success, message = self.controller.handle_update_item(item_id, 2.0, 150.0)
        self.assertTrue(success)
        
        # Verify item was updated
        items = self.sales_invoice_item_model.get_by_sales_invoice(invoice_id)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['quantity'], 2.0)
        self.assertEqual(items[0]['unit_price'], 150.0)
        
        # Verify reversal entries were created
        entries = self.journal_entry_model.get_all(self.user_id)
        reversal_entries = [e for e in entries if 'Reversal' in e.get('transaction_type', '')]
        self.assertGreater(len(reversal_entries), 0)
        
        # Verify new entries were created
        self.assertGreater(len(entries), initial_count)
    
    def test_delete_sales_invoice_item_reverses_entries(self):
        """Test that deleting a sales invoice item reverses journal entries."""
        # Create sales invoice
        success, _, invoice_id = self.sales_invoice_model.create(
            self.customer_id, "2024-01-01", "invoice", "", self.user_id
        )
        self.assertTrue(success)
        
        # Add sales invoice item
        success, _, item_id = self.controller.handle_add_item(
            invoice_id, None, None, "ITEM005", "Test Item", 1.0, 100.0, "S"
        )
        self.assertTrue(success)
        
        # Get initial entry count
        initial_entries = self.journal_entry_model.get_all(self.user_id)
        initial_count = len(initial_entries)
        
        # Delete sales invoice item
        success, message = self.controller.handle_delete_item(item_id)
        self.assertTrue(success)
        
        # Verify item was deleted
        items = self.sales_invoice_item_model.get_by_sales_invoice(invoice_id)
        self.assertEqual(len(items), 0)
        
        # Verify reversal entries were created
        entries = self.journal_entry_model.get_all(self.user_id)
        reversal_entries = [e for e in entries if 'Reversal' in e.get('transaction_type', '')]
        self.assertGreater(len(reversal_entries), 0)
        self.assertGreater(len(entries), initial_count)


if __name__ == "__main__":
    unittest.main()

