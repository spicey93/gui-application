"""Reports dialog GUI for financial statements."""
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QDateEdit, QPushButton, QHeaderView, QMessageBox, QTabWidget
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QShortcut, QKeySequence
from typing import List, Dict
from utils.styles import apply_theme
from datetime import date


class ReportsDialog(QDialog):
    """Reports dialog for financial statements."""
    
    # Signals
    generate_vat_return_requested = Signal(str, str)  # start_date, end_date
    generate_profit_loss_requested = Signal(str, str)  # start_date, end_date
    generate_trial_balance_requested = Signal(str)  # as_at_date
    generate_balance_sheet_requested = Signal(str)  # as_at_date
    
    def __init__(self, parent=None):
        """Initialize the reports dialog."""
        super().__init__(parent)
        self.setWindowTitle("Financial Reports")
        self.setModal(True)
        self.setMinimumSize(900, 700)
        self.resize(900, 700)
        apply_theme(self)
        
        # Add Escape key shortcut for cancel
        esc_shortcut = QShortcut(QKeySequence("Escape"), self)
        esc_shortcut.activated.connect(self.reject)
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create and layout UI widgets."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Financial Reports")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Create tabs widget
        self.tab_widget = QTabWidget()
        
        # Tab 1: VAT Return
        vat_widget = QWidget()
        vat_layout = QVBoxLayout(vat_widget)
        vat_layout.setSpacing(20)
        vat_layout.setContentsMargins(20, 20, 20, 20)
        
        # Date range selector
        date_range_layout = QHBoxLayout()
        date_range_layout.setSpacing(10)
        
        start_date_label = QLabel("From Date:")
        start_date_label.setMinimumWidth(80)
        date_range_layout.addWidget(start_date_label)
        
        self.vat_start_date = QDateEdit()
        self.vat_start_date.setCalendarPopup(True)
        # Default to start of current quarter
        today = QDate.currentDate()
        quarter_start_month = ((today.month() - 1) // 3) * 3 + 1
        self.vat_start_date.setDate(QDate(today.year(), quarter_start_month, 1))
        self.vat_start_date.setStyleSheet("font-size: 11px;")
        date_range_layout.addWidget(self.vat_start_date)
        
        end_date_label = QLabel("To Date:")
        end_date_label.setMinimumWidth(80)
        date_range_layout.addWidget(end_date_label)
        
        self.vat_end_date = QDateEdit()
        self.vat_end_date.setCalendarPopup(True)
        self.vat_end_date.setDate(QDate.currentDate())
        self.vat_end_date.setStyleSheet("font-size: 11px;")
        date_range_layout.addWidget(self.vat_end_date)
        
        generate_vat_btn = QPushButton("Generate VAT Return")
        generate_vat_btn.setMinimumHeight(30)
        generate_vat_btn.setStyleSheet("font-size: 11px;")
        generate_vat_btn.clicked.connect(self._handle_generate_vat_return)
        date_range_layout.addWidget(generate_vat_btn)
        
        date_range_layout.addStretch()
        vat_layout.addLayout(date_range_layout)
        
        # VAT Return table
        self.vat_table = QTableWidget()
        self.vat_table.setColumnCount(4)
        self.vat_table.setHorizontalHeaderLabels(["Description", "Output VAT", "Input VAT", "Net VAT"])
        self.vat_table.horizontalHeader().setStretchLastSection(False)
        self.vat_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.vat_table.setAlternatingRowColors(True)
        self.vat_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        header = self.vat_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(1, 120)
        header.resizeSection(2, 120)
        header.resizeSection(3, 120)
        
        vat_layout.addWidget(self.vat_table, stretch=1)
        
        self.tab_widget.addTab(vat_widget, "VAT Return")
        
        # Tab 2: Profit & Loss
        pl_widget = QWidget()
        pl_layout = QVBoxLayout(pl_widget)
        pl_layout.setSpacing(20)
        pl_layout.setContentsMargins(20, 20, 20, 20)
        
        # Date range selector
        pl_date_range_layout = QHBoxLayout()
        pl_date_range_layout.setSpacing(10)
        
        pl_start_date_label = QLabel("From Date:")
        pl_start_date_label.setMinimumWidth(80)
        pl_date_range_layout.addWidget(pl_start_date_label)
        
        self.pl_start_date = QDateEdit()
        self.pl_start_date.setCalendarPopup(True)
        # Default to start of current year
        self.pl_start_date.setDate(QDate(today.year(), 1, 1))
        self.pl_start_date.setStyleSheet("font-size: 11px;")
        pl_date_range_layout.addWidget(self.pl_start_date)
        
        pl_end_date_label = QLabel("To Date:")
        pl_end_date_label.setMinimumWidth(80)
        pl_date_range_layout.addWidget(pl_end_date_label)
        
        self.pl_end_date = QDateEdit()
        self.pl_end_date.setCalendarPopup(True)
        self.pl_end_date.setDate(QDate.currentDate())
        self.pl_end_date.setStyleSheet("font-size: 11px;")
        pl_date_range_layout.addWidget(self.pl_end_date)
        
        generate_pl_btn = QPushButton("Generate Profit & Loss")
        generate_pl_btn.setMinimumHeight(30)
        generate_pl_btn.setStyleSheet("font-size: 11px;")
        generate_pl_btn.clicked.connect(self._handle_generate_profit_loss)
        pl_date_range_layout.addWidget(generate_pl_btn)
        
        pl_date_range_layout.addStretch()
        pl_layout.addLayout(pl_date_range_layout)
        
        # Profit & Loss table
        self.pl_table = QTableWidget()
        self.pl_table.setColumnCount(2)
        self.pl_table.setHorizontalHeaderLabels(["Account", "Amount"])
        self.pl_table.horizontalHeader().setStretchLastSection(False)
        self.pl_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.pl_table.setAlternatingRowColors(True)
        self.pl_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        pl_header = self.pl_table.horizontalHeader()
        pl_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        pl_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        pl_header.resizeSection(1, 150)
        
        pl_layout.addWidget(self.pl_table, stretch=1)
        
        self.tab_widget.addTab(pl_widget, "Profit & Loss")
        
        # Tab 3: Trial Balance
        tb_widget = QWidget()
        tb_layout = QVBoxLayout(tb_widget)
        tb_layout.setSpacing(20)
        tb_layout.setContentsMargins(20, 20, 20, 20)
        
        # Date selector
        tb_date_layout = QHBoxLayout()
        tb_date_layout.setSpacing(10)
        
        tb_date_label = QLabel("As At Date:")
        tb_date_label.setMinimumWidth(80)
        tb_date_layout.addWidget(tb_date_label)
        
        self.tb_date = QDateEdit()
        self.tb_date.setCalendarPopup(True)
        self.tb_date.setDate(QDate.currentDate())
        self.tb_date.setStyleSheet("font-size: 11px;")
        tb_date_layout.addWidget(self.tb_date)
        
        generate_tb_btn = QPushButton("Generate Trial Balance")
        generate_tb_btn.setMinimumHeight(30)
        generate_tb_btn.setStyleSheet("font-size: 11px;")
        generate_tb_btn.clicked.connect(self._handle_generate_trial_balance)
        tb_date_layout.addWidget(generate_tb_btn)
        
        tb_date_layout.addStretch()
        tb_layout.addLayout(tb_date_layout)
        
        # Trial Balance table
        self.tb_table = QTableWidget()
        self.tb_table.setColumnCount(5)
        self.tb_table.setHorizontalHeaderLabels(["Account Code", "Account Name", "Debit", "Credit", "Balance"])
        self.tb_table.horizontalHeader().setStretchLastSection(False)
        self.tb_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tb_table.setAlternatingRowColors(True)
        self.tb_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        tb_header = self.tb_table.horizontalHeader()
        tb_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        tb_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        tb_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        tb_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        tb_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        tb_header.resizeSection(0, 100)
        tb_header.resizeSection(2, 120)
        tb_header.resizeSection(3, 120)
        tb_header.resizeSection(4, 120)
        
        tb_layout.addWidget(self.tb_table, stretch=1)
        
        self.tab_widget.addTab(tb_widget, "Trial Balance")
        
        # Tab 4: Balance Sheet
        bs_widget = QWidget()
        bs_layout = QVBoxLayout(bs_widget)
        bs_layout.setSpacing(20)
        bs_layout.setContentsMargins(20, 20, 20, 20)
        
        # Date selector
        bs_date_layout = QHBoxLayout()
        bs_date_layout.setSpacing(10)
        
        bs_date_label = QLabel("As At Date:")
        bs_date_label.setMinimumWidth(80)
        bs_date_layout.addWidget(bs_date_label)
        
        self.bs_date = QDateEdit()
        self.bs_date.setCalendarPopup(True)
        self.bs_date.setDate(QDate.currentDate())
        self.bs_date.setStyleSheet("font-size: 11px;")
        bs_date_layout.addWidget(self.bs_date)
        
        generate_bs_btn = QPushButton("Generate Balance Sheet")
        generate_bs_btn.setMinimumHeight(30)
        generate_bs_btn.setStyleSheet("font-size: 11px;")
        generate_bs_btn.clicked.connect(self._handle_generate_balance_sheet)
        bs_date_layout.addWidget(generate_bs_btn)
        
        bs_date_layout.addStretch()
        bs_layout.addLayout(bs_date_layout)
        
        # Balance Sheet table
        self.bs_table = QTableWidget()
        self.bs_table.setColumnCount(2)
        self.bs_table.setHorizontalHeaderLabels(["Account", "Amount"])
        self.bs_table.horizontalHeader().setStretchLastSection(False)
        self.bs_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.bs_table.setAlternatingRowColors(True)
        self.bs_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        bs_header = self.bs_table.horizontalHeader()
        bs_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        bs_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        bs_header.resizeSection(1, 150)
        
        bs_layout.addWidget(self.bs_table, stretch=1)
        
        self.tab_widget.addTab(bs_widget, "Balance Sheet")
        
        layout.addWidget(self.tab_widget, stretch=1)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Close (Esc)")
        close_btn.setMinimumWidth(120)
        close_btn.setMinimumHeight(30)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _handle_generate_vat_return(self):
        """Handle generate VAT return request."""
        start_date = self.vat_start_date.date().toPython()
        end_date = self.vat_end_date.date().toPython()
        
        if start_date > end_date:
            QMessageBox.warning(self, "Invalid Date Range", "Start date must be before or equal to end date.")
            return
        
        self.generate_vat_return_requested.emit(start_date.isoformat(), end_date.isoformat())
    
    def _handle_generate_profit_loss(self):
        """Handle generate Profit & Loss request."""
        start_date = self.pl_start_date.date().toPython()
        end_date = self.pl_end_date.date().toPython()
        
        if start_date > end_date:
            QMessageBox.warning(self, "Invalid Date Range", "Start date must be before or equal to end date.")
            return
        
        self.generate_profit_loss_requested.emit(start_date.isoformat(), end_date.isoformat())
    
    def _handle_generate_trial_balance(self):
        """Handle generate Trial Balance request."""
        as_at_date = self.tb_date.date().toPython()
        self.generate_trial_balance_requested.emit(as_at_date.isoformat())
    
    def _handle_generate_balance_sheet(self):
        """Handle generate Balance Sheet request."""
        as_at_date = self.bs_date.date().toPython()
        self.generate_balance_sheet_requested.emit(as_at_date.isoformat())
    
    def load_vat_return(self, vat_data: List[Dict]):
        """Load VAT return data into table."""
        self.vat_table.setRowCount(len(vat_data))
        
        for row, item in enumerate(vat_data):
            self.vat_table.setItem(row, 0, QTableWidgetItem(item.get('description', '')))
            
            output_vat = item.get('output_vat', 0.0)
            output_item = QTableWidgetItem(f"£{output_vat:,.2f}")
            output_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.vat_table.setItem(row, 1, output_item)
            
            input_vat = item.get('input_vat', 0.0)
            input_item = QTableWidgetItem(f"£{input_vat:,.2f}")
            input_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.vat_table.setItem(row, 2, input_item)
            
            net_vat = item.get('net_vat', 0.0)
            net_item = QTableWidgetItem(f"£{net_vat:,.2f}")
            net_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.vat_table.setItem(row, 3, net_item)
    
    def load_profit_loss(self, pl_data: List[Dict]):
        """Load Profit & Loss data into table."""
        self.pl_table.setRowCount(len(pl_data))
        
        for row, item in enumerate(pl_data):
            self.pl_table.setItem(row, 0, QTableWidgetItem(item.get('account', '')))
            
            amount = item.get('amount', 0.0)
            amount_item = QTableWidgetItem(f"£{amount:,.2f}")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.pl_table.setItem(row, 1, amount_item)
    
    def load_trial_balance(self, tb_data: List[Dict]):
        """Load Trial Balance data into table."""
        self.tb_table.setRowCount(len(tb_data))
        
        for row, item in enumerate(tb_data):
            self.tb_table.setItem(row, 0, QTableWidgetItem(str(item.get('account_code', ''))))
            self.tb_table.setItem(row, 1, QTableWidgetItem(item.get('account_name', '')))
            
            debit = item.get('debit', 0.0)
            debit_item = QTableWidgetItem(f"£{debit:,.2f}" if debit > 0 else "")
            debit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tb_table.setItem(row, 2, debit_item)
            
            credit = item.get('credit', 0.0)
            credit_item = QTableWidgetItem(f"£{credit:,.2f}" if credit > 0 else "")
            credit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tb_table.setItem(row, 3, credit_item)
            
            balance = item.get('balance', 0.0)
            balance_item = QTableWidgetItem(f"£{balance:,.2f}")
            balance_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tb_table.setItem(row, 4, balance_item)
    
    def load_balance_sheet(self, bs_data: List[Dict]):
        """Load Balance Sheet data into table."""
        self.bs_table.setRowCount(len(bs_data))
        
        for row, item in enumerate(bs_data):
            self.bs_table.setItem(row, 0, QTableWidgetItem(item.get('account', '')))
            
            amount = item.get('amount', 0.0)
            amount_item = QTableWidgetItem(f"£{amount:,.2f}")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.bs_table.setItem(row, 1, amount_item)
    
    def show_success_dialog(self, message: str):
        """Show a success dialog."""
        QMessageBox.information(self, "Success", message)
    
    def show_error_dialog(self, message: str):
        """Show an error dialog."""
        QMessageBox.critical(self, "Error", message)

