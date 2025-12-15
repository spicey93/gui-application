"""Tests for Supplier model."""
import unittest
import os
import tempfile
from models.supplier import Supplier


class TestSupplier(unittest.TestCase):
    """Test cases for Supplier model."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary database for each test
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.supplier_model = Supplier(db_path=self.temp_db.name)
    
    def tearDown(self):
        """Clean up after tests."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_create_supplier_success(self):
        """Test successful supplier creation."""
        success, message = self.supplier_model.create("ACC001", "Test Supplier")
        self.assertTrue(success)
        self.assertIn("created successfully", message)
    
    def test_create_supplier_duplicate_account_number(self):
        """Test creating supplier with duplicate account number."""
        self.supplier_model.create("ACC001", "Supplier 1")
        success, message = self.supplier_model.create("ACC001", "Supplier 2")
        self.assertFalse(success)
        self.assertIn("already exists", message)
    
    def test_create_supplier_empty_fields(self):
        """Test creating supplier with empty fields."""
        success, message = self.supplier_model.create("", "Test Supplier")
        self.assertFalse(success)
        self.assertIn("required", message)
        
        success, message = self.supplier_model.create("ACC001", "")
        self.assertFalse(success)
        self.assertIn("required", message)
    
    def test_get_all_suppliers(self):
        """Test getting all suppliers."""
        # Initially empty
        suppliers = self.supplier_model.get_all()
        self.assertEqual(len(suppliers), 0)
        
        # Add suppliers
        self.supplier_model.create("ACC001", "Supplier 1")
        self.supplier_model.create("ACC002", "Supplier 2")
        
        suppliers = self.supplier_model.get_all()
        self.assertEqual(len(suppliers), 2)
        self.assertEqual(suppliers[0]['account_number'], "ACC001")
        self.assertEqual(suppliers[1]['account_number'], "ACC002")
    
    def test_get_supplier_by_id(self):
        """Test getting supplier by ID."""
        self.supplier_model.create("ACC001", "Test Supplier")
        suppliers = self.supplier_model.get_all()
        supplier_id = suppliers[0]['id']
        
        supplier = self.supplier_model.get_by_id(supplier_id)
        self.assertIsNotNone(supplier)
        self.assertEqual(supplier['account_number'], "ACC001")
        self.assertEqual(supplier['name'], "Test Supplier")
    
    def test_get_supplier_by_id_not_found(self):
        """Test getting non-existent supplier."""
        supplier = self.supplier_model.get_by_id(999)
        self.assertIsNone(supplier)
    
    def test_update_supplier_success(self):
        """Test successful supplier update."""
        self.supplier_model.create("ACC001", "Old Name")
        suppliers = self.supplier_model.get_all()
        supplier_id = suppliers[0]['id']
        
        success, message = self.supplier_model.update(supplier_id, "ACC001", "New Name")
        self.assertTrue(success)
        self.assertIn("updated successfully", message)
        
        supplier = self.supplier_model.get_by_id(supplier_id)
        self.assertEqual(supplier['name'], "New Name")
    
    def test_update_supplier_account_number(self):
        """Test updating supplier account number."""
        self.supplier_model.create("ACC001", "Supplier 1")
        suppliers = self.supplier_model.get_all()
        supplier_id = suppliers[0]['id']
        
        success, message = self.supplier_model.update(supplier_id, "ACC002", "Supplier 1")
        self.assertTrue(success)
        
        supplier = self.supplier_model.get_by_id(supplier_id)
        self.assertEqual(supplier['account_number'], "ACC002")
    
    def test_update_supplier_duplicate_account_number(self):
        """Test updating to duplicate account number."""
        self.supplier_model.create("ACC001", "Supplier 1")
        self.supplier_model.create("ACC002", "Supplier 2")
        
        suppliers = self.supplier_model.get_all()
        supplier_id = suppliers[0]['id']
        
        success, message = self.supplier_model.update(supplier_id, "ACC002", "Supplier 1")
        self.assertFalse(success)
        self.assertIn("already exists", message)
    
    def test_update_supplier_not_found(self):
        """Test updating non-existent supplier."""
        success, message = self.supplier_model.update(999, "ACC001", "Test")
        self.assertFalse(success)
        self.assertIn("not found", message)
    
    def test_delete_supplier_success(self):
        """Test successful supplier deletion."""
        self.supplier_model.create("ACC001", "Test Supplier")
        suppliers = self.supplier_model.get_all()
        supplier_id = suppliers[0]['id']
        
        success, message = self.supplier_model.delete(supplier_id)
        self.assertTrue(success)
        self.assertIn("deleted successfully", message)
        
        suppliers = self.supplier_model.get_all()
        self.assertEqual(len(suppliers), 0)
    
    def test_delete_supplier_not_found(self):
        """Test deleting non-existent supplier."""
        success, message = self.supplier_model.delete(999)
        self.assertFalse(success)
        self.assertIn("not found", message)
    
    def test_supplier_exists(self):
        """Test checking if supplier exists."""
        self.assertFalse(self.supplier_model.exists("ACC001"))
        self.supplier_model.create("ACC001", "Test Supplier")
        self.assertTrue(self.supplier_model.exists("ACC001"))


if __name__ == "__main__":
    unittest.main()

