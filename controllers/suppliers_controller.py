"""Suppliers controller."""
from typing import TYPE_CHECKING, Optional
from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from views.suppliers_view import SuppliersView
    from models.supplier import Supplier
    from models.product import Product
    from controllers.invoice_controller import InvoiceController
    from controllers.payment_controller import PaymentController


class SuppliersController(QObject):
    """Controller for suppliers functionality."""
    
    # Signals
    dashboard_requested = Signal()
    customers_requested = Signal()
    products_requested = Signal()
    inventory_requested = Signal()
    bookkeeper_requested = Signal()
    vehicles_requested = Signal()
    services_requested = Signal()
    sales_requested = Signal()
    configuration_requested = Signal()
    logout_requested = Signal()
    balance_changed = Signal()  # Emitted when invoices/payments change
    
    def __init__(self, suppliers_view: "SuppliersView", supplier_model: "Supplier", user_id: int,
                 invoice_controller: Optional["InvoiceController"] = None,
                 payment_controller: Optional["PaymentController"] = None,
                 product_model: Optional["Product"] = None,
                 tyre_model=None):
        """Initialize the suppliers controller."""
        super().__init__()
        self.suppliers_view = suppliers_view
        self.supplier_model = supplier_model
        self.user_id = user_id
        self.invoice_controller = invoice_controller
        self.payment_controller = payment_controller
        self.product_model = product_model
        self.tyre_model = tyre_model
        
        # Connect view signals to controller handlers
        self.suppliers_view.dashboard_requested.connect(self.handle_dashboard)
        self.suppliers_view.customers_requested.connect(self.handle_customers)
        self.suppliers_view.products_requested.connect(self.handle_products)
        self.suppliers_view.inventory_requested.connect(self.handle_inventory)
        self.suppliers_view.bookkeeper_requested.connect(self.handle_bookkeeper)
        self.suppliers_view.vehicles_requested.connect(self.handle_vehicles)
        self.suppliers_view.services_requested.connect(self.handle_services)
        self.suppliers_view.sales_requested.connect(self.handle_sales)
        self.suppliers_view.configuration_requested.connect(self.handle_configuration)
        self.suppliers_view.logout_requested.connect(self.handle_logout)
        self.suppliers_view.create_requested.connect(self.handle_create)
        self.suppliers_view.update_requested.connect(self.handle_update)
        self.suppliers_view.delete_requested.connect(self.handle_delete)
        self.suppliers_view.refresh_requested.connect(self.refresh_suppliers)
        
        # Connect invoice/payment signals to refresh balances
        if self.invoice_controller:
            self.invoice_controller.invoice_created.connect(self._on_invoice_change)
            self.invoice_controller.invoice_updated.connect(self._on_invoice_change)
            self.invoice_controller.invoice_deleted.connect(self._on_invoice_change)
            self.invoice_controller.item_added.connect(self._on_invoice_change)
            self.invoice_controller.item_updated.connect(self._on_invoice_change)
            self.invoice_controller.item_deleted.connect(self._on_invoice_change)
        
        if self.payment_controller:
            self.payment_controller.payment_created.connect(self._on_payment_change)
            self.payment_controller.payment_deleted.connect(self._on_payment_change)
            self.payment_controller.allocation_created.connect(self._on_payment_change)
            self.payment_controller.allocation_updated.connect(self._on_payment_change)
            self.payment_controller.allocation_deleted.connect(self._on_payment_change)
        
        # Set controllers in view
        if self.invoice_controller and self.payment_controller:
            self.suppliers_view.set_controllers(
                self.invoice_controller, self.payment_controller, self.supplier_model, self.user_id,
                self.product_model, self.tyre_model
            )
        
        # Load initial suppliers
        self.refresh_suppliers()
    
    def set_user_id(self, user_id: int):
        """Update the user ID and refresh suppliers."""
        self.user_id = user_id
        if self.invoice_controller:
            self.invoice_controller.set_user_id(user_id)
        if self.payment_controller:
            self.payment_controller.set_user_id(user_id)
        if self.invoice_controller and self.payment_controller:
            self.suppliers_view.set_controllers(
                self.invoice_controller, self.payment_controller, self.supplier_model, self.user_id,
                self.product_model, self.tyre_model
            )
        self.refresh_suppliers()
    
    def _on_invoice_change(self):
        """Handle invoice changes - refresh suppliers to update balances and invoices tab."""
        self.refresh_suppliers()
        # Refresh invoices tab if it's currently visible and a supplier is selected
        if hasattr(self.suppliers_view, 'tab_widget'):
            if self.suppliers_view.tab_widget.currentIndex() == 2:  # Invoices tab
                self.suppliers_view._refresh_invoices_tab()
        self.balance_changed.emit()
    
    def _on_payment_change(self):
        """Handle payment changes - refresh suppliers to update balances and payments tab."""
        self.refresh_suppliers()
        # Refresh payments tab if it's currently visible and a supplier is selected
        if hasattr(self.suppliers_view, 'tab_widget'):
            if self.suppliers_view.tab_widget.currentIndex() == 3:  # Payments tab
                self.suppliers_view._refresh_payments_tab()
        self.balance_changed.emit()
    
    def handle_create(self, account_number: str, name: str):
        """Handle create supplier."""
        success, message = self.supplier_model.create(account_number, name, self.user_id)
        
        if success:
            self.suppliers_view.show_success_dialog(message)
            self.refresh_suppliers()
        else:
            self.suppliers_view.show_error_dialog(message)
    
    def handle_update(self, supplier_id: int, account_number: str, name: str):
        """Handle update supplier."""
        success, message = self.supplier_model.update(supplier_id, account_number, name, self.user_id)
        
        if success:
            self.suppliers_view.show_success_dialog(message)
            self.refresh_suppliers()
        else:
            self.suppliers_view.show_error_dialog(message)
    
    def handle_delete(self, supplier_id: int):
        """Handle delete supplier."""
        success, message = self.supplier_model.delete(supplier_id, self.user_id)
        
        if success:
            self.suppliers_view.show_success_dialog(message)
            self.refresh_suppliers()
        else:
            self.suppliers_view.show_error_dialog(message)
    
    def refresh_suppliers(self):
        """Refresh the suppliers list."""
        suppliers = self.supplier_model.get_all(self.user_id)
        self.suppliers_view.load_suppliers(suppliers)
        
        # Note: Invoices and payments are now supplier-specific and will be refreshed
        # when a supplier is selected or when switching to those tabs
    
    def handle_dashboard(self):
        """Handle dashboard navigation."""
        self.dashboard_requested.emit()
    
    def handle_customers(self):
        """Handle customers navigation."""
        self.customers_requested.emit()
    
    def handle_products(self):
        """Handle products navigation."""
        self.products_requested.emit()
    
    def handle_inventory(self):
        """Handle inventory navigation."""
        self.inventory_requested.emit()
    
    def handle_bookkeeper(self):
        """Handle bookkeeper navigation."""
        self.bookkeeper_requested.emit()

    def handle_vehicles(self):
        """Handle vehicles navigation."""
        self.vehicles_requested.emit()

    def handle_services(self):
        """Handle services navigation."""
        self.services_requested.emit()
    
    def handle_sales(self):
        """Handle sales navigation."""
        self.sales_requested.emit()
    
    def handle_configuration(self):
        """Handle configuration navigation."""
        self.configuration_requested.emit()
    
    def handle_logout(self):
        """Handle logout."""
        self.logout_requested.emit()
