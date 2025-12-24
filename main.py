"""Main entry point for the GUI application."""
import sys
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence
from utils.styles import load_theme_stylesheet, apply_theme

from models.user import User
from models.supplier import Supplier
from models.customer import Customer
from models.product import Product
from models.product_type import ProductType
from models.invoice import Invoice
from models.invoice_item import InvoiceItem
from models.payment import Payment
from models.payment_allocation import PaymentAllocation
from models.nominal_account import NominalAccount
from models.journal_entry import JournalEntry
from models.api_key import ApiKey
from models.vehicle import Vehicle
from models.tyre import Tyre
from models.service import Service
from models.sales_invoice import SalesInvoice
from models.sales_invoice_item import SalesInvoiceItem
from models.customer_payment import CustomerPayment
from models.customer_payment_allocation import CustomerPaymentAllocation
from views.login_view import LoginView
from views.dashboard_view import DashboardView
from views.suppliers_view import SuppliersView
from views.customers_view import CustomersView
from views.products_view import ProductsView
from views.inventory_view import InventoryView
from views.bookkeeper_view import BookkeeperView
from views.configuration_view import ConfigurationView
from views.vehicles_view import VehiclesView
from views.services_view import ServicesView
from views.sales_view import SalesView
from views.shortcuts_dialog import ShortcutsDialog
from controllers.login_controller import LoginController
from controllers.dashboard_controller import DashboardController
from controllers.suppliers_controller import SuppliersController
from controllers.customers_controller import CustomersController
from controllers.products_controller import ProductsController
from controllers.inventory_controller import InventoryController
from controllers.bookkeeper_controller import BookkeeperController
from controllers.configuration_controller import ConfigurationController
from controllers.vehicles_controller import VehiclesController
from controllers.services_controller import ServicesController
from controllers.sales_controller import SalesController
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
        self.customer_model = Customer()
        self.product_model = Product()
        self.product_type_model = ProductType()
        self.invoice_model = Invoice()
        self.invoice_item_model = InvoiceItem()
        self.payment_model = Payment()
        self.payment_allocation_model = PaymentAllocation()
        self.nominal_account_model = NominalAccount()
        self.journal_entry_model = JournalEntry()
        self.api_key_model = ApiKey()
        self.vehicle_model = Vehicle()
        self.tyre_model = Tyre()
        self.service_model = Service()
        self.sales_invoice_model = SalesInvoice()
        self.sales_invoice_item_model = SalesInvoiceItem()
        self.customer_payment_model = CustomerPayment()
        self.customer_payment_allocation_model = CustomerPaymentAllocation()
        
        # Current user ID (None until login)
        self.current_user_id: Optional[int] = None
        
        # Create stacked widget for views
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Initialize views
        self.login_view = LoginView()
        self.dashboard_view = DashboardView()
        self.suppliers_view = SuppliersView()
        self.customers_view = CustomersView()
        self.products_view = ProductsView()
        self.inventory_view = InventoryView()
        self.bookkeeper_view = BookkeeperView()
        self.vehicles_view = VehiclesView()
        self.services_view = ServicesView()
        self.sales_view = SalesView()
        self.configuration_view = ConfigurationView()
        
        # Add views to stacked widget
        self.login_index = self.stacked_widget.addWidget(self.login_view)
        self.dashboard_index = self.stacked_widget.addWidget(self.dashboard_view)
        self.suppliers_index = self.stacked_widget.addWidget(self.suppliers_view)
        self.customers_index = self.stacked_widget.addWidget(self.customers_view)
        self.products_index = self.stacked_widget.addWidget(self.products_view)
        self.inventory_index = self.stacked_widget.addWidget(self.inventory_view)
        self.bookkeeper_index = self.stacked_widget.addWidget(self.bookkeeper_view)
        self.vehicles_index = self.stacked_widget.addWidget(self.vehicles_view)
        self.services_index = self.stacked_widget.addWidget(self.services_view)
        self.sales_index = self.stacked_widget.addWidget(self.sales_view)
        self.configuration_index = self.stacked_widget.addWidget(self.configuration_view)
        
        # Show login view initially
        self.stacked_widget.setCurrentIndex(self.login_index)
        
        # Initialize controllers
        self.login_controller = LoginController(self.user_model, self.login_view)
        self.dashboard_controller = DashboardController(self.dashboard_view)
        self.suppliers_controller = None
        self.customers_controller = None
        self.products_controller = None
        self.inventory_controller = None
        self.bookkeeper_controller = None
        self.vehicles_controller = None
        self.services_controller = None
        self.sales_controller = None
        self.configuration_controller = None
        self.invoice_controller = None
        self.payment_controller = None
        
        # Set up navigation callbacks
        self.login_controller.login_success.connect(self.on_login_success)
        self.dashboard_controller.logout_requested.connect(self.on_logout)
        self.dashboard_controller.suppliers_requested.connect(self.on_suppliers)
        self.dashboard_controller.customers_requested.connect(self.on_customers)
        self.dashboard_controller.products_requested.connect(self.on_products)
        self.dashboard_controller.inventory_requested.connect(self.on_inventory)
        self.dashboard_controller.bookkeeper_requested.connect(self.on_bookkeeper)
        self.dashboard_controller.vehicles_requested.connect(self.on_vehicles)
        self.dashboard_controller.services_requested.connect(self.on_services)
        self.dashboard_controller.sales_requested.connect(self.on_sales)
        self.dashboard_controller.configuration_requested.connect(self.on_configuration)
        
        # Center the window
        self._center_window()
        
        # Set up global keyboard shortcuts
        self._setup_shortcuts()
    
    def _load_xp_theme(self):
        """Load Windows XP theme stylesheet."""
        apply_theme(self)
    
    def _center_window(self):
        """Center the window on the screen."""
        frame_geometry = self.frameGeometry()
        screen = QApplication.primaryScreen().availableGeometry().center()
        frame_geometry.moveCenter(screen)
        self.move(frame_geometry.topLeft())
    
    def _setup_shortcuts(self):
        """Set up global keyboard shortcuts."""
        # F1: Dashboard
        self.shortcut_dashboard = QShortcut(QKeySequence("F1"), self)
        self.shortcut_dashboard.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_dashboard.activated.connect(self._navigate_to_dashboard)
        
        # F2: Suppliers
        self.shortcut_suppliers = QShortcut(QKeySequence("F2"), self)
        self.shortcut_suppliers.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_suppliers.activated.connect(self._navigate_to_suppliers)
        
        # F3: Customers
        self.shortcut_customers = QShortcut(QKeySequence("F3"), self)
        self.shortcut_customers.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_customers.activated.connect(self._navigate_to_customers)
        
        # F4: Products
        self.shortcut_products = QShortcut(QKeySequence("F4"), self)
        self.shortcut_products.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_products.activated.connect(self._navigate_to_products)
        
        # F5: Services
        self.shortcut_services = QShortcut(QKeySequence("F5"), self)
        self.shortcut_services.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_services.activated.connect(self._navigate_to_services)
        
        # F6: Sales
        self.shortcut_sales = QShortcut(QKeySequence("F6"), self)
        self.shortcut_sales.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_sales.activated.connect(self._navigate_to_sales)
        
        # F7: Inventory
        self.shortcut_inventory = QShortcut(QKeySequence("F7"), self)
        self.shortcut_inventory.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_inventory.activated.connect(self._navigate_to_inventory)
        
        # F8: Vehicles
        self.shortcut_vehicles = QShortcut(QKeySequence("F8"), self)
        self.shortcut_vehicles.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_vehicles.activated.connect(self._navigate_to_vehicles)
        
        # F9: Book Keeper
        self.shortcut_bookkeeper = QShortcut(QKeySequence("F9"), self)
        self.shortcut_bookkeeper.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_bookkeeper.activated.connect(self._navigate_to_bookkeeper)
        
        # F10: Configuration
        self.shortcut_configuration = QShortcut(QKeySequence("F10"), self)
        self.shortcut_configuration.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_configuration.activated.connect(self._navigate_to_configuration)
        
        # Ctrl+N: Add Supplier/Product/Account (context-dependent)
        self.shortcut_add = QShortcut(QKeySequence("Ctrl+N"), self)
        self.shortcut_add.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_add.activated.connect(self._handle_add_shortcut)
        
        # Ctrl+T: Transfer Funds (Book Keeper only)
        self.shortcut_transfer = QShortcut(QKeySequence("Ctrl+T"), self)
        self.shortcut_transfer.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_transfer.activated.connect(self._handle_transfer_shortcut)
        
        # Ctrl+Shift+C: View Tyre Catalogue (Products only)
        self.shortcut_catalogue = QShortcut(QKeySequence("Ctrl+Shift+C"), self)
        self.shortcut_catalogue.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_catalogue.activated.connect(self._handle_catalogue_shortcut)
        
        # Ctrl+Q: Exit application
        self.shortcut_quit = QShortcut(QKeySequence("Ctrl+Q"), self)
        self.shortcut_quit.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_quit.activated.connect(self._exit_application)
    
    def _navigate_to_dashboard(self):
        """Navigate to dashboard if logged in."""
        if self.current_user_id is not None:
            self.dashboard_view.nav_panel.set_current_view("dashboard")
            self.stacked_widget.setCurrentIndex(self.dashboard_index)
            self.setWindowTitle("Dashboard")
            self.setMinimumSize(800, 600)
    
    def _navigate_to_suppliers(self):
        """Navigate to suppliers if logged in."""
        if self.current_user_id is not None:
            if self.suppliers_controller:
                self.suppliers_controller.refresh_suppliers()
            self.suppliers_view.nav_panel.set_current_view("suppliers")
            self.stacked_widget.setCurrentIndex(self.suppliers_index)
            self.setWindowTitle("Suppliers")
            self.setMinimumSize(800, 600)
    
    def _navigate_to_customers(self):
        """Navigate to customers if logged in."""
        if self.current_user_id is not None:
            if self.customers_controller:
                self.customers_controller.refresh_customers()
            self.customers_view.nav_panel.set_current_view("customers")
            self.stacked_widget.setCurrentIndex(self.customers_index)
            self.setWindowTitle("Customers")
            self.setMinimumSize(800, 600)
    
    def _navigate_to_products(self):
        """Navigate to products if logged in."""
        if self.current_user_id is not None:
            if self.products_controller:
                self.products_controller.refresh_products()
            self.products_view.nav_panel.set_current_view("products")
            self.stacked_widget.setCurrentIndex(self.products_index)
            self.setWindowTitle("Products")
            self.setMinimumSize(800, 600)
    
    def _navigate_to_inventory(self):
        """Navigate to inventory if logged in."""
        if self.current_user_id is not None:
            if self.inventory_controller:
                self.inventory_controller.refresh_inventory()
            self.inventory_view.nav_panel.set_current_view("inventory")
            self.stacked_widget.setCurrentIndex(self.inventory_index)
            self.setWindowTitle("Inventory")
            self.setMinimumSize(800, 600)
    
    def _navigate_to_bookkeeper(self):
        """Navigate to bookkeeper if logged in."""
        if self.current_user_id is not None:
            if self.bookkeeper_controller:
                self.bookkeeper_controller.refresh_accounts()
            self.bookkeeper_view.nav_panel.set_current_view("bookkeeper")
            self.stacked_widget.setCurrentIndex(self.bookkeeper_index)
            self.setWindowTitle("Book Keeper")
            self.setMinimumSize(800, 600)
    
    def _navigate_to_vehicles(self):
        """Navigate to vehicles if logged in."""
        if self.current_user_id is not None:
            if self.vehicles_controller:
                self.vehicles_controller.refresh_vehicles()
            self.vehicles_view.nav_panel.set_current_view("vehicles")
            self.stacked_widget.setCurrentIndex(self.vehicles_index)
            self.setWindowTitle("Vehicles")
            self.setMinimumSize(800, 600)
    
    def _navigate_to_services(self):
        """Navigate to services if logged in."""
        if self.current_user_id is not None:
            if self.services_controller:
                self.services_controller.refresh_services()
            self.services_view.nav_panel.set_current_view("services")
            self.stacked_widget.setCurrentIndex(self.services_index)
            self.setWindowTitle("Services")
            self.setMinimumSize(800, 600)
    
    def _navigate_to_sales(self):
        """Navigate to sales if logged in."""
        if self.current_user_id is not None:
            if self.sales_controller:
                self.sales_controller.refresh_documents()
            self.sales_view.nav_panel.set_current_view("sales")
            self.stacked_widget.setCurrentIndex(self.sales_index)
            self.setWindowTitle("Sales")
            self.setMinimumSize(800, 600)
    
    def _navigate_to_configuration(self):
        """Navigate to configuration if logged in."""
        if self.current_user_id is not None:
            self.configuration_view.nav_panel.set_current_view("configuration")
            self.stacked_widget.setCurrentIndex(self.configuration_index)
            self.setWindowTitle("Configuration")
            self.setMinimumSize(800, 600)
    
    def _handle_add_shortcut(self):
        """Handle add item keyboard shortcut (supplier, customer, product, service, or account)."""
        if self.current_user_id is not None:
            current_index = self.stacked_widget.currentIndex()
            if current_index == self.suppliers_index:
                self.suppliers_view.add_supplier()
            elif current_index == self.customers_index:
                self.customers_view.add_customer()
            elif current_index == self.products_index:
                self.products_view.add_product()
            elif current_index == self.services_index:
                self.services_view.add_service()
            elif current_index == self.sales_index:
                self.sales_view.add_document()
            elif current_index == self.bookkeeper_index:
                self.bookkeeper_view.add_account()
    
    def _handle_transfer_shortcut(self):
        """Handle transfer funds keyboard shortcut (Book Keeper only)."""
        if self.current_user_id is not None:
            current_index = self.stacked_widget.currentIndex()
            if current_index == self.bookkeeper_index:
                self.bookkeeper_view.transfer_funds()
    
    def _handle_catalogue_shortcut(self):
        """Handle view catalogue keyboard shortcut (Products only)."""
        if self.current_user_id is not None:
            current_index = self.stacked_widget.currentIndex()
            if current_index == self.products_index:
                self.products_view._handle_view_catalogue()
    
    def _exit_application(self):
        """Exit the application with confirmation."""
        reply = QMessageBox.question(
            self,
            "Exit Application",
            "Are you sure you want to exit the application?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            QApplication.instance().quit()
    
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
                self.payment_controller,
                self.product_model,
                self.tyre_model
            )
            self.suppliers_controller.dashboard_requested.connect(self.on_back_to_dashboard)
            self.suppliers_controller.customers_requested.connect(self.on_customers)
            self.suppliers_controller.products_requested.connect(self.on_products)
            self.suppliers_controller.inventory_requested.connect(self.on_inventory)
            self.suppliers_controller.bookkeeper_requested.connect(self.on_bookkeeper)
            self.suppliers_controller.vehicles_requested.connect(self.on_vehicles)
            self.suppliers_controller.services_requested.connect(self.on_services)
            self.suppliers_controller.sales_requested.connect(self.on_sales)
            self.suppliers_controller.configuration_requested.connect(self.on_configuration)
            self.suppliers_controller.logout_requested.connect(self.on_logout)
        else:
            self.suppliers_controller.set_user_id(user_id)
        
        # Initialize or update customers controller with user_id
        if self.customers_controller is None:
            self.customers_controller = CustomersController(
                self.customers_view,
                self.customer_model,
                user_id
            )
            self.customers_controller.dashboard_requested.connect(self.on_back_to_dashboard)
            self.customers_controller.suppliers_requested.connect(self.on_suppliers)
            self.customers_controller.products_requested.connect(self.on_products)
            self.customers_controller.inventory_requested.connect(self.on_inventory)
            self.customers_controller.bookkeeper_requested.connect(self.on_bookkeeper)
            self.customers_controller.vehicles_requested.connect(self.on_vehicles)
            self.customers_controller.services_requested.connect(self.on_services)
            self.customers_controller.sales_requested.connect(self.on_sales)
            self.customers_controller.configuration_requested.connect(self.on_configuration)
            self.customers_controller.logout_requested.connect(self.on_logout)
        else:
            self.customers_controller.set_user_id(user_id)
        
        # Initialize or update products controller with user_id
        if self.products_controller is None:
            self.products_controller = ProductsController(
                self.products_view,
                self.product_model,
                self.product_type_model,
                self.tyre_model,
                user_id
            )
            self.products_controller.dashboard_requested.connect(self.on_back_to_dashboard)
            self.products_controller.suppliers_requested.connect(self.on_suppliers)
            self.products_controller.customers_requested.connect(self.on_customers)
            self.products_controller.inventory_requested.connect(self.on_inventory)
            self.products_controller.bookkeeper_requested.connect(self.on_bookkeeper)
            self.products_controller.vehicles_requested.connect(self.on_vehicles)
            self.products_controller.services_requested.connect(self.on_services)
            self.products_controller.sales_requested.connect(self.on_sales)
            self.products_controller.configuration_requested.connect(self.on_configuration)
            self.products_controller.logout_requested.connect(self.on_logout)
        else:
            self.products_controller.set_user_id(user_id)
        
        # Initialize or update inventory controller with user_id
        if self.inventory_controller is None:
            self.inventory_controller = InventoryController(
                self.inventory_view,
                self.product_model,
                user_id
            )
            self.inventory_controller.dashboard_requested.connect(self.on_back_to_dashboard)
            self.inventory_controller.suppliers_requested.connect(self.on_suppliers)
            self.inventory_controller.customers_requested.connect(self.on_customers)
            self.inventory_controller.products_requested.connect(self.on_products)
            self.inventory_controller.bookkeeper_requested.connect(self.on_bookkeeper)
            self.inventory_controller.vehicles_requested.connect(self.on_vehicles)
            self.inventory_controller.services_requested.connect(self.on_services)
            self.inventory_controller.sales_requested.connect(self.on_sales)
            self.inventory_controller.configuration_requested.connect(self.on_configuration)
            self.inventory_controller.logout_requested.connect(self.on_logout)
        else:
            self.inventory_controller.set_user_id(user_id)
        
        # Initialize or update bookkeeper controller with user_id
        if self.bookkeeper_controller is None:
            self.bookkeeper_controller = BookkeeperController(
                self.bookkeeper_view,
                self.nominal_account_model,
                self.journal_entry_model,
                user_id
            )
            self.bookkeeper_controller.dashboard_requested.connect(self.on_back_to_dashboard)
            self.bookkeeper_controller.suppliers_requested.connect(self.on_suppliers)
            self.bookkeeper_controller.customers_requested.connect(self.on_customers)
            self.bookkeeper_controller.products_requested.connect(self.on_products)
            self.bookkeeper_controller.inventory_requested.connect(self.on_inventory)
            self.bookkeeper_controller.vehicles_requested.connect(self.on_vehicles)
            self.bookkeeper_controller.services_requested.connect(self.on_services)
            self.bookkeeper_controller.sales_requested.connect(self.on_sales)
            self.bookkeeper_controller.configuration_requested.connect(self.on_configuration)
            self.bookkeeper_controller.logout_requested.connect(self.on_logout)
        else:
            self.bookkeeper_controller.set_user_id(user_id)
        
        # Initialize or update vehicles controller
        if self.vehicles_controller is None:
            self.vehicles_controller = VehiclesController(
                self.vehicles_view,
                self.vehicle_model,
                self.api_key_model,
                user_id
            )
            self.vehicles_controller.dashboard_requested.connect(self.on_back_to_dashboard)
            self.vehicles_controller.suppliers_requested.connect(self.on_suppliers)
            self.vehicles_controller.customers_requested.connect(self.on_customers)
            self.vehicles_controller.products_requested.connect(self.on_products)
            self.vehicles_controller.inventory_requested.connect(self.on_inventory)
            self.vehicles_controller.bookkeeper_requested.connect(self.on_bookkeeper)
            self.vehicles_controller.services_requested.connect(self.on_services)
            self.vehicles_controller.sales_requested.connect(self.on_sales)
            self.vehicles_controller.configuration_requested.connect(self.on_configuration)
            self.vehicles_controller.logout_requested.connect(self.on_logout)
        else:
            self.vehicles_controller.set_user_id(user_id)
        
        # Initialize or update services controller
        if self.services_controller is None:
            self.services_controller = ServicesController(
                self.services_view,
                self.service_model,
                self.nominal_account_model,
                user_id
            )
            self.services_controller.dashboard_requested.connect(self.on_back_to_dashboard)
            self.services_controller.suppliers_requested.connect(self.on_suppliers)
            self.services_controller.customers_requested.connect(self.on_customers)
            self.services_controller.products_requested.connect(self.on_products)
            self.services_controller.inventory_requested.connect(self.on_inventory)
            self.services_controller.bookkeeper_requested.connect(self.on_bookkeeper)
            self.services_controller.vehicles_requested.connect(self.on_vehicles)
            self.services_controller.sales_requested.connect(self.on_sales)
            self.services_controller.configuration_requested.connect(self.on_configuration)
            self.services_controller.logout_requested.connect(self.on_logout)
        else:
            self.services_controller.set_user_id(user_id)
        
        # Initialize or update sales controller
        if self.sales_controller is None:
            self.sales_controller = SalesController(
                self.sales_view,
                self.sales_invoice_model,
                self.sales_invoice_item_model,
                self.customer_payment_model,
                self.customer_payment_allocation_model,
                self.customer_model,
                self.product_model,
                self.service_model,
                self.vehicle_model,
                user_id
            )
            self.sales_controller.dashboard_requested.connect(self.on_back_to_dashboard)
            self.sales_controller.suppliers_requested.connect(self.on_suppliers)
            self.sales_controller.customers_requested.connect(self.on_customers)
            self.sales_controller.products_requested.connect(self.on_products)
            self.sales_controller.inventory_requested.connect(self.on_inventory)
            self.sales_controller.bookkeeper_requested.connect(self.on_bookkeeper)
            self.sales_controller.vehicles_requested.connect(self.on_vehicles)
            self.sales_controller.services_requested.connect(self.on_services)
            self.sales_controller.configuration_requested.connect(self.on_configuration)
            self.sales_controller.logout_requested.connect(self.on_logout)
        else:
            self.sales_controller.set_user_id(user_id)
        
        # Initialize or update configuration controller
        if self.configuration_controller is None:
            self.configuration_controller = ConfigurationController(
                self.configuration_view,
                self.api_key_model,
                user_id
            )
            self.configuration_controller.dashboard_requested.connect(self.on_back_to_dashboard)
            self.configuration_controller.suppliers_requested.connect(self.on_suppliers)
            self.configuration_controller.customers_requested.connect(self.on_customers)
            self.configuration_controller.products_requested.connect(self.on_products)
            self.configuration_controller.inventory_requested.connect(self.on_inventory)
            self.configuration_controller.bookkeeper_requested.connect(self.on_bookkeeper)
            self.configuration_controller.vehicles_requested.connect(self.on_vehicles)
            self.configuration_controller.services_requested.connect(self.on_services)
            self.configuration_controller.sales_requested.connect(self.on_sales)
            self.configuration_controller.logout_requested.connect(self.on_logout)
        else:
            self.configuration_controller.set_user_id(user_id)
        
        # Update window for dashboard - maximize to full screen
        self.setWindowTitle("Dashboard")
        self.setMinimumSize(800, 600)
        self.showMaximized()
        
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
    
    def on_customers(self):
        """Handle navigation to customers."""
        # Refresh customers for current user
        if self.customers_controller:
            self.customers_controller.refresh_customers()
        # Update navigation highlighting
        self.customers_view.nav_panel.set_current_view("customers")
        # Switch to customers view
        self.stacked_widget.setCurrentIndex(self.customers_index)
        self.setWindowTitle("Customers")
        self.setMinimumSize(800, 600)
    
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
    
    def on_inventory(self):
        """Handle navigation to inventory."""
        # Refresh inventory for current user
        if self.inventory_controller:
            self.inventory_controller.refresh_inventory()
        # Update navigation highlighting
        self.inventory_view.nav_panel.set_current_view("inventory")
        # Switch to inventory view
        self.stacked_widget.setCurrentIndex(self.inventory_index)
        self.setWindowTitle("Inventory")
        self.setMinimumSize(800, 600)
    
    def on_bookkeeper(self):
        """Handle navigation to bookkeeper."""
        # Refresh accounts for current user
        if self.bookkeeper_controller:
            self.bookkeeper_controller.refresh_accounts()
        # Update navigation highlighting
        self.bookkeeper_view.nav_panel.set_current_view("bookkeeper")
        # Switch to bookkeeper view
        self.stacked_widget.setCurrentIndex(self.bookkeeper_index)
        self.setWindowTitle("Book Keeper")
        self.setMinimumSize(800, 600)
    
    def on_vehicles(self):
        """Handle navigation to vehicles."""
        # Refresh vehicles for current user
        if self.vehicles_controller:
            self.vehicles_controller.refresh_vehicles()
        # Update navigation highlighting
        self.vehicles_view.nav_panel.set_current_view("vehicles")
        # Switch to vehicles view
        self.stacked_widget.setCurrentIndex(self.vehicles_index)
        self.setWindowTitle("Vehicles")
        self.setMinimumSize(800, 600)
    
    def on_services(self):
        """Handle navigation to services."""
        # Refresh services for current user
        if self.services_controller:
            self.services_controller.refresh_services()
        # Update navigation highlighting
        self.services_view.nav_panel.set_current_view("services")
        # Switch to services view
        self.stacked_widget.setCurrentIndex(self.services_index)
        self.setWindowTitle("Services")
        self.setMinimumSize(800, 600)
    
    def on_sales(self):
        """Handle navigation to sales."""
        # Refresh sales documents for current user
        if self.sales_controller:
            self.sales_controller.refresh_documents()
        # Update navigation highlighting
        self.sales_view.nav_panel.set_current_view("sales")
        # Switch to sales view
        self.stacked_widget.setCurrentIndex(self.sales_index)
        self.setWindowTitle("Sales")
        self.setMinimumSize(800, 600)
    
    def on_configuration(self):
        """Handle navigation to configuration."""
        # Update navigation highlighting
        self.configuration_view.nav_panel.set_current_view("configuration")
        # Switch to configuration view
        self.stacked_widget.setCurrentIndex(self.configuration_index)
        self.setWindowTitle("Configuration")
        self.setMinimumSize(800, 600)
    
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
