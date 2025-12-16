"""Main entry point for the GUI application."""
import sys
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence

from models.user import User
from models.supplier import Supplier
from models.product import Product
from models.product_type import ProductType
from models.invoice import Invoice
from models.invoice_item import InvoiceItem
from models.payment import Payment
from models.payment_allocation import PaymentAllocation
from views.login_view import LoginView
from views.dashboard_view import DashboardView
from views.suppliers_view import SuppliersView
from views.products_view import ProductsView
from views.configuration_view import ConfigurationView
from views.shortcuts_dialog import ShortcutsDialog
from controllers.login_controller import LoginController
from controllers.dashboard_controller import DashboardController
from controllers.suppliers_controller import SuppliersController
from controllers.products_controller import ProductsController
from controllers.configuration_controller import ConfigurationController
from controllers.invoice_controller import InvoiceController
from controllers.payment_controller import PaymentController


class Application(QMainWindow):
    """Main application class to manage views and navigation."""
    
    def __init__(self):
        """Initialize the application."""
        super().__init__()
        
        # Set window properties
        self.setWindowTitle("Login")
        self.setGeometry(100, 100, 400, 250)
        self.setMinimumSize(400, 250)
        
        # Load Windows XP theme
        self._load_xp_theme()
        
        # Initialize models
        self.user_model = User()
        self.supplier_model = Supplier()
        self.product_model = Product()
        self.product_type_model = ProductType()
        self.invoice_model = Invoice()
        self.invoice_item_model = InvoiceItem()
        self.payment_model = Payment()
        self.payment_allocation_model = PaymentAllocation()
        
        # Current user ID (None until login)
        self.current_user_id: Optional[int] = None
        
        # Create stacked widget for views
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Initialize views
        self.login_view = LoginView()
        self.dashboard_view = DashboardView()
        self.suppliers_view = SuppliersView()
        self.products_view = ProductsView()
        self.configuration_view = ConfigurationView()
        
        # Add views to stacked widget
        self.login_index = self.stacked_widget.addWidget(self.login_view)
        self.dashboard_index = self.stacked_widget.addWidget(self.dashboard_view)
        self.suppliers_index = self.stacked_widget.addWidget(self.suppliers_view)
        self.products_index = self.stacked_widget.addWidget(self.products_view)
        self.configuration_index = self.stacked_widget.addWidget(self.configuration_view)
        
        # Show login view initially
        self.stacked_widget.setCurrentIndex(self.login_index)
        
        # Initialize controllers
        self.login_controller = LoginController(self.user_model, self.login_view)
        self.dashboard_controller = DashboardController(self.dashboard_view)
        self.suppliers_controller = None
        self.products_controller = None
        self.configuration_controller = None
        self.invoice_controller = None
        self.payment_controller = None
        
        # Set up navigation callbacks
        self.login_controller.login_success.connect(self.on_login_success)
        self.dashboard_controller.logout_requested.connect(self.on_logout)
        self.dashboard_controller.suppliers_requested.connect(self.on_suppliers)
        self.dashboard_controller.products_requested.connect(self.on_products)
        self.dashboard_controller.configuration_requested.connect(self.on_configuration)
        
        # Center the window
        self._center_window()
        
        # Set up global keyboard shortcuts
        self._setup_shortcuts()
    
    def _load_xp_theme(self):
        """Load Windows XP theme stylesheet."""
        stylesheet_path = Path(__file__).parent / "styles" / "xp_theme.qss"
        if stylesheet_path.exists():
            with open(stylesheet_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
    
    def _center_window(self):
        """Center the window on the screen."""
        frame_geometry = self.frameGeometry()
        screen = QApplication.primaryScreen().availableGeometry().center()
        frame_geometry.moveCenter(screen)
        self.move(frame_geometry.topLeft())
    
    def _setup_shortcuts(self):
        """Set up global keyboard shortcuts."""
        # Ctrl+D: Dashboard
        self.shortcut_dashboard = QShortcut(QKeySequence("Ctrl+D"), self)
        self.shortcut_dashboard.activated.connect(self._navigate_to_dashboard)
        
        # Ctrl+S: Suppliers
        self.shortcut_suppliers = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_suppliers.activated.connect(self._navigate_to_suppliers)
        
        # Ctrl+P: Products
        self.shortcut_products = QShortcut(QKeySequence("Ctrl+P"), self)
        self.shortcut_products.activated.connect(self._navigate_to_products)
        
        # Ctrl+O: Configuration
        self.shortcut_configuration = QShortcut(QKeySequence("Ctrl+O"), self)
        self.shortcut_configuration.activated.connect(self._navigate_to_configuration)
        
        # Ctrl+L: Logout
        self.shortcut_logout = QShortcut(QKeySequence("Ctrl+L"), self)
        self.shortcut_logout.activated.connect(self._handle_logout_shortcut)
        
        # Ctrl+N: Add Supplier/Product (context-dependent)
        self.shortcut_add = QShortcut(QKeySequence("Ctrl+N"), self)
        self.shortcut_add.activated.connect(self._handle_add_shortcut)
        
        # F5: Refresh (context-dependent)
        self.shortcut_refresh = QShortcut(QKeySequence("F5"), self)
        self.shortcut_refresh.activated.connect(self._handle_refresh_shortcut)
        
        # F1: Show keyboard shortcuts help
        self.shortcut_help = QShortcut(QKeySequence("F1"), self)
        self.shortcut_help.activated.connect(self._show_shortcuts_help)
    
    def _navigate_to_dashboard(self):
        """Navigate to dashboard if logged in."""
        if self.current_user_id is not None:
            self.dashboard_view.nav_panel.set_current_view("dashboard")
            self.stacked_widget.setCurrentIndex(self.dashboard_index)
            self.setWindowTitle("Dashboard")
            self.setMinimumSize(800, 600)
            self._center_window()
    
    def _navigate_to_suppliers(self):
        """Navigate to suppliers if logged in."""
        if self.current_user_id is not None:
            if self.suppliers_controller:
                self.suppliers_controller.refresh_suppliers()
            self.suppliers_view.nav_panel.set_current_view("suppliers")
            self.stacked_widget.setCurrentIndex(self.suppliers_index)
            self.setWindowTitle("Suppliers")
            self.setMinimumSize(800, 600)
            self._center_window()
    
    def _navigate_to_products(self):
        """Navigate to products if logged in."""
        if self.current_user_id is not None:
            if self.products_controller:
                self.products_controller.refresh_products()
            self.products_view.nav_panel.set_current_view("products")
            self.stacked_widget.setCurrentIndex(self.products_index)
            self.setWindowTitle("Products")
            self.setMinimumSize(800, 600)
            self._center_window()
    
    def _navigate_to_configuration(self):
        """Navigate to configuration if logged in."""
        if self.current_user_id is not None:
            self.configuration_view.nav_panel.set_current_view("configuration")
            self.stacked_widget.setCurrentIndex(self.configuration_index)
            self.setWindowTitle("Configuration")
            self.setMinimumSize(800, 600)
            self._center_window()
    
    def _handle_logout_shortcut(self):
        """Handle logout keyboard shortcut."""
        if self.current_user_id is not None:
            self.on_logout()
    
    def _handle_add_shortcut(self):
        """Handle add item keyboard shortcut (supplier or product)."""
        if self.current_user_id is not None:
            current_index = self.stacked_widget.currentIndex()
            if current_index == self.suppliers_index:
                self.suppliers_view.add_supplier()
            elif current_index == self.products_index:
                self.products_view.add_product()
    
    def _handle_refresh_shortcut(self):
        """Handle refresh keyboard shortcut."""
        if self.current_user_id is not None:
            current_index = self.stacked_widget.currentIndex()
            if current_index == self.suppliers_index:
                if self.suppliers_controller:
                    self.suppliers_controller.refresh_suppliers()
            elif current_index == self.products_index:
                if self.products_controller:
                    self.products_controller.refresh_products()
    
    def _show_shortcuts_help(self):
        """Show keyboard shortcuts help dialog."""
        if self.current_user_id is not None:
            dialog = ShortcutsDialog(self)
            dialog.exec()
    
    def on_login_success(self, username: str, user_id: int):
        """Handle successful login."""
        # Store current user ID
        self.current_user_id = user_id
        
        # Initialize invoice and payment controllers
        if self.invoice_controller is None:
            self.invoice_controller = InvoiceController(
                self.invoice_model,
                self.invoice_item_model,
                user_id
            )
        else:
            self.invoice_controller.set_user_id(user_id)
        
        if self.payment_controller is None:
            self.payment_controller = PaymentController(
                self.payment_model,
                self.payment_allocation_model,
                self.invoice_model,
                user_id
            )
        else:
            self.payment_controller.set_user_id(user_id)
        
        # Initialize or update suppliers controller with user_id
        if self.suppliers_controller is None:
            self.suppliers_controller = SuppliersController(
                self.suppliers_view, 
                self.supplier_model, 
                user_id,
                self.invoice_controller,
                self.payment_controller
            )
            self.suppliers_controller.dashboard_requested.connect(self.on_back_to_dashboard)
            self.suppliers_controller.configuration_requested.connect(self.on_configuration)
            self.suppliers_controller.logout_requested.connect(self.on_logout)
        else:
            self.suppliers_controller.set_user_id(user_id)
        
        # Initialize or update products controller with user_id
        if self.products_controller is None:
            self.products_controller = ProductsController(
                self.products_view,
                self.product_model,
                self.product_type_model,
                user_id
            )
            self.products_controller.dashboard_requested.connect(self.on_back_to_dashboard)
            self.products_controller.suppliers_requested.connect(self.on_suppliers)
            self.products_controller.configuration_requested.connect(self.on_configuration)
            self.products_controller.logout_requested.connect(self.on_logout)
        else:
            self.products_controller.set_user_id(user_id)
        
        # Initialize configuration controller
        if self.configuration_controller is None:
            self.configuration_controller = ConfigurationController(
                self.configuration_view,
                self.product_type_model
            )
            self.configuration_controller.dashboard_requested.connect(self.on_back_to_dashboard)
            self.configuration_controller.suppliers_requested.connect(self.on_suppliers)
            self.configuration_controller.products_requested.connect(self.on_products)
            self.configuration_controller.logout_requested.connect(self.on_logout)
        
        # Update window for dashboard
        self.setWindowTitle("Dashboard")
        self.setMinimumSize(800, 600)
        self.resize(1200, 800)
        self._center_window()
        
        # Update navigation highlighting
        self.dashboard_view.nav_panel.set_current_view("dashboard")
        # Switch views
        self.stacked_widget.setCurrentIndex(self.dashboard_index)
        self.dashboard_view.set_username(username)
    
    def on_suppliers(self):
        """Handle navigation to suppliers."""
        # Refresh suppliers for current user
        if self.suppliers_controller:
            self.suppliers_controller.refresh_suppliers()
        # Update navigation highlighting
        self.suppliers_view.nav_panel.set_current_view("suppliers")
        # Switch to suppliers view
        self.stacked_widget.setCurrentIndex(self.suppliers_index)
        self.setWindowTitle("Suppliers")
        self.setMinimumSize(800, 600)
        self._center_window()
    
    def on_products(self):
        """Handle navigation to products."""
        # Refresh products for current user
        if self.products_controller:
            self.products_controller.refresh_products()
        # Update navigation highlighting
        self.products_view.nav_panel.set_current_view("products")
        # Switch to products view
        self.stacked_widget.setCurrentIndex(self.products_index)
        self.setWindowTitle("Products")
        self.setMinimumSize(800, 600)
        self._center_window()
    
    def on_configuration(self):
        """Handle navigation to configuration."""
        # Update navigation highlighting
        self.configuration_view.nav_panel.set_current_view("configuration")
        # Switch to configuration view
        self.stacked_widget.setCurrentIndex(self.configuration_index)
        self.setWindowTitle("Configuration")
        self.setMinimumSize(800, 600)
        self._center_window()
    
    def _refresh_product_types_after_change(self):
        """Refresh product types in products view after configuration changes."""
        # This will be called after type creation/deletion completes
        if self.products_controller:
            self.products_controller.refresh_types()
    
    def on_back_to_dashboard(self):
        """Handle navigation back to dashboard."""
        # Update navigation highlighting
        self.dashboard_view.nav_panel.set_current_view("dashboard")
        # Switch to dashboard view
        self.stacked_widget.setCurrentIndex(self.dashboard_index)
        self.setWindowTitle("Dashboard")
        self.setMinimumSize(800, 600)
        self._center_window()
    
    def on_logout(self):
        """Handle logout."""
        # Update window for login
        self.setWindowTitle("Login")
        self.setMinimumSize(400, 250)
        self.resize(400, 250)
        self._center_window()
        
        # Switch views - show login
        self.stacked_widget.setCurrentIndex(self.login_index)
        self.current_user_id = None
        self.login_view.clear_fields()


def main():
    """Initialize and run the application."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("GUI Application")
    app.setOrganizationName("GUI App")
    
    # Create and show main window
    window = Application()
    window.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
