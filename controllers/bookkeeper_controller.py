"""Book Keeper controller."""
from typing import TYPE_CHECKING, Optional
from PySide6.QtCore import QObject, Signal
from datetime import date

if TYPE_CHECKING:
    from views.bookkeeper_view import BookkeeperView
    from models.nominal_account import NominalAccount
    from models.journal_entry import JournalEntry


class BookkeeperController(QObject):
    """Controller for bookkeeper functionality."""
    
    # Signals
    dashboard_requested = Signal()
    suppliers_requested = Signal()
    customers_requested = Signal()
    products_requested = Signal()
    inventory_requested = Signal()
    vehicles_requested = Signal()
    services_requested = Signal()
    sales_requested = Signal()
    configuration_requested = Signal()
    logout_requested = Signal()
    
    def __init__(self, bookkeeper_view: "BookkeeperView", 
                 nominal_account_model: "NominalAccount",
                 journal_entry_model: "JournalEntry",
                 user_id: int):
        """Initialize the bookkeeper controller."""
        super().__init__()
        self.bookkeeper_view = bookkeeper_view
        self.nominal_account_model = nominal_account_model
        self.journal_entry_model = journal_entry_model
        self.user_id = user_id
        
        # Connect view signals to controller handlers
        self.bookkeeper_view.dashboard_requested.connect(self.handle_dashboard)
        self.bookkeeper_view.suppliers_requested.connect(self.handle_suppliers)
        self.bookkeeper_view.customers_requested.connect(self.handle_customers)
        self.bookkeeper_view.products_requested.connect(self.handle_products)
        self.bookkeeper_view.inventory_requested.connect(self.handle_inventory)
        self.bookkeeper_view.vehicles_requested.connect(self.handle_vehicles)
        self.bookkeeper_view.services_requested.connect(self.handle_services)
        self.bookkeeper_view.sales_requested.connect(self.handle_sales)
        self.bookkeeper_view.configuration_requested.connect(self.handle_configuration)
        self.bookkeeper_view.logout_requested.connect(self.handle_logout)
        self.bookkeeper_view.create_account_requested.connect(self.handle_create_account)
        self.bookkeeper_view.update_account_requested.connect(self.handle_update_account)
        self.bookkeeper_view.delete_account_requested.connect(self.handle_delete_account)
        self.bookkeeper_view.transfer_funds_requested.connect(self.handle_transfer_funds)
        self.bookkeeper_view.transfer_accounts_requested.connect(self.handle_populate_transfer_accounts)
        self.bookkeeper_view.refresh_requested.connect(self.handle_refresh_activity)
        
        # Load initial accounts
        self.refresh_accounts()
    
    def set_user_id(self, user_id: int):
        """Update the user ID and refresh accounts."""
        self.user_id = user_id
        self.refresh_accounts()
    
    def handle_create_account(self, account_code: int, account_name: str, 
                              account_type: str, opening_balance: float, 
                              is_bank_account: bool):
        """Handle create account."""
        success, message, account_id = self.nominal_account_model.create(
            account_code, account_name, account_type, opening_balance, 
            is_bank_account, self.user_id
        )
        
        if success:
            self.bookkeeper_view.show_success_dialog(message)
            self.refresh_accounts()
        else:
            self.bookkeeper_view.show_error_dialog(message)
    
    def handle_update_account(self, account_id: int, account_code: int, 
                             account_name: str, account_type: str, 
                             opening_balance: float, is_bank_account: bool):
        """Handle update account."""
        success, message = self.nominal_account_model.update(
            account_id, account_code, account_name, account_type, 
            opening_balance, is_bank_account, self.user_id
        )
        
        if success:
            self.bookkeeper_view.show_success_dialog(message)
            self.refresh_accounts()
        else:
            self.bookkeeper_view.show_error_dialog(message)
    
    def handle_delete_account(self, account_id: int):
        """Handle delete account."""
        success, message = self.nominal_account_model.delete(account_id, self.user_id)
        
        if success:
            self.bookkeeper_view.show_success_dialog(message)
            self.refresh_accounts()
        else:
            self.bookkeeper_view.show_error_dialog(message)
    
    def handle_populate_transfer_accounts(self):
        """Handle request to populate transfer dialog with accounts."""
        accounts = self.get_accounts_for_transfer()
        # Populate the transfer dialog combos if dialog exists
        if hasattr(self.bookkeeper_view, '_transfer_dialog') and self.bookkeeper_view._transfer_dialog:
            dialog = self.bookkeeper_view._transfer_dialog
            if hasattr(dialog, 'from_combo') and hasattr(dialog, 'to_combo'):
                self.bookkeeper_view.populate_transfer_accounts(accounts, dialog.from_combo, dialog.to_combo)
    
    def handle_transfer_funds(self, from_account_id: int, to_account_id: int, 
                              amount: float, description: str, 
                              entry_date_str: str, reference: str):
        """Handle fund transfer between accounts."""
        try:
            # Parse date string
            entry_date = date.fromisoformat(entry_date_str)
        except (ValueError, AttributeError):
            self.bookkeeper_view.show_error_dialog("Invalid date format")
            return
        
        # Convert empty string to None for reference
        reference = reference if reference else None
        
        # Create journal entry: debit to_account, credit from_account
        # This represents money moving FROM from_account TO to_account
        success, message, entry_id = self.journal_entry_model.create(
            entry_date, description, to_account_id, from_account_id, 
            amount, reference, self.user_id
        )
        
        if success:
            self.bookkeeper_view.show_success_dialog(f"Transfer completed: {message}")
            self.refresh_accounts()
            # Refresh activity if an account is selected
            if self.bookkeeper_view.selected_account_id:
                self.handle_refresh_activity()
        else:
            self.bookkeeper_view.show_error_dialog(message)
    
    def handle_refresh_activity(self):
        """Handle refresh activity request."""
        if self.bookkeeper_view.selected_account_id:
            account_id = self.bookkeeper_view.selected_account_id
            entries = self.journal_entry_model.get_account_entries(account_id, self.user_id)
            
            # Get account info to determine balance calculation
            account = self.nominal_account_model.get_by_id(account_id, self.user_id)
            if account:
                # Calculate running balance based on account type
                opening_balance = account.get('opening_balance', 0.0)
                account_type = account.get('account_type', '')
                
                # Calculate running balance for each entry
                running_balance = opening_balance
                for entry in entries:
                    amount = entry.get('amount', 0.0)
                    is_debit = entry.get('is_debit', False)
                    
                    # Assets and Expenses: Opening + Debits - Credits
                    # Liabilities, Equity, Income: Opening + Credits - Debits
                    if account_type in ['Asset', 'Expense']:
                        if is_debit:
                            running_balance += amount
                        else:
                            running_balance -= amount
                    else:
                        if is_debit:
                            running_balance -= amount
                        else:
                            running_balance += amount
                    
                    entry['running_balance'] = running_balance
                
                self.bookkeeper_view.load_activity(entries, account_id)
    
    def refresh_accounts(self):
        """Refresh the accounts list."""
        accounts = self.nominal_account_model.get_all(self.user_id)
        self.bookkeeper_view.load_accounts(accounts)
    
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
    
    def handle_logout(self):
        """Handle logout."""
        self.logout_requested.emit()
    
    def get_accounts_for_transfer(self):
        """Get accounts list for transfer dialog."""
        accounts = self.nominal_account_model.get_all(self.user_id)
        return accounts

