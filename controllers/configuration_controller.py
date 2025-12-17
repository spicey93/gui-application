"""Configuration controller."""
from typing import TYPE_CHECKING
from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from views.configuration_view import ConfigurationView
    from models.product_type import ProductType


class ConfigurationController(QObject):
    """Controller for configuration functionality."""
    
    # Signals
    dashboard_requested = Signal()
    suppliers_requested = Signal()
    customers_requested = Signal()
    products_requested = Signal()
    inventory_requested = Signal()
    bookkeeper_requested = Signal()
    logout_requested = Signal()
    types_changed = Signal()  # Emitted when types are created or deleted
    
    def __init__(self, configuration_view: "ConfigurationView", product_type_model: "ProductType"):
        """Initialize the configuration controller."""
        super().__init__()
        self.configuration_view = configuration_view
        self.product_type_model = product_type_model
        
        # Connect view signals to controller handlers
        self.configuration_view.dashboard_requested.connect(self.handle_dashboard)
        self.configuration_view.suppliers_requested.connect(self.handle_suppliers)
        self.configuration_view.customers_requested.connect(self.handle_customers)
        self.configuration_view.products_requested.connect(self.handle_products)
        self.configuration_view.inventory_requested.connect(self.handle_inventory)
        self.configuration_view.bookkeeper_requested.connect(self.handle_bookkeeper)
        self.configuration_view.logout_requested.connect(self.handle_logout)
    
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
    
    def handle_inventory(self):
        """Handle inventory navigation."""
        self.inventory_requested.emit()
    
    def handle_bookkeeper(self):
        """Handle bookkeeper navigation."""
        self.bookkeeper_requested.emit()
    
    def handle_logout(self):
        """Handle logout."""
        self.logout_requested.emit()

