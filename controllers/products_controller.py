"""Products controller."""
from typing import TYPE_CHECKING
from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from views.products_view import ProductsView
    from models.product import Product
    from models.product_type import ProductType


class ProductsController(QObject):
    """Controller for products functionality."""
    
    # Signals
    dashboard_requested = Signal()
    suppliers_requested = Signal()
    customers_requested = Signal()
    inventory_requested = Signal()
    bookkeeper_requested = Signal()
    vehicles_requested = Signal()
    configuration_requested = Signal()
    logout_requested = Signal()
    
    def __init__(self, products_view: "ProductsView", product_model: "Product", product_type_model: "ProductType", user_id: int):
        """Initialize the products controller."""
        super().__init__()
        self.products_view = products_view
        self.product_model = product_model
        self.product_type_model = product_type_model
        self.user_id = user_id
        
        # Connect view signals to controller handlers
        self.products_view.dashboard_requested.connect(self.handle_dashboard)
        self.products_view.suppliers_requested.connect(self.handle_suppliers)
        self.products_view.customers_requested.connect(self.handle_customers)
        self.products_view.inventory_requested.connect(self.handle_inventory)
        self.products_view.bookkeeper_requested.connect(self.handle_bookkeeper)
        self.products_view.vehicles_requested.connect(self.handle_vehicles)
        self.products_view.configuration_requested.connect(self.handle_configuration)
        self.products_view.logout_requested.connect(self.handle_logout)
        self.products_view.create_requested.connect(self.handle_create)
        self.products_view.update_requested.connect(self.handle_update)
        self.products_view.delete_requested.connect(self.handle_delete)
        self.products_view.refresh_requested.connect(self.refresh_products)
        self.products_view.add_product_type_requested.connect(self.handle_add_product_type)
        
        # Load initial products and types
        self.refresh_products()
        self.refresh_types()
    
    def set_user_id(self, user_id: int):
        """Update the user ID and refresh products and types."""
        self.user_id = user_id
        self.refresh_products()
        self.refresh_types()
    
    def _ensure_product_type_exists(self, type_name: str) -> bool:
        """
        Ensure a product type exists, creating it if necessary.
        
        Args:
            type_name: The product type name to ensure exists
            
        Returns:
            True if the type exists or was created successfully, False otherwise
        """
        if not type_name:
            return True  # Empty type is allowed
        
        # Check if type already exists
        existing_types = self.product_type_model.get_names(self.user_id)
        if type_name in existing_types:
            return True
        
        # Type doesn't exist, create it
        success, message = self.product_type_model.create(type_name, self.user_id)
        if success:
            # Refresh types list so it's available for future operations
            self.refresh_types()
        # Don't show error dialog here - if creation fails, we'll let the product creation handle it
        return success
    
    def handle_create(self, stock_number: str, description: str, type: str):
        """Handle create product."""
        # Ensure product type exists before creating product
        if type and not self._ensure_product_type_exists(type):
            # Type creation failed, but don't show error - product creation will handle it
            # The type might already exist from a race condition
            pass
        
        success, message = self.product_model.create(stock_number, description, type, self.user_id)
        
        if success:
            self.products_view.show_success_dialog(message)
            self.refresh_products()
        else:
            self.products_view.show_error_dialog(message)
    
    def handle_update(self, product_id: int, stock_number: str, description: str, type: str):
        """Handle update product."""
        # Ensure product type exists before updating product
        if type and not self._ensure_product_type_exists(type):
            # Type creation failed, but don't show error - product update will handle it
            # The type might already exist from a race condition
            pass
        
        success, message = self.product_model.update(product_id, stock_number, description, type, self.user_id)
        
        if success:
            self.products_view.show_success_dialog(message)
            self.refresh_products()
        else:
            self.products_view.show_error_dialog(message)
    
    def handle_delete(self, product_id: int):
        """Handle delete product."""
        success, message = self.product_model.delete(product_id, self.user_id)
        
        if success:
            self.products_view.show_success_dialog(message)
            self.refresh_products()
        else:
            self.products_view.show_error_dialog(message)
    
    def refresh_products(self):
        """Refresh the products list."""
        products = self.product_model.get_all(self.user_id)
        self.products_view.load_products(products)
    
    def refresh_types(self):
        """Refresh the product types list."""
        types = self.product_type_model.get_names(self.user_id)
        self.products_view.load_product_types(types)
    
    def handle_add_product_type(self, type_name: str):
        """Handle add product type request."""
        success, message = self.product_type_model.create(type_name, self.user_id)
        
        if success:
            # Refresh types so they appear in dropdowns immediately
            self.refresh_types()
            # Show success message
            self.products_view.show_success_dialog(message)
        else:
            # Show error message
            self.products_view.show_error_dialog(message)
    
    def handle_dashboard(self):
        """Handle dashboard navigation."""
        self.dashboard_requested.emit()
    
    def handle_suppliers(self):
        """Handle suppliers navigation."""
        self.suppliers_requested.emit()
    
    def handle_customers(self):
        """Handle customers navigation."""
        self.customers_requested.emit()
    
    def handle_inventory(self):
        """Handle inventory navigation."""
        self.inventory_requested.emit()
    
    def handle_bookkeeper(self):
        """Handle bookkeeper navigation."""
        self.bookkeeper_requested.emit()

    def handle_vehicles(self):
        """Handle vehicles navigation."""
        self.vehicles_requested.emit()

    def handle_configuration(self):
        """Handle configuration navigation."""
        self.configuration_requested.emit()
    
    def handle_logout(self):
        """Handle logout."""
        self.logout_requested.emit()

