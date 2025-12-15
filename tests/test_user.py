"""Tests for User model."""
import unittest
import os
import tempfile
from models.user import User


class TestUser(unittest.TestCase):
    """Test cases for User model."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary database for each test
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.user_model = User(db_path=self.temp_db.name)
    
    def tearDown(self):
        """Clean up after tests."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_create_user_success(self):
        """Test successful user creation."""
        success, message = self.user_model.create_user("testuser", "password123")
        self.assertTrue(success)
        self.assertEqual(message, "User created successfully")
    
    def test_create_user_duplicate(self):
        """Test creating duplicate user."""
        self.user_model.create_user("testuser", "password123")
        success, message = self.user_model.create_user("testuser", "password456")
        self.assertFalse(success)
        self.assertIn("already exists", message)
    
    def test_create_user_short_username(self):
        """Test creating user with short username."""
        success, message = self.user_model.create_user("ab", "password123")
        self.assertFalse(success)
        self.assertIn("at least 3 characters", message)
    
    def test_create_user_short_password(self):
        """Test creating user with short password."""
        success, message = self.user_model.create_user("testuser", "abc")
        self.assertFalse(success)
        self.assertIn("at least 4 characters", message)
    
    def test_create_user_empty_fields(self):
        """Test creating user with empty fields."""
        success, message = self.user_model.create_user("", "password123")
        self.assertFalse(success)
        self.assertIn("required", message)
        
        success, message = self.user_model.create_user("testuser", "")
        self.assertFalse(success)
        self.assertIn("required", message)
    
    def test_authenticate_success(self):
        """Test successful authentication."""
        self.user_model.create_user("testuser", "password123")
        success, message = self.user_model.authenticate("testuser", "password123")
        self.assertTrue(success)
        self.assertEqual(message, "Login successful")
    
    def test_authenticate_wrong_password(self):
        """Test authentication with wrong password."""
        self.user_model.create_user("testuser", "password123")
        success, message = self.user_model.authenticate("testuser", "wrongpassword")
        self.assertFalse(success)
        self.assertIn("Invalid", message)
    
    def test_authenticate_nonexistent_user(self):
        """Test authentication with non-existent user."""
        success, message = self.user_model.authenticate("nonexistent", "password123")
        self.assertFalse(success)
        self.assertIn("Invalid", message)
    
    def test_authenticate_empty_fields(self):
        """Test authentication with empty fields."""
        success, message = self.user_model.authenticate("", "password123")
        self.assertFalse(success)
        self.assertIn("required", message)
        
        success, message = self.user_model.authenticate("testuser", "")
        self.assertFalse(success)
        self.assertIn("required", message)
    
    def test_user_exists(self):
        """Test user_exists method."""
        self.assertFalse(self.user_model.user_exists("testuser"))
        self.user_model.create_user("testuser", "password123")
        self.assertTrue(self.user_model.user_exists("testuser"))


if __name__ == "__main__":
    unittest.main()

