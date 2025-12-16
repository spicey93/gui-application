"""Invoice item model for invoice line items."""
import sqlite3
from typing import Optional, Tuple, List, Dict
import os


class InvoiceItem:
    """Invoice item model with database operations."""
    
    def __init__(self, db_path: str = "data/app.db"):
        """Initialize invoice item model with database path."""
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_database(self):
        """Initialize the database with invoice_items table."""
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='invoice_items'
            """)
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Create new table
                cursor.execute("""
                    CREATE TABLE invoice_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        invoice_id INTEGER NOT NULL,
                        product_id INTEGER,
                        stock_number TEXT NOT NULL,
                        description TEXT,
                        quantity REAL NOT NULL,
                        unit_price REAL NOT NULL,
                        line_total REAL NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
                    )
                """)
            
            conn.commit()
    
    def create(self, invoice_id: int, product_id: Optional[int], stock_number: str,
               description: str, quantity: float, unit_price: float) -> Tuple[bool, str, Optional[int]]:
        """
        Add an item to an invoice.
        
        Args:
            invoice_id: Invoice ID
            product_id: Product ID (optional, can be None for manual items)
            stock_number: Stock number (denormalized for display)
            description: Item description
            quantity: Quantity
            unit_price: Unit price
        
        Returns:
            Tuple of (success: bool, message: str, item_id: Optional[int])
        """
        if not stock_number or not stock_number.strip():
            return False, "Stock number is required", None
        
        if quantity <= 0:
            return False, "Quantity must be greater than zero", None
        
        if unit_price < 0:
            return False, "Unit price cannot be negative", None
        
        stock_number = stock_number.strip()
        description = description.strip() if description else ""
        line_total = quantity * unit_price
        
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO invoice_items (invoice_id, product_id, stock_number, description, quantity, unit_price, line_total)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (invoice_id, product_id, stock_number, description, quantity, unit_price, line_total))
                
                item_id = cursor.lastrowid
                conn.commit()
                
                # Update product stock if product_id exists
                if product_id is not None:
                    from models.product import Product
                    product_model = Product(self.db_path)
                    stock_success, stock_message = product_model.update_stock(product_id, quantity)
                    if not stock_success:
                        # Log error but don't fail the item creation
                        pass
                
                # Recalculate invoice totals
                from models.invoice import Invoice
                invoice_model = Invoice(self.db_path)
                # Get user_id from invoice
                cursor.execute("SELECT user_id FROM invoices WHERE id = ?", (invoice_id,))
                result = cursor.fetchone()
                if result:
                    user_id = result[0]
                    invoice_model.calculate_totals(invoice_id, user_id)
            
            return True, "Item added successfully", item_id
        except Exception as e:
            return False, f"Error adding item: {str(e)}", None
    
    def get_by_invoice(self, invoice_id: int) -> List[Dict[str, any]]:
        """
        Get all items for an invoice.
        
        Args:
            invoice_id: Invoice ID
        
        Returns:
            List of invoice item dictionaries
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, product_id, stock_number, description, quantity, unit_price, line_total, created_at
                    FROM invoice_items 
                    WHERE invoice_id = ?
                    ORDER BY id
                """, (invoice_id,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception:
            return []
    
    def update(self, item_id: int, quantity: float, unit_price: float) -> Tuple[bool, str]:
        """
        Update an invoice item's quantity or unit price.
        
        Args:
            item_id: Item ID
            quantity: New quantity
            unit_price: New unit price
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if quantity <= 0:
            return False, "Quantity must be greater than zero"
        
        if unit_price < 0:
            return False, "Unit price cannot be negative"
        
        line_total = quantity * unit_price
        
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Get invoice_id for recalculation
                cursor.execute("SELECT invoice_id FROM invoice_items WHERE id = ?", (item_id,))
                result = cursor.fetchone()
                if not result:
                    return False, "Item not found"
                
                invoice_id = result[0]
                
                # Update item
                cursor.execute("""
                    UPDATE invoice_items 
                    SET quantity = ?, unit_price = ?, line_total = ?
                    WHERE id = ?
                """, (quantity, unit_price, line_total, item_id))
                
                if cursor.rowcount == 0:
                    return False, "Item not found"
                
                conn.commit()
                
                # Recalculate invoice totals
                cursor.execute("SELECT user_id FROM invoices WHERE id = ?", (invoice_id,))
                result = cursor.fetchone()
                if result:
                    user_id = result[0]
                    from models.invoice import Invoice
                    invoice_model = Invoice(self.db_path)
                    invoice_model.calculate_totals(invoice_id, user_id)
            
            return True, "Item updated successfully"
        except Exception as e:
            return False, f"Error updating item: {str(e)}"
    
    def delete(self, item_id: int) -> Tuple[bool, str]:
        """
        Remove an item from an invoice.
        
        Args:
            item_id: Item ID
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Get invoice_id for recalculation
                cursor.execute("SELECT invoice_id FROM invoice_items WHERE id = ?", (item_id,))
                result = cursor.fetchone()
                if not result:
                    return False, "Item not found"
                
                invoice_id = result[0]
                
                # Get product_id and quantity before deleting (for stock reversal)
                cursor.execute("SELECT product_id, quantity FROM invoice_items WHERE id = ?", (item_id,))
                item_result = cursor.fetchone()
                product_id = None
                quantity = 0.0
                if item_result:
                    product_id = item_result[0]
                    quantity = item_result[1]
                
                # Delete item
                cursor.execute("DELETE FROM invoice_items WHERE id = ?", (item_id,))
                
                if cursor.rowcount == 0:
                    return False, "Item not found"
                
                conn.commit()
                
                # Reverse product stock if product_id exists
                if product_id is not None:
                    from models.product import Product
                    product_model = Product(self.db_path)
                    stock_success, stock_message = product_model.update_stock(product_id, -quantity)
                    if not stock_success:
                        # Log error but don't fail the item deletion
                        pass
                
                # Recalculate invoice totals
                cursor.execute("SELECT user_id FROM invoices WHERE id = ?", (invoice_id,))
                result = cursor.fetchone()
                if result:
                    user_id = result[0]
                    from models.invoice import Invoice
                    invoice_model = Invoice(self.db_path)
                    invoice_model.calculate_totals(invoice_id, user_id)
            
            return True, "Item deleted successfully"
        except Exception as e:
            return False, f"Error deleting item: {str(e)}"
    
    def recalculate_line_total(self, item_id: int) -> Tuple[bool, str]:
        """
        Recalculate line total for an item.
        
        Args:
            item_id: Item ID
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Get quantity and unit_price
                cursor.execute("SELECT quantity, unit_price FROM invoice_items WHERE id = ?", (item_id,))
                result = cursor.fetchone()
                if not result:
                    return False, "Item not found"
                
                quantity, unit_price = result
                line_total = quantity * unit_price
                
                # Update line_total
                cursor.execute("UPDATE invoice_items SET line_total = ? WHERE id = ?", (line_total, item_id))
                conn.commit()
            
            return True, "Line total recalculated"
        except Exception as e:
            return False, f"Error recalculating line total: {str(e)}"

