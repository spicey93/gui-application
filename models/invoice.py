"""Invoice model for purchase invoice management."""
import sqlite3
from typing import Optional, Tuple, List, Dict
import os
from datetime import datetime


class Invoice:
    """Invoice model with database operations."""
    
    def __init__(self, db_path: str = "data/app.db"):
        """Initialize invoice model with database path."""
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_database(self):
        """Initialize the database with invoices table."""
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='invoices'
            """)
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Create new table
                cursor.execute("""
                    CREATE TABLE invoices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        supplier_id INTEGER NOT NULL,
                        invoice_number TEXT NOT NULL,
                        invoice_date DATE NOT NULL,
                        vat_rate REAL NOT NULL DEFAULT 20.0,
                        subtotal REAL NOT NULL DEFAULT 0.0,
                        vat_amount REAL NOT NULL DEFAULT 0.0,
                        total REAL NOT NULL DEFAULT 0.0,
                        status TEXT NOT NULL DEFAULT 'draft',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE,
                        UNIQUE(user_id, supplier_id, invoice_number)
                    )
                """)
            
            conn.commit()
    
    def create(self, supplier_id: int, invoice_number: str, invoice_date: str, 
               vat_rate: float, user_id: int) -> Tuple[bool, str, Optional[int]]:
        """
        Create a new invoice.
        
        Args:
            supplier_id: ID of the supplier
            invoice_number: Invoice number (user-entered)
            invoice_date: Invoice date (YYYY-MM-DD format)
            vat_rate: VAT rate as percentage (e.g., 20.0 for 20%)
            user_id: ID of the user creating the invoice
        
        Returns:
            Tuple of (success: bool, message: str, invoice_id: Optional[int])
        """
        if not invoice_number or not invoice_number.strip():
            return False, "Invoice number is required", None
        
        if not invoice_date:
            return False, "Invoice date is required", None
        
        if vat_rate < 0 or vat_rate > 100:
            return False, "VAT rate must be between 0 and 100", None
        
        if not user_id or not supplier_id:
            return False, "User ID and supplier ID are required", None
        
        invoice_number = invoice_number.strip()
        
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO invoices (user_id, supplier_id, invoice_number, invoice_date, vat_rate, subtotal, vat_amount, total, status)
                    VALUES (?, ?, ?, ?, ?, 0.0, 0.0, 0.0, 'draft')
                """, (user_id, supplier_id, invoice_number, invoice_date, vat_rate))
                
                invoice_id = cursor.lastrowid
                conn.commit()
            return True, f"Invoice '{invoice_number}' created successfully", invoice_id
        except sqlite3.IntegrityError:
            return False, "Invoice number already exists for this supplier", None
        except Exception as e:
            return False, f"Error creating invoice: {str(e)}", None
    
    def get_all(self, user_id: int, supplier_id: Optional[int] = None) -> List[Dict[str, any]]:
        """
        Get all invoices for a user, optionally filtered by supplier.
        
        Args:
            user_id: ID of the user
            supplier_id: Optional supplier ID to filter by
        
        Returns:
            List of invoice dictionaries
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if supplier_id:
                    cursor.execute("""
                        SELECT id, supplier_id, invoice_number, invoice_date, vat_rate,
                               subtotal, vat_amount, total, status, created_at, updated_at
                        FROM invoices 
                        WHERE user_id = ? AND supplier_id = ?
                        ORDER BY invoice_date DESC, invoice_number DESC
                    """, (user_id, supplier_id))
                else:
                    cursor.execute("""
                        SELECT id, supplier_id, invoice_number, invoice_date, vat_rate,
                               subtotal, vat_amount, total, status, created_at, updated_at
                        FROM invoices 
                        WHERE user_id = ?
                        ORDER BY invoice_date DESC, invoice_number DESC
                    """, (user_id,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception:
            return []
    
    def get_by_id(self, invoice_id: int, user_id: int) -> Optional[Dict[str, any]]:
        """
        Get an invoice by ID for a specific user.
        
        Args:
            invoice_id: Invoice ID
            user_id: ID of the user
        
        Returns:
            Invoice dictionary or None if not found
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, supplier_id, invoice_number, invoice_date, vat_rate,
                           subtotal, vat_amount, total, status, created_at, updated_at
                    FROM invoices 
                    WHERE id = ? AND user_id = ?
                """, (invoice_id, user_id))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception:
            return None
    
    def update(self, invoice_id: int, invoice_number: str, invoice_date: str,
               vat_rate: float, status: str, user_id: int) -> Tuple[bool, str]:
        """
        Update invoice details.
        
        Args:
            invoice_id: Invoice ID
            invoice_number: New invoice number
            invoice_date: New invoice date
            vat_rate: New VAT rate
            status: New status
            user_id: ID of the user
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not invoice_number or not invoice_number.strip():
            return False, "Invoice number is required"
        
        if not invoice_date:
            return False, "Invoice date is required"
        
        if vat_rate < 0 or vat_rate > 100:
            return False, "VAT rate must be between 0 and 100"
        
        if status not in ['draft', 'finalized', 'paid', 'cancelled']:
            return False, "Invalid status"
        
        invoice_number = invoice_number.strip()
        
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Check if invoice exists and belongs to user, and get current status
                cursor.execute("SELECT id, status FROM invoices WHERE id = ? AND user_id = ?", (invoice_id, user_id))
                result = cursor.fetchone()
                if not result:
                    return False, "Invoice not found"
                
                old_status = result[1]
                
                cursor.execute("""
                    UPDATE invoices 
                    SET invoice_number = ?, invoice_date = ?, vat_rate = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ?
                """, (invoice_number, invoice_date, vat_rate, status, invoice_id, user_id))
                
                conn.commit()
                
                # If status changed to 'cancelled', reverse stock for all items
                if old_status != 'cancelled' and status == 'cancelled':
                    self._reverse_invoice_stock(invoice_id)
            
            return True, "Invoice updated successfully"
        except sqlite3.IntegrityError:
            return False, "Invoice number already exists for this supplier"
        except Exception as e:
            return False, f"Error updating invoice: {str(e)}"
    
    def calculate_totals(self, invoice_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Recalculate invoice totals from items using per-item VAT codes.
        
        Args:
            invoice_id: Invoice ID
            user_id: ID of the user
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Check if invoice exists
                cursor.execute("SELECT id FROM invoices WHERE id = ? AND user_id = ?", (invoice_id, user_id))
                if not cursor.fetchone():
                    return False, "Invoice not found"
                
                # Get all items with their VAT codes
                cursor.execute("""
                    SELECT line_total, COALESCE(vat_code, 'S') as vat_code
                    FROM invoice_items 
                    WHERE invoice_id = ?
                """, (invoice_id,))
                
                items = cursor.fetchall()
                
                # Calculate subtotal and VAT per item
                subtotal = 0.0
                vat_amount = 0.0
                
                # VAT rates by code: S=Standard (20%), E=Exempt (0%), Z=Zero (0%)
                vat_rates = {'S': 20.0, 'E': 0.0, 'Z': 0.0}
                
                for line_total, vat_code in items:
                    subtotal += line_total
                    vat_code = (vat_code or 'S').strip().upper()
                    vat_rate = vat_rates.get(vat_code, 20.0)  # Default to 20% if unknown
                    line_vat = line_total * (vat_rate / 100.0)
                    vat_amount += line_vat
                
                total = subtotal + vat_amount
                
                # Update invoice
                cursor.execute("""
                    UPDATE invoices 
                    SET subtotal = ?, vat_amount = ?, total = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ?
                """, (subtotal, vat_amount, total, invoice_id, user_id))
                
                conn.commit()
            return True, "Totals calculated successfully"
        except Exception as e:
            return False, f"Error calculating totals: {str(e)}"
    
    def update_totals(self, invoice_id: int, subtotal: float, vat_amount: float, total: float, user_id: int) -> Tuple[bool, str]:
        """
        Update invoice totals directly (for manual VAT override).
        
        Args:
            invoice_id: Invoice ID
            subtotal: Subtotal amount
            vat_amount: VAT amount
            total: Total amount
            user_id: ID of the user
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Check if invoice exists
                cursor.execute("SELECT id FROM invoices WHERE id = ? AND user_id = ?", (invoice_id, user_id))
                if not cursor.fetchone():
                    return False, "Invoice not found"
                
                # Update invoice totals
                cursor.execute("""
                    UPDATE invoices 
                    SET subtotal = ?, vat_amount = ?, total = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ?
                """, (subtotal, vat_amount, total, invoice_id, user_id))
                
                conn.commit()
            return True, "Totals updated successfully"
        except Exception as e:
            return False, f"Error updating totals: {str(e)}"
    
    def get_outstanding_balance(self, invoice_id: int, user_id: int) -> float:
        """
        Calculate outstanding balance for an invoice (total - allocated payments).
        
        Args:
            invoice_id: Invoice ID
            user_id: ID of the user
        
        Returns:
            Outstanding balance amount
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Get invoice total
                cursor.execute("SELECT total FROM invoices WHERE id = ? AND user_id = ?", (invoice_id, user_id))
                result = cursor.fetchone()
                if not result:
                    return 0.0
                
                invoice_total = result[0]
                
                # Sum allocated payments
                cursor.execute("""
                    SELECT COALESCE(SUM(amount_allocated), 0.0)
                    FROM payment_allocations
                    WHERE invoice_id = ?
                """, (invoice_id,))
                allocated = cursor.fetchone()[0]
                
                return max(0.0, invoice_total - allocated)
        except Exception:
            return 0.0
    
    def update_status_if_paid(self, invoice_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Update invoice status to 'paid' if fully paid (outstanding balance <= 0).
        
        Args:
            invoice_id: Invoice ID
            user_id: ID of the user
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Check if invoice exists and belongs to user
                cursor.execute("SELECT id, status FROM invoices WHERE id = ? AND user_id = ?", (invoice_id, user_id))
                result = cursor.fetchone()
                if not result:
                    return False, "Invoice not found"
                
                current_status = result[1]
                
                # Get outstanding balance
                outstanding = self.get_outstanding_balance(invoice_id, user_id)
                
                # If fully paid and not already marked as paid, update status
                if outstanding <= 0.01 and current_status != 'paid':
                    cursor.execute("""
                        UPDATE invoices 
                        SET status = 'paid', updated_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND user_id = ?
                    """, (invoice_id, user_id))
                    conn.commit()
                    return True, "Invoice status updated to paid"
                # If not fully paid and currently marked as paid, revert to finalized
                elif outstanding > 0.01 and current_status == 'paid':
                    cursor.execute("""
                        UPDATE invoices 
                        SET status = 'finalized', updated_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND user_id = ?
                    """, (invoice_id, user_id))
                    conn.commit()
                    return True, "Invoice status updated to finalized"
                
                return True, "Status check completed"
        except Exception as e:
            return False, f"Error updating invoice status: {str(e)}"
    
    def delete(self, invoice_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Delete an invoice (only if no payments allocated).
        
        Args:
            invoice_id: Invoice ID
            user_id: ID of the user
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Check if invoice exists and belongs to user
                cursor.execute("SELECT id FROM invoices WHERE id = ? AND user_id = ?", (invoice_id, user_id))
                if not cursor.fetchone():
                    return False, "Invoice not found"
                
                # Check if any payments are allocated
                cursor.execute("""
                    SELECT COUNT(*) FROM payment_allocations WHERE invoice_id = ?
                """, (invoice_id,))
                allocation_count = cursor.fetchone()[0]
                
                if allocation_count > 0:
                    return False, "Cannot delete invoice: payments have been allocated to this invoice"
                
                # Reverse stock for all items before deletion
                self._reverse_invoice_stock(invoice_id)
                
                # Delete invoice items first (CASCADE should handle this, but explicit is safer)
                cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
                
                # Delete invoice
                cursor.execute("DELETE FROM invoices WHERE id = ? AND user_id = ?", (invoice_id, user_id))
                
                if cursor.rowcount == 0:
                    return False, "Invoice not found"
                
                conn.commit()
            return True, "Invoice deleted successfully"
        except Exception as e:
            return False, f"Error deleting invoice: {str(e)}"
    
    def _reverse_invoice_stock(self, invoice_id: int) -> None:
        """
        Reverse stock for all items in an invoice (subtract quantities).
        
        Args:
            invoice_id: Invoice ID
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Get all items with product_id
                cursor.execute("""
                    SELECT product_id, quantity 
                    FROM invoice_items 
                    WHERE invoice_id = ? AND product_id IS NOT NULL
                """, (invoice_id,))
                
                items = cursor.fetchall()
                
                if items:
                    from models.product import Product
                    product_model = Product(self.db_path)
                    
                    for product_id, quantity in items:
                        if product_id is not None:
                            # Subtract quantity (reverse the stock)
                            product_model.update_stock(product_id, -quantity)
        except Exception:
            # Silently fail - stock reversal is not critical for invoice operations
            pass

