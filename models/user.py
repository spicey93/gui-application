"""User model for authentication."""
import sqlite3
import hashlib
from typing import Optional, Tuple
import os


class User:
    """User model with database operations."""
    
    def __init__(self, db_path: str = "data/app.db"):
        """Initialize user model with database path."""
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_database(self):
        """Initialize the database with users table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Create a new user.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not username or not password:
            return False, "Username and password are required"
        
        if len(username) < 3:
            return False, "Username must be at least 3 characters"
        
        if len(password) < 4:
            return False, "Password must be at least 4 characters"
        
        password_hash = self._hash_password(password)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )
            conn.commit()
            conn.close()
            return True, "User created successfully"
        except sqlite3.IntegrityError:
            return False, "Username already exists"
        except Exception as e:
            return False, f"Error creating user: {str(e)}"
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, str, Optional[int]]:
        """
        Authenticate a user.
        
        Returns:
            Tuple of (success: bool, message: str, user_id: Optional[int])
        """
        if not username or not password:
            return False, "Username and password are required", None
        
        password_hash = self._hash_password(password)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM users WHERE username = ? AND password_hash = ?",
                (username, password_hash)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                user_id = result[0]
                return True, "Login successful", user_id
            else:
                return False, "Invalid username or password", None
        except Exception as e:
            return False, f"Error authenticating: {str(e)}", None
    
    def user_exists(self, username: str) -> bool:
        """Check if a user exists."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            conn.close()
            return result is not None
        except Exception:
            return False
    
    def delete_user(self, username: str, delete_suppliers: bool = True) -> Tuple[bool, str]:
        """
        Delete a user by username.
        
        Args:
            username: Username to delete
            delete_suppliers: If True, also delete all suppliers belonging to this user
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not username:
            return False, "Username is required"
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return False, "User not found"
            
            user_id = result[0]
            
            # Always delete suppliers first (before deleting user to maintain referential integrity)
            cursor.execute("DELETE FROM suppliers WHERE user_id = ?", (user_id,))
            deleted_suppliers = cursor.rowcount
            
            # Delete the user
            cursor.execute("DELETE FROM users WHERE username = ?", (username,))
            conn.commit()
            conn.close()
            
            message = f"User '{username}' deleted successfully"
            if deleted_suppliers > 0:
                message += f" ({deleted_suppliers} supplier(s) also deleted)"
            
            return True, message
        except Exception as e:
            return False, f"Error deleting user: {str(e)}"

