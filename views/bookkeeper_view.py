"""Book Keeper view GUI."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QDialog, QLineEdit, QComboBox, QMessageBox, QHeaderView,
    QDateEdit, QDoubleSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QEvent, QDate
from PySide6.QtGui import QKeyEvent
from typing import List, Dict, Optional, Callable
from views.base_view import BaseTabbedView
from utils.styles import apply_theme
from datetime import date


class AccountsTableWidget(QTableWidget):
    """Custom table widget with Enter key support."""
    
    def __init__(self, enter_callback: Callable[[], None]):
        """Initialize the table widget."""
        super().__init__()
        self.enter_callback = enter_callback
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.selectedItems():
                self.enter_callback()
                event.accept()
                return
        super().keyPressEvent(event)


class BookkeeperView(BaseTabbedView):
    """Book Keeper management GUI."""
    
    # Additional signals beyond base class
    create_account_requested = Signal(int, str, str, float, bool)
    update_account_requested = Signal(int, int, str, str, float, bool)
    delete_account_requested = Signal(int)
    transfer_funds_requested = Signal(int, int, float, str, str, str)  # from_account_id, to_account_id, amount, description, date_str, reference
    transfer_accounts_requested = Signal()  # Request accounts for transfer dialog
    refresh_requested = Signal()
    
    def __init__(self):
        """Initialize the bookkeeper view."""
        super().__init__(title="Book Keeper", current_view="bookkeeper")
        self.selected_account_id: Optional[int] = None
        self._transfer_dialog = None  # Store reference to transfer dialog
        self._create_widgets()
        self._setup_keyboard_navigation()
    
    def _create_widgets(self):
        """Create and layout UI widgets."""
        # Add action buttons using base class method
        self.add_account_button = self.add_action_button(
            "Add Account (Ctrl+N)", 
            self._handle_add_account,
            "Ctrl+N"
        )
        
        self.transfer_button = self.add_action_button(
            "Transfer Funds (Ctrl+T)",
            self._handle_transfer_funds,
            "Ctrl+T"
        )
        
        # Create tabs widget
        self.tab_widget = self.create_tabs()
        
        # Tab 1: Chart of Accounts
        accounts_widget = QWidget()
        accounts_layout = QVBoxLayout(accounts_widget)
        accounts_layout.setSpacing(20)
        accounts_layout.setContentsMargins(0, 0, 0, 0)
        
        # Accounts table
        self.accounts_table = AccountsTableWidget(self._switch_to_activity_tab)
        self.accounts_table.setColumnCount(5)
        self.accounts_table.setHorizontalHeaderLabels(["Code", "Name", "Type", "Balance", "Bank"])
        self.accounts_table.horizontalHeader().setStretchLastSection(True)
        self.accounts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.accounts_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.accounts_table.setAlternatingRowColors(True)
        self.accounts_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Set column widths
        header = self.accounts_table.horizontalHeader()
        header.resizeSection(0, 100)
        header.resizeSection(1, 250)
        header.resizeSection(2, 120)
        header.resizeSection(3, 120)
        header.resizeSection(4, 60)
        
        # Enable keyboard navigation
        self.accounts_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Selection changed - update activity panel
        self.accounts_table.itemSelectionChanged.connect(self._on_account_selection_changed)
        
        # Double-click to edit
        self.accounts_table.itemDoubleClicked.connect(self._on_table_double_click)
        
        accounts_layout.addWidget(self.accounts_table)
        
        self.add_tab(accounts_widget, "Chart of Accounts (Ctrl+1)", "Ctrl+1")
        
        # Tab 2: Account Activity
        activity_widget = QWidget()
        activity_layout = QVBoxLayout(activity_widget)
        activity_layout.setSpacing(20)
        activity_layout.setContentsMargins(0, 0, 0, 0)
        
        # Activity table
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(6)
        self.activity_table.setHorizontalHeaderLabels(["Date", "Description", "Debit", "Credit", "Balance", "Ref"])
        self.activity_table.horizontalHeader().setStretchLastSection(True)
        self.activity_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.activity_table.setAlternatingRowColors(True)
        self.activity_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Set column widths
        activity_header = self.activity_table.horizontalHeader()
        activity_header.resizeSection(0, 100)
        activity_header.resizeSection(1, 200)
        activity_header.resizeSection(2, 100)
        activity_header.resizeSection(3, 100)
        activity_header.resizeSection(4, 100)
        
        activity_layout.addWidget(self.activity_table)
        
        self.add_tab(activity_widget, "Account Activity (Ctrl+2)", "Ctrl+2")
        
        # Set Chart of Accounts tab as the default (first tab)
        self.tab_widget.setCurrentIndex(0)
    
    def _setup_keyboard_navigation(self):
        """Set up keyboard navigation."""
        # Tab order: Table -> Add Account -> Transfer -> Navigation panel
        self.setTabOrder(self.accounts_table, self.add_account_button)
        self.setTabOrder(self.add_account_button, self.transfer_button)
        self.setTabOrder(self.transfer_button, self.nav_panel.logout_button)
        
        # Arrow keys work automatically in QTableWidget
        self.accounts_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def showEvent(self, event: QEvent):
        """Handle show event - set focus to table if it has data."""
        super().showEvent(event)
        # Ensure Chart of Accounts tab is shown first
        self.tab_widget.setCurrentIndex(0)
        # Set focus to table if it has rows
        if self.accounts_table.rowCount() > 0:
            self.accounts_table.setFocus()
            # Ensure first row is selected if nothing is selected
            if not self.accounts_table.selectedItems():
                self.accounts_table.selectRow(0)
    
    def _handle_add_account(self):
        """Handle Add Account button click."""
        self.add_account()
    
    def _handle_transfer_funds(self):
        """Handle Transfer Funds button click."""
        self.transfer_funds()
    
    def _on_table_double_click(self, item: QTableWidgetItem):
        """Handle double-click on table item."""
        self._open_selected_account()
    
    def _on_account_selection_changed(self):
        """Handle account selection change - update selected account ID only (don't switch tabs)."""
        selected_items = self.accounts_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            account_id_item = self.accounts_table.item(row, 0)
            if account_id_item:
                # Get account ID from data (stored in item data)
                account_id = account_id_item.data(Qt.ItemDataRole.UserRole)
                if account_id:
                    self.selected_account_id = account_id
                    # Only refresh if we're already on the activity tab
                    if self.tab_widget.currentIndex() == 1:
                        self.refresh_requested.emit()
    
    def _switch_to_activity_tab(self):
        """Switch to activity tab for the currently selected account (called by Enter key)."""
        selected_items = self.accounts_table.selectedItems()
        if not selected_items:
            return
        
        row = selected_items[0].row()
        account_id_item = self.accounts_table.item(row, 0)
        if account_id_item:
            account_id = account_id_item.data(Qt.ItemDataRole.UserRole)
            if account_id:
                self.selected_account_id = account_id
                # Switch to activity tab and refresh
                self.tab_widget.setCurrentIndex(1)
                self.refresh_requested.emit()
    
    def _open_selected_account(self):
        """Open details dialog for the currently selected account (called by double-click)."""
        selected_items = self.accounts_table.selectedItems()
        if not selected_items:
            return
        
        row = selected_items[0].row()
        account_id = self.accounts_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        account_code = self.accounts_table.item(row, 0).text()
        account_name = self.accounts_table.item(row, 1).text()
        account_type = self.accounts_table.item(row, 2).text()
        balance_item = self.accounts_table.item(row, 3)
        balance = float(balance_item.text().replace('£', '').replace(',', '')) if balance_item else 0.0
        is_bank = self.accounts_table.item(row, 4).text() == "Yes"
        
        self._show_account_details(account_id, account_code, account_name, account_type, balance, is_bank)
    
    def _show_account_details(self, account_id: int, account_code: str, account_name: str, 
                              account_type: str, balance: float, is_bank: bool):
        """Show account details in a popup dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Account Details")
        dialog.setModal(True)
        dialog.setMinimumSize(600, 500)
        dialog.resize(600, 500)
        apply_theme(dialog)
        
        # Add Escape key shortcut for cancel
        esc_shortcut = QShortcut(QKeySequence("Escape"), dialog)
        esc_shortcut.activated.connect(dialog.reject)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("Account Information")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Account Code
        code_layout = QHBoxLayout()
        code_label = QLabel("Account Code:")
        code_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        code_label.setMinimumWidth(150)
        code_layout.addWidget(code_label)
        code_entry = QLineEdit(account_code)
        code_entry.setStyleSheet("font-size: 12px;")
        code_layout.addWidget(code_entry, stretch=1)
        layout.addLayout(code_layout)
        
        # Account Name
        name_layout = QHBoxLayout()
        name_label = QLabel("Account Name:")
        name_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        name_label.setMinimumWidth(150)
        name_layout.addWidget(name_label)
        name_entry = QLineEdit(account_name)
        name_entry.setStyleSheet("font-size: 12px;")
        name_layout.addWidget(name_entry, stretch=1)
        layout.addLayout(name_layout)
        
        # Account Type
        type_layout = QHBoxLayout()
        type_label = QLabel("Account Type:")
        type_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        type_label.setMinimumWidth(150)
        type_layout.addWidget(type_label)
        type_combo = QComboBox()
        type_combo.setStyleSheet("font-size: 12px;")
        type_combo.addItems(["Asset", "Liability", "Equity", "Income", "Expense"])
        type_combo.setCurrentText(account_type)
        type_layout.addWidget(type_combo, stretch=1)
        layout.addLayout(type_layout)
        
        # Opening Balance
        balance_layout = QHBoxLayout()
        balance_label = QLabel("Opening Balance:")
        balance_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        balance_label.setMinimumWidth(150)
        balance_layout.addWidget(balance_label)
        balance_entry = QDoubleSpinBox()
        balance_entry.setStyleSheet("font-size: 12px;")
        balance_entry.setRange(-999999999.99, 999999999.99)
        balance_entry.setDecimals(2)
        balance_entry.setPrefix("£ ")
        balance_entry.setValue(balance)
        balance_layout.addWidget(balance_entry, stretch=1)
        layout.addLayout(balance_layout)
        
        # Is Bank Account
        bank_layout = QHBoxLayout()
        bank_checkbox = QCheckBox("Bank Account (for future reconciliation)")
        bank_checkbox.setChecked(is_bank)
        bank_checkbox.setStyleSheet("font-size: 12px;")
        bank_layout.addWidget(bank_checkbox)
        bank_layout.addStretch()
        layout.addLayout(bank_layout)
        
        layout.addStretch()
        
        # Button frame
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        def handle_save():
            try:
                new_code = int(code_entry.text().strip())
            except ValueError:
                QMessageBox.critical(dialog, "Error", "Account code must be a number")
                return
            
            new_name = name_entry.text().strip()
            new_type = type_combo.currentText()
            new_balance = balance_entry.value()
            new_is_bank = bank_checkbox.isChecked()
            
            if not new_name:
                QMessageBox.critical(dialog, "Error", "Please enter an account name")
                return
            
            self.update_account_requested.emit(account_id, new_code, new_name, new_type, new_balance, new_is_bank)
            dialog.accept()
        
        def handle_delete():
            reply = QMessageBox.question(
                dialog,
                "Confirm Delete",
                f"Are you sure you want to delete account '{name_entry.text()}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                dialog.accept()
                self.delete_account_requested.emit(account_id)
        
        save_btn = QPushButton("Save Changes (Ctrl+Enter)")
        save_btn.setMinimumWidth(200)
        save_btn.setMinimumHeight(30)
        save_btn.setDefault(True)
        save_btn.clicked.connect(handle_save)
        
        # Ctrl+Enter shortcut for save
        ctrl_enter_shortcut = QShortcut(QKeySequence("Ctrl+Return"), dialog)
        ctrl_enter_shortcut.activated.connect(handle_save)
        button_layout.addWidget(save_btn)
        
        delete_btn = QPushButton("Delete Account (Ctrl+Shift+D)")
        delete_btn.setMinimumWidth(220)
        delete_btn.setMinimumHeight(30)
        delete_btn.clicked.connect(handle_delete)
        
        # Ctrl+Shift+D shortcut for delete
        delete_shortcut = QShortcut(QKeySequence("Ctrl+Shift+D"), dialog)
        delete_shortcut.activated.connect(handle_delete)
        button_layout.addWidget(delete_btn)
        
        cancel_btn = QPushButton("Cancel (Esc)")
        cancel_btn.setMinimumWidth(140)
        cancel_btn.setMinimumHeight(30)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Set focus to account code entry
        code_entry.setFocus()
        code_entry.selectAll()
        
        # Show dialog
        dialog.exec()
    
    def add_account(self):
        """Show dialog for adding a new account."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Account")
        dialog.setModal(True)
        dialog.setMinimumSize(500, 400)
        dialog.resize(500, 400)
        apply_theme(dialog)
        
        # Add Escape key shortcut for cancel
        esc_shortcut = QShortcut(QKeySequence("Escape"), dialog)
        esc_shortcut.activated.connect(dialog.reject)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("Add New Account")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Account Code
        code_layout = QHBoxLayout()
        code_label = QLabel("Account Code:")
        code_label.setMinimumWidth(150)
        code_label.setStyleSheet("font-size: 11px;")
        code_layout.addWidget(code_label)
        code_entry = QLineEdit()
        code_entry.setStyleSheet("font-size: 11px;")
        code_entry.setPlaceholderText("e.g., 1000 for Assets")
        code_layout.addWidget(code_entry, stretch=1)
        layout.addLayout(code_layout)
        
        # Account Name
        name_layout = QHBoxLayout()
        name_label = QLabel("Account Name:")
        name_label.setMinimumWidth(150)
        name_label.setStyleSheet("font-size: 11px;")
        name_layout.addWidget(name_label)
        name_entry = QLineEdit()
        name_entry.setStyleSheet("font-size: 11px;")
        name_layout.addWidget(name_entry, stretch=1)
        layout.addLayout(name_layout)
        
        # Account Type
        type_layout = QHBoxLayout()
        type_label = QLabel("Account Type:")
        type_label.setMinimumWidth(150)
        type_label.setStyleSheet("font-size: 11px;")
        type_layout.addWidget(type_label)
        type_combo = QComboBox()
        type_combo.setStyleSheet("font-size: 11px;")
        type_combo.addItems(["Asset", "Liability", "Equity", "Income", "Expense"])
        type_layout.addWidget(type_combo, stretch=1)
        layout.addLayout(type_layout)
        
        # Opening Balance
        balance_layout = QHBoxLayout()
        balance_label = QLabel("Opening Balance:")
        balance_label.setMinimumWidth(150)
        balance_label.setStyleSheet("font-size: 11px;")
        balance_layout.addWidget(balance_label)
        balance_entry = QDoubleSpinBox()
        balance_entry.setStyleSheet("font-size: 11px;")
        balance_entry.setRange(-999999999.99, 999999999.99)
        balance_entry.setDecimals(2)
        balance_entry.setPrefix("£ ")
        balance_entry.setValue(0.0)
        balance_layout.addWidget(balance_entry, stretch=1)
        layout.addLayout(balance_layout)
        
        # Is Bank Account
        bank_layout = QHBoxLayout()
        bank_checkbox = QCheckBox("Bank Account (for future reconciliation)")
        bank_checkbox.setStyleSheet("font-size: 11px;")
        bank_layout.addWidget(bank_checkbox)
        bank_layout.addStretch()
        layout.addLayout(bank_layout)
        
        # Status label
        status_label = QLabel("")
        status_label.setStyleSheet("color: red; font-size: 9px;")
        layout.addWidget(status_label)
        
        layout.addStretch()
        
        # Button frame
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        def handle_save():
            try:
                account_code = int(code_entry.text().strip())
            except ValueError:
                status_label.setText("Account code must be a number")
                return
            
            account_name = name_entry.text().strip()
            account_type = type_combo.currentText()
            opening_balance = balance_entry.value()
            is_bank = bank_checkbox.isChecked()
            
            if not account_name:
                status_label.setText("Please enter an account name")
                return
            
            self.create_account_requested.emit(account_code, account_name, account_type, opening_balance, is_bank)
            dialog.accept()
        
        save_btn = QPushButton("Save (Ctrl+Enter)")
        save_btn.setMinimumWidth(160)
        save_btn.setMinimumHeight(30)
        save_btn.setDefault(True)
        save_btn.clicked.connect(handle_save)
        
        # Ctrl+Enter shortcut for save
        ctrl_enter_shortcut = QShortcut(QKeySequence("Ctrl+Return"), dialog)
        ctrl_enter_shortcut.activated.connect(handle_save)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel (Esc)")
        cancel_btn.setMinimumWidth(140)
        cancel_btn.setMinimumHeight(30)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Set focus to account code entry
        code_entry.setFocus()
        
        # Show dialog
        dialog.exec()
    
    def transfer_funds(self):
        """Show dialog for transferring funds between accounts."""
        dialog = QDialog(self)
        self._transfer_dialog = dialog  # Store reference
        dialog.setWindowTitle("Transfer Funds")
        dialog.setModal(True)
        apply_theme(dialog)
        dialog.setMinimumSize(500, 400)
        dialog.resize(500, 400)
        
        # Add Escape key shortcut for cancel
        esc_shortcut = QShortcut(QKeySequence("Escape"), dialog)
        esc_shortcut.activated.connect(dialog.reject)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("Transfer Funds Between Accounts")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # From Account
        from_layout = QHBoxLayout()
        from_label = QLabel("From Account:")
        from_label.setMinimumWidth(150)
        from_label.setStyleSheet("font-size: 11px;")
        from_layout.addWidget(from_label)
        from_combo = QComboBox()
        from_combo.setStyleSheet("font-size: 11px;")
        from_combo.setEditable(False)
        from_layout.addWidget(from_combo, stretch=1)
        layout.addLayout(from_layout)
        
        # To Account
        to_layout = QHBoxLayout()
        to_label = QLabel("To Account:")
        to_label.setMinimumWidth(150)
        to_label.setStyleSheet("font-size: 11px;")
        to_layout.addWidget(to_label)
        to_combo = QComboBox()
        to_combo.setStyleSheet("font-size: 11px;")
        to_combo.setEditable(False)
        to_layout.addWidget(to_combo, stretch=1)
        layout.addLayout(to_layout)
        
        # Amount
        amount_layout = QHBoxLayout()
        amount_label = QLabel("Amount:")
        amount_label.setMinimumWidth(150)
        amount_label.setStyleSheet("font-size: 11px;")
        amount_layout.addWidget(amount_label)
        amount_entry = QDoubleSpinBox()
        amount_entry.setStyleSheet("font-size: 11px;")
        amount_entry.setRange(0.01, 999999999.99)
        amount_entry.setDecimals(2)
        amount_entry.setPrefix("£ ")
        amount_entry.setValue(0.0)
        amount_layout.addWidget(amount_entry, stretch=1)
        layout.addLayout(amount_layout)
        
        # Date
        date_layout = QHBoxLayout()
        date_label = QLabel("Date:")
        date_label.setMinimumWidth(150)
        date_label.setStyleSheet("font-size: 11px;")
        date_layout.addWidget(date_label)
        date_entry = QDateEdit()
        date_entry.setStyleSheet("font-size: 11px;")
        date_entry.setCalendarPopup(True)
        date_entry.setDate(QDate.currentDate())
        date_layout.addWidget(date_entry, stretch=1)
        layout.addLayout(date_layout)
        
        # Description
        desc_layout = QHBoxLayout()
        desc_label = QLabel("Description:")
        desc_label.setMinimumWidth(150)
        desc_label.setStyleSheet("font-size: 11px;")
        desc_layout.addWidget(desc_label)
        desc_entry = QLineEdit()
        desc_entry.setStyleSheet("font-size: 11px;")
        desc_entry.setPlaceholderText("e.g., Transfer to operating account")
        desc_layout.addWidget(desc_entry, stretch=1)
        layout.addLayout(desc_layout)
        
        # Reference
        ref_layout = QHBoxLayout()
        ref_label = QLabel("Reference (optional):")
        ref_label.setMinimumWidth(150)
        ref_label.setStyleSheet("font-size: 11px;")
        ref_layout.addWidget(ref_label)
        ref_entry = QLineEdit()
        ref_entry.setStyleSheet("font-size: 11px;")
        ref_layout.addWidget(ref_entry, stretch=1)
        layout.addLayout(ref_layout)
        
        # Status label
        status_label = QLabel("")
        status_label.setStyleSheet("color: red; font-size: 9px;")
        layout.addWidget(status_label)
        
        layout.addStretch()
        
        # Button frame
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        def handle_transfer():
            from_account_id = from_combo.currentData()
            to_account_id = to_combo.currentData()
            amount = amount_entry.value()
            transfer_date = date_entry.date().toPython()
            description = desc_entry.text().strip()
            reference = ref_entry.text().strip() or None
            
            if not from_account_id or not to_account_id:
                status_label.setText("Please select both accounts")
                return
            
            if from_account_id == to_account_id:
                status_label.setText("From and To accounts cannot be the same")
                return
            
            if amount <= 0:
                status_label.setText("Amount must be greater than zero")
                return
            
            if not description:
                status_label.setText("Please enter a description")
                return
            
            from_account_name = from_combo.currentText()
            to_account_name = to_combo.currentText()
            
            self.transfer_funds_requested.emit(
                from_account_id, to_account_id, amount, description, 
                transfer_date.isoformat(), reference if reference else ""
            )
            dialog.accept()
        
        transfer_btn = QPushButton("Transfer (Ctrl+Enter)")
        transfer_btn.setMinimumWidth(160)
        transfer_btn.setMinimumHeight(30)
        transfer_btn.setDefault(True)
        transfer_btn.clicked.connect(handle_transfer)
        
        # Ctrl+Enter shortcut for transfer
        ctrl_enter_shortcut = QShortcut(QKeySequence("Ctrl+Return"), dialog)
        ctrl_enter_shortcut.activated.connect(handle_transfer)
        button_layout.addWidget(transfer_btn)
        
        cancel_btn = QPushButton("Cancel (Esc)")
        cancel_btn.setMinimumWidth(140)
        cancel_btn.setMinimumHeight(30)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Set focus to from account combo
        from_combo.setFocus()
        
        # Store combos for controller to populate
        dialog.from_combo = from_combo
        dialog.to_combo = to_combo
        
        # Request accounts to populate combos
        self.transfer_accounts_requested.emit()
        
        # Show dialog
        result = dialog.exec()
        self._transfer_dialog = None  # Clear reference after dialog closes
        return result
    
    def load_accounts(self, accounts: List[Dict[str, any]]):
        """Load accounts into the table."""
        self.accounts_table.setRowCount(len(accounts))
        
        for row, account in enumerate(accounts):
            # Store account ID in first item's user data
            code_item = QTableWidgetItem(str(account['account_code']))
            code_item.setData(Qt.ItemDataRole.UserRole, account['id'])
            self.accounts_table.setItem(row, 0, code_item)
            
            self.accounts_table.setItem(row, 1, QTableWidgetItem(account.get('account_name', '')))
            self.accounts_table.setItem(row, 2, QTableWidgetItem(account.get('account_type', '')))
            
            # Format balance with currency
            balance = account.get('current_balance', 0.0)
            balance_item = QTableWidgetItem(f"£{balance:,.2f}")
            balance_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.accounts_table.setItem(row, 3, balance_item)
            
            # Bank account indicator
            is_bank = "Yes" if account.get('is_bank_account', 0) else "No"
            self.accounts_table.setItem(row, 4, QTableWidgetItem(is_bank))
        
        # Resize columns to content
        self.accounts_table.resizeColumnsToContents()
        header = self.accounts_table.horizontalHeader()
        header.resizeSection(0, 100)
        header.resizeSection(1, 250)
        header.resizeSection(2, 120)
        header.resizeSection(3, 120)
        header.resizeSection(4, 60)
        
        # Auto-select first row and set focus to table if data exists
        if len(accounts) > 0:
            self.accounts_table.selectRow(0)
            self.accounts_table.setFocus()
            # Ensure the first row is visible
            self.accounts_table.scrollToItem(self.accounts_table.item(0, 0))
            # Trigger selection changed to load activity
            self._on_account_selection_changed()
    
    def load_activity(self, entries: List[Dict[str, any]], account_id: int):
        """Load journal entries into the activity table."""
        self.activity_table.setRowCount(len(entries))
        
        running_balance = 0.0
        
        # Get account type to determine balance calculation direction
        # This will be passed from controller or calculated here
        
        for row, entry in enumerate(entries):
            # Date
            entry_date = entry.get('entry_date', '')
            if isinstance(entry_date, date):
                date_str = entry_date.strftime('%Y-%m-%d')
            else:
                date_str = str(entry_date)
            self.activity_table.setItem(row, 0, QTableWidgetItem(date_str))
            
            # Description
            self.activity_table.setItem(row, 1, QTableWidgetItem(entry.get('description', '')))
            
            # Debit/Credit
            amount = entry.get('amount', 0.0)
            is_debit = entry.get('is_debit', False)
            is_credit = entry.get('is_credit', False)
            
            if is_debit:
                debit_item = QTableWidgetItem(f"£{amount:,.2f}")
                debit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.activity_table.setItem(row, 2, debit_item)
                self.activity_table.setItem(row, 3, QTableWidgetItem(""))
                running_balance += amount  # Simplified - actual depends on account type
            elif is_credit:
                self.activity_table.setItem(row, 2, QTableWidgetItem(""))
                credit_item = QTableWidgetItem(f"£{amount:,.2f}")
                credit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.activity_table.setItem(row, 3, credit_item)
                running_balance -= amount  # Simplified - actual depends on account type
            
            # Balance (running balance)
            balance_item = QTableWidgetItem(f"£{running_balance:,.2f}")
            balance_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.activity_table.setItem(row, 4, balance_item)
            
            # Reference
            ref = entry.get('reference', '')
            self.activity_table.setItem(row, 5, QTableWidgetItem(ref if ref else ""))
        
        # Resize columns
        self.activity_table.resizeColumnsToContents()
        activity_header = self.activity_table.horizontalHeader()
        activity_header.resizeSection(0, 100)
        activity_header.resizeSection(1, 200)
        activity_header.resizeSection(2, 100)
        activity_header.resizeSection(3, 100)
        activity_header.resizeSection(4, 100)
    
    def populate_transfer_accounts(self, accounts: List[Dict[str, any]], from_combo: QComboBox, to_combo: QComboBox):
        """Populate account combos in transfer dialog."""
        from_combo.clear()
        to_combo.clear()
        
        for account in accounts:
            account_text = f"{account['account_code']} - {account['account_name']}"
            from_combo.addItem(account_text, account['id'])
            to_combo.addItem(account_text, account['id'])
    
    def show_success_dialog(self, message: str):
        """Show a success dialog."""
        QMessageBox.information(self, "Success", message)
    
    def show_error_dialog(self, message: str):
        """Show an error dialog."""
        QMessageBox.critical(self, "Error", message)

