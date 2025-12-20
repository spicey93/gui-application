"""Payment controller."""
from typing import TYPE_CHECKING, Optional, List, Dict
from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from models.payment import Payment
    from models.payment_allocation import PaymentAllocation
    from models.invoice import Invoice


class PaymentController(QObject):
    """Controller for payment functionality."""
    
    # Signals
    payment_created = Signal()
    payment_deleted = Signal()
    allocation_created = Signal()
    allocation_updated = Signal()
    allocation_deleted = Signal()
    
    def __init__(self, payment_model: "Payment", payment_allocation_model: "PaymentAllocation", 
                 invoice_model: "Invoice", user_id: int):
        """Initialize the payment controller."""
        super().__init__()
        self.payment_model = payment_model
        self.payment_allocation_model = payment_allocation_model
        self.invoice_model = invoice_model
        self.user_id = user_id
    
    def set_user_id(self, user_id: int):
        """Update the user ID."""
        self.user_id = user_id
    
    def create_payment(self, supplier_id: int, payment_date: str, amount: float,
                      reference: str, payment_method: str) -> tuple[bool, str, Optional[int]]:
        """
        Create a new payment.
        
        Args:
            supplier_id: User supplier ID
            payment_date: Payment date (YYYY-MM-DD)
            amount: Payment amount
            reference: Payment reference
            payment_method: Payment method (Cash, Card, Cheque, BACS)
        
        Returns:
            Tuple of (success: bool, message: str, payment_id: Optional[int])
        """
        # Get internal supplier ID
        from models.supplier import Supplier
        supplier_model = Supplier(self.payment_model.db_path)
        supplier_data = supplier_model.get_by_id(supplier_id, self.user_id)
        if not supplier_data:
            return False, "Supplier not found", None
        
        internal_supplier_id = supplier_data['internal_id']
        
        success, message, payment_id = self.payment_model.create(
            internal_supplier_id, payment_date, amount, reference, payment_method, self.user_id
        )
        
        if success:
            self.payment_created.emit()
        
        return success, message, payment_id
    
    def delete_payment(self, payment_id: int) -> tuple[bool, str]:
        """
        Delete a payment.
        
        Args:
            payment_id: Payment ID
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        success, message = self.payment_model.delete(payment_id, self.user_id)
        
        if success:
            self.payment_deleted.emit()
        
        return success, message
    
    def get_payments(self, supplier_id: Optional[int] = None) -> List[Dict]:
        """
        Get payments, optionally filtered by supplier.
        
        Args:
            supplier_id: Optional user supplier ID to filter by
        
        Returns:
            List of payment dictionaries
        """
        if supplier_id:
            # Get internal supplier ID
            from models.supplier import Supplier
            supplier_model = Supplier(self.payment_model.db_path)
            supplier_data = supplier_model.get_by_id(supplier_id, self.user_id)
            if not supplier_data:
                return []
            internal_supplier_id = supplier_data['internal_id']
            return self.payment_model.get_all(self.user_id, internal_supplier_id)
        else:
            return self.payment_model.get_all(self.user_id)
    
    def get_payment(self, payment_id: int) -> Optional[Dict]:
        """
        Get a payment by ID.
        
        Args:
            payment_id: Payment ID
        
        Returns:
            Payment dictionary or None
        """
        return self.payment_model.get_by_id(payment_id, self.user_id)
    
    def get_payment_unallocated_amount(self, payment_id: int) -> float:
        """
        Get unallocated amount for a payment.
        
        Args:
            payment_id: Payment ID
        
        Returns:
            Unallocated amount
        """
        return self.payment_model.get_unallocated_amount(payment_id)
    
    def allocate_payment(self, payment_id: int, invoice_id: int, amount: float) -> tuple[bool, str, Optional[int]]:
        """
        Allocate payment amount to an invoice.
        
        Args:
            payment_id: Payment ID
            invoice_id: Invoice ID
            amount: Amount to allocate
        
        Returns:
            Tuple of (success: bool, message: str, allocation_id: Optional[int])
        """
        success, message, allocation_id = self.payment_allocation_model.create(
            payment_id, invoice_id, amount
        )
        
        if success:
            # Update invoice status if fully paid
            self.invoice_model.update_status_if_paid(invoice_id, self.user_id)
            self.allocation_created.emit()
        
        return success, message, allocation_id
    
    def update_allocation(self, allocation_id: int, amount: float) -> tuple[bool, str]:
        """
        Update a payment allocation.
        
        Args:
            allocation_id: Allocation ID
            amount: New allocation amount
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        success, message, invoice_id = self.payment_allocation_model.update(allocation_id, amount)
        
        if success:
            # Update invoice status if fully paid
            if invoice_id:
                self.invoice_model.update_status_if_paid(invoice_id, self.user_id)
            self.allocation_updated.emit()
        
        return success, message
    
    def delete_allocation(self, allocation_id: int) -> tuple[bool, str]:
        """
        Delete a payment allocation.
        
        Args:
            allocation_id: Allocation ID
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        success, message, invoice_id = self.payment_allocation_model.delete(allocation_id)
        
        if success:
            # Update invoice status if it was fully paid and now isn't
            if invoice_id:
                self.invoice_model.update_status_if_paid(invoice_id, self.user_id)
            self.allocation_deleted.emit()
        
        return success, message
    
    def get_payment_allocations(self, payment_id: int) -> List[Dict]:
        """
        Get all allocations for a payment.
        
        Args:
            payment_id: Payment ID
        
        Returns:
            List of allocation dictionaries
        """
        return self.payment_allocation_model.get_by_payment(payment_id)
    
    def get_invoice_allocations(self, invoice_id: int) -> List[Dict]:
        """
        Get all allocations for an invoice.
        
        Args:
            invoice_id: Invoice ID
        
        Returns:
            List of allocation dictionaries
        """
        return self.payment_allocation_model.get_by_invoice(invoice_id)
    
    def get_outstanding_invoices(self, supplier_id: int) -> List[Dict]:
        """
        Get invoices with outstanding balances for a supplier.
        
        Args:
            supplier_id: User supplier ID
        
        Returns:
            List of invoice dictionaries with outstanding balances
        """
        # Get internal supplier ID
        from models.supplier import Supplier
        supplier_model = Supplier(self.invoice_model.db_path)
        supplier_data = supplier_model.get_by_id(supplier_id, self.user_id)
        if not supplier_data:
            return []
        
        internal_supplier_id = supplier_data['internal_id']
        invoices = self.invoice_model.get_all(self.user_id, internal_supplier_id)
        
        # Add outstanding balance to each invoice
        for invoice in invoices:
            invoice_id = invoice['id']
            invoice['outstanding_balance'] = self.invoice_model.get_outstanding_balance(invoice_id, self.user_id)
        
        # Filter to only invoices with outstanding balance > 0 (exclude fully allocated invoices)
        # Use a small epsilon to account for floating point precision
        return [inv for inv in invoices if inv['outstanding_balance'] > 0.01]

