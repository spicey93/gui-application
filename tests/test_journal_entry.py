"""Tests for JournalEntry model."""
import unittest
import os
import tempfile
from datetime import date
from models.journal_entry import JournalEntry
from models.nominal_account import NominalAccount
from models.user import User


class TestJournalEntry(unittest.TestCase):
    """Test cases for JournalEntry model."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary database for each test
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.entry_model = JournalEntry(db_path=self.temp_db.name)
        self.account_model = NominalAccount(db_path=self.temp_db.name)
        self.user_model = User(db_path=self.temp_db.name)
        
        # Create a test user
        self.user_model.create_user("testuser", "password123")
        # Get user_id
        success, _, user_id = self.user_model.authenticate("testuser", "password123")
        self.assertTrue(success)
        self.user_id = user_id
        
        # Create test accounts
        _, _, self.bank_account_id = self.account_model.create(
            1000, "Bank Account", "Asset", 0.0, False, self.user_id
        )
        _, _, self.expense_account_id = self.account_model.create(
            5000, "Office Expenses", "Expense", 0.0, False, self.user_id
        )
        _, _, self.income_account_id = self.account_model.create(
            4000, "Sales", "Income", 0.0, False, self.user_id
        )
    
    def tearDown(self):
        """Clean up after tests."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_create_entry_success(self):
        """Test successful journal entry creation."""
        success, message, entry_id = self.entry_model.create(
            date.today(), "Test Entry", self.bank_account_id, 
            self.expense_account_id, 100.0, None, self.user_id
        )
        self.assertTrue(success)
        self.assertIsNotNone(entry_id)
        self.assertIn("created successfully", message)
    
    def test_create_entry_with_reference(self):
        """Test creating entry with reference."""
        success, message, entry_id = self.entry_model.create(
            date.today(), "Test Entry", self.bank_account_id,
            self.expense_account_id, 100.0, "REF001", self.user_id
        )
        self.assertTrue(success)
        
        entry = self.entry_model.get_by_id(entry_id, self.user_id)
        self.assertEqual(entry['reference'], "REF001")
    
    def test_create_entry_empty_description(self):
        """Test creating entry with empty description."""
        success, message, entry_id = self.entry_model.create(
            date.today(), "", self.bank_account_id,
            self.expense_account_id, 100.0, None, self.user_id
        )
        self.assertFalse(success)
        self.assertIn("required", message)
    
    def test_create_entry_zero_amount(self):
        """Test creating entry with zero amount."""
        success, message, entry_id = self.entry_model.create(
            date.today(), "Test Entry", self.bank_account_id,
            self.expense_account_id, 0.0, None, self.user_id
        )
        self.assertFalse(success)
        self.assertIn("greater than zero", message)
    
    def test_create_entry_negative_amount(self):
        """Test creating entry with negative amount."""
        success, message, entry_id = self.entry_model.create(
            date.today(), "Test Entry", self.bank_account_id,
            self.expense_account_id, -100.0, None, self.user_id
        )
        self.assertFalse(success)
        self.assertIn("greater than zero", message)
    
    def test_create_entry_same_accounts(self):
        """Test creating entry with same debit and credit accounts."""
        success, message, entry_id = self.entry_model.create(
            date.today(), "Test Entry", self.bank_account_id,
            self.bank_account_id, 100.0, None, self.user_id
        )
        self.assertFalse(success)
        self.assertIn("cannot be the same", message)
    
    def test_create_entry_invalid_debit_account(self):
        """Test creating entry with invalid debit account."""
        success, message, entry_id = self.entry_model.create(
            date.today(), "Test Entry", 999,
            self.expense_account_id, 100.0, None, self.user_id
        )
        self.assertFalse(success)
        self.assertIn("not found", message)
    
    def test_create_entry_invalid_credit_account(self):
        """Test creating entry with invalid credit account."""
        success, message, entry_id = self.entry_model.create(
            date.today(), "Test Entry", self.bank_account_id,
            999, 100.0, None, self.user_id
        )
        self.assertFalse(success)
        self.assertIn("not found", message)
    
    def test_get_all_entries(self):
        """Test getting all journal entries."""
        # Initially empty
        entries = self.entry_model.get_all(self.user_id)
        self.assertEqual(len(entries), 0)
        
        # Add entries
        self.entry_model.create(
            date.today(), "Entry 1", self.bank_account_id,
            self.expense_account_id, 100.0, None, self.user_id
        )
        self.entry_model.create(
            date.today(), "Entry 2", self.bank_account_id,
            self.expense_account_id, 200.0, None, self.user_id
        )
        
        entries = self.entry_model.get_all(self.user_id)
        self.assertEqual(len(entries), 2)
        # Should be sorted by date (newest first)
        self.assertEqual(entries[0]['description'], "Entry 2")
        self.assertEqual(entries[1]['description'], "Entry 1")
    
    def test_get_entries_by_account(self):
        """Test getting entries filtered by account."""
        # Create entries affecting different accounts
        self.entry_model.create(
            date.today(), "Entry 1", self.bank_account_id,
            self.expense_account_id, 100.0, None, self.user_id
        )
        self.entry_model.create(
            date.today(), "Entry 2", self.income_account_id,
            self.bank_account_id, 200.0, None, self.user_id
        )
        
        # Get entries for bank account (should be 2 - one as debit, one as credit)
        entries = self.entry_model.get_all(self.user_id, self.bank_account_id)
        self.assertEqual(len(entries), 2)
        
        # Get entries for expense account (should be 1 - as credit)
        entries = self.entry_model.get_all(self.user_id, self.expense_account_id)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['description'], "Entry 1")
    
    def test_get_entry_by_id(self):
        """Test getting entry by ID."""
        success, _, entry_id = self.entry_model.create(
            date.today(), "Test Entry", self.bank_account_id,
            self.expense_account_id, 100.0, "REF001", self.user_id
        )
        
        entry = self.entry_model.get_by_id(entry_id, self.user_id)
        self.assertIsNotNone(entry)
        self.assertEqual(entry['description'], "Test Entry")
        self.assertEqual(entry['debit_account_id'], self.bank_account_id)
        self.assertEqual(entry['credit_account_id'], self.expense_account_id)
        self.assertEqual(entry['amount'], 100.0)
        self.assertEqual(entry['reference'], "REF001")
    
    def test_get_entry_by_id_not_found(self):
        """Test getting non-existent entry."""
        entry = self.entry_model.get_by_id(999, self.user_id)
        self.assertIsNone(entry)
    
    def test_delete_entry_success(self):
        """Test successful entry deletion."""
        success, _, entry_id = self.entry_model.create(
            date.today(), "Test Entry", self.bank_account_id,
            self.expense_account_id, 100.0, None, self.user_id
        )
        
        success, message = self.entry_model.delete(entry_id, self.user_id)
        self.assertTrue(success)
        self.assertIn("deleted successfully", message)
        
        entries = self.entry_model.get_all(self.user_id)
        self.assertEqual(len(entries), 0)
    
    def test_delete_entry_not_found(self):
        """Test deleting non-existent entry."""
        success, message = self.entry_model.delete(999, self.user_id)
        self.assertFalse(success)
        self.assertIn("not found", message)
    
    def test_get_account_entries(self):
        """Test getting entries for a specific account."""
        # Create entries
        self.entry_model.create(
            date.today(), "Entry 1", self.bank_account_id,
            self.expense_account_id, 100.0, None, self.user_id
        )
        self.entry_model.create(
            date.today(), "Entry 2", self.income_account_id,
            self.bank_account_id, 200.0, None, self.user_id
        )
        
        # Get entries for bank account
        entries = self.entry_model.get_account_entries(self.bank_account_id, self.user_id)
        self.assertEqual(len(entries), 2)
        
        # Check debit/credit indicators
        self.assertTrue(entries[0]['is_debit'] or entries[0]['is_credit'])
        self.assertTrue(entries[1]['is_debit'] or entries[1]['is_credit'])
        
        # One should be debit, one should be credit
        debit_count = sum(1 for e in entries if e['is_debit'])
        credit_count = sum(1 for e in entries if e['is_credit'])
        self.assertEqual(debit_count, 1)
        self.assertEqual(credit_count, 1)


if __name__ == "__main__":
    unittest.main()

