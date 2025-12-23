"""Configuration controller."""
from typing import TYPE_CHECKING, Optional
from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from views.configuration_view import ConfigurationView
    from models.api_key import ApiKey


class ConfigurationController(QObject):
    """Controller for configuration functionality."""
    
    # Signals
    dashboard_requested = Signal()
    suppliers_requested = Signal()
    customers_requested = Signal()
    products_requested = Signal()
    inventory_requested = Signal()
    bookkeeper_requested = Signal()
    vehicles_requested = Signal()
    services_requested = Signal()
    sales_requested = Signal()
    logout_requested = Signal()
    types_changed = Signal()  # Emitted when types are created or deleted
    
    def __init__(
        self, 
        configuration_view: "ConfigurationView", 
        api_key_model: "ApiKey",
        user_id: Optional[int] = None
    ):
        """Initialize the configuration controller."""
        super().__init__()
        self.configuration_view = configuration_view
        self.api_key_model = api_key_model
        self.user_id = user_id
        
        # Connect view signals to controller handlers
        self.configuration_view.dashboard_requested.connect(self.handle_dashboard)
        self.configuration_view.suppliers_requested.connect(self.handle_suppliers)
        self.configuration_view.customers_requested.connect(self.handle_customers)
        self.configuration_view.products_requested.connect(self.handle_products)
        self.configuration_view.inventory_requested.connect(self.handle_inventory)
        self.configuration_view.bookkeeper_requested.connect(self.handle_bookkeeper)
        self.configuration_view.vehicles_requested.connect(self.handle_vehicles)
        self.configuration_view.services_requested.connect(self.handle_services)
        self.configuration_view.sales_requested.connect(self.handle_sales)
        self.configuration_view.logout_requested.connect(self.handle_logout)
        
        # Connect API key signals
        self.configuration_view.api_key_save_requested.connect(self.handle_save_api_key)
        
        # Load existing API keys
        self._load_api_keys()
    
    def set_user_id(self, user_id: int) -> None:
        """Set the current user ID and reload API keys."""
        self.user_id = user_id
        self._load_api_keys()
    
    def _load_api_keys(self) -> None:
        """Load existing API keys into the view."""
        if self.user_id is None:
            return
        
        uk_vehicle_key = self.api_key_model.get_api_key(self.user_id, "uk_vehicle_data")
        self.configuration_view.set_uk_vehicle_api_key(uk_vehicle_key or "")
    
    def handle_save_api_key(self, service_name: str, api_key: str) -> None:
        """Handle saving an API key."""
        if self.user_id is None:
            self.configuration_view.show_message(
                "Error", "No user logged in", is_error=True
            )
            return
        
        if not api_key:
            # Delete the key if empty
            success, message = self.api_key_model.delete_api_key(self.user_id, service_name)
            self.configuration_view.show_message(
                "Success" if success else "Info",
                "API key cleared" if success else message
            )
            return
        
        success, message = self.api_key_model.save_api_key(
            self.user_id, service_name, api_key
        )
        self.configuration_view.show_message(
            "Success" if success else "Error",
            message,
            is_error=not success
        )
    
    def handle_dashboard(self) -> None:
        """Handle dashboard navigation."""
        self.dashboard_requested.emit()
    
    def handle_suppliers(self) -> None:
        """Handle suppliers navigation."""
        self.suppliers_requested.emit()
    
    def handle_customers(self) -> None:
        """Handle customers navigation."""
        self.customers_requested.emit()
    
    def handle_products(self) -> None:
        """Handle products navigation."""
        self.products_requested.emit()
    
    def handle_inventory(self) -> None:
        """Handle inventory navigation."""
        self.inventory_requested.emit()
    
    def handle_bookkeeper(self) -> None:
        """Handle bookkeeper navigation."""
        self.bookkeeper_requested.emit()
    
    def handle_vehicles(self) -> None:
        """Handle vehicles navigation."""
        self.vehicles_requested.emit()
    
    def handle_services(self) -> None:
        """Handle services navigation."""
        self.services_requested.emit()
    
    def handle_sales(self) -> None:
        """Handle sales navigation."""
        self.sales_requested.emit()
    
    def handle_logout(self) -> None:
        """Handle logout."""
        self.logout_requested.emit()
