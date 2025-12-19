"""Customers controller."""
from typing import TYPE_CHECKING
from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from views.customers_view import CustomersView
    from models.customer import Customer


class CustomersController(QObject):
    """Controller for customers functionality."""
    
    # Signals
    dashboard_requested = Signal()
    suppliers_requested = Signal()
    products_requested = Signal()
    inventory_requested = Signal()
    bookkeeper_requested = Signal()
    vehicles_requested = Signal()
    configuration_requested = Signal()
    logout_requested = Signal()
    
    def __init__(self, customers_view: "CustomersView", 
                 customer_model: "Customer", user_id: int):
        """Initialize the customers controller."""
        super().__init__()
        self.customers_view = customers_view
        self.customer_model = customer_model
        self.user_id = user_id
        
        # Connect view signals to controller handlers
        self.customers_view.dashboard_requested.connect(self.handle_dashboard)
        self.customers_view.suppliers_requested.connect(self.handle_suppliers)
        self.customers_view.products_requested.connect(self.handle_products)
        self.customers_view.inventory_requested.connect(self.handle_inventory)
        self.customers_view.bookkeeper_requested.connect(self.handle_bookkeeper)
        self.customers_view.vehicles_requested.connect(self.handle_vehicles)
        self.customers_view.configuration_requested.connect(self.handle_configuration)
        self.customers_view.logout_requested.connect(self.handle_logout)
        self.customers_view.create_requested.connect(self.handle_create)
        self.customers_view.update_requested.connect(self.handle_update)
        self.customers_view.delete_requested.connect(self.handle_delete)
        self.customers_view.refresh_requested.connect(self.refresh_customers)
        
        # Load initial customers
        self.refresh_customers()
    
    def set_user_id(self, user_id: int) -> None:
        """Update the user ID and refresh customers."""
        self.user_id = user_id
        self.refresh_customers()
    
    def handle_create(self, name: str, phone: str, house_name_no: str,
                      street_address: str, city: str, county: str, postcode: str) -> None:
        """Handle create customer."""
        success, message = self.customer_model.create(
            name, phone, house_name_no, street_address, city, county, postcode, self.user_id
        )
        
        if success:
            self.customers_view.show_success_dialog(message)
            self.refresh_customers()
        else:
            self.customers_view.show_error_dialog(message)
    
    def handle_update(self, customer_id: int, name: str, phone: str, house_name_no: str,
                      street_address: str, city: str, county: str, postcode: str) -> None:
        """Handle update customer."""
        success, message = self.customer_model.update(
            customer_id, name, phone, house_name_no, street_address, city, county, postcode,
            self.user_id
        )
        
        if success:
            self.customers_view.show_success_dialog(message)
            self.refresh_customers()
        else:
            self.customers_view.show_error_dialog(message)
    
    def handle_delete(self, customer_id: int) -> None:
        """Handle delete customer."""
        success, message = self.customer_model.delete(customer_id, self.user_id)
        
        if success:
            self.customers_view.show_success_dialog(message)
            self.refresh_customers()
        else:
            self.customers_view.show_error_dialog(message)
    
    def refresh_customers(self) -> None:
        """Refresh the customers list."""
        customers = self.customer_model.get_all(self.user_id)
        self.customers_view.load_customers(customers)
    
    def handle_dashboard(self) -> None:
        """Handle dashboard navigation."""
        self.dashboard_requested.emit()
    
    def handle_suppliers(self) -> None:
        """Handle suppliers navigation."""
        self.suppliers_requested.emit()
    
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

    def handle_configuration(self) -> None:
        """Handle configuration navigation."""
        self.configuration_requested.emit()
    
    def handle_logout(self) -> None:
        """Handle logout."""
        self.logout_requested.emit()

