"""Payment allocation model for allocating payments to invoices."""
import sqlite3
from typing import Optional, Tuple, List, Dict
import os


class PaymentAllocation:
    """Payment allocation model with database operations."""
    
    def __init__(self, db_path: str = "data/app.db"):
        """Initialize payment allocation model with database path."""
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_database(self):
        """Initialize the database with payment_allocations table."""
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='payment_allocations'
            """)
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Create new table
                cursor.execute("""
                    CREATE TABLE payment_allocations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        payment_id INTEGER NOT NULL,
                        invoice_id INTEGER NOT NULL,
                        amount_allocated REAL NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE CASCADE,
                        FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
                        UNIQUE(payment_id, invoice_id)
                    )
                """)
            
            conn.commit()
    
    def create(self, payment_id: int, invoice_id: int, amount_allocated: float) -> Tuple[bool, str, Optional[int]]:
        """
        Allocate payment amount to an invoice.
        
        Args:
            payment_id: Payment ID
            invoice_id: Invoice ID
            amount_allocated: Amount to allocate
        
        Returns:
            Tuple of (success: bool, message: str, allocation_id: Optional[int])
        """
        if amount_allocated <= 0:
            return False, "Allocation amount must be greater than zero", None
        
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Check if allocation already exists
                cursor.execute("""
                    SELECT id FROM payment_allocations 
                    WHERE payment_id = ? AND invoice_id = ?
                """, (payment_id, invoice_id))
                if cursor.fetchone():
                    return False, "Allocation already exists for this payment and invoice", None
                
                # Validate allocation amount doesn't exceed payment unallocated amount
                from models.payment import Payment
                payment_model = Payment(self.db_path)
                unallocated = payment_model.get_unallocated_amount(payment_id)
                if amount_allocated > unallocated:
                    return False, f"Allocation amount exceeds unallocated payment amount (£{unallocated:.2f})", None
                
                # Validate allocation doesn't exceed invoice outstanding balance
                from models.invoice import Invoice
                invoice_model = Invoice(self.db_path)
                # Get user_id from payment
                cursor.execute("SELECT user_id FROM payments WHERE id = ?", (payment_id,))
                result = cursor.fetchone()
                if not result:
                    return False, "Payment not found", None
                user_id = result[0]
                
                outstanding = invoice_model.get_outstanding_balance(invoice_id, user_id)
                if amount_allocated > outstanding:
                    return False, f"Allocation amount exceeds invoice outstanding balance (£{outstanding:.2f})", None
                
                # Check if allocation already exists for this payment and invoice
                cursor.execute("""
                    SELECT id, amount_allocated FROM payment_allocations
                    WHERE payment_id = ? AND invoice_id = ?
                """, (payment_id, invoice_id))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing allocation by adding to it
                    existing_id, existing_amount = existing
                    new_amount = existing_amount + amount_allocated
                    
                    # Validate new total doesn't exceed outstanding balance
                    outstanding = invoice_model.get_outstanding_balance(invoice_id, user_id)
                    outstanding_with_existing = outstanding + existing_amount
                    if new_amount > outstanding_with_existing:
                        return False, f"Total allocation amount (£{new_amount:.2f}) exceeds invoice outstanding balance (£{outstanding_with_existing:.2f})", None
                    
                    # Update the allocation
                    cursor.execute("""
                        UPDATE payment_allocations
                        SET amount_allocated = ?
                        WHERE id = ?
                    """, (new_amount, existing_id))
                    allocation_id = existing_id
                else:
                    # Create new allocation
                    cursor.execute("""
                        INSERT INTO payment_allocations (payment_id, invoice_id, amount_allocated)
                        VALUES (?, ?, ?)
                    """, (payment_id, invoice_id, amount_allocated))
                    allocation_id = cursor.lastrowid
                
                conn.commit()
            return True, f"Allocated £{amount_allocated:.2f} to invoice", allocation_id
        except sqlite3.IntegrityError:
            return False, "Allocation already exists for this payment and invoice", None
        except Exception as e:
            return False, f"Error creating allocation: {str(e)}", None
    
    def get_by_payment(self, payment_id: int) -> List[Dict[str, any]]:
        """
        Get all allocations for a payment.
        
        Args:
            payment_id: Payment ID
        
        Returns:
            List of allocation dictionaries
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, payment_id, invoice_id, amount_allocated, created_at
                    FROM payment_allocations 
                    WHERE payment_id = ?
                    ORDER BY created_at
                """, (payment_id,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception:
            return []
    
    def get_by_invoice(self, invoice_id: int) -> List[Dict[str, any]]:
        """
        Get all allocations for an invoice.
        
        Args:
            invoice_id: Invoice ID
        
        Returns:
            List of allocation dictionaries
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, payment_id, invoice_id, amount_allocated, created_at
                    FROM payment_allocations 
                    WHERE invoice_id = ?
                    ORDER BY created_at
                """, (invoice_id,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception:
            return []
    
    def update(self, allocation_id: int, amount_allocated: float) -> Tuple[bool, str, Optional[int]]:
        """
        Update an allocation amount.
        
        Args:
            allocation_id: Allocation ID
            amount_allocated: New allocation amount
        
        Returns:
            Tuple of (success: bool, message: str, invoice_id: Optional[int])
        """
        if amount_allocated <= 0:
            return False, "Allocation amount must be greater than zero", None
        
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Get payment_id and invoice_id for validation
                cursor.execute("""
                    SELECT payment_id, invoice_id FROM payment_allocations WHERE id = ?
                """, (allocation_id,))
                result = cursor.fetchone()
                if not result:
                    return False, "Allocation not found", None
                
                payment_id, invoice_id = result
                
                # Validate new amount
                from models.payment import Payment
                payment_model = Payment(self.db_path)
                unallocated = payment_model.get_unallocated_amount(payment_id)
                
                # Get current allocation to calculate available amount
                cursor.execute("SELECT amount_allocated FROM payment_allocations WHERE id = ?", (allocation_id,))
                current_amount = cursor.fetchone()[0]
                available = unallocated + current_amount
                
                if amount_allocated > available:
                    return False, f"Allocation amount exceeds available payment amount (£{available:.2f})", None
                
                # Validate against invoice outstanding
                from models.invoice import Invoice
                invoice_model = Invoice(self.db_path)
                cursor.execute("SELECT user_id FROM payments WHERE id = ?", (payment_id,))
                user_id = cursor.fetchone()[0]
                outstanding = invoice_model.get_outstanding_balance(invoice_id, user_id)
                outstanding_with_current = outstanding + current_amount
                
                if amount_allocated > outstanding_with_current:
                    return False, f"Allocation amount exceeds invoice outstanding balance (£{outstanding_with_current:.2f})", None
                
                # Update allocation
                cursor.execute("""
                    UPDATE payment_allocations 
                    SET amount_allocated = ?
                    WHERE id = ?
                """, (amount_allocated, allocation_id))
                
                if cursor.rowcount == 0:
                    return False, "Allocation not found", None
                
                conn.commit()
            return True, "Allocation updated successfully", invoice_id
        except Exception as e:
            return False, f"Error updating allocation: {str(e)}", None
    
    def get_by_id(self, allocation_id: int) -> Optional[Dict[str, any]]:
        """
        Get an allocation by ID.
        
        Args:
            allocation_id: Allocation ID
        
        Returns:
            Allocation dictionary or None if not found
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, payment_id, invoice_id, amount_allocated, created_at
                    FROM payment_allocations 
                    WHERE id = ?
                """, (allocation_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception:
            return None
    
    def delete(self, allocation_id: int) -> Tuple[bool, str, Optional[int]]:
        """
        Remove an allocation.
        
        Args:
            allocation_id: Allocation ID
        
        Returns:
            Tuple of (success: bool, message: str, invoice_id: Optional[int])
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Get invoice_id before deletion
                cursor.execute("SELECT invoice_id FROM payment_allocations WHERE id = ?", (allocation_id,))
                result = cursor.fetchone()
                if not result:
                    return False, "Allocation not found", None
                
                invoice_id = result[0]
                
                cursor.execute("DELETE FROM payment_allocations WHERE id = ?", (allocation_id,))
                
                if cursor.rowcount == 0:
                    return False, "Allocation not found", None
                
                conn.commit()
            return True, "Allocation deleted successfully", invoice_id
        except Exception as e:
            return False, f"Error deleting allocation: {str(e)}", None
    
    def get_total_allocated_to_invoice(self, invoice_id: int) -> float:
        """
        Get total amount allocated to an invoice.
        
        Args:
            invoice_id: Invoice ID
        
        Returns:
            Total allocated amount
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COALESCE(SUM(amount_allocated), 0.0)
                    FROM payment_allocations
                    WHERE invoice_id = ?
                """, (invoice_id,))
                result = cursor.fetchone()
                return result[0] if result else 0.0
        except Exception:
            return 0.0

