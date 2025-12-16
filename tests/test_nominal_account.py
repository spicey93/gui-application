"""Tests for NominalAccount model."""
import unittest
import os
import tempfile
from models.nominal_account import NominalAccount
from models.user import User


class TestNominalAccount(unittest.TestCase):
    """Test cases for NominalAccount model."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary database for each test
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.account_model = NominalAccount(db_path=self.temp_db.name)
        self.user_model = User(db_path=self.temp_db.name)
        
        # Create a test user
        self.user_model.create_user("testuser", "password123")
        # Get user_id
        success, _, user_id = self.user_model.authenticate("testuser", "password123")
        self.assertTrue(success)
        self.user_id = user_id
    
    def tearDown(self):
        """Clean up after tests."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_create_account_success(self):
        """Test successful account creation."""
        success, message, account_id = self.account_model.create(
            1000, "Bank Account", "Asset", 0.0, False, self.user_id
        )
        self.assertTrue(success)
        self.assertIsNotNone(account_id)
        self.assertIn("created successfully", message)
    
    def test_create_account_with_opening_balance(self):
        """Test creating account with opening balance."""
        success, message, account_id = self.account_model.create(
            1000, "Bank Account", "Asset", 1000.50, False, self.user_id
        )
        self.assertTrue(success)
        account = self.account_model.get_by_id(account_id, self.user_id)
        self.assertEqual(account['opening_balance'], 1000.50)
    
    def test_create_account_bank_account_flag(self):
        """Test creating account with bank account flag."""
        success, message, account_id = self.account_model.create(
            1000, "Bank Account", "Asset", 0.0, True, self.user_id
        )
        self.assertTrue(success)
        account = self.account_model.get_by_id(account_id, self.user_id)
        self.assertEqual(account['is_bank_account'], 1)
    
    def test_create_account_duplicate_code(self):
        """Test creating account with duplicate account code."""
        self.account_model.create(1000, "Account 1", "Asset", 0.0, False, self.user_id)
        success, message, account_id = self.account_model.create(
            1000, "Account 2", "Asset", 0.0, False, self.user_id
        )
        self.assertFalse(success)
        self.assertIn("already exists", message)
    
    def test_create_account_invalid_code_range(self):
        """Test creating account with invalid code range."""
        # Asset account with liability code
        success, message, account_id = self.account_model.create(
            2000, "Asset Account", "Asset", 0.0, False, self.user_id
        )
        self.assertFalse(success)
        self.assertIn("must use codes", message)
    
    def test_create_account_empty_name(self):
        """Test creating account with empty name."""
        success, message, account_id = self.account_model.create(
            1000, "", "Asset", 0.0, False, self.user_id
        )
        self.assertFalse(success)
        self.assertIn("required", message)
    
    def test_get_all_accounts(self):
        """Test getting all accounts."""
        # Initially empty
        accounts = self.account_model.get_all(self.user_id)
        self.assertEqual(len(accounts), 0)
        
        # Add accounts
        self.account_model.create(1000, "Bank Account", "Asset", 0.0, False, self.user_id)
        self.account_model.create(2000, "Accounts Payable", "Liability", 0.0, False, self.user_id)
        
        accounts = self.account_model.get_all(self.user_id)
        self.assertEqual(len(accounts), 2)
        # Should be sorted by account code
        self.assertEqual(accounts[0]['account_code'], 1000)
        self.assertEqual(accounts[1]['account_code'], 2000)
    
    def test_get_account_by_id(self):
        """Test getting account by ID."""
        success, _, account_id = self.account_model.create(
            1000, "Bank Account", "Asset", 500.0, False, self.user_id
        )
        
        account = self.account_model.get_by_id(account_id, self.user_id)
        self.assertIsNotNone(account)
        self.assertEqual(account['account_code'], 1000)
        self.assertEqual(account['account_name'], "Bank Account")
        self.assertEqual(account['account_type'], "Asset")
        self.assertEqual(account['opening_balance'], 500.0)
        self.assertEqual(account['current_balance'], 500.0)  # No journal entries yet
    
    def test_get_account_by_id_not_found(self):
        """Test getting non-existent account."""
        account = self.account_model.get_by_id(999, self.user_id)
        self.assertIsNone(account)
    
    def test_update_account_success(self):
        """Test successful account update."""
        success, _, account_id = self.account_model.create(
            1000, "Old Name", "Asset", 0.0, False, self.user_id
        )
        
        success, message = self.account_model.update(
            account_id, 1000, "New Name", "Asset", 0.0, False, self.user_id
        )
        self.assertTrue(success)
        self.assertIn("updated successfully", message)
        
        account = self.account_model.get_by_id(account_id, self.user_id)
        self.assertEqual(account['account_name'], "New Name")
    
    def test_update_account_code(self):
        """Test updating account code."""
        success, _, account_id = self.account_model.create(
            1000, "Bank Account", "Asset", 0.0, False, self.user_id
        )
        
        success, message = self.account_model.update(
            account_id, 1001, "Bank Account", "Asset", 0.0, False, self.user_id
        )
        self.assertTrue(success)
        
        account = self.account_model.get_by_id(account_id, self.user_id)
        self.assertEqual(account['account_code'], 1001)
    
    def test_update_account_duplicate_code(self):
        """Test updating to duplicate account code."""
        self.account_model.create(1000, "Account 1", "Asset", 0.0, False, self.user_id)
        success, _, account_id2 = self.account_model.create(
            1001, "Account 2", "Asset", 0.0, False, self.user_id
        )
        
        success, message = self.account_model.update(
            account_id2, 1000, "Account 2", "Asset", 0.0, False, self.user_id
        )
        self.assertFalse(success)
        self.assertIn("already exists", message)
    
    def test_update_account_not_found(self):
        """Test updating non-existent account."""
        success, message = self.account_model.update(
            999, 1000, "Test", "Asset", 0.0, False, self.user_id
        )
        self.assertFalse(success)
        self.assertIn("not found", message)
    
    def test_delete_account_success(self):
        """Test successful account deletion."""
        success, _, account_id = self.account_model.create(
            1000, "Test Account", "Asset", 0.0, False, self.user_id
        )
        
        success, message = self.account_model.delete(account_id, self.user_id)
        self.assertTrue(success)
        self.assertIn("deleted successfully", message)
        
        accounts = self.account_model.get_all(self.user_id)
        self.assertEqual(len(accounts), 0)
    
    def test_delete_account_not_found(self):
        """Test deleting non-existent account."""
        success, message = self.account_model.delete(999, self.user_id)
        self.assertFalse(success)
        self.assertIn("not found", message)
    
    def test_account_code_validation_asset(self):
        """Test account code validation for Asset accounts."""
        # Valid asset code
        success, _, _ = self.account_model.create(
            1500, "Asset Account", "Asset", 0.0, False, self.user_id
        )
        self.assertTrue(success)
        
        # Invalid asset code (liability range)
        success, message, _ = self.account_model.create(
            2500, "Invalid Asset", "Asset", 0.0, False, self.user_id
        )
        self.assertFalse(success)
        self.assertIn("must use codes", message)
    
    def test_account_code_validation_liability(self):
        """Test account code validation for Liability accounts."""
        # Valid liability code
        success, _, _ = self.account_model.create(
            2000, "Liability Account", "Liability", 0.0, False, self.user_id
        )
        self.assertTrue(success)
        
        # Invalid liability code (asset range)
        success, message, _ = self.account_model.create(
            1500, "Invalid Liability", "Liability", 0.0, False, self.user_id
        )
        self.assertFalse(success)
        self.assertIn("must use codes", message)
    
    def test_get_balance_no_entries(self):
        """Test getting balance for account with no journal entries."""
        success, _, account_id = self.account_model.create(
            1000, "Bank Account", "Asset", 1000.0, False, self.user_id
        )
        
        balance = self.account_model.get_balance(account_id, self.user_id)
        self.assertEqual(balance, 1000.0)


if __name__ == "__main__":
    unittest.main()

