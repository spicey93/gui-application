"""Product type model for product type management."""
import sqlite3
from typing import Optional, Tuple, List, Dict
import os


class ProductType:
    """Product type model with database operations."""
    
    def __init__(self, db_path: str = "data/app.db"):
        """Initialize product type model with database path."""
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_database(self):
        """Initialize the database with product_types table."""
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='product_types'
            """)
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Create new table with user_id
                cursor.execute("""
                    CREATE TABLE product_types (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        UNIQUE(user_id, name)
                    )
                """)
            else:
                # Table exists - check if migration needed
                cursor.execute("PRAGMA table_info(product_types)")
                column_info = cursor.fetchall()
                columns = [row[1] for row in column_info]
                
                if 'user_id' not in columns:
                    # Migrate: add user_id column
                    cursor.execute("ALTER TABLE product_types ADD COLUMN user_id INTEGER")
                    
                    # Set default user_id to 1 for existing records (or delete them)
                    # We'll set to 1 as a safe default, but ideally these should be user-specific
                    cursor.execute("UPDATE product_types SET user_id = 1 WHERE user_id IS NULL")
                    
                    # Drop old UNIQUE constraint on name and add new one on (user_id, name)
                    # SQLite doesn't support dropping constraints directly, so we need to recreate
                    cursor.execute("SELECT id, name, created_at FROM product_types")
                    old_data = cursor.fetchall()
                    
                    cursor.execute("DROP TABLE product_types")
                    cursor.execute("""
                        CREATE TABLE product_types (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            name TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                            UNIQUE(user_id, name)
                        )
                    """)
                    
                    # Re-insert data with user_id = 1
                    for row in old_data:
                        old_id, old_name, old_created_at = row
                        cursor.execute("""
                            INSERT INTO product_types (id, user_id, name, created_at)
                            VALUES (?, 1, ?, ?)
                        """, (old_id, old_name, old_created_at))
            
            conn.commit()
    
    def create(self, name: str, user_id: int) -> Tuple[bool, str]:
        """
        Create a new product type.
        
        Args:
            name: Product type name
            user_id: ID of the user creating the product type
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not name:
            return False, "Product type name is required"
        
        if not user_id:
            return False, "User ID is required"
        
        name = name.strip()
        
        if not name:
            return False, "Product type name cannot be empty"
        
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "INSERT INTO product_types (name, user_id) VALUES (?, ?)",
                    (name, user_id)
                )
                conn.commit()
            return True, f"Product type '{name}' created successfully"
        except sqlite3.IntegrityError:
            return False, "Product type already exists"
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower():
                return False, "Database is locked. Please try again in a moment."
            return False, f"Database error: {str(e)}"
        except Exception as e:
            return False, f"Error creating product type: {str(e)}"
    
    def get_all(self, user_id: int) -> List[Dict[str, any]]:
        """
        Get all product types for a specific user.
        
        Args:
            user_id: ID of the user
        
        Returns:
            List of product type dictionaries
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, created_at 
                    FROM product_types 
                    WHERE user_id = ?
                    ORDER BY name
                """, (user_id,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception:
            return []
    
    def get_names(self, user_id: int) -> List[str]:
        """
        Get all product type names as a simple list for a specific user.
        
        Args:
            user_id: ID of the user
        
        Returns:
            List of product type names
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name FROM product_types 
                    WHERE user_id = ?
                    ORDER BY name
                """, (user_id,))
                rows = cursor.fetchall()
                return [row[0] for row in rows]
        except Exception:
            return []
    
    def delete(self, type_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Delete a product type by ID for a specific user.
        
        Args:
            type_id: Product type ID
            user_id: ID of the user
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Check if any products are using this type (for this user)
                cursor.execute("""
                    SELECT COUNT(*) FROM products 
                    WHERE type = (SELECT name FROM product_types WHERE id = ? AND user_id = ?)
                    AND user_id = ?
                """, (type_id, user_id, user_id))
                count = cursor.fetchone()[0]
                
                if count > 0:
                    return False, f"Cannot delete product type: {count} product(s) are using this type"
                
                cursor.execute("DELETE FROM product_types WHERE id = ? AND user_id = ?", (type_id, user_id))
                
                if cursor.rowcount == 0:
                    return False, "Product type not found"
                
                conn.commit()
            return True, "Product type deleted successfully"
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower():
                return False, "Database is locked. Please try again in a moment."
            return False, f"Database error: {str(e)}"
        except Exception as e:
            return False, f"Error deleting product type: {str(e)}"
    
    def exists(self, name: str, user_id: int) -> bool:
        """Check if a product type exists for a specific user."""
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM product_types WHERE name = ? AND user_id = ?", (name, user_id))
                result = cursor.fetchone()
                return result is not None
        except Exception:
            return False

