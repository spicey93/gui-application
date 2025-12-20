"""Supplier model for supplier management."""
import sqlite3
from typing import Optional, Tuple, List, Dict
import os


class Supplier:
    """Supplier model with database operations."""
    
    def __init__(self, db_path: str = "data/app.db"):
        """Initialize supplier model with database path."""
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_database(self):
        """Initialize the database with suppliers table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='suppliers'
        """)
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            # Create new table with proper constraints
            cursor.execute("""
                CREATE TABLE suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    user_supplier_id INTEGER NOT NULL,
                    account_number TEXT NOT NULL,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE(user_id, account_number),
                    UNIQUE(user_id, user_supplier_id)
                )
            """)
        else:
            # Table exists - check if we need to add user_id column
            cursor.execute("PRAGMA table_info(suppliers)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'user_id' not in columns:
                # Add user_id column
                cursor.execute("ALTER TABLE suppliers ADD COLUMN user_id INTEGER")
                # Delete orphaned suppliers (can't assign to non-existent users)
                cursor.execute("DELETE FROM suppliers WHERE user_id IS NULL")
            
            # Add user_supplier_id column if it doesn't exist
            if 'user_supplier_id' not in columns:
                cursor.execute("ALTER TABLE suppliers ADD COLUMN user_supplier_id INTEGER")
                # Calculate user_supplier_id for existing records
                cursor.execute("""
                    UPDATE suppliers 
                    SET user_supplier_id = (
                        SELECT COUNT(*) + 1
                        FROM suppliers s2
                        WHERE s2.user_id = suppliers.user_id 
                        AND s2.id < suppliers.id
                    )
                    WHERE user_supplier_id IS NULL
                """)
                # Set to 1 for any that are still NULL (first supplier per user)
                cursor.execute("UPDATE suppliers SET user_supplier_id = 1 WHERE user_supplier_id IS NULL")
                
                # Create unique index for user_supplier_id
                try:
                    cursor.execute("""
                        CREATE UNIQUE INDEX IF NOT EXISTS idx_supplier_user_supplier_id 
                        ON suppliers(user_id, user_supplier_id)
                    """)
                except sqlite3.OperationalError:
                    pass
            
            # Ensure UNIQUE constraint exists (drop and recreate if needed)
            try:
                # Try to create unique index (will fail if it exists, which is fine)
                cursor.execute("""
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_supplier_user_account 
                    ON suppliers(user_id, account_number)
                """)
            except sqlite3.OperationalError:
                pass
        
        # Clean up orphaned suppliers (suppliers with user_id that doesn't exist in users table)
        cursor.execute("""
            DELETE FROM suppliers 
            WHERE user_id NOT IN (SELECT id FROM users)
            AND user_id IS NOT NULL
        """)
        
        conn.commit()
        conn.close()
    
    def create(self, account_number: str, name: str, user_id: int) -> Tuple[bool, str]:
        """
        Create a new supplier.
        
        Args:
            account_number: Unique account number for the supplier (unique per user)
            name: Supplier name
            user_id: ID of the user creating the supplier
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not account_number or not name:
            return False, "Account number and name are required"
        
        if not user_id:
            return False, "User ID is required"
        
        account_number = account_number.strip()
        name = name.strip()
        
        if not account_number:
            return False, "Account number cannot be empty"
        
        if not name:
            return False, "Name cannot be empty"
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate the next user_supplier_id for this user
            cursor.execute("""
                SELECT COALESCE(MAX(user_supplier_id), 0) + 1 
                FROM suppliers 
                WHERE user_id = ?
            """, (user_id,))
            next_user_supplier_id = cursor.fetchone()[0]
            
            cursor.execute(
                "INSERT INTO suppliers (account_number, name, user_id, user_supplier_id) VALUES (?, ?, ?, ?)",
                (account_number, name, user_id, next_user_supplier_id)
            )
            conn.commit()
            supplier_id = cursor.lastrowid
            conn.close()
            return True, f"Supplier created successfully (ID: {next_user_supplier_id})"
        except sqlite3.IntegrityError as e:
            if "account_number" in str(e).lower():
                return False, "Account number already exists for this user"
            else:
                return False, f"Error creating supplier: {str(e)}"
        except Exception as e:
            return False, f"Error creating supplier: {str(e)}"
    
    def get_all(self, user_id: int) -> List[Dict[str, any]]:
        """
        Get all suppliers for a specific user.
        
        Args:
            user_id: ID of the user
        
        Returns:
            List of supplier dictionaries (using user_supplier_id as id for display)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    id as internal_id,
                    COALESCE(user_supplier_id, id) as id,
                    account_number, 
                    name, 
                    created_at 
                FROM suppliers 
                WHERE user_id = ? 
                ORDER BY user_supplier_id
            """, (user_id,))
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            return []
    
    def get_by_id(self, supplier_id: int, user_id: int) -> Optional[Dict[str, any]]:
        """
        Get a supplier by user_supplier_id for a specific user.
        
        Args:
            supplier_id: User supplier ID (user_supplier_id)
            user_id: ID of the user
        
        Returns:
            Supplier dictionary or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    id as internal_id,
                    COALESCE(user_supplier_id, id) as id,
                    account_number, 
                    name, 
                    created_at 
                FROM suppliers 
                WHERE user_supplier_id = ? AND user_id = ?
            """, (supplier_id, user_id))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception:
            return None
    
    def update(self, supplier_id: int, account_number: str, name: str, user_id: int) -> Tuple[bool, str]:
        """
        Update a supplier by user_supplier_id.
        
        Args:
            supplier_id: User supplier ID (user_supplier_id)
            account_number: New account number
            name: New name
            user_id: ID of the user
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not account_number or not name:
            return False, "Account number and name are required"
        
        account_number = account_number.strip()
        name = name.strip()
        
        if not account_number:
            return False, "Account number cannot be empty"
        
        if not name:
            return False, "Name cannot be empty"
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get the internal ID for this supplier
            cursor.execute(
                "SELECT id FROM suppliers WHERE user_supplier_id = ? AND user_id = ?",
                (supplier_id, user_id)
            )
            internal_id_result = cursor.fetchone()
            
            if not internal_id_result:
                conn.close()
                return False, "Supplier not found"
            
            internal_id = internal_id_result[0]
            
            # Check if account number already exists for another supplier of the same user
            cursor.execute(
                "SELECT id FROM suppliers WHERE account_number = ? AND id != ? AND user_id = ?",
                (account_number, internal_id, user_id)
            )
            if cursor.fetchone():
                conn.close()
                return False, "Account number already exists"
            
            cursor.execute(
                "UPDATE suppliers SET account_number = ?, name = ? WHERE user_supplier_id = ? AND user_id = ?",
                (account_number, name, supplier_id, user_id)
            )
            
            if cursor.rowcount == 0:
                conn.close()
                return False, "Supplier not found"
            
            conn.commit()
            conn.close()
            return True, "Supplier updated successfully"
        except Exception as e:
            return False, f"Error updating supplier: {str(e)}"
    
    def delete(self, supplier_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Delete a supplier by user_supplier_id.
        
        Args:
            supplier_id: User supplier ID (user_supplier_id)
            user_id: ID of the user
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM suppliers WHERE user_supplier_id = ? AND user_id = ?", 
                (supplier_id, user_id)
            )
            
            if cursor.rowcount == 0:
                conn.close()
                return False, "Supplier not found"
            
            # Recalculate user_supplier_id for remaining suppliers to maintain sequential IDs
            # Get all remaining suppliers for this user ordered by internal id
            cursor.execute("""
                SELECT id FROM suppliers 
                WHERE user_id = ? 
                ORDER BY id
            """, (user_id,))
            remaining_ids = [row[0] for row in cursor.fetchall()]
            
            # Update each supplier with sequential user_supplier_id
            for index, internal_id in enumerate(remaining_ids, start=1):
                cursor.execute("""
                    UPDATE suppliers 
                    SET user_supplier_id = ? 
                    WHERE id = ? AND user_id = ?
                """, (index, internal_id, user_id))
            
            conn.commit()
            conn.close()
            return True, "Supplier deleted successfully"
        except Exception as e:
            return False, f"Error deleting supplier: {str(e)}"
    
    def exists(self, account_number: str, user_id: int) -> bool:
        """Check if a supplier with the account number exists for a user."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM suppliers WHERE account_number = ? AND user_id = ?",
                (account_number, user_id)
            )
            result = cursor.fetchone()
            conn.close()
            return result is not None
        except Exception:
            return False
    
    def cleanup_orphaned_suppliers(self) -> int:
        """
        Delete suppliers that belong to non-existent users.
        
        Returns:
            Number of suppliers deleted
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM suppliers 
                WHERE user_id NOT IN (SELECT id FROM users)
                AND user_id IS NOT NULL
            """)
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            return deleted_count
        except Exception:
            return 0
    
    def get_outstanding_balance(self, supplier_id: int, user_id: int) -> float:
        """
        Calculate outstanding balance for a supplier.
        Outstanding balance = Total invoices - Total payments (all payments, regardless of allocation).
        
        Args:
            supplier_id: User supplier ID (user_supplier_id)
            user_id: ID of the user
        
        Returns:
            Outstanding balance amount
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Get internal supplier ID
                cursor.execute("""
                    SELECT id FROM suppliers WHERE user_supplier_id = ? AND user_id = ?
                """, (supplier_id, user_id))
                result = cursor.fetchone()
                if not result:
                    return 0.0
                
                internal_supplier_id = result[0]
                
                # Get total of all invoices for this supplier
                cursor.execute("""
                    SELECT COALESCE(SUM(total), 0.0)
                    FROM invoices 
                    WHERE supplier_id = ? AND user_id = ?
                """, (internal_supplier_id, user_id))
                total_invoiced = cursor.fetchone()[0] or 0.0
                
                # Get total of all payments for this supplier (regardless of allocation)
                cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0.0)
                    FROM payments 
                    WHERE supplier_id = ? AND user_id = ?
                """, (internal_supplier_id, user_id))
                total_payments = cursor.fetchone()[0] or 0.0
                
                # Outstanding balance = Total invoices - Total payments
                # Negative values indicate overpayment
                outstanding = total_invoiced - total_payments
                
                return outstanding
        except Exception:
            return 0.0
    
    def get_total_invoiced(self, supplier_id: int, user_id: int) -> float:
        """
        Get total amount invoiced to a supplier.
        
        Args:
            supplier_id: User supplier ID (user_supplier_id)
            user_id: ID of the user
        
        Returns:
            Total invoiced amount
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Get internal supplier ID
                cursor.execute("""
                    SELECT id FROM suppliers WHERE user_supplier_id = ? AND user_id = ?
                """, (supplier_id, user_id))
                result = cursor.fetchone()
                if not result:
                    return 0.0
                
                internal_supplier_id = result[0]
                
                # Sum all invoice totals
                cursor.execute("""
                    SELECT COALESCE(SUM(total), 0.0)
                    FROM invoices
                    WHERE supplier_id = ? AND user_id = ?
                """, (internal_supplier_id, user_id))
                result = cursor.fetchone()
                return result[0] if result else 0.0
        except Exception:
            return 0.0
    
    def get_total_paid(self, supplier_id: int, user_id: int) -> float:
        """
        Get total amount paid to a supplier.
        
        Args:
            supplier_id: User supplier ID (user_supplier_id)
            user_id: ID of the user
        
        Returns:
            Total paid amount
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Get internal supplier ID
                cursor.execute("""
                    SELECT id FROM suppliers WHERE user_supplier_id = ? AND user_id = ?
                """, (supplier_id, user_id))
                result = cursor.fetchone()
                if not result:
                    return 0.0
                
                internal_supplier_id = result[0]
                
                # Sum all payment amounts
                cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0.0)
                    FROM payments
                    WHERE supplier_id = ? AND user_id = ?
                """, (internal_supplier_id, user_id))
                result = cursor.fetchone()
                return result[0] if result else 0.0
        except Exception:
            return 0.0

