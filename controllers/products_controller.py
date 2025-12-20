"""Products controller."""
from typing import TYPE_CHECKING
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox

if TYPE_CHECKING:
    from views.products_view import ProductsView
    from models.product import Product
    from models.product_type import ProductType
    from models.tyre import Tyre


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
    
    def __init__(self, products_view: "ProductsView", product_model: "Product", product_type_model: "ProductType", tyre_model: "Tyre", user_id: int):
        """Initialize the products controller."""
        super().__init__()
        self.products_view = products_view
        self.product_model = product_model
        self.product_type_model = product_type_model
        self.tyre_model = tyre_model
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
        self.products_view.create_tyre_requested.connect(self.handle_create_tyre)
        self.products_view.update_requested.connect(self.handle_update)
        self.products_view.update_tyre_requested.connect(self.handle_update_tyre)
        self.products_view.delete_requested.connect(self.handle_delete)
        self.products_view.refresh_requested.connect(self.refresh_products)
        self.products_view.add_product_type_requested.connect(self.handle_add_product_type)
        self.products_view.catalogue_requested.connect(self.handle_catalogue)
        self.products_view.get_product_details_requested.connect(self.handle_get_product_details)
        
        # Set tyre_model in view for brand/model dropdowns
        self.products_view.tyre_model = self.tyre_model
        
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
    
    def handle_create_tyre(
        self, stock_number: str, description: str, type: str,
        brand: str, model: str, pattern: str, width: str, profile: str, diameter: str,
        speed_rating: str, load_index: str, oe_fitment: str, ean: str, manufacturer_code: str,
        vehicle_type: str, product_type: str, rolling_resistance: str, wet_grip: str,
        run_flat: str, tyre_url: str, brand_url: str
    ):
        """Handle create tyre product."""
        # Check if a matching record exists in the catalogue
        if width and profile and diameter and speed_rating and load_index and brand and model:
            match_exists = self.tyre_model.check_matching_record(
                width, profile, diameter, speed_rating, load_index, brand, model
            )
            
            if match_exists:
                # Show confirmation dialog
                reply = QMessageBox.question(
                    self.products_view,
                    "Duplicate Catalogue Record",
                    f"A record already exists in the catalogue that matches this product:\n\n"
                    f"Brand: {brand}\n"
                    f"Model: {model}\n"
                    f"Size: {width}/{profile}R{diameter}\n"
                    f"Speed/Load: {speed_rating}/{load_index}\n\n"
                    "Do you want to continue and create the product anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.No:
                    # User chose not to continue
                    return
        
        # Ensure product type exists before creating product
        if type and not self._ensure_product_type_exists(type):
            pass
        
        success, message = self.product_model.create(
            stock_number, description, type, self.user_id,
            is_tyre=True,
            tyre_brand=brand or None,
            tyre_model=model or None,
            tyre_pattern=pattern or None,
            tyre_width=width or None,
            tyre_profile=profile or None,
            tyre_diameter=diameter or None,
            tyre_speed_rating=speed_rating or None,
            tyre_load_index=load_index or None,
            tyre_oe_fitment=oe_fitment or None,
            tyre_ean=ean or None,
            tyre_manufacturer_code=manufacturer_code or None,
            tyre_vehicle_type=vehicle_type or None,
            tyre_product_type=product_type or None,
            tyre_rolling_resistance=rolling_resistance or None,
            tyre_wet_grip=wet_grip or None,
            tyre_run_flat=run_flat or None,
            tyre_url=tyre_url or None,
            tyre_brand_url=brand_url or None
        )
        
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
    
    def handle_update_tyre(
        self, product_id: int, stock_number: str, description: str, type: str,
        brand: str, model: str, pattern: str, width: str, profile: str, diameter: str,
        speed_rating: str, load_index: str, oe_fitment: str, ean: str, manufacturer_code: str,
        vehicle_type: str, product_type: str, rolling_resistance: str, wet_grip: str,
        run_flat: str, tyre_url: str, brand_url: str
    ):
        """Handle update tyre product."""
        # Ensure product type exists before updating product
        if type and not self._ensure_product_type_exists(type):
            pass
        
        success, message = self.product_model.update(
            product_id, stock_number, description, type, self.user_id,
            is_tyre=True,
            tyre_brand=brand or None,
            tyre_model=model or None,
            tyre_pattern=pattern or None,
            tyre_width=width or None,
            tyre_profile=profile or None,
            tyre_diameter=diameter or None,
            tyre_speed_rating=speed_rating or None,
            tyre_load_index=load_index or None,
            tyre_oe_fitment=oe_fitment or None,
            tyre_ean=ean or None,
            tyre_manufacturer_code=manufacturer_code or None,
            tyre_vehicle_type=vehicle_type or None,
            tyre_product_type=product_type or None,
            tyre_rolling_resistance=rolling_resistance or None,
            tyre_wet_grip=wet_grip or None,
            tyre_run_flat=run_flat or None,
            tyre_url=tyre_url or None,
            tyre_brand_url=brand_url or None
        )
        
        if success:
            self.products_view.show_success_dialog(message)
            self.refresh_products()
        else:
            self.products_view.show_error_dialog(message)
    
    def handle_get_product_details(self, product_id: int):
        """Handle get product details request."""
        product = self.product_model.get_by_id(product_id, self.user_id)
        if product:
            self.products_view.show_product_details(product)
        else:
            self.products_view.show_error_dialog("Product not found")
    
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
    
    def handle_catalogue(self):
        """Handle catalogue view request."""
        from views.tyre_catalogue_view import TyreCatalogueView
        
        catalogue_dialog = TyreCatalogueView(self.tyre_model, self.products_view)
        catalogue_dialog.exec()

