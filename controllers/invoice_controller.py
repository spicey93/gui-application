"""Invoice controller."""
from typing import TYPE_CHECKING, Optional
from PySide6.QtCore import QObject, Signal

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
                        description: str, quantity: float, unit_price: float, vat_code: str = 'S') -> tuple[bool, str, Optional[int]]:
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
        
        Returns:
            Tuple of (success: bool, message: str, item_id: Optional[int])
        """
        success, message, item_id = self.invoice_item_model.create(
            invoice_id, product_id, stock_number, description, quantity, unit_price, vat_code
        )
        
        if success:
            self.item_added.emit()
        
        return success, message, item_id
    
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
        success, message = self.invoice_item_model.update(item_id, quantity, unit_price)
        
        if success:
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
        success, message = self.invoice_item_model.delete(item_id)
        
        if success:
            self.item_deleted.emit()
        
        return success, message
    
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


