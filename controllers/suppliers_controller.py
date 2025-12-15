"""Suppliers controller."""
from typing import TYPE_CHECKING
from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from views.suppliers_view import SuppliersView
    from models.supplier import Supplier


class SuppliersController(QObject):
    """Controller for suppliers functionality."""
    
    # Signals
    dashboard_requested = Signal()
    configuration_requested = Signal()
    logout_requested = Signal()
    
    def __init__(self, suppliers_view: "SuppliersView", supplier_model: "Supplier", user_id: int):
        """Initialize the suppliers controller."""
        super().__init__()
        self.suppliers_view = suppliers_view
        self.supplier_model = supplier_model
        self.user_id = user_id
        
        # Connect view signals to controller handlers
        self.suppliers_view.dashboard_requested.connect(self.handle_dashboard)
        self.suppliers_view.configuration_requested.connect(self.handle_configuration)
        self.suppliers_view.logout_requested.connect(self.handle_logout)
        self.suppliers_view.create_requested.connect(self.handle_create)
        self.suppliers_view.update_requested.connect(self.handle_update)
        self.suppliers_view.delete_requested.connect(self.handle_delete)
        self.suppliers_view.refresh_requested.connect(self.refresh_suppliers)
        
        # Load initial suppliers
        self.refresh_suppliers()
    
    def set_user_id(self, user_id: int):
        """Update the user ID and refresh suppliers."""
        self.user_id = user_id
        self.refresh_suppliers()
    
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
    
    def handle_dashboard(self):
        """Handle dashboard navigation."""
        self.dashboard_requested.emit()
    
    def handle_configuration(self):
        """Handle configuration navigation."""
        self.configuration_requested.emit()
    
    def handle_logout(self):
        """Handle logout."""
        self.logout_requested.emit()
