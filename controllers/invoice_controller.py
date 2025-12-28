"""Invoice controller."""
from typing import TYPE_CHECKING, Optional
from PySide6.QtCore import QObject, Signal
from datetime import datetime
from utils.transaction_logger import TransactionLogger
from utils.account_finder import (
    find_trade_creditors_account,
    find_stock_asset_account,
    find_vat_input_account
)

if TYPE_CHECKING:
    from views.suppliers_view import SuppliersView
    from models.invoice import Invoice
    from models.invoice_item import InvoiceItem


class InvoiceController(QObject):
    """Controller for invoice functionality."""
    
    # Signals
    invoice_created = Signal()
    invoice_updated = Signal()
    invoice_deleted = Signal()
    item_added = Signal()
    item_updated = Signal()
    item_deleted = Signal()
    
    def __init__(self, invoice_model: "Invoice", invoice_item_model: "InvoiceItem", user_id: int):
        """Initialize the invoice controller."""
        super().__init__()
        self.invoice_model = invoice_model
        self.invoice_item_model = invoice_item_model
        self.user_id = user_id
        self.transaction_logger = TransactionLogger(invoice_model.db_path)
    
    def set_user_id(self, user_id: int):
        """Update the user ID."""
        self.user_id = user_id
    
    def create_invoice(self, supplier_id: int, invoice_number: str, invoice_date: str, vat_rate: float) -> tuple[bool, str, Optional[int]]:
        """
        Create a new invoice.
        
        Args:
            supplier_id: User supplier ID
            invoice_number: Invoice number
            invoice_date: Invoice date (YYYY-MM-DD)
            vat_rate: VAT rate as percentage
        
        Returns:
            Tuple of (success: bool, message: str, invoice_id: Optional[int])
        """
        # Get internal supplier ID
        from models.supplier import Supplier
        supplier_model = Supplier(self.invoice_model.db_path)
        supplier_data = supplier_model.get_by_id(supplier_id, self.user_id)
        if not supplier_data:
            return False, "Supplier not found", None
        
        internal_supplier_id = supplier_data['internal_id']
        
        success, message, invoice_id = self.invoice_model.create(
            internal_supplier_id, invoice_number, invoice_date, vat_rate, self.user_id
        )
        
        if success:
            self.invoice_created.emit()
        
        return success, message, invoice_id
    
    def update_invoice(self, invoice_id: int, invoice_number: str, invoice_date: str, 
                      vat_rate: float, status: str) -> tuple[bool, str]:
        """
        Update an invoice.
        
        Args:
            invoice_id: Invoice ID
            invoice_number: New invoice number
            invoice_date: New invoice date
            vat_rate: New VAT rate
            status: New status
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        success, message = self.invoice_model.update(
            invoice_id, invoice_number, invoice_date, vat_rate, status, self.user_id
        )
        
        if success:
            # Recalculate totals
            self.invoice_model.calculate_totals(invoice_id, self.user_id)
            self.invoice_updated.emit()
        
        return success, message
    
    def update_invoice_totals(self, invoice_id: int, subtotal: float, vat_amount: float, total: float) -> tuple[bool, str]:
        """
        Update invoice totals directly (for manual VAT override).
        
        Args:
            invoice_id: Invoice ID
            subtotal: Subtotal amount
            vat_amount: VAT amount
            total: Total amount
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        success, message = self.invoice_model.update_totals(invoice_id, subtotal, vat_amount, total, self.user_id)
        if success:
            self.invoice_updated.emit()
        return success, message
    
    def recalculate_invoice_totals(self, invoice_id: int) -> tuple[bool, str]:
        """
        Recalculate invoice totals from items.
        
        Args:
            invoice_id: Invoice ID
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        success, message = self.invoice_model.calculate_totals(invoice_id, self.user_id)
        if success:
            self.invoice_updated.emit()
        return success, message
    
    def delete_invoice(self, invoice_id: int) -> tuple[bool, str]:
        """
        Delete an invoice.
        
        Args:
            invoice_id: Invoice ID
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        success, message = self.invoice_model.delete(invoice_id, self.user_id)
        
        if success:
            self.invoice_deleted.emit()
        
        return success, message
    
    def get_invoices(self, supplier_id: Optional[int] = None) -> list:
        """
        Get invoices, optionally filtered by supplier.
        
        Args:
            supplier_id: Optional user supplier ID to filter by
        
        Returns:
            List of invoice dictionaries
        """
        if supplier_id:
            # Get internal supplier ID
            from models.supplier import Supplier
            supplier_model = Supplier(self.invoice_model.db_path)
            supplier_data = supplier_model.get_by_id(supplier_id, self.user_id)
            if not supplier_data:
                return []
            internal_supplier_id = supplier_data['internal_id']
            return self.invoice_model.get_all(self.user_id, internal_supplier_id)
        else:
            return self.invoice_model.get_all(self.user_id)
    
    def get_invoice(self, invoice_id: int) -> Optional[dict]:
        """
        Get an invoice by ID.
        
        Args:
            invoice_id: Invoice ID
        
        Returns:
            Invoice dictionary or None
        """
        return self.invoice_model.get_by_id(invoice_id, self.user_id)
    
    def get_invoice_outstanding_balance(self, invoice_id: int) -> float:
        """
        Get outstanding balance for an invoice.
        
        Args:
            invoice_id: Invoice ID
        
        Returns:
            Outstanding balance amount
        """
        return self.invoice_model.get_outstanding_balance(invoice_id, self.user_id)
    
    def add_invoice_item(self, invoice_id: int, product_id: Optional[int], stock_number: str,
                        description: str, quantity: float, unit_price: float, vat_code: str = 'S',
                        nominal_account_id: Optional[int] = None) -> tuple[bool, str, Optional[int]]:
        """
        Add an item to an invoice.
        
        Args:
            invoice_id: Invoice ID
            product_id: Optional product ID
            stock_number: Stock number
            description: Item description
            quantity: Quantity
            unit_price: Unit price
            vat_code: VAT code (S, E, or Z)
            nominal_account_id: Nominal account ID for expense lines (optional)
        
        Returns:
            Tuple of (success: bool, message: str, item_id: Optional[int])
        """
        success, message, item_id = self.invoice_item_model.create(
            invoice_id, product_id, stock_number, description, quantity, unit_price, vat_code, nominal_account_id
        )
        
        if success:
            # Log transaction to journal entries
            self._log_invoice_item_transaction(
                invoice_id, product_id, nominal_account_id, description, quantity, unit_price, vat_code, item_id
            )
            self.item_added.emit()
        
        return success, message, item_id
    
    def _log_invoice_item_transaction(self, invoice_id: int, product_id: Optional[int],
                                     nominal_account_id: Optional[int], description: str,
                                     quantity: float, unit_price: float, vat_code: str = 'S',
                                     item_id: Optional[int] = None):
        """
        Log invoice item transaction to journal entries.
        
        Args:
            invoice_id: Invoice ID
            product_id: Product ID (if product item)
            nominal_account_id: Nominal account ID (if expense item)
            description: Item description
            quantity: Quantity
            unit_price: Unit price
            vat_code: VAT code (S, E, or Z)
            item_id: Invoice item ID (optional, for getting VAT code if not provided)
        """
        try:
            # Get invoice details
            invoice = self.invoice_model.get_by_id(invoice_id, self.user_id)
            if not invoice:
                return
            
            invoice_date_str = invoice.get('invoice_date')
            invoice_number = invoice.get('invoice_number', '')
            supplier_id = invoice.get('supplier_id')
            
            # Parse invoice date
            try:
                if isinstance(invoice_date_str, str):
                    invoice_date = datetime.strptime(invoice_date_str, '%Y-%m-%d').date()
                else:
                    invoice_date = invoice_date_str
            except (ValueError, AttributeError):
                invoice_date = datetime.now().date()
            
            # Get supplier name by internal supplier ID
            import sqlite3
            supplier_name = 'Unknown Supplier'
            try:
                with sqlite3.connect(self.invoice_model.db_path, timeout=10.0) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM suppliers WHERE id = ? AND user_id = ?", (supplier_id, self.user_id))
                    row = cursor.fetchone()
                    if row:
                        supplier_name = row[0]
            except Exception:
                pass
            
            # Get VAT code from item if not provided and item_id is available
            if not vat_code and item_id:
                try:
                    import sqlite3
                    with sqlite3.connect(self.invoice_model.db_path, timeout=10.0) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT vat_code FROM invoice_items WHERE id = ?", (item_id,))
                        result = cursor.fetchone()
                        if result:
                            vat_code = result[0] or 'S'
                except Exception:
                    vat_code = 'S'
            
            vat_code = (vat_code or 'S').strip().upper()
            
            # Calculate amount (excluding VAT - we log the net amount)
            amount = quantity * unit_price
            
            # Find Trade Creditors account using utility function
            creditor_account_id = find_trade_creditors_account(self.user_id, self.invoice_model.db_path)
            if not creditor_account_id:
                # Account not found, skip logging (but don't fail the item creation)
                # This means the invoice won't appear in the purchase ledger
                # User should create a Trade Creditors/Purchase Ledger account (code 2100)
                import logging
                logging.warning(
                    f"Trade Creditors/Purchase Ledger account not found for user {self.user_id}. "
                    f"Journal entries not created for invoice item '{description}'. "
                    f"Please create a Trade Creditors account (code 2100) in Bookkeeper."
                )
                return
            
            # Determine debit account
            if product_id is not None:
                # Product item - debit Stock Asset
                stock_account_id = find_stock_asset_account(self.user_id, self.invoice_model.db_path)
                if not stock_account_id:
                    # Stock account not found, skip logging
                    import logging
                    logging.warning(f"Stock Asset account not found for user {self.user_id}. Journal entries not created for invoice item.")
                    return
                debit_account_id = stock_account_id
            elif nominal_account_id is not None:
                # Expense line - debit the specified expense account
                debit_account_id = nominal_account_id
            else:
                # No account specified, skip logging
                import logging
                logging.warning(f"No debit account specified for invoice item. Journal entries not created.")
                return
            
            # Log the net purchase transaction
            self.transaction_logger.log_supplier_invoice_item(
                user_id=self.user_id,
                invoice_date=invoice_date,
                invoice_number=invoice_number,
                supplier_name=supplier_name,
                expense_account_id=debit_account_id,
                creditor_account_id=creditor_account_id,
                amount=amount,
                description=description
            )
            
            # Log VAT Input if VAT code is 'S' (Standard rate 20%)
            if vat_code == 'S':
                vat_amount = amount * 0.20  # 20% VAT
                vat_input_account_id = find_vat_input_account(self.user_id, self.invoice_model.db_path)
                if vat_input_account_id:
                    self.transaction_logger.log_vat_input(
                        user_id=self.user_id,
                        invoice_date=invoice_date,
                        invoice_number=invoice_number,
                        supplier_name=supplier_name,
                        vat_input_account_id=vat_input_account_id,
                        creditor_account_id=creditor_account_id,
                        vat_amount=vat_amount,
                        description=description
                    )
        except Exception as e:
            # Don't fail the item creation if logging fails
            # Log error but continue
            pass
    
    def update_invoice_item(self, item_id: int, quantity: float, unit_price: float) -> tuple[bool, str]:
        """
        Update an invoice item.
        
        Args:
            item_id: Item ID
            quantity: New quantity
            unit_price: New unit price
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Get old item data before update for reversal
        import sqlite3
        old_item_data = None
        try:
            with sqlite3.connect(self.invoice_model.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT invoice_id, product_id, nominal_account_id, description, quantity, unit_price, vat_code
                    FROM invoice_items WHERE id = ?
                """, (item_id,))
                result = cursor.fetchone()
                if result:
                    old_item_data = {
                        'invoice_id': result[0],
                        'product_id': result[1],
                        'nominal_account_id': result[2],
                        'description': result[3],
                        'quantity': result[4],
                        'unit_price': result[5],
                        'vat_code': result[6] or 'S'
                    }
        except Exception:
            pass
        
        success, message = self.invoice_item_model.update(item_id, quantity, unit_price)
        
        if success and old_item_data:
            # Reverse old journal entries
            self._reverse_invoice_item_entries(
                old_item_data['invoice_id'], old_item_data['product_id'],
                old_item_data['nominal_account_id'], old_item_data['description'],
                old_item_data['quantity'], old_item_data['unit_price'],
                old_item_data['vat_code']
            )
            
            # Create new journal entries with updated amounts
            self._log_invoice_item_transaction(
                old_item_data['invoice_id'], old_item_data['product_id'],
                old_item_data['nominal_account_id'], old_item_data['description'],
                quantity, unit_price, old_item_data['vat_code'], item_id
            )
            self.item_updated.emit()
        
        return success, message
    
    def delete_invoice_item(self, item_id: int) -> tuple[bool, str]:
        """
        Delete an invoice item.
        
        Args:
            item_id: Item ID
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Get item data before deletion for reversal
        import sqlite3
        item_data = None
        try:
            with sqlite3.connect(self.invoice_model.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT invoice_id, product_id, nominal_account_id, description, quantity, unit_price, vat_code
                    FROM invoice_items WHERE id = ?
                """, (item_id,))
                result = cursor.fetchone()
                if result:
                    item_data = {
                        'invoice_id': result[0],
                        'product_id': result[1],
                        'nominal_account_id': result[2],
                        'description': result[3],
                        'quantity': result[4],
                        'unit_price': result[5],
                        'vat_code': result[6] or 'S'
                    }
        except Exception:
            pass
        
        success, message = self.invoice_item_model.delete(item_id)
        
        if success and item_data:
            # Reverse journal entries
            self._reverse_invoice_item_entries(
                item_data['invoice_id'], item_data['product_id'],
                item_data['nominal_account_id'], item_data['description'],
                item_data['quantity'], item_data['unit_price'],
                item_data['vat_code']
            )
            self.item_deleted.emit()
        
        return success, message
    
    def _reverse_invoice_item_entries(self, invoice_id: int, product_id: Optional[int],
                                     nominal_account_id: Optional[int], description: str,
                                     quantity: float, unit_price: float, vat_code: str):
        """
        Reverse journal entries for an invoice item.
        
        Args:
            invoice_id: Invoice ID
            product_id: Product ID
            nominal_account_id: Nominal account ID
            description: Item description
            quantity: Quantity
            unit_price: Unit price
            vat_code: VAT code
        """
        try:
            # Get invoice details
            invoice = self.invoice_model.get_by_id(invoice_id, self.user_id)
            if not invoice:
                return
            
            invoice_number = invoice.get('invoice_number', '')
            invoice_date_str = invoice.get('invoice_date')
            
            # Parse invoice date
            try:
                if isinstance(invoice_date_str, str):
                    invoice_date = datetime.strptime(invoice_date_str, '%Y-%m-%d').date()
                else:
                    invoice_date = invoice_date_str
            except (ValueError, AttributeError):
                invoice_date = datetime.now().date()
            
            # Find entries to reverse by reference and description
            entries_to_reverse = self.transaction_logger.find_entries_by_reference_and_description(
                self.user_id, invoice_number, description
            )
            
            # Also find VAT entries if applicable
            if vat_code == 'S':
                vat_entries = self.transaction_logger.find_entries_by_reference_and_description(
                    self.user_id, invoice_number, f"VAT Input: {description}"
                )
                entries_to_reverse.extend(vat_entries)
            
            # Reverse all found entries
            for entry in entries_to_reverse:
                self.transaction_logger.reverse_journal_entry(
                    entry['id'], self.user_id, invoice_date, f"REV-{invoice_number}"
                )
        except Exception:
            # Don't fail if reversal fails
            pass
    
    def get_invoice_items(self, invoice_id: int) -> list:
        """
        Get all items for an invoice.
        
        Args:
            invoice_id: Invoice ID
        
        Returns:
            List of invoice item dictionaries
        """
        return self.invoice_item_model.get_by_invoice(invoice_id)
    
    def recalculate_invoice_totals(self, invoice_id: int) -> tuple[bool, str]:
        """
        Recalculate invoice totals from items.
        
        Args:
            invoice_id: Invoice ID
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        return self.invoice_model.calculate_totals(invoice_id, self.user_id)


