"""Dashboard controller."""
from typing import TYPE_CHECKING
from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from views.dashboard_view import DashboardView


class DashboardController(QObject):
    """Controller for dashboard functionality."""
    
    # Signals
    logout_requested = Signal()
    suppliers_requested = Signal()
    customers_requested = Signal()
    products_requested = Signal()
    inventory_requested = Signal()
    bookkeeper_requested = Signal()
    configuration_requested = Signal()
    
    def __init__(self, dashboard_view: "DashboardView"):
        """Initialize the dashboard controller."""
        super().__init__()
        self.dashboard_view = dashboard_view
        
        # Connect view signals to controller
        self.dashboard_view.logout_requested.connect(self.handle_logout)
        self.dashboard_view.suppliers_requested.connect(self.handle_suppliers)
        self.dashboard_view.customers_requested.connect(self.handle_customers)
        self.dashboard_view.products_requested.connect(self.handle_products)
        self.dashboard_view.inventory_requested.connect(self.handle_inventory)
        self.dashboard_view.bookkeeper_requested.connect(self.handle_bookkeeper)
        self.dashboard_view.configuration_requested.connect(self.handle_configuration)
    
    def handle_logout(self):
        """Handle logout."""
        self.logout_requested.emit()
    
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
    
    def handle_configuration(self):
        """Handle configuration navigation."""
        self.configuration_requested.emit()
