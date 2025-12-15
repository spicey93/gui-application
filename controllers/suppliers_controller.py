"""Suppliers controller."""
from typing import TYPE_CHECKING, Optional, Callable

if TYPE_CHECKING:
    from views.suppliers_view import SuppliersView
    from models.supplier import Supplier


class SuppliersController:
    """Controller for suppliers functionality."""
    
    def __init__(self, suppliers_view: "SuppliersView", supplier_model: "Supplier", user_id: int):
        """Initialize the suppliers controller."""
        self.suppliers_view = suppliers_view
        self.supplier_model = supplier_model
        self.user_id = user_id
        
        # Set up view callbacks
        self.suppliers_view.set_dashboard_callback(self.handle_dashboard)
        self.suppliers_view.set_logout_callback(self.handle_logout)
        self.suppliers_view.set_create_callback(self.handle_create)
        self.suppliers_view.set_update_callback(self.handle_update)
        self.suppliers_view.set_delete_callback(self.handle_delete)
        self.suppliers_view.set_refresh_callback(self.refresh_suppliers)
        
        # Navigation callbacks
        self.on_dashboard: Optional[Callable[[], None]] = None
        self.on_logout: Optional[Callable[[], None]] = None
    
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
        if self.on_dashboard:
            self.on_dashboard()
    
    def handle_logout(self):
        """Handle logout."""
        if self.on_logout:
            self.on_logout()
    
    def set_dashboard_callback(self, callback: Callable[[], None]):
        """Set callback for dashboard navigation."""
        self.on_dashboard = callback
    
    def set_logout_callback(self, callback: Callable[[], None]):
        """Set callback for logout."""
        self.on_logout = callback

