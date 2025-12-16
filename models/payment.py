"""Payment model for supplier payment management."""
import sqlite3
from typing import Optional, Tuple, List, Dict
import os


class Payment:
    """Payment model with database operations."""
    
    def __init__(self, db_path: str = "data/app.db"):
        """Initialize payment model with database path."""
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_database(self):
        """Initialize the database with payments table."""
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='payments'
            """)
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Create new table
                cursor.execute("""
                    CREATE TABLE payments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        supplier_id INTEGER NOT NULL,
                        payment_date DATE NOT NULL,
                        amount REAL NOT NULL,
                        reference TEXT,
                        payment_method TEXT NOT NULL DEFAULT 'Cash',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE
                    )
                """)
            else:
                # Migrate existing table: add payment_method, remove notes
                # Check if payment_method column exists
                cursor.execute("PRAGMA table_info(payments)")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'payment_method' not in columns:
                    cursor.execute("""
                        ALTER TABLE payments 
                        ADD COLUMN payment_method TEXT NOT NULL DEFAULT 'Cash'
                    """)
                
                # Note: We don't remove the notes column to preserve existing data
                # but it won't be used in new code
            
            conn.commit()
    
    def create(self, supplier_id: int, payment_date: str, amount: float,
               reference: str, payment_method: str, user_id: int) -> Tuple[bool, str, Optional[int]]:
        """
        Create a new payment.
        
        Args:
            supplier_id: ID of the supplier
            payment_date: Payment date (YYYY-MM-DD format)
            amount: Payment amount
            reference: Payment reference (optional)
            payment_method: Payment method (Cash, Card, Cheque, BACS)
            user_id: ID of the user creating the payment
        
        Returns:
            Tuple of (success: bool, message: str, payment_id: Optional[int])
        """
        if not payment_date:
            return False, "Payment date is required", None
        
        if amount <= 0:
            return False, "Payment amount must be greater than zero", None
        
        if not user_id or not supplier_id:
            return False, "User ID and supplier ID are required", None
        
        if payment_method not in ['Cash', 'Card', 'Cheque', 'BACS']:
            return False, "Payment method must be one of: Cash, Card, Cheque, BACS", None
        
        reference = reference.strip() if reference else ""
        
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO payments (user_id, supplier_id, payment_date, amount, reference, payment_method)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, supplier_id, payment_date, amount, reference, payment_method))
                
                payment_id = cursor.lastrowid
                conn.commit()
            return True, f"Payment of £{amount:.2f} created successfully", payment_id
        except Exception as e:
            return False, f"Error creating payment: {str(e)}", None
    
    def get_all(self, user_id: int, supplier_id: Optional[int] = None) -> List[Dict[str, any]]:
        """
        Get all payments for a user, optionally filtered by supplier.
        
        Args:
            user_id: ID of the user
            supplier_id: Optional supplier ID to filter by
        
        Returns:
            List of payment dictionaries
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if supplier_id:
                    cursor.execute("""
                        SELECT id, supplier_id, payment_date, amount, reference, payment_method, created_at
                        FROM payments 
                        WHERE user_id = ? AND supplier_id = ?
                        ORDER BY payment_date DESC, id DESC
                    """, (user_id, supplier_id))
                else:
                    cursor.execute("""
                        SELECT id, supplier_id, payment_date, amount, reference, payment_method, created_at
                        FROM payments 
                        WHERE user_id = ?
                        ORDER BY payment_date DESC, id DESC
                    """, (user_id,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception:
            return []
    
    def get_by_id(self, payment_id: int, user_id: int) -> Optional[Dict[str, any]]:
        """
        Get a payment by ID for a specific user.
        
        Args:
            payment_id: Payment ID
            user_id: ID of the user
        
        Returns:
            Payment dictionary or None if not found
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, supplier_id, payment_date, amount, reference, payment_method, created_at
                    FROM payments 
                    WHERE id = ? AND user_id = ?
                """, (payment_id, user_id))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception:
            return None
    
    def get_unallocated_amount(self, payment_id: int) -> float:
        """
        Calculate remaining unallocated amount for a payment.
        
        Args:
            payment_id: Payment ID
        
        Returns:
            Unallocated amount
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Get payment amount
                cursor.execute("SELECT amount FROM payments WHERE id = ?", (payment_id,))
                result = cursor.fetchone()
                if not result:
                    return 0.0
                
                payment_amount = result[0]
                
                # Sum allocated amounts
                cursor.execute("""
                    SELECT COALESCE(SUM(amount_allocated), 0.0)
                    FROM payment_allocations
                    WHERE payment_id = ?
                """, (payment_id,))
                allocated = cursor.fetchone()[0]
                
                return max(0.0, payment_amount - allocated)
        except Exception:
            return 0.0
    
    def delete(self, payment_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Delete a payment (removes allocations).
        
        Args:
            payment_id: Payment ID
            user_id: ID of the user
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Check if payment exists and belongs to user
                cursor.execute("SELECT id FROM payments WHERE id = ? AND user_id = ?", (payment_id, user_id))
                if not cursor.fetchone():
                    return False, "Payment not found"
                
                # Delete allocations first
                cursor.execute("DELETE FROM payment_allocations WHERE payment_id = ?", (payment_id,))
                
                # Delete payment
                cursor.execute("DELETE FROM payments WHERE id = ? AND user_id = ?", (payment_id, user_id))
                
                if cursor.rowcount == 0:
                    return False, "Payment not found"
                
                conn.commit()
            return True, "Payment deleted successfully"
        except Exception as e:
            return False, f"Error deleting payment: {str(e)}"

