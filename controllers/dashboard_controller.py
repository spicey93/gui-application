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
        self.dashboard_view.cash_up_requested.connect(self.handle_cash_up)
    
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
    
    def handle_cash_up(self, start_date_str: str, end_date_str: str):
        """Handle cash up request - move card payments from Undeposited Funds to Bank."""
        if not self.user_id:
            self.dashboard_view.show_error_dialog("User not logged in")
            return
        
        try:
            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)
        except (ValueError, AttributeError):
            self.dashboard_view.show_error_dialog("Invalid date format")
            return
        
        # Find accounts
        bank_account_id = find_bank_account(self.user_id, self.db_path)
        undeposited_funds_id = find_undeposited_funds_account(self.user_id, self.db_path)
        
        if not bank_account_id:
            self.dashboard_view.show_error_dialog("Bank account not found. Please create a Bank Account in Book Keeper.")
            return
        
        if not undeposited_funds_id:
            self.dashboard_view.show_error_dialog("Undeposited Funds account not found. Please create an Undeposited Funds account in Book Keeper.")
            return
        
        # Get card payments in date range from journal entries
        # Look for Customer Payment entries with Card payment method
        import sqlite3
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get customer payments in date range with Card payment method
                cursor.execute("""
                    SELECT cp.id, cp.amount, cp.payment_date, cp.reference, c.name as customer_name
                    FROM customer_payments cp
                    JOIN customers c ON cp.customer_id = c.id
                    WHERE cp.user_id = ? 
                    AND cp.payment_method = 'Card'
                    AND cp.payment_date >= ? 
                    AND cp.payment_date <= ?
                    ORDER BY cp.payment_date
                """, (self.user_id, start_date_str, end_date_str))
                
                payments = cursor.fetchall()
                
                if not payments:
                    self.dashboard_view.show_success_dialog(f"No card payments found for the selected date range ({start_date_str} to {end_date_str}).")
                    return
                
                # Calculate total amount
                total_amount = sum(p['amount'] for p in payments)
                
                # Check if journal entries already exist for these payments (to avoid duplicates)
                # We'll create a single journal entry for the total amount
                # Debit Bank, Credit Undeposited Funds
                today = date.today()
                description = f"Cash Up - Card payments from {start_date_str} to {end_date_str}"
                reference = f"CASHUP-{today.strftime('%Y%m%d')}"
                
                success, message, entry_id = self.journal_entry_model.create(
                    entry_date=today,
                    description=description,
                    debit_account_id=bank_account_id,
                    credit_account_id=undeposited_funds_id,
                    amount=total_amount,
                    reference=reference,
                    user_id=self.user_id,
                    transaction_type="Cash Up",
                    stakeholder=None
                )
                
                if success:
                    self.dashboard_view.show_success_dialog(
                        f"Cash Up completed successfully.\n"
                        f"Moved £{total_amount:,.2f} from Undeposited Funds to Bank account.\n"
                        f"Date range: {start_date_str} to {end_date_str}\n"
                        f"Number of payments: {len(payments)}"
                    )
                else:
                    self.dashboard_view.show_error_dialog(f"Error completing cash up: {message}")
        except Exception as e:
            self.dashboard_view.show_error_dialog(f"Error processing cash up: {str(e)}")
