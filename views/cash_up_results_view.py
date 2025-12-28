"""Cash Up Results View - Table displaying filtered payment results."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QCheckBox, QHeaderView, QLabel, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from typing import List, Dict, Optional
from utils.styles import apply_theme


class CashUpResultsTable(QTableWidget):
    """Table widget for displaying cash up results with checkbox selection."""
    
    def __init__(self, parent=None):
        """Initialize the cash up results table."""
        super().__init__(parent)
        self._setup_table()
        self._payment_data: List[Dict] = []  # Store payment data for each row
    
    def _setup_table(self):
        """Set up the table structure and appearance."""
        # Column order: Checkbox, Date, Type, Account Number, Name, Reference, 
        # External Reference, Financial Account, Batch No, Payment Method, Amount, Allocated
        self.setColumnCount(12)
        self.setHorizontalHeaderLabels([
            "",  # Checkbox
            "Date",
            "Type",
            "Account Number",
            "Name",
            "Reference",
            "External Reference",
            "Financial Account",
            "Batch No",
            "Payment Method",
            "Amount",
            "Allocated"
        ])
        
        # Set column resize modes
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Checkbox
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Date
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Type
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Account Number
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Name
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Reference
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # External Reference
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Financial Account
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # Batch No
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)  # Payment Method
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.Fixed)  # Amount
        header.setSectionResizeMode(11, QHeaderView.ResizeMode.Fixed)  # Allocated
        
        # Set column widths
        header.resizeSection(0, 40)   # Checkbox
        header.resizeSection(1, 100)  # Date
        header.resizeSection(2, 120)  # Type
        header.resizeSection(9, 100)  # Payment Method
        header.resizeSection(10, 100)  # Amount
        header.resizeSection(11, 80)   # Allocated
        
        # Table settings
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Enable sorting
        self.setSortingEnabled(True)
    
    def load_results(self, results: List[Dict]):
        """
        Load payment results into the table.
        
        Args:
            results: List of payment dictionaries with all required fields
        """
        self.clearContents()
        self.setRowCount(len(results))
        self._payment_data = results
        
        for row, payment in enumerate(results):
            # Store payment data for row lookup
            payment_id = payment.get('id')
            payment_type = payment.get('type', '')  # 'Customer Payment' or 'Supplier Payment'
            
            # Checkbox column (column 0)
            checkbox = QCheckBox()
            checkbox.setStyleSheet("padding-left: 10px;")
            # Store payment ID in checkbox for easy retrieval
            checkbox.setProperty('payment_id', payment_id)
            checkbox.setProperty('payment_type', payment_type)
            self.setCellWidget(row, 0, checkbox)
            
            # Date (column 1)
            date_str = payment.get('payment_date', '')
            if hasattr(date_str, 'strftime'):  # If it's a date object
                date_str = date_str.strftime('%Y-%m-%d')
            self.setItem(row, 1, QTableWidgetItem(str(date_str)))
            
            # Type (column 2) - Customer Payment or Supplier Payment
            self.setItem(row, 2, QTableWidgetItem(payment_type))
            
            # Account Number (column 3)
            account_number = payment.get('account_number', '')
            self.setItem(row, 3, QTableWidgetItem(str(account_number)))
            
            # Name (column 4)
            name = payment.get('name', '')
            self.setItem(row, 4, QTableWidgetItem(str(name)))
            
            # Reference (column 5)
            reference = payment.get('reference', '')
            self.setItem(row, 5, QTableWidgetItem(str(reference)))
            
            # External Reference (column 6) - may not exist in current schema
            external_ref = payment.get('external_reference', '')
            self.setItem(row, 6, QTableWidgetItem(str(external_ref)))
            
            # Financial Account (column 7) - e.g., "Undeposited Funds"
            financial_account = payment.get('financial_account', '')
            self.setItem(row, 7, QTableWidgetItem(str(financial_account)))
            
            # Batch No (column 8) - may not exist in current schema
            batch_no = payment.get('batch_no', '')
            self.setItem(row, 8, QTableWidgetItem(str(batch_no)))
            
            # Payment Method (column 9)
            payment_method = payment.get('payment_method', 'Cash')
            self.setItem(row, 9, QTableWidgetItem(str(payment_method)))
            
            # Amount (column 10)
            amount = payment.get('amount', 0.0)
            amount_item = QTableWidgetItem(f"£{amount:,.2f}")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            # Store numeric value for sorting
            amount_item.setData(Qt.ItemDataRole.UserRole, amount)
            self.setItem(row, 10, amount_item)
            
            # Allocated (column 11) - show check mark or empty
            is_allocated = payment.get('is_allocated', False)
            allocated_item = QTableWidgetItem()
            allocated_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if is_allocated:
                allocated_item.setText("✓")
                allocated_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                allocated_item.setText("")
            self.setItem(row, 11, allocated_item)
            
            # Store row data for easy access
            checkbox.setProperty('row_index', row)
        
        # Resize columns to content
        self.resizeColumnsToContents()
        # Restore fixed column widths
        header = self.horizontalHeader()
        header.resizeSection(0, 40)   # Checkbox
        header.resizeSection(1, 100)  # Date
        header.resizeSection(2, 120)  # Type
        header.resizeSection(9, 100)  # Payment Method
        header.resizeSection(10, 100)  # Amount
        header.resizeSection(11, 80)   # Allocated
    
    def get_selected_payments(self) -> List[Dict]:
        """
        Get list of selected payment data based on checked checkboxes.
        
        Returns:
            List of payment dictionaries for selected rows
        """
        selected = []
        for row in range(self.rowCount()):
            checkbox = self.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                # Get payment data from stored list
                if row < len(self._payment_data):
                    payment = self._payment_data[row].copy()
                    payment['row_index'] = row
                    selected.append(payment)
        return selected
    
    def select_all(self):
        """Select all rows (check all checkboxes)."""
        for row in range(self.rowCount()):
            checkbox = self.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)
    
    def deselect_all(self):
        """Deselect all rows (uncheck all checkboxes)."""
        for row in range(self.rowCount()):
            checkbox = self.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)
    
    def get_row_count(self) -> int:
        """Get the number of rows in the table."""
        return self.rowCount()


class CashUpResultsView(QWidget):
    """View widget containing the cash up results table and action buttons."""
    
    # Signal emitted when cash up action is requested for selected payments
    cash_up_selected = Signal(list)  # List of selected payment dictionaries
    
    def __init__(self, parent=None):
        """Initialize the cash up results view."""
        super().__init__(parent)
        self._create_widgets()
    
    def _create_widgets(self):
        """Create and layout UI widgets."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header with title and buttons
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Cash Up Results")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Select All button
        select_all_btn = QPushButton("Select All")
        select_all_btn.setMinimumWidth(120)
        select_all_btn.setMinimumHeight(30)
        select_all_btn.clicked.connect(self._handle_select_all)
        header_layout.addWidget(select_all_btn)
        
        # Deselect All button
        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.setMinimumWidth(120)
        deselect_all_btn.setMinimumHeight(30)
        deselect_all_btn.clicked.connect(self._handle_deselect_all)
        header_layout.addWidget(deselect_all_btn)
        
        # Cash Up Selected button
        cash_up_btn = QPushButton("Cash Up Selected")
        cash_up_btn.setMinimumWidth(140)
        cash_up_btn.setMinimumHeight(30)
        cash_up_btn.setStyleSheet("font-weight: bold;")
        cash_up_btn.clicked.connect(self._handle_cash_up)
        header_layout.addWidget(cash_up_btn)
        
        layout.addLayout(header_layout)
        
        # Results count label
        self.count_label = QLabel("No results")
        self.count_label.setStyleSheet("font-size: 11px; color: gray;")
        layout.addWidget(self.count_label)
        
        # Results table
        self.results_table = CashUpResultsTable()
        layout.addWidget(self.results_table, stretch=1)
    
    def load_results(self, results: List[Dict]):
        """
        Load payment results into the table.
        
        Args:
            results: List of payment dictionaries
        """
        self.results_table.load_results(results)
        count = len(results)
        if count == 0:
            self.count_label.setText("No results")
        elif count == 1:
            self.count_label.setText("1 result")
        else:
            self.count_label.setText(f"{count} results")
    
    def _handle_select_all(self):
        """Handle Select All button click."""
        self.results_table.select_all()
    
    def _handle_deselect_all(self):
        """Handle Deselect All button click."""
        self.results_table.deselect_all()
    
    def _handle_cash_up(self):
        """Handle Cash Up Selected button click."""
        selected = self.results_table.get_selected_payments()
        if not selected:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No Selection", "Please select at least one payment to cash up.")
            return
        self.cash_up_selected.emit(selected)
    
    def get_selected_payments(self) -> List[Dict]:
        """
        Get list of selected payment data.
        
        Returns:
            List of selected payment dictionaries
        """
        return self.results_table.get_selected_payments()
    
    def clear_results(self):
        """Clear all results from the table."""
        self.results_table.clearContents()
        self.results_table.setRowCount(0)
        self.results_table._payment_data = []
        self.count_label.setText("No results")


