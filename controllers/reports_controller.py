"""Reports controller for financial statements."""
from typing import TYPE_CHECKING, List, Dict, Optional, Union
from PySide6.QtCore import QObject, Signal
from datetime import date, datetime
import sqlite3

if TYPE_CHECKING:
    from views.reports_view import ReportsView
    from views.reports_dialog import ReportsDialog
    from models.nominal_account import NominalAccount
    from models.journal_entry import JournalEntry


class ReportsController(QObject):
    """Controller for reports functionality."""
    
    # Navigation signals
    dashboard_requested = Signal()
    suppliers_requested = Signal()
    customers_requested = Signal()
    products_requested = Signal()
    inventory_requested = Signal()
    bookkeeper_requested = Signal()
    vehicles_requested = Signal()
    services_requested = Signal()
    sales_requested = Signal()
    configuration_requested = Signal()
    logout_requested = Signal()
    
    def __init__(self, reports_view: Union["ReportsView", "ReportsDialog"],
                 nominal_account_model: "NominalAccount",
                 journal_entry_model: "JournalEntry",
                 user_id: int):
        """Initialize the reports controller."""
        super().__init__()
        self.reports_view = reports_view
        self.nominal_account_model = nominal_account_model
        self.journal_entry_model = journal_entry_model
        self.user_id = user_id
        
        # Connect view signals to controller handlers (only if they exist - dialogs don't have navigation signals)
        if hasattr(self.reports_view, 'dashboard_requested'):
            self.reports_view.dashboard_requested.connect(self.handle_dashboard)
            self.reports_view.suppliers_requested.connect(self.handle_suppliers)
            self.reports_view.customers_requested.connect(self.handle_customers)
            self.reports_view.products_requested.connect(self.handle_products)
            self.reports_view.inventory_requested.connect(self.handle_inventory)
            self.reports_view.bookkeeper_requested.connect(self.handle_bookkeeper)
            self.reports_view.vehicles_requested.connect(self.handle_vehicles)
            self.reports_view.services_requested.connect(self.handle_services)
            self.reports_view.sales_requested.connect(self.handle_sales)
            self.reports_view.configuration_requested.connect(self.handle_configuration)
            self.reports_view.logout_requested.connect(self.handle_logout)
        
        # Report generation signals (always present)
        self.reports_view.generate_vat_return_requested.connect(self.handle_generate_vat_return)
        self.reports_view.generate_profit_loss_requested.connect(self.handle_generate_profit_loss)
        self.reports_view.generate_trial_balance_requested.connect(self.handle_generate_trial_balance)
        self.reports_view.generate_balance_sheet_requested.connect(self.handle_generate_balance_sheet)
    
    def set_user_id(self, user_id: int):
        """Update the user ID."""
        self.user_id = user_id
    
    def handle_generate_vat_return(self, start_date_str: str, end_date_str: str):
        """Generate VAT return for date range."""
        try:
            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)
        except (ValueError, AttributeError):
            if hasattr(self.reports_view, 'show_error_dialog'):
                self.reports_view.show_error_dialog("Invalid date format")
            return
        
        vat_data = self.generate_vat_return(start_date, end_date)
        if hasattr(self.reports_view, 'load_vat_return'):
            self.reports_view.load_vat_return(vat_data)
    
    def handle_generate_profit_loss(self, start_date_str: str, end_date_str: str):
        """Generate Profit & Loss for date range."""
        try:
            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)
        except (ValueError, AttributeError):
            if hasattr(self.reports_view, 'show_error_dialog'):
                self.reports_view.show_error_dialog("Invalid date format")
            return
        
        pl_data = self.generate_profit_loss(start_date, end_date)
        if hasattr(self.reports_view, 'load_profit_loss'):
            self.reports_view.load_profit_loss(pl_data)
    
    def handle_generate_trial_balance(self, as_at_date_str: str):
        """Generate Trial Balance as at date."""
        try:
            as_at_date = date.fromisoformat(as_at_date_str)
        except (ValueError, AttributeError):
            if hasattr(self.reports_view, 'show_error_dialog'):
                self.reports_view.show_error_dialog("Invalid date format")
            return
        
        tb_data = self.generate_trial_balance(as_at_date)
        if hasattr(self.reports_view, 'load_trial_balance'):
            self.reports_view.load_trial_balance(tb_data)
    
    def handle_generate_balance_sheet(self, as_at_date_str: str):
        """Generate Balance Sheet as at date."""
        try:
            as_at_date = date.fromisoformat(as_at_date_str)
        except (ValueError, AttributeError):
            if hasattr(self.reports_view, 'show_error_dialog'):
                self.reports_view.show_error_dialog("Invalid date format")
            return
        
        bs_data = self.generate_balance_sheet(as_at_date)
        if hasattr(self.reports_view, 'load_balance_sheet'):
            self.reports_view.load_balance_sheet(bs_data)
    
    def generate_vat_return(self, start_date: date, end_date: date) -> List[Dict]:
        """
        Generate VAT return for date range.
        
        Args:
            start_date: Start date
            end_date: End date
        
        Returns:
            List of VAT return line items
        """
        db_path = self.journal_entry_model.db_path
        vat_data = []
        
        try:
            with sqlite3.connect(db_path, timeout=10.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get sales invoices with VAT in date range
                cursor.execute("""
                    SELECT 
                        sii.vat_code,
                        SUM(sii.line_total) as net_amount,
                        SUM(CASE 
                            WHEN sii.vat_code = 'S' THEN sii.line_total * 0.20
                            ELSE 0.0
                        END) as vat_amount
                    FROM sales_invoice_items sii
                    JOIN sales_invoices si ON sii.sales_invoice_id = si.id
                    WHERE si.user_id = ?
                    AND si.document_date >= ?
                    AND si.document_date <= ?
                    AND si.document_type = 'invoice'
                    GROUP BY sii.vat_code
                """, (self.user_id, start_date.isoformat(), end_date.isoformat()))
                
                sales_vat = {}
                total_output_vat = 0.0
                for row in cursor.fetchall():
                    vat_code = row['vat_code'] or 'S'
                    net_amount = row['net_amount'] or 0.0
                    vat_amount = row['vat_amount'] or 0.0
                    sales_vat[vat_code] = {'net': net_amount, 'vat': vat_amount}
                    total_output_vat += vat_amount
                
                # Get supplier invoices with VAT in date range
                cursor.execute("""
                    SELECT 
                        ii.vat_code,
                        SUM(ii.line_total) as net_amount,
                        SUM(CASE 
                            WHEN ii.vat_code = 'S' THEN ii.line_total * 0.20
                            ELSE 0.0
                        END) as vat_amount
                    FROM invoice_items ii
                    JOIN invoices i ON ii.invoice_id = i.id
                    WHERE i.user_id = ?
                    AND i.invoice_date >= ?
                    AND i.invoice_date <= ?
                    GROUP BY ii.vat_code
                """, (self.user_id, start_date.isoformat(), end_date.isoformat()))
                
                purchase_vat = {}
                total_input_vat = 0.0
                for row in cursor.fetchall():
                    vat_code = row['vat_code'] or 'S'
                    net_amount = row['net_amount'] or 0.0
                    vat_amount = row['vat_amount'] or 0.0
                    purchase_vat[vat_code] = {'net': net_amount, 'vat': vat_amount}
                    total_input_vat += vat_amount
                
                # Build VAT return data
                vat_data.append({
                    'description': 'Output VAT (Sales)',
                    'output_vat': total_output_vat,
                    'input_vat': 0.0,
                    'net_vat': total_output_vat
                })
                
                vat_data.append({
                    'description': 'Input VAT (Purchases)',
                    'output_vat': 0.0,
                    'input_vat': total_input_vat,
                    'net_vat': -total_input_vat
                })
                
                net_vat = total_output_vat - total_input_vat
                vat_data.append({
                    'description': 'Net VAT Payable/(Refundable)',
                    'output_vat': total_output_vat,
                    'input_vat': total_input_vat,
                    'net_vat': net_vat
                })
        except Exception as e:
            if hasattr(self.reports_view, 'show_error_dialog'):
                self.reports_view.show_error_dialog(f"Error generating VAT return: {str(e)}")
            return []
        
        return vat_data
    
    def generate_profit_loss(self, start_date: date, end_date: date) -> List[Dict]:
        """
        Generate Profit & Loss for date range.
        
        Args:
            start_date: Start date
            end_date: End date
        
        Returns:
            List of P&L line items
        """
        db_path = self.nominal_account_model.db_path
        pl_data = []
        
        try:
            accounts = self.nominal_account_model.get_all(self.user_id)
            
            # Filter to Income and Expense accounts
            income_accounts = [a for a in accounts if a.get('account_type') == 'Income']
            expense_accounts = [a for a in accounts if a.get('account_type') == 'Expense']
            
            # Calculate income
            total_income = 0.0
            income_items = []
            for account in income_accounts:
                balance = self._calculate_account_balance_for_period(
                    account['id'], account['opening_balance'], start_date, end_date
                )
                # For income accounts, credits increase, debits decrease
                # Balance = opening + credits - debits
                if abs(balance) > 0.01:
                    income_items.append({
                        'account': f"{account['account_code']} - {account['account_name']}",
                        'amount': balance
                    })
                    total_income += balance
            
            # Calculate expenses
            total_expenses = 0.0
            expense_items = []
            for account in expense_accounts:
                balance = self._calculate_account_balance_for_period(
                    account['id'], account['opening_balance'], start_date, end_date
                )
                # For expense accounts, debits increase, credits decrease
                # Balance = opening + debits - credits
                if abs(balance) > 0.01:
                    expense_items.append({
                        'account': f"{account['account_code']} - {account['account_name']}",
                        'amount': -balance  # Expenses shown as negative
                    })
                    total_expenses += balance
            
            # Build P&L data
            pl_data.append({'account': 'INCOME', 'amount': 0.0})  # Header
            pl_data.extend(income_items)
            pl_data.append({'account': 'Total Income', 'amount': total_income})
            
            pl_data.append({'account': '', 'amount': 0.0})  # Spacer
            pl_data.append({'account': 'EXPENSES', 'amount': 0.0})  # Header
            pl_data.extend(expense_items)
            pl_data.append({'account': 'Total Expenses', 'amount': -total_expenses})
            
            pl_data.append({'account': '', 'amount': 0.0})  # Spacer
            net_profit = total_income - total_expenses
            pl_data.append({'account': 'NET PROFIT/(LOSS)', 'amount': net_profit})
        except Exception as e:
            if hasattr(self.reports_view, 'show_error_dialog'):
                self.reports_view.show_error_dialog(f"Error generating Profit & Loss: {str(e)}")
            return []
        
        return pl_data
    
    def generate_trial_balance(self, as_at_date: date) -> List[Dict]:
        """
        Generate Trial Balance as at date.
        
        Args:
            as_at_date: As at date
        
        Returns:
            List of trial balance line items
        """
        db_path = self.nominal_account_model.db_path
        tb_data = []
        
        try:
            accounts = self.nominal_account_model.get_all(self.user_id)
            
            total_debits = 0.0
            total_credits = 0.0
            
            for account in accounts:
                balance = self._calculate_account_balance_as_at(
                    account['id'], account['opening_balance'], account['account_type'], as_at_date
                )
                
                # Determine if balance is debit or credit
                account_type = account.get('account_type', '')
                if account_type in ['Asset', 'Expense']:
                    # Debit balance (positive = debit, negative = credit)
                    debit = balance if balance > 0 else 0.0
                    credit = -balance if balance < 0 else 0.0
                else:
                    # Credit balance (positive = credit, negative = debit)
                    credit = balance if balance > 0 else 0.0
                    debit = -balance if balance < 0 else 0.0
                
                total_debits += debit
                total_credits += credit
                
                tb_data.append({
                    'account_code': account['account_code'],
                    'account_name': account['account_name'],
                    'debit': debit,
                    'credit': credit,
                    'balance': balance
                })
            
            # Add totals row
            tb_data.append({
                'account_code': '',
                'account_name': 'TOTAL',
                'debit': total_debits,
                'credit': total_credits,
                'balance': total_debits - total_credits
            })
        except Exception as e:
            if hasattr(self.reports_view, 'show_error_dialog'):
                self.reports_view.show_error_dialog(f"Error generating Trial Balance: {str(e)}")
            return []
        
        return tb_data
    
    def generate_balance_sheet(self, as_at_date: date) -> List[Dict]:
        """
        Generate Balance Sheet as at date.
        
        Args:
            as_at_date: As at date
        
        Returns:
            List of balance sheet line items
        """
        db_path = self.nominal_account_model.db_path
        bs_data = []
        
        try:
            accounts = self.nominal_account_model.get_all(self.user_id)
            
            # Group accounts by type
            assets = [a for a in accounts if a.get('account_type') == 'Asset']
            liabilities = [a for a in accounts if a.get('account_type') == 'Liability']
            equity = [a for a in accounts if a.get('account_type') == 'Equity']
            
            # Calculate totals
            total_assets = 0.0
            asset_items = []
            for account in assets:
                balance = self._calculate_account_balance_as_at(
                    account['id'], account['opening_balance'], 'Asset', as_at_date
                )
                if abs(balance) > 0.01:
                    asset_items.append({
                        'account': f"{account['account_code']} - {account['account_name']}",
                        'amount': balance
                    })
                    total_assets += balance
            
            total_liabilities = 0.0
            liability_items = []
            for account in liabilities:
                balance = self._calculate_account_balance_as_at(
                    account['id'], account['opening_balance'], 'Liability', as_at_date
                )
                if abs(balance) > 0.01:
                    liability_items.append({
                        'account': f"{account['account_code']} - {account['account_name']}",
                        'amount': balance
                    })
                    total_liabilities += balance
            
            total_equity = 0.0
            equity_items = []
            for account in equity:
                balance = self._calculate_account_balance_as_at(
                    account['id'], account['opening_balance'], 'Equity', as_at_date
                )
                if abs(balance) > 0.01:
                    equity_items.append({
                        'account': f"{account['account_code']} - {account['account_name']}",
                        'amount': balance
                    })
                    total_equity += balance
            
            # Calculate retained earnings (profit/loss from P&L)
            # This is a simplified calculation - in practice, you'd track retained earnings separately
            # For now, we'll calculate it as: Assets - Liabilities - Equity
            retained_earnings = total_assets - total_liabilities - total_equity
            
            # Build Balance Sheet data
            bs_data.append({'account': 'ASSETS', 'amount': 0.0})  # Header
            bs_data.extend(asset_items)
            bs_data.append({'account': 'Total Assets', 'amount': total_assets})
            
            bs_data.append({'account': '', 'amount': 0.0})  # Spacer
            bs_data.append({'account': 'LIABILITIES', 'amount': 0.0})  # Header
            bs_data.extend(liability_items)
            bs_data.append({'account': 'Total Liabilities', 'amount': total_liabilities})
            
            bs_data.append({'account': '', 'amount': 0.0})  # Spacer
            bs_data.append({'account': 'EQUITY', 'amount': 0.0})  # Header
            bs_data.extend(equity_items)
            if abs(retained_earnings) > 0.01:
                bs_data.append({'account': 'Retained Earnings', 'amount': retained_earnings})
            bs_data.append({'account': 'Total Equity', 'amount': total_equity + retained_earnings})
            
            bs_data.append({'account': '', 'amount': 0.0})  # Spacer
            total_liabilities_equity = total_liabilities + total_equity + retained_earnings
            bs_data.append({'account': 'Total Liabilities & Equity', 'amount': total_liabilities_equity})
        except Exception as e:
            if hasattr(self.reports_view, 'show_error_dialog'):
                self.reports_view.show_error_dialog(f"Error generating Balance Sheet: {str(e)}")
            return []
        
        return bs_data
    
    def _calculate_account_balance_for_period(self, account_id: int, opening_balance: float,
                                             start_date: date, end_date: date) -> float:
        """
        Calculate account balance for a period (from start_date to end_date).
        
        Args:
            account_id: Account ID
            opening_balance: Opening balance
            start_date: Start date
            end_date: End date
        
        Returns:
            Account balance for the period
        """
        db_path = self.journal_entry_model.db_path
        
        try:
            with sqlite3.connect(db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Get total debits in period
                cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0.0)
                    FROM journal_entries
                    WHERE debit_account_id = ?
                    AND entry_date >= ?
                    AND entry_date <= ?
                """, (account_id, start_date.isoformat(), end_date.isoformat()))
                total_debits = cursor.fetchone()[0] or 0.0
                
                # Get total credits in period
                cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0.0)
                    FROM journal_entries
                    WHERE credit_account_id = ?
                    AND entry_date >= ?
                    AND entry_date <= ?
                """, (account_id, start_date.isoformat(), end_date.isoformat()))
                total_credits = cursor.fetchone()[0] or 0.0
                
                # Get account type
                cursor.execute("SELECT account_type FROM nominal_accounts WHERE id = ?", (account_id,))
                result = cursor.fetchone()
                if not result:
                    return opening_balance
                
                account_type = result[0]
                
                # Calculate balance based on account type
                # For period reports, we only show transactions in the period (not opening balance)
                if account_type in ['Asset', 'Expense']:
                    return total_debits - total_credits
                else:
                    return total_credits - total_debits
        except Exception:
            return 0.0
    
    def _calculate_account_balance_as_at(self, account_id: int, opening_balance: float,
                                          account_type: str, as_at_date: date) -> float:
        """
        Calculate account balance as at a specific date.
        
        Args:
            account_id: Account ID
            opening_balance: Opening balance
            account_type: Account type
            as_at_date: As at date
        
        Returns:
            Account balance as at date
        """
        db_path = self.journal_entry_model.db_path
        
        try:
            with sqlite3.connect(db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Get total debits up to and including as_at_date
                cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0.0)
                    FROM journal_entries
                    WHERE debit_account_id = ?
                    AND entry_date <= ?
                """, (account_id, as_at_date.isoformat()))
                total_debits = cursor.fetchone()[0] or 0.0
                
                # Get total credits up to and including as_at_date
                cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0.0)
                    FROM journal_entries
                    WHERE credit_account_id = ?
                    AND entry_date <= ?
                """, (account_id, as_at_date.isoformat()))
                total_credits = cursor.fetchone()[0] or 0.0
                
                # Calculate balance based on account type
                if account_type in ['Asset', 'Expense']:
                    balance = opening_balance + total_debits - total_credits
                else:
                    balance = opening_balance + total_credits - total_debits
                
                return balance
        except Exception:
            return opening_balance
    
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

