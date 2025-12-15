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
    
    def handle_create(self, stock_number: str, description: str, type: str):
        """Handle create product."""
        success, message = self.product_model.create(stock_number, description, type, self.user_id)
        
        if success:
            self.products_view.show_success_dialog(message)
            self.refresh_products()
        else:
            self.products_view.show_error_dialog(message)
    
    def handle_update(self, product_id: int, stock_number: str, description: str, type: str):
        """Handle update product."""
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
    
    def handle_configuration(self):
        """Handle configuration navigation."""
        self.configuration_requested.emit()
    
    def handle_logout(self):
        """Handle logout."""
        self.logout_requested.emit()

