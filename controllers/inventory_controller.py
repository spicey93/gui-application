"""Inventory controller."""
from typing import TYPE_CHECKING
from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from views.inventory_view import InventoryView
    from models.product import Product


class InventoryController(QObject):
    """Controller for inventory functionality."""
    
    # Signals
    dashboard_requested = Signal()
    suppliers_requested = Signal()
    products_requested = Signal()
    configuration_requested = Signal()
    logout_requested = Signal()
    
    def __init__(self, inventory_view: "InventoryView", product_model: "Product", user_id: int):
        """Initialize the inventory controller."""
        super().__init__()
        self.inventory_view = inventory_view
        self.product_model = product_model
        self.user_id = user_id
        
        # Connect view signals to controller handlers
        self.inventory_view.dashboard_requested.connect(self.handle_dashboard)
        self.inventory_view.suppliers_requested.connect(self.handle_suppliers)
        self.inventory_view.products_requested.connect(self.handle_products)
        self.inventory_view.configuration_requested.connect(self.handle_configuration)
        self.inventory_view.logout_requested.connect(self.handle_logout)
        
        # Load initial inventory
        self.refresh_inventory()
    
    def set_user_id(self, user_id: int):
        """Update the user ID and refresh inventory."""
        self.user_id = user_id
        self.refresh_inventory()
    
    def refresh_inventory(self):
        """Refresh the inventory list."""
        products = self.product_model.get_all(self.user_id)
        # Products already include stock_quantity from the model
        self.inventory_view.load_inventory(products)
    
    def handle_dashboard(self):
        """Handle dashboard navigation."""
        self.dashboard_requested.emit()
    
    def handle_suppliers(self):
        """Handle suppliers navigation."""
        self.suppliers_requested.emit()
    
    def handle_products(self):
        """Handle products navigation."""
        self.products_requested.emit()
    
    def handle_configuration(self):
        """Handle configuration navigation."""
        self.configuration_requested.emit()
    
    def handle_logout(self):
        """Handle logout."""
        self.logout_requested.emit()

