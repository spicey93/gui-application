"""Sales invoice model for customer sales document management."""
import sqlite3
from typing import Optional, Tuple, List, Dict
import os
from datetime import datetime


class SalesInvoice:
    """Sales invoice model with database operations."""
    
    def __init__(self, db_path: str = "data/app.db"):
        """Initialize sales invoice model with database path."""
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_database(self):
        """Initialize the database with sales_invoices table."""
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='sales_invoices'
            """)
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Create new table
                cursor.execute("""
                    CREATE TABLE sales_invoices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        customer_id INTEGER,
                        vehicle_id INTEGER,
                        document_number TEXT NOT NULL,
                        document_date DATE NOT NULL,
                        document_type TEXT NOT NULL DEFAULT 'order',
                        notes TEXT,
                        subtotal REAL NOT NULL DEFAULT 0.0,
                        vat_amount REAL NOT NULL DEFAULT 0.0,
                        total REAL NOT NULL DEFAULT 0.0,
                        status TEXT NOT NULL DEFAULT 'draft',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
                        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
                        UNIQUE(user_id, document_number)
                    )
                """)
            else:
                # Check if vehicle_id column exists, add it if not
                cursor.execute("PRAGMA table_info(sales_invoices)")
                columns = [row[1] for row in cursor.fetchall()]
                if 'vehicle_id' not in columns:
                    cursor.execute("""
                        ALTER TABLE sales_invoices 
                        ADD COLUMN vehicle_id INTEGER
                    """)
                    try:
                        cursor.execute("""
                            CREATE INDEX IF NOT EXISTS idx_sales_invoice_vehicle 
                            ON sales_invoices(vehicle_id)
                        """)
                    except sqlite3.OperationalError:
                        pass
                
                # Migrate customer_id to allow NULL if needed
                # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
                # Check if we need to migrate by trying to read table info
                cursor.execute("PRAGMA table_info(sales_invoices)")
                column_info = cursor.fetchall()
                customer_id_col = next((col for col in column_info if col[1] == 'customer_id'), None)
                
                # Check if customer_id is NOT NULL by examining the schema
                cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='sales_invoices'")
                schema = cursor.fetchone()
                if schema and 'customer_id INTEGER NOT NULL' in schema[0]:
                    # Need to migrate - recreate table with nullable customer_id
                    try:
                        # Create new table with nullable customer_id
                        cursor.execute("""
                            CREATE TABLE sales_invoices_new (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id INTEGER NOT NULL,
                                customer_id INTEGER,
                                vehicle_id INTEGER,
                                document_number TEXT NOT NULL,
                                document_date DATE NOT NULL,
                                document_type TEXT NOT NULL DEFAULT 'order',
                                notes TEXT,
                                subtotal REAL NOT NULL DEFAULT 0.0,
                                vat_amount REAL NOT NULL DEFAULT 0.0,
                                total REAL NOT NULL DEFAULT 0.0,
                                status TEXT NOT NULL DEFAULT 'draft',
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
                                FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
                                UNIQUE(user_id, document_number)
                            )
                        """)
                        
                        # Copy data (customer_id will be copied as-is, NULLs allowed)
                        cursor.execute("""
                            INSERT INTO sales_invoices_new 
                            SELECT * FROM sales_invoices
                        """)
                        
                        # Drop old table
                        cursor.execute("DROP TABLE sales_invoices")
                        
                        # Rename new table
                        cursor.execute("ALTER TABLE sales_invoices_new RENAME TO sales_invoices")
                        
                        # Recreate indexes
                        try:
                            cursor.execute("""
                                CREATE INDEX IF NOT EXISTS idx_sales_invoice_vehicle 
                                ON sales_invoices(vehicle_id)
                            """)
                        except sqlite3.OperationalError:
                            pass
                    except Exception:
                        # Migration failed, but table exists - continue with existing schema
                        # Application will need to handle this case
                        pass
            
            conn.commit()
    
    def generate_document_number(self, document_type: str, user_id: int) -> str:
        """
        Generate the next sequential document number for a document type.
        
        Args:
            document_type: Document type ('quote', 'order', 'invoice')
            user_id: ID of the user
        
        Returns:
            Generated document number (e.g., QU000005, ORD000032, INV032)
        """
        if document_type not in ['quote', 'order', 'invoice']:
            document_type = 'order'
        
        # Prefixes for each type
        prefixes = {
            'quote': 'QU',
            'order': 'ORD',
            'invoice': 'INV'
        }
        prefix = prefixes[document_type]
        
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Get the highest number for this document type and user
                cursor.execute("""
                    SELECT document_number FROM sales_invoices 
                    WHERE user_id = ? AND document_type = ?
                    ORDER BY document_number DESC
                    LIMIT 1
                """, (user_id, document_type))
                
                result = cursor.fetchone()
                next_number = 1
                
                if result:
                    # Extract number from existing document number
                    existing = result[0]
                    try:
                        # Try to extract number (handle both formats: QU000005 and INV032)
                        if existing.startswith(prefix):
                            number_part = existing[len(prefix):].lstrip('0')
                            if number_part:
                                next_number = int(number_part) + 1
                            else:
                                next_number = 1
                    except (ValueError, AttributeError):
                        next_number = 1
                
                # Format with leading zeros (6 digits for quotes/orders, 3 for invoices)
                if document_type == 'invoice':
                    return f"{prefix}{next_number:03d}"
                else:
                    return f"{prefix}{next_number:06d}"
        except Exception:
            # Fallback to simple format
            return f"{prefix}001"
    
    def create(self, customer_id: Optional[int], document_date: str, 
               document_type: str, notes: str, user_id: int,
               vehicle_id: Optional[int] = None, document_number: Optional[str] = None) -> Tuple[bool, str, Optional[int]]:
        """
        Create a new sales invoice.
        
        Args:
            customer_id: Internal customer ID (optional, can be None)
            document_date: Document date (YYYY-MM-DD format)
            document_type: Document type ('quote', 'order', 'invoice')
            notes: Notes text (optional)
            user_id: ID of the user creating the document
            vehicle_id: Optional vehicle ID
            document_number: Optional document number (auto-generated if not provided)
        
        Returns:
            Tuple of (success: bool, message: str, sales_invoice_id: Optional[int])
        """
        if not document_date:
            return False, "Document date is required", None
        
        if document_type not in ['quote', 'order', 'invoice']:
            return False, "Document type must be 'quote', 'order', or 'invoice'", None
        
        if not user_id:
            return False, "User ID is required", None
        
        # Auto-generate document number if not provided
        if not document_number:
            document_number = self.generate_document_number(document_type, user_id)
        else:
            document_number = document_number.strip()
        
        notes = notes.strip() if notes else ""
        
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO sales_invoices (user_id, customer_id, vehicle_id, document_number, document_date, 
                                                document_type, notes, subtotal, vat_amount, total, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0.0, 0.0, 0.0, 'draft')
                """, (user_id, customer_id, vehicle_id, document_number, document_date, document_type, notes))
                
                sales_invoice_id = cursor.lastrowid
                conn.commit()
            return True, f"Sales document '{document_number}' created successfully", sales_invoice_id
        except sqlite3.IntegrityError:
            return False, "Document number already exists", None
        except Exception as e:
            return False, f"Error creating sales document: {str(e)}", None
    
    def get_all(self, user_id: int, customer_id: Optional[int] = None, 
                document_type: Optional[str] = None) -> List[Dict[str, any]]:
        """
        Get all sales invoices for a user, optionally filtered by customer or type.
        
        Args:
            user_id: ID of the user
            customer_id: Optional customer ID to filter by
            document_type: Optional document type to filter by
        
        Returns:
            List of sales invoice dictionaries
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = """
                    SELECT id, customer_id, vehicle_id, document_number, document_date, document_type,
                           notes, subtotal, vat_amount, total, status, created_at, updated_at
                    FROM sales_invoices 
                    WHERE user_id = ?
                """
                params = [user_id]
                
                if customer_id:
                    query += " AND customer_id = ?"
                    params.append(customer_id)
                
                if document_type:
                    query += " AND document_type = ?"
                    params.append(document_type)
                
                query += " ORDER BY document_date DESC, document_number DESC"
                
                cursor.execute(query, tuple(params))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception:
            return []
    
    def get_by_id(self, sales_invoice_id: int, user_id: int) -> Optional[Dict[str, any]]:
        """
        Get a sales invoice by ID for a specific user.
        
        Args:
            sales_invoice_id: Sales invoice ID
            user_id: ID of the user
        
        Returns:
            Sales invoice dictionary or None if not found
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, customer_id, vehicle_id, document_number, document_date, document_type,
                           notes, subtotal, vat_amount, total, status, created_at, updated_at
                    FROM sales_invoices 
                    WHERE id = ? AND user_id = ?
                """, (sales_invoice_id, user_id))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception:
            return None
    
    def update(self, sales_invoice_id: int, document_number: str, document_date: str,
              document_type: str, notes: str, status: str, user_id: int,
              vehicle_id: Optional[int] = None) -> Tuple[bool, str]:
        """
        Update sales invoice details.
        
        Args:
            sales_invoice_id: Sales invoice ID
            document_number: New document number
            document_date: New document date
            document_type: New document type
            notes: New notes
            status: New status
            user_id: ID of the user
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not document_number or not document_number.strip():
            return False, "Document number is required"
        
        if not document_date:
            return False, "Document date is required"
        
        if document_type not in ['quote', 'order', 'invoice']:
            return False, "Document type must be 'quote', 'order', or 'invoice'"
        
        if status not in ['draft', 'sent', 'finalized', 'paid', 'cancelled']:
            return False, "Invalid status"
        
        document_number = document_number.strip()
        notes = notes.strip() if notes else ""
        
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Check if sales invoice exists and belongs to user
                cursor.execute("SELECT id FROM sales_invoices WHERE id = ? AND user_id = ?", 
                             (sales_invoice_id, user_id))
                if not cursor.fetchone():
                    return False, "Sales invoice not found"
                
                old_status = None
                cursor.execute("SELECT status FROM sales_invoices WHERE id = ? AND user_id = ?",
                             (sales_invoice_id, user_id))
                result = cursor.fetchone()
                if result:
                    old_status = result[0]
                
                cursor.execute("""
                    UPDATE sales_invoices 
                    SET document_number = ?, document_date = ?, document_type = ?, 
                        notes = ?, status = ?, vehicle_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ?
                """, (document_number, document_date, document_type, notes, status, vehicle_id,
                      sales_invoice_id, user_id))
                
                conn.commit()
                
                # If status changed to 'cancelled', restore stock for all items
                if old_status != 'cancelled' and status == 'cancelled':
                    self._restore_sales_invoice_stock(sales_invoice_id)
            
            return True, "Sales invoice updated successfully"
        except sqlite3.IntegrityError:
            return False, "Document number already exists"
        except Exception as e:
            return False, f"Error updating sales invoice: {str(e)}"
    
    def calculate_totals(self, sales_invoice_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Recalculate sales invoice totals from items using per-item VAT codes.
        
        Args:
            sales_invoice_id: Sales invoice ID
            user_id: ID of the user
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Check if sales invoice exists
                cursor.execute("SELECT id FROM sales_invoices WHERE id = ? AND user_id = ?", 
                             (sales_invoice_id, user_id))
                if not cursor.fetchone():
                    return False, "Sales invoice not found"
                
                # Get all items with their VAT codes
                cursor.execute("""
                    SELECT line_total, COALESCE(vat_code, 'S') as vat_code
                    FROM sales_invoice_items 
                    WHERE sales_invoice_id = ?
                """, (sales_invoice_id,))
                
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
                
                # Update sales invoice
                cursor.execute("""
                    UPDATE sales_invoices 
                    SET subtotal = ?, vat_amount = ?, total = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ?
                """, (subtotal, vat_amount, total, sales_invoice_id, user_id))
                
                conn.commit()
            return True, "Totals calculated successfully"
        except Exception as e:
            return False, f"Error calculating totals: {str(e)}"
    
    def get_outstanding_balance(self, sales_invoice_id: int, user_id: int) -> float:
        """
        Calculate outstanding balance for a sales invoice (total - allocated payments).
        
        Args:
            sales_invoice_id: Sales invoice ID
            user_id: ID of the user
        
        Returns:
            Outstanding balance amount
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Get sales invoice total
                cursor.execute("SELECT total FROM sales_invoices WHERE id = ? AND user_id = ?", 
                             (sales_invoice_id, user_id))
                result = cursor.fetchone()
                if not result:
                    return 0.0
                
                invoice_total = result[0]
                
                # Sum allocated payments
                cursor.execute("""
                    SELECT COALESCE(SUM(amount_allocated), 0.0)
                    FROM customer_payment_allocations
                    WHERE sales_invoice_id = ?
                """, (sales_invoice_id,))
                allocated = cursor.fetchone()[0]
                
                return max(0.0, invoice_total - allocated)
        except Exception:
            return 0.0
    
    def update_status_if_paid(self, sales_invoice_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Update sales invoice status to 'paid' if fully paid (outstanding balance <= 0).
        
        Args:
            sales_invoice_id: Sales invoice ID
            user_id: ID of the user
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Check if sales invoice exists and belongs to user
                cursor.execute("SELECT id, status FROM sales_invoices WHERE id = ? AND user_id = ?", 
                             (sales_invoice_id, user_id))
                result = cursor.fetchone()
                if not result:
                    return False, "Sales invoice not found"
                
                current_status = result[1]
                
                # Get outstanding balance
                outstanding = self.get_outstanding_balance(sales_invoice_id, user_id)
                
                # If fully paid and not already marked as paid, update status
                if outstanding <= 0.01 and current_status != 'paid':
                    cursor.execute("""
                        UPDATE sales_invoices 
                        SET status = 'paid', updated_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND user_id = ?
                    """, (sales_invoice_id, user_id))
                    conn.commit()
                    return True, "Sales invoice status updated to paid"
                # If not fully paid and currently marked as paid, revert to finalized
                elif outstanding > 0.01 and current_status == 'paid':
                    cursor.execute("""
                        UPDATE sales_invoices 
                        SET status = 'finalized', updated_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND user_id = ?
                    """, (sales_invoice_id, user_id))
                    conn.commit()
                    return True, "Sales invoice status updated to finalized"
                
                return True, "Status check completed"
        except Exception as e:
            return False, f"Error updating sales invoice status: {str(e)}"
    
    def delete(self, sales_invoice_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Delete a sales invoice (only if no payments allocated).
        
        Args:
            sales_invoice_id: Sales invoice ID
            user_id: ID of the user
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Check if sales invoice exists and belongs to user
                cursor.execute("SELECT id FROM sales_invoices WHERE id = ? AND user_id = ?", 
                             (sales_invoice_id, user_id))
                if not cursor.fetchone():
                    return False, "Sales invoice not found"
                
                # Check if any payments are allocated
                cursor.execute("""
                    SELECT COUNT(*) FROM customer_payment_allocations WHERE sales_invoice_id = ?
                """, (sales_invoice_id,))
                allocation_count = cursor.fetchone()[0]
                
                if allocation_count > 0:
                    return False, "Cannot delete sales invoice: payments have been allocated to this invoice"
                
                # Restore stock for all items before deletion
                self._restore_sales_invoice_stock(sales_invoice_id)
                
                # Delete sales invoice items first (CASCADE should handle this, but explicit is safer)
                cursor.execute("DELETE FROM sales_invoice_items WHERE sales_invoice_id = ?", 
                             (sales_invoice_id,))
                
                # Delete sales invoice
                cursor.execute("DELETE FROM sales_invoices WHERE id = ? AND user_id = ?", 
                             (sales_invoice_id, user_id))
                
                if cursor.rowcount == 0:
                    return False, "Sales invoice not found"
                
                conn.commit()
            return True, "Sales invoice deleted successfully"
        except Exception as e:
            return False, f"Error deleting sales invoice: {str(e)}"
    
    def _restore_sales_invoice_stock(self, sales_invoice_id: int) -> None:
        """
        Restore stock for all items in a sales invoice (add quantities back).
        
        Args:
            sales_invoice_id: Sales invoice ID
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Get all items with product_id
                cursor.execute("""
                    SELECT product_id, quantity 
                    FROM sales_invoice_items 
                    WHERE sales_invoice_id = ? AND product_id IS NOT NULL
                """, (sales_invoice_id,))
                
                items = cursor.fetchall()
                
                if items:
                    from models.product import Product
                    product_model = Product(self.db_path)
                    
                    for product_id, quantity in items:
                        if product_id is not None:
                            # Add quantity back (restore the stock)
                            product_model.update_stock(product_id, quantity)
        except Exception:
            # Silently fail - stock restoration is not critical for sales invoice operations
            pass

