"""Cash Up Filter Dialog for filtering payments in the cash up process."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QCheckBox, QLineEdit, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QShortcut, QKeySequence, QKeyEvent
from typing import Optional, List, Dict
from utils.styles import apply_theme


class CashUpFilterDialog(QDialog):
    """Dialog for filtering payments in the cash up process."""
    
    # Signal emitted when filter is applied, with filter criteria
    filters_applied = Signal(dict)
    
    def __init__(self, parent=None, nominal_accounts: Optional[List[Dict]] = None):
        """
        Initialize the cash up filter dialog.
        
        Args:
            parent: Parent widget
            nominal_accounts: Optional list of nominal accounts for filtering
        """
        super().__init__(parent)
        self.setWindowTitle("Cash Up Filter")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        self.resize(550, 450)
        apply_theme(self)
        self._nominal_accounts = nominal_accounts or []
        self._create_widgets()
        self._setup_keyboard_shortcuts()
    
    def _create_widgets(self):
        """Create and layout UI widgets."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("Cash Up Filter")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Payment Method Filter
        payment_method_layout = QHBoxLayout()
        payment_method_label = QLabel("Payment Method:")
        payment_method_label.setMinimumWidth(180)
        payment_method_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        payment_method_layout.addWidget(payment_method_label)
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.setStyleSheet("font-size: 12px;")
        self.payment_method_combo.addItems(["All", "Cash", "Card", "Cheque", "BACS"])
        payment_method_layout.addWidget(self.payment_method_combo, stretch=1)
        layout.addLayout(payment_method_layout)
        
        # Reconciled Status Filter
        reconciled_layout = QHBoxLayout()
        reconciled_label = QLabel("Reconciled Status:")
        reconciled_label.setMinimumWidth(180)
        reconciled_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        reconciled_layout.addWidget(reconciled_label)
        self.reconciled_combo = QComboBox()
        self.reconciled_combo.setStyleSheet("font-size: 12px;")
        self.reconciled_combo.addItems(["All", "Yes", "No"])
        reconciled_layout.addWidget(self.reconciled_combo, stretch=1)
        layout.addLayout(reconciled_layout)
        
        # Posted Status Filter
        posted_status_layout = QHBoxLayout()
        posted_status_label = QLabel("Posted Status:")
        posted_status_label.setMinimumWidth(180)
        posted_status_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        posted_status_layout.addWidget(posted_status_label)
        self.posted_status_combo = QComboBox()
        self.posted_status_combo.setStyleSheet("font-size: 12px;")
        self.posted_status_combo.addItems(["All", "Yes", "No"])
        posted_status_layout.addWidget(self.posted_status_combo, stretch=1)
        layout.addLayout(posted_status_layout)
        
        # Posted Batch No Filter
        batch_no_layout = QHBoxLayout()
        batch_no_label = QLabel("Posted Batch No:")
        batch_no_label.setMinimumWidth(180)
        batch_no_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        batch_no_layout.addWidget(batch_no_label)
        self.batch_no_entry = QLineEdit()
        self.batch_no_entry.setStyleSheet("font-size: 12px;")
        self.batch_no_entry.setPlaceholderText("Enter batch number or leave blank for all")
        batch_no_layout.addWidget(self.batch_no_entry, stretch=1)
        layout.addLayout(batch_no_layout)
        
        # Nominal Account Filter
        account_layout = QHBoxLayout()
        account_label = QLabel("Nominal Account:")
        account_label.setMinimumWidth(180)
        account_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        account_layout.addWidget(account_label)
        self.account_combo = QComboBox()
        self.account_combo.setStyleSheet("font-size: 12px;")
        self.account_combo.setEditable(False)
        self.account_combo.addItem("All", None)
        # Populate with nominal accounts
        for account in self._nominal_accounts:
            account_text = f"{account.get('account_code', '')} - {account.get('account_name', '')}"
            self.account_combo.addItem(account_text, account.get('id'))
        account_layout.addWidget(self.account_combo, stretch=1)
        layout.addLayout(account_layout)
        
        # Include Customer Payments Checkbox
        self.include_customer_payments_check = QCheckBox("Include Customer Payments")
        self.include_customer_payments_check.setStyleSheet("font-size: 12px;")
        self.include_customer_payments_check.setChecked(True)
        layout.addWidget(self.include_customer_payments_check)
        
        # Include Supplier Payments Checkbox
        self.include_supplier_payments_check = QCheckBox("Include Supplier Payments")
        self.include_supplier_payments_check.setStyleSheet("font-size: 12px;")
        self.include_supplier_payments_check.setChecked(True)
        layout.addWidget(self.include_supplier_payments_check)
        
        layout.addStretch()
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Apply button
        apply_btn = QPushButton("Apply Filter (Ctrl+Enter)")
        apply_btn.setMinimumWidth(180)
        apply_btn.setMinimumHeight(30)
        apply_btn.setDefault(True)
        apply_btn.clicked.connect(self._handle_apply)
        button_layout.addWidget(apply_btn)
        
        # Clear button
        clear_btn = QPushButton("Clear All")
        clear_btn.setMinimumWidth(140)
        clear_btn.setMinimumHeight(30)
        clear_btn.clicked.connect(self._handle_clear)
        button_layout.addWidget(clear_btn)
        
        # Cancel button
        cancel_btn = QPushButton("Cancel (Esc)")
        cancel_btn.setMinimumWidth(140)
        cancel_btn.setMinimumHeight(30)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Set focus to payment method combo
        self.payment_method_combo.setFocus()
    
    def _setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts."""
        # Escape to cancel
        esc_shortcut = QShortcut(QKeySequence("Escape"), self)
        esc_shortcut.activated.connect(self.reject)
        
        # Ctrl+Enter to apply
        ctrl_enter_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        ctrl_enter_shortcut.activated.connect(self._handle_apply)
    
    def _handle_apply(self):
        """Handle apply filter button click."""
        filter_criteria = self._get_filter_criteria()
        self.filters_applied.emit(filter_criteria)
        self.accept()
    
    def _handle_clear(self):
        """Clear all filters to default values."""
        self.payment_method_combo.setCurrentIndex(0)  # "All"
        self.reconciled_combo.setCurrentIndex(0)  # "All"
        self.posted_status_combo.setCurrentIndex(0)  # "All"
        self.batch_no_entry.clear()
        self.account_combo.setCurrentIndex(0)  # "All"
        self.include_customer_payments_check.setChecked(True)
        self.include_supplier_payments_check.setChecked(True)
    
    def _get_filter_criteria(self) -> Dict:
        """
        Get current filter criteria as a dictionary.
        
        Returns:
            Dictionary containing all filter criteria
        """
        payment_method = self.payment_method_combo.currentText()
        payment_method = None if payment_method == "All" else payment_method
        
        reconciled_status = self.reconciled_combo.currentText()
        reconciled = None if reconciled_status == "All" else (reconciled_status == "Yes")
        
        posted_status = self.posted_status_combo.currentText()
        posted = None if posted_status == "All" else (posted_status == "Yes")
        
        batch_no = self.batch_no_entry.text().strip()
        batch_no = None if not batch_no else batch_no
        
        account_id = self.account_combo.currentData()
        
        include_customer = self.include_customer_payments_check.isChecked()
        include_supplier = self.include_supplier_payments_check.isChecked()
        
        return {
            'payment_method': payment_method,
            'reconciled': reconciled,
            'posted': posted,
            'posted_batch_no': batch_no,
            'nominal_account_id': account_id,
            'include_customer_payments': include_customer,
            'include_supplier_payments': include_supplier
        }
    
    def set_nominal_accounts(self, accounts: List[Dict]):
        """
        Update the nominal accounts list.
        
        Args:
            accounts: List of nominal account dictionaries
        """
        self._nominal_accounts = accounts
        current_selection = self.account_combo.currentData()
        
        self.account_combo.clear()
        self.account_combo.addItem("All", None)
        
        for account in accounts:
            account_text = f"{account.get('account_code', '')} - {account.get('account_name', '')}"
            account_id = account.get('id')
            self.account_combo.addItem(account_text, account_id)
        
        # Restore previous selection if it still exists
        if current_selection:
            index = self.account_combo.findData(current_selection)
            if index >= 0:
                self.account_combo.setCurrentIndex(index)

