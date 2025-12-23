"""Sales invoice item model for sales document line items."""
import sqlite3
from typing import Optional, Tuple, List, Dict
import os


class SalesInvoiceItem:
    """Sales invoice item model with database operations."""
    
    def __init__(self, db_path: str = "data/app.db"):
        """Initialize sales invoice item model with database path."""
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_database(self):
        """Initialize the database with sales_invoice_items table."""
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='sales_invoice_items'
            """)
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Create new table
                cursor.execute("""
                    CREATE TABLE sales_invoice_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sales_invoice_id INTEGER NOT NULL,
                        product_id INTEGER,
                        service_id INTEGER,
                        stock_number TEXT NOT NULL,
                        description TEXT,
                        quantity REAL NOT NULL,
                        unit_price REAL NOT NULL,
                        line_total REAL NOT NULL,
                        vat_code TEXT NOT NULL DEFAULT 'S',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (sales_invoice_id) REFERENCES sales_invoices(id) ON DELETE CASCADE,
                        FOREIGN KEY (product_id) REFERENCES products(id),
                        FOREIGN KEY (service_id) REFERENCES services(id)
                    )
                """)
            
            conn.commit()
    
    def create(self, sales_invoice_id: int, product_id: Optional[int], service_id: Optional[int],
               stock_number: str, description: str, quantity: float, unit_price: float, 
               vat_code: str = 'S') -> Tuple[bool, str, Optional[int]]:
        """
        Add an item to a sales invoice.
        
        Args:
            sales_invoice_id: Sales invoice ID
            product_id: Product ID (optional, can be None for manual items)
            service_id: Service ID (optional, can be None for manual items)
            stock_number: Stock number (denormalized for display)
            description: Item description
            quantity: Quantity
            unit_price: Unit price
            vat_code: VAT code (S, E, or Z)
        
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
                
                vat_code = vat_code.strip().upper() if vat_code else 'S'
                if vat_code not in ['S', 'E', 'Z']:
                    vat_code = 'S'  # Default to Standard if invalid
                
                cursor.execute("""
                    INSERT INTO sales_invoice_items (sales_invoice_id, product_id, service_id, stock_number, 
                                                     description, quantity, unit_price, line_total, vat_code)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (sales_invoice_id, product_id, service_id, stock_number, description, 
                      quantity, unit_price, line_total, vat_code))
                
                item_id = cursor.lastrowid
                conn.commit()
                
                # Reduce product stock if product_id exists
                if product_id is not None:
                    from models.product import Product
                    product_model = Product(self.db_path)
                    stock_success, stock_message = product_model.update_stock(product_id, -quantity)
                    if not stock_success:
                        # Log error but don't fail the item creation
                        pass
                
                # Recalculate sales invoice totals
                from models.sales_invoice import SalesInvoice
                sales_invoice_model = SalesInvoice(self.db_path)
                # Get user_id from sales invoice
                cursor.execute("SELECT user_id FROM sales_invoices WHERE id = ?", (sales_invoice_id,))
                result = cursor.fetchone()
                if result:
                    user_id = result[0]
                    sales_invoice_model.calculate_totals(sales_invoice_id, user_id)
            
            return True, "Item added successfully", item_id
        except Exception as e:
            return False, f"Error adding item: {str(e)}", None
    
    def get_by_sales_invoice(self, sales_invoice_id: int) -> List[Dict[str, any]]:
        """
        Get all items for a sales invoice.
        
        Args:
            sales_invoice_id: Sales invoice ID
        
        Returns:
            List of sales invoice item dictionaries
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, product_id, service_id, stock_number, description, quantity, 
                           unit_price, line_total, vat_code, created_at
                    FROM sales_invoice_items 
                    WHERE sales_invoice_id = ?
                    ORDER BY id
                """, (sales_invoice_id,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception:
            return []
    
    def update(self, item_id: int, quantity: float, unit_price: float) -> Tuple[bool, str]:
        """
        Update a sales invoice item's quantity or unit price.
        
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
                
                # Get sales_invoice_id and product_id for stock adjustment
                cursor.execute("""
                    SELECT sales_invoice_id, product_id, quantity 
                    FROM sales_invoice_items WHERE id = ?
                """, (item_id,))
                result = cursor.fetchone()
                if not result:
                    return False, "Item not found"
                
                sales_invoice_id, product_id, old_quantity = result
                
                # Update item
                cursor.execute("""
                    UPDATE sales_invoice_items 
                    SET quantity = ?, unit_price = ?, line_total = ?
                    WHERE id = ?
                """, (quantity, unit_price, line_total, item_id))
                
                if cursor.rowcount == 0:
                    return False, "Item not found"
                
                conn.commit()
                
                # Adjust product stock if product_id exists
                if product_id is not None:
                    from models.product import Product
                    product_model = Product(self.db_path)
                    quantity_delta = old_quantity - quantity  # Positive if reducing, negative if increasing
                    stock_success, stock_message = product_model.update_stock(product_id, quantity_delta)
                    if not stock_success:
                        # Log error but don't fail the item update
                        pass
                
                # Recalculate sales invoice totals
                cursor.execute("SELECT user_id FROM sales_invoices WHERE id = ?", (sales_invoice_id,))
                result = cursor.fetchone()
                if result:
                    user_id = result[0]
                    from models.sales_invoice import SalesInvoice
                    sales_invoice_model = SalesInvoice(self.db_path)
                    sales_invoice_model.calculate_totals(sales_invoice_id, user_id)
            
            return True, "Item updated successfully"
        except Exception as e:
            return False, f"Error updating item: {str(e)}"
    
    def delete(self, item_id: int) -> Tuple[bool, str]:
        """
        Remove an item from a sales invoice.
        
        Args:
            item_id: Item ID
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Get sales_invoice_id and product_id/quantity before deleting (for stock restoration)
                cursor.execute("""
                    SELECT sales_invoice_id, product_id, quantity 
                    FROM sales_invoice_items WHERE id = ?
                """, (item_id,))
                result = cursor.fetchone()
                if not result:
                    return False, "Item not found"
                
                sales_invoice_id, product_id, quantity = result
                
                # Delete item
                cursor.execute("DELETE FROM sales_invoice_items WHERE id = ?", (item_id,))
                
                if cursor.rowcount == 0:
                    return False, "Item not found"
                
                conn.commit()
                
                # Restore product stock if product_id exists
                if product_id is not None:
                    from models.product import Product
                    product_model = Product(self.db_path)
                    stock_success, stock_message = product_model.update_stock(product_id, quantity)
                    if not stock_success:
                        # Log error but don't fail the item deletion
                        pass
                
                # Recalculate sales invoice totals
                cursor.execute("SELECT user_id FROM sales_invoices WHERE id = ?", (sales_invoice_id,))
                result = cursor.fetchone()
                if result:
                    user_id = result[0]
                    from models.sales_invoice import SalesInvoice
                    sales_invoice_model = SalesInvoice(self.db_path)
                    sales_invoice_model.calculate_totals(sales_invoice_id, user_id)
            
            return True, "Item deleted successfully"
        except Exception as e:
            return False, f"Error deleting item: {str(e)}"

