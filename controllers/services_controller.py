"""Services controller."""
from typing import TYPE_CHECKING, Optional
from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from views.services_view import ServicesView
    from models.service import Service
    from models.nominal_account import NominalAccount


class ServicesController(QObject):
    """Controller for services functionality."""
    
    # Signals
    dashboard_requested = Signal()
    suppliers_requested = Signal()
    customers_requested = Signal()
    products_requested = Signal()
    inventory_requested = Signal()
    bookkeeper_requested = Signal()
    vehicles_requested = Signal()
    sales_requested = Signal()
    configuration_requested = Signal()
    logout_requested = Signal()
    
    def __init__(
        self,
        services_view: "ServicesView",
        service_model: "Service",
        nominal_account_model: "NominalAccount",
        user_id: int
    ):
        """Initialize the services controller."""
        super().__init__()
        self.services_view = services_view
        self.service_model = service_model
        self.nominal_account_model = nominal_account_model
        self.user_id = user_id
        
        # Set models in view
        self.services_view.set_models(self.nominal_account_model, self.user_id)
        
        # Connect view signals to controller handlers
        self.services_view.dashboard_requested.connect(self.handle_dashboard)
        self.services_view.suppliers_requested.connect(self.handle_suppliers)
        self.services_view.customers_requested.connect(self.handle_customers)
        self.services_view.products_requested.connect(self.handle_products)
        self.services_view.inventory_requested.connect(self.handle_inventory)
        self.services_view.bookkeeper_requested.connect(self.handle_bookkeeper)
        self.services_view.vehicles_requested.connect(self.handle_vehicles)
        self.services_view.sales_requested.connect(self.handle_sales)
        self.services_view.configuration_requested.connect(self.handle_configuration)
        self.services_view.logout_requested.connect(self.handle_logout)
        self.services_view.create_requested.connect(self.handle_create)
        self.services_view.update_requested.connect(self.handle_update)
        self.services_view.delete_requested.connect(self.handle_delete)
        self.services_view.refresh_requested.connect(self.refresh_services)
        self.services_view.get_service_details_requested.connect(self.handle_service_details_request)
        
        # Load initial services
        self.refresh_services()
    
    def set_user_id(self, user_id: int):
        """Update the user ID and refresh services."""
        self.user_id = user_id
        self.services_view.set_models(self.nominal_account_model, user_id)
        self.refresh_services()
    
    def handle_create(
        self,
        name: str,
        code: str,
        group: str,
        description: str,
        estimated_cost: float,
        vat_code: str,
        income_account_id: int,
        retail_price: float,
        trade_price: float
    ):
        """Handle create service."""
        income_account_id = income_account_id if income_account_id > 0 else None
        success, message = self.service_model.create(
            name=name,
            code=code,
            user_id=self.user_id,
            group_name=group if group else None,
            description=description if description else None,
            estimated_cost=estimated_cost,
            vat_code=vat_code,
            income_account_id=income_account_id,
            retail_price=retail_price,
            trade_price=trade_price
        )
        
        if success:
            self.services_view.show_success_dialog(message)
            self.refresh_services()
        else:
            self.services_view.show_error_dialog(message)
    
    def handle_update(
        self,
        service_id: int,
        name: str,
        code: str,
        group: str,
        description: str,
        estimated_cost: float,
        vat_code: str,
        income_account_id: int,
        retail_price: float,
        trade_price: float
    ):
        """Handle update service."""
        income_account_id = income_account_id if income_account_id > 0 else None
        success, message = self.service_model.update(
            service_id=service_id,
            name=name,
            code=code,
            user_id=self.user_id,
            group_name=group if group else None,
            description=description if description else None,
            estimated_cost=estimated_cost,
            vat_code=vat_code,
            income_account_id=income_account_id,
            retail_price=retail_price,
            trade_price=trade_price
        )
        
        if success:
            self.services_view.show_success_dialog(message)
            self.refresh_services()
        else:
            self.services_view.show_error_dialog(message)
    
    def handle_delete(self, service_id: int):
        """Handle delete service."""
        success, message = self.service_model.delete(service_id, self.user_id)
        
        if success:
            self.services_view.show_success_dialog(message)
            self.refresh_services()
        else:
            self.services_view.show_error_dialog(message)
    
    def refresh_services(self):
        """Refresh the services list."""
        services = self.service_model.get_all(self.user_id)
        self.services_view.load_services(services)
    
    def handle_service_details_request(self, service_id: int):
        """Handle request for service details."""
        service = self.service_model.get_by_id(service_id, self.user_id)
        if service:
            self.services_view.show_service_details(service)
    
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
    
    def handle_vehicles(self):
        """Handle vehicles navigation."""
        self.vehicles_requested.emit()
    
    def handle_sales(self):
        """Handle sales navigation."""
        self.sales_requested.emit()
    
    def handle_configuration(self):
        """Handle configuration navigation."""
        self.configuration_requested.emit()
    
    def handle_logout(self):
        """Handle logout."""
        self.logout_requested.emit()

