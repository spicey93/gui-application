"""Dashboard controller."""
from typing import TYPE_CHECKING
from PySide6.QtCore import QObject, Signal
from datetime import datetime, date
from utils.transaction_logger import TransactionLogger
from utils.account_finder import find_bank_account, find_undeposited_funds_account
from models.journal_entry import JournalEntry

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
    vehicles_requested = Signal()
    services_requested = Signal()
    sales_requested = Signal()
    configuration_requested = Signal()
    cash_up_requested = Signal()
    
    def __init__(self, dashboard_view: "DashboardView", user_id: int = None, db_path: str = "data/app.db"):
        """Initialize the dashboard controller."""
        super().__init__()
        self.dashboard_view = dashboard_view
        self.user_id = user_id
        self.db_path = db_path
        self.transaction_logger = TransactionLogger(db_path)
        self.journal_entry_model = JournalEntry(db_path)
        
        # Connect view signals to controller
        self.dashboard_view.logout_requested.connect(self.handle_logout)
        self.dashboard_view.suppliers_requested.connect(self.handle_suppliers)
        self.dashboard_view.customers_requested.connect(self.handle_customers)
        self.dashboard_view.products_requested.connect(self.handle_products)
        self.dashboard_view.inventory_requested.connect(self.handle_inventory)
        self.dashboard_view.bookkeeper_requested.connect(self.handle_bookkeeper)
        self.dashboard_view.vehicles_requested.connect(self.handle_vehicles)
        self.dashboard_view.services_requested.connect(self.handle_services)
        self.dashboard_view.sales_requested.connect(self.handle_sales)
        self.dashboard_view.configuration_requested.connect(self.handle_configuration)
        self.dashboard_view.cash_up_requested.connect(self.handle_cash_up_navigation)
    
    def set_user_id(self, user_id: int):
        """Update the user ID."""
        self.user_id = user_id
    
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
    
    def handle_vehicles(self):
        """Handle vehicles navigation."""
        self.vehicles_requested.emit()
    
    def handle_services(self):
        """Handle services navigation."""
        self.services_requested.emit()
    
    def handle_sales(self):
        """Handle sales navigation."""
        self.sales_requested.emit()
    
    def handle_configuration(self):
        """Handle configuration navigation."""
        self.configuration_requested.emit()
    
    def handle_cash_up_navigation(self):
        """Handle cash up request - open cash up dialog."""
        # Import here to avoid circular imports
        from views.cash_up_view import CashUpDialog
        from models.nominal_account import NominalAccount
        
        # Get nominal accounts for the filter dialog
        nominal_account_model = NominalAccount(self.db_path)
        nominal_accounts = nominal_account_model.get_all(self.user_id) if self.user_id else []
        
        # Create and show cash up dialog
        dialog = CashUpDialog(
            parent=self.dashboard_view, 
            nominal_accounts=nominal_accounts,
            user_id=self.user_id,
            db_path=self.db_path
        )
        # The dialog will handle its own signals internally
        dialog.exec()
