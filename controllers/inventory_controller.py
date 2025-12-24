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
    customers_requested = Signal()
    products_requested = Signal()
    bookkeeper_requested = Signal()
    vehicles_requested = Signal()
    services_requested = Signal()
    sales_requested = Signal()
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
        self.inventory_view.customers_requested.connect(self.handle_customers)
        self.inventory_view.products_requested.connect(self.handle_products)
        self.inventory_view.bookkeeper_requested.connect(self.handle_bookkeeper)
        self.inventory_view.vehicles_requested.connect(self.handle_vehicles)
        self.inventory_view.services_requested.connect(self.handle_services)
        self.inventory_view.sales_requested.connect(self.handle_sales)
        self.inventory_view.configuration_requested.connect(self.handle_configuration)
        self.inventory_view.logout_requested.connect(self.handle_logout)
        self.inventory_view.filter_changed.connect(self.handle_filter_changed)
        
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
        # Check checkbox state to determine if we should include out-of-stock items
        show_out_of_stock = self.inventory_view.show_out_of_stock_checkbox.isChecked()
        self.inventory_view.load_inventory(products, include_out_of_stock=show_out_of_stock)
    
    def handle_filter_changed(self, show_out_of_stock: bool):
        """Handle filter checkbox state change."""
        self.refresh_inventory()
    
    def handle_dashboard(self):
        """Handle dashboard navigation."""
        self.dashboard_requested.emit()
    
    def handle_suppliers(self):
        """Handle suppliers navigation."""
        self.suppliers_requested.emit()
    
    def handle_customers(self):
        """Handle customers navigation."""
        self.customers_requested.emit()
    
    def handle_products(self):
        """Handle products navigation."""
        self.products_requested.emit()
    
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

