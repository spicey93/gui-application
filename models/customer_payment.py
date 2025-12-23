"""Customer payment model for customer payment management."""
import sqlite3
from typing import Optional, Tuple, List, Dict
import os


class CustomerPayment:
    """Customer payment model with database operations."""
    
    def __init__(self, db_path: str = "data/app.db"):
        """Initialize customer payment model with database path."""
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_database(self):
        """Initialize the database with customer_payments table."""
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='customer_payments'
            """)
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Create new table
                cursor.execute("""
                    CREATE TABLE customer_payments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        customer_id INTEGER NOT NULL,
                        payment_date DATE NOT NULL,
                        amount REAL NOT NULL,
                        reference TEXT,
                        payment_method TEXT NOT NULL DEFAULT 'Cash',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
                    )
                """)
            
            conn.commit()
    
    def create(self, customer_id: int, payment_date: str, amount: float,
               reference: str, payment_method: str, user_id: int) -> Tuple[bool, str, Optional[int]]:
        """
        Create a new customer payment.
        
        Args:
            customer_id: Internal customer ID
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
        
        if not user_id or not customer_id:
            return False, "User ID and customer ID are required", None
        
        if payment_method not in ['Cash', 'Card', 'Cheque', 'BACS']:
            return False, "Payment method must be one of: Cash, Card, Cheque, BACS", None
        
        reference = reference.strip() if reference else ""
        
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO customer_payments (user_id, customer_id, payment_date, amount, reference, payment_method)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, customer_id, payment_date, amount, reference, payment_method))
                
                payment_id = cursor.lastrowid
                conn.commit()
            return True, f"Payment of £{amount:.2f} created successfully", payment_id
        except Exception as e:
            return False, f"Error creating payment: {str(e)}", None
    
    def get_all(self, user_id: int, customer_id: Optional[int] = None) -> List[Dict[str, any]]:
        """
        Get all customer payments for a user, optionally filtered by customer.
        
        Args:
            user_id: ID of the user
            customer_id: Optional customer ID to filter by
        
        Returns:
            List of payment dictionaries
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if customer_id:
                    cursor.execute("""
                        SELECT id, customer_id, payment_date, amount, reference, payment_method, created_at
                        FROM customer_payments 
                        WHERE user_id = ? AND customer_id = ?
                        ORDER BY payment_date DESC, id DESC
                    """, (user_id, customer_id))
                else:
                    cursor.execute("""
                        SELECT id, customer_id, payment_date, amount, reference, payment_method, created_at
                        FROM customer_payments 
                        WHERE user_id = ?
                        ORDER BY payment_date DESC, id DESC
                    """, (user_id,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception:
            return []
    
    def get_by_id(self, payment_id: int, user_id: int) -> Optional[Dict[str, any]]:
        """
        Get a customer payment by ID for a specific user.
        
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
                    SELECT id, customer_id, payment_date, amount, reference, payment_method, created_at
                    FROM customer_payments 
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
                cursor.execute("SELECT amount FROM customer_payments WHERE id = ?", (payment_id,))
                result = cursor.fetchone()
                if not result:
                    return 0.0
                
                payment_amount = result[0]
                
                # Sum allocated amounts
                cursor.execute("""
                    SELECT COALESCE(SUM(amount_allocated), 0.0)
                    FROM customer_payment_allocations
                    WHERE payment_id = ?
                """, (payment_id,))
                allocated = cursor.fetchone()[0]
                
                return max(0.0, payment_amount - allocated)
        except Exception:
            return 0.0
    
    def delete(self, payment_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Delete a customer payment (only if no allocations).
        
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
                cursor.execute("SELECT id FROM customer_payments WHERE id = ? AND user_id = ?", 
                             (payment_id, user_id))
                if not cursor.fetchone():
                    return False, "Payment not found"
                
                # Check if any allocations exist
                cursor.execute("""
                    SELECT COUNT(*) FROM customer_payment_allocations WHERE payment_id = ?
                """, (payment_id,))
                allocation_count = cursor.fetchone()[0]
                
                if allocation_count > 0:
                    return False, "Cannot delete payment: payment has been allocated to invoices. Please unallocate first."
                
                # Delete payment
                cursor.execute("DELETE FROM customer_payments WHERE id = ? AND user_id = ?", 
                             (payment_id, user_id))
                
                if cursor.rowcount == 0:
                    return False, "Payment not found"
                
                conn.commit()
            return True, "Payment deleted successfully"
        except Exception as e:
            return False, f"Error deleting payment: {str(e)}"

