"""Cash Up Dialog - Separate window for the cash up process."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, 
    QDateEdit, QComboBox, QCheckBox, QLineEdit, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QShortcut, QKeySequence
from typing import List, Dict, Optional
from datetime import date
from views.cash_up_results_view import CashUpResultsView
from utils.styles import apply_theme


class CashUpDialog(QDialog):
    """Dialog window for cash up process with filtering and results display."""
    
    # Signals
    cash_up_requested = Signal(list)  # List of selected payment dictionaries to cash up
    filters_applied = Signal(dict)  # Filter criteria dictionary
    
    def __init__(self, parent=None, nominal_accounts: Optional[List[Dict]] = None, user_id: Optional[int] = None, db_path: str = "data/app.db"):
        """Initialize the cash up dialog."""
        super().__init__(parent)
        self.setWindowTitle("Cash Up")
        self.setModal(False)  # Non-modal so user can interact with main window
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        apply_theme(self)
        
        self._nominal_accounts: List[Dict] = nominal_accounts or []
        self._current_filters: Optional[Dict] = None
        self._user_id = user_id
        self._db_path = db_path
        self._create_widgets()
        self._setup_keyboard_shortcuts()
    
    def _create_widgets(self):
        """Create and layout UI widgets."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header with title
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Cash Up")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Filter section - Date range and all filters in one section
        filter_frame = QFrame()
        filter_frame.setFrameShape(QFrame.Shape.StyledPanel)
        filter_layout = QVBoxLayout(filter_frame)
        filter_layout.setSpacing(15)
        filter_layout.setContentsMargins(15, 15, 15, 15)
        
        # Section title
        filter_title = QLabel("Filters")
        filter_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        filter_layout.addWidget(filter_title)
        
        # Grid layout for filters
        filter_grid = QGridLayout()
        filter_grid.setSpacing(10)
        filter_grid.setColumnStretch(1, 1)
        filter_grid.setColumnStretch(3, 1)
        
        row = 0
        
        # Row 1: Quick Range, From Date, To Date
        quick_range_label = QLabel("Quick Range:")
        quick_range_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        quick_range_label.setMinimumWidth(100)
        filter_grid.addWidget(quick_range_label, row, 0)
        
        self.quick_range_combo = QComboBox()
        self.quick_range_combo.setStyleSheet("font-size: 12px;")
        self.quick_range_combo.addItems([
            "Custom",
            "Today",
            "Yesterday",
            "This Week",
            "Last Week",
            "This Month",
            "Last Month",
            "This Year",
            "Last Year"
        ])
        filter_grid.addWidget(self.quick_range_combo, row, 1)
        
        from_date_label = QLabel("From Date:")
        from_date_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        from_date_label.setMinimumWidth(80)
        filter_grid.addWidget(from_date_label, row, 2)
        
        self.from_date_edit = QDateEdit()
        self.from_date_edit.setCalendarPopup(True)
        self.from_date_edit.setDate(QDate.currentDate())
        self.from_date_edit.setStyleSheet("font-size: 12px;")
        self.from_date_edit.dateChanged.connect(self._handle_date_changed)
        filter_grid.addWidget(self.from_date_edit, row, 3)
        
        to_date_label = QLabel("To Date:")
        to_date_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        to_date_label.setMinimumWidth(80)
        filter_grid.addWidget(to_date_label, row, 4)
        
        self.to_date_edit = QDateEdit()
        self.to_date_edit.setCalendarPopup(True)
        self.to_date_edit.setDate(QDate.currentDate())
        self.to_date_edit.setStyleSheet("font-size: 12px;")
        self.to_date_edit.dateChanged.connect(self._handle_date_changed)
        filter_grid.addWidget(self.to_date_edit, row, 5)
        
        # Connect signal and set default after date edits are created
        self.quick_range_combo.currentTextChanged.connect(self._handle_quick_range_changed)
        self.quick_range_combo.setCurrentText("Today")
        
        row += 1
        
        # Row 2: Payment Method, Reconciled Status
        payment_method_label = QLabel("Payment Method:")
        payment_method_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        filter_grid.addWidget(payment_method_label, row, 0)
        
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.setStyleSheet("font-size: 12px;")
        self.payment_method_combo.addItems(["All", "Cash", "Card", "Cheque", "BACS"])
        filter_grid.addWidget(self.payment_method_combo, row, 1)
        
        reconciled_label = QLabel("Reconciled Status:")
        reconciled_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        filter_grid.addWidget(reconciled_label, row, 2)
        
        self.reconciled_combo = QComboBox()
        self.reconciled_combo.setStyleSheet("font-size: 12px;")
        self.reconciled_combo.addItems(["All", "Reconciled Only", "Unreconciled Only"])
        # Set default to "Unreconciled Only"
        self.reconciled_combo.setCurrentText("Unreconciled Only")
        filter_grid.addWidget(self.reconciled_combo, row, 3)
        
        row += 1
        
        # Row 3: Posted Status, Posted Batch No
        posted_status_label = QLabel("Posted Status:")
        posted_status_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        filter_grid.addWidget(posted_status_label, row, 0)
        
        self.posted_status_combo = QComboBox()
        self.posted_status_combo.setStyleSheet("font-size: 12px;")
        self.posted_status_combo.addItems(["All", "Yes", "No"])
        filter_grid.addWidget(self.posted_status_combo, row, 1)
        
        batch_no_label = QLabel("Posted Batch No:")
        batch_no_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        filter_grid.addWidget(batch_no_label, row, 2)
        
        self.batch_no_entry = QLineEdit()
        self.batch_no_entry.setStyleSheet("font-size: 12px;")
        self.batch_no_entry.setPlaceholderText("Enter batch number or leave blank")
        filter_grid.addWidget(self.batch_no_entry, row, 3, 1, 3)
        
        row += 1
        
        # Row 4: Nominal Account
        account_label = QLabel("Nominal Account:")
        account_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        filter_grid.addWidget(account_label, row, 0)
        
        self.account_combo = QComboBox()
        self.account_combo.setStyleSheet("font-size: 12px;")
        self.account_combo.setEditable(False)
        self.account_combo.addItem("All", None)
        # Populate with only Bank Account and Cash Account types
        undeposited_funds_id = None
        for account in self._nominal_accounts:
            account_type = account.get('account_type', '')
            account_subtype = account.get('account_subtype', '')
            account_name = account.get('account_name', '').lower()
            
            # Only include Bank Account or Cash Account types
            if account_type == 'Asset' and account_subtype in ['Bank Account', 'Cash Account']:
                account_text = f"{account.get('account_code', '')} - {account.get('account_name', '')}"
                account_id = account.get('id')
                self.account_combo.addItem(account_text, account_id)
        
        # Try to find Undeposited Funds account using account_finder
        if self._user_id:
            from utils.account_finder import find_undeposited_funds_account
            undeposited_funds_id = find_undeposited_funds_account(self._user_id, self._db_path)
        
        # If not found via account_finder, search in nominal_accounts for Current Asset with "undeposited" or "funds"
        if not undeposited_funds_id:
            for account in self._nominal_accounts:
                account_type = account.get('account_type', '')
                account_subtype = account.get('account_subtype', '')
                account_name = account.get('account_name', '').lower()
                if account_type == 'Asset' and account_subtype == 'Current Asset':
                    if 'undeposited' in account_name or 'funds' in account_name:
                        undeposited_funds_id = account.get('id')
                        # Add it to the combo if it's not already there
                        account_text = f"{account.get('account_code', '')} - {account.get('account_name', '')}"
                        self.account_combo.addItem(account_text, undeposited_funds_id)
                        break
        
        # Set default to Undeposited Funds if found, otherwise "All"
        if undeposited_funds_id:
            index = self.account_combo.findData(undeposited_funds_id)
            if index >= 0:
                self.account_combo.setCurrentIndex(index)
        filter_grid.addWidget(self.account_combo, row, 1, 1, 5)
        
        row += 1
        
        # Row 5: Include checkboxes
        checkbox_layout = QHBoxLayout()
        self.include_customer_payments_check = QCheckBox("Include Customer Payments")
        self.include_customer_payments_check.setStyleSheet("font-size: 12px;")
        self.include_customer_payments_check.setChecked(True)
        checkbox_layout.addWidget(self.include_customer_payments_check)
        
        self.include_supplier_payments_check = QCheckBox("Include Supplier Payments")
        self.include_supplier_payments_check.setStyleSheet("font-size: 12px;")
        self.include_supplier_payments_check.setChecked(True)
        checkbox_layout.addWidget(self.include_supplier_payments_check)
        
        checkbox_layout.addStretch()
        filter_grid.addLayout(checkbox_layout, row, 0, 1, 6)
        
        filter_layout.addLayout(filter_grid)
        
        # Apply and Clear buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_filter_button = QPushButton("Search (Ctrl+Enter)")
        self.apply_filter_button.setMinimumWidth(150)
        self.apply_filter_button.setMinimumHeight(30)
        self.apply_filter_button.setDefault(True)
        self.apply_filter_button.clicked.connect(self._handle_apply_filters)
        button_layout.addWidget(self.apply_filter_button)
        
        clear_filter_button = QPushButton("Clear All")
        clear_filter_button.setMinimumWidth(120)
        clear_filter_button.setMinimumHeight(30)
        clear_filter_button.clicked.connect(self._handle_clear_filters)
        button_layout.addWidget(clear_filter_button)
        
        filter_layout.addLayout(button_layout)
        
        layout.addWidget(filter_frame)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator2)
        
        # Results view
        self.results_view = CashUpResultsView()
        self.results_view.cash_up_selected.connect(self._handle_cash_up_selected)
        layout.addWidget(self.results_view, stretch=1)
        
        # Initially show empty state
        self.results_view.clear_results()
    
    def _setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts."""
        # Escape to close
        esc_shortcut = QShortcut(QKeySequence("Escape"), self)
        esc_shortcut.activated.connect(self.close)
        
        # Ctrl+Enter to apply filters
        ctrl_enter_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        ctrl_enter_shortcut.activated.connect(self._handle_apply_filters)
    
    def _handle_quick_range_changed(self, text: str):
        """
        Handle quick date range selection change.
        
        Args:
            text: Selected quick range option
        """
        # Block signals on date edits to prevent triggering _handle_date_changed
        self.from_date_edit.blockSignals(True)
        self.to_date_edit.blockSignals(True)
        
        today = QDate.currentDate()
        
        if text == "Today":
            self.from_date_edit.setDate(today)
            self.to_date_edit.setDate(today)
        elif text == "Yesterday":
            yesterday = today.addDays(-1)
            self.from_date_edit.setDate(yesterday)
            self.to_date_edit.setDate(yesterday)
        elif text == "This Week":
            # Monday of current week
            days_since_monday = today.dayOfWeek() - 1
            monday = today.addDays(-days_since_monday)
            self.from_date_edit.setDate(monday)
            self.to_date_edit.setDate(today)
        elif text == "Last Week":
            # Monday to Sunday of last week
            days_since_monday = today.dayOfWeek() - 1
            last_sunday = today.addDays(-days_since_monday - 1)
            last_monday = last_sunday.addDays(-6)
            self.from_date_edit.setDate(last_monday)
            self.to_date_edit.setDate(last_sunday)
        elif text == "This Month":
            # First day of current month
            first_day = QDate(today.year(), today.month(), 1)
            self.from_date_edit.setDate(first_day)
            self.to_date_edit.setDate(today)
        elif text == "Last Month":
            # First and last day of last month
            if today.month() == 1:
                last_month = QDate(today.year() - 1, 12, 1)
            else:
                last_month = QDate(today.year(), today.month() - 1, 1)
            last_day = last_month.addDays(last_month.daysInMonth() - 1)
            self.from_date_edit.setDate(last_month)
            self.to_date_edit.setDate(last_day)
        elif text == "This Year":
            # January 1st to today
            first_day = QDate(today.year(), 1, 1)
            self.from_date_edit.setDate(first_day)
            self.to_date_edit.setDate(today)
        elif text == "Last Year":
            # January 1st to December 31st of last year
            first_day = QDate(today.year() - 1, 1, 1)
            last_day = QDate(today.year() - 1, 12, 31)
            self.from_date_edit.setDate(first_day)
            self.to_date_edit.setDate(last_day)
        # "Custom" - do nothing, let user set dates manually
        
        # Re-enable signals
        self.from_date_edit.blockSignals(False)
        self.to_date_edit.blockSignals(False)
    
    def _handle_date_changed(self):
        """Handle manual date change - switch to Custom if not already."""
        if self.quick_range_combo.currentText() != "Custom":
            # Temporarily block signals to avoid recursion
            self.quick_range_combo.blockSignals(True)
            self.quick_range_combo.setCurrentText("Custom")
            self.quick_range_combo.blockSignals(False)
    
    def get_date_range(self) -> tuple[date, date]:
        """
        Get the selected date range.
        
        Returns:
            Tuple of (from_date, to_date) as Python date objects
        """
        from_date = self.from_date_edit.date().toPython()
        to_date = self.to_date_edit.date().toPython()
        return from_date, to_date
    
    def set_nominal_accounts(self, accounts: List[Dict]):
        """
        Set the nominal accounts list for filtering.
        
        Args:
            accounts: List of nominal account dictionaries
        """
        self._nominal_accounts = accounts
        # Update account combo - only Bank Account and Cash Account types
        current_selection = self.account_combo.currentData()
        self.account_combo.clear()
        self.account_combo.addItem("All", None)
        
        for account in accounts:
            account_type = account.get('account_type', '')
            account_subtype = account.get('account_subtype', '')
            
            # Only include Bank Account or Cash Account types
            if account_type == 'Asset' and account_subtype in ['Bank Account', 'Cash Account']:
                account_text = f"{account.get('account_code', '')} - {account.get('account_name', '')}"
                self.account_combo.addItem(account_text, account.get('id'))
        
        # Also check for Undeposited Funds (Current Asset) and add it if found
        if self._user_id:
            from utils.account_finder import find_undeposited_funds_account
            undeposited_funds_id = find_undeposited_funds_account(self._user_id, self._db_path)
            if undeposited_funds_id:
                # Check if it's already in the combo
                index = self.account_combo.findData(undeposited_funds_id)
                if index < 0:
                    # Find the account in the list and add it
                    for account in accounts:
                        if account.get('id') == undeposited_funds_id:
                            account_text = f"{account.get('account_code', '')} - {account.get('account_name', '')}"
                            self.account_combo.addItem(account_text, undeposited_funds_id)
                            break
        
        # Restore previous selection if it still exists, otherwise set to Undeposited Funds
        if current_selection:
            index = self.account_combo.findData(current_selection)
            if index >= 0:
                self.account_combo.setCurrentIndex(index)
        elif self._user_id:
            from utils.account_finder import find_undeposited_funds_account
            undeposited_funds_id = find_undeposited_funds_account(self._user_id, self._db_path)
            if undeposited_funds_id:
                index = self.account_combo.findData(undeposited_funds_id)
                if index >= 0:
                    self.account_combo.setCurrentIndex(index)
    
    def _handle_apply_filters(self):
        """Handle Apply Filters button click."""
        filter_criteria = self._get_filter_criteria()
        self._current_filters = filter_criteria
        # Emit signal for controller to handle filtering
        # The controller will call load_results when data is ready
        self.filters_applied.emit(filter_criteria)
    
    def _handle_clear_filters(self):
        """Clear all filters to default values."""
        # Set date range to Today
        self.quick_range_combo.setCurrentText("Today")
        today = QDate.currentDate()
        self.from_date_edit.blockSignals(True)
        self.to_date_edit.blockSignals(True)
        self.from_date_edit.setDate(today)
        self.to_date_edit.setDate(today)
        self.from_date_edit.blockSignals(False)
        self.to_date_edit.blockSignals(False)
        
        # Reset other filters
        self.payment_method_combo.setCurrentIndex(0)  # "All"
        self.reconciled_combo.setCurrentText("Unreconciled Only")
        self.posted_status_combo.setCurrentIndex(0)  # "All"
        self.batch_no_entry.clear()
        
        # Reset to Undeposited Funds if available
        if self._user_id:
            from utils.account_finder import find_undeposited_funds_account
            undeposited_funds_id = find_undeposited_funds_account(self._user_id, self._db_path)
            if undeposited_funds_id:
                index = self.account_combo.findData(undeposited_funds_id)
                if index >= 0:
                    self.account_combo.setCurrentIndex(index)
                else:
                    self.account_combo.setCurrentIndex(0)  # "All"
            else:
                self.account_combo.setCurrentIndex(0)  # "All"
        else:
            self.account_combo.setCurrentIndex(0)  # "All"
        
        self.include_customer_payments_check.setChecked(True)
        self.include_supplier_payments_check.setChecked(True)
        self._current_filters = None
    
    def _get_filter_criteria(self) -> Dict:
        """
        Get current filter criteria as a dictionary.
        
        Returns:
            Dictionary containing all filter criteria including date range
        """
        # Date range
        from_date = self.from_date_edit.date().toPython()
        to_date = self.to_date_edit.date().toPython()
        
        # Payment method
        payment_method = self.payment_method_combo.currentText()
        payment_method = None if payment_method == "All" else payment_method
        
        # Reconciled status
        reconciled_status = self.reconciled_combo.currentText()
        if reconciled_status == "All":
            reconciled = None
        elif reconciled_status == "Reconciled Only":
            reconciled = True
        else:  # "Unreconciled Only"
            reconciled = False
        
        # Posted status
        posted_status = self.posted_status_combo.currentText()
        posted = None if posted_status == "All" else (posted_status == "Yes")
        
        # Batch no
        batch_no = self.batch_no_entry.text().strip()
        batch_no = None if not batch_no else batch_no
        
        # Nominal account
        account_id = self.account_combo.currentData()
        
        # Include checkboxes
        include_customer = self.include_customer_payments_check.isChecked()
        include_supplier = self.include_supplier_payments_check.isChecked()
        
        return {
            'from_date': from_date,
            'to_date': to_date,
            'payment_method': payment_method,
            'reconciled': reconciled,
            'posted': posted,
            'posted_batch_no': batch_no,
            'nominal_account_id': account_id,
            'include_customer_payments': include_customer,
            'include_supplier_payments': include_supplier
        }
    
    def load_results(self, results: List[Dict]):
        """
        Load filtered payment results into the results view.
        
        Args:
            results: List of payment dictionaries with all required fields
        """
        self.results_view.load_results(results)
    
    def _handle_cash_up_selected(self, selected_payments: List[Dict]):
        """
        Handle cash up selected signal from results view.
        
        Args:
            selected_payments: List of selected payment dictionaries
        """
        self.cash_up_requested.emit(selected_payments)
    
    def clear_results(self):
        """Clear all results from the view."""
        self.results_view.clear_results()
        self._current_filters = None

