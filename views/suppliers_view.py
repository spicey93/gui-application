"""Suppliers view GUI."""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QDialog, QLineEdit, QTabWidget, QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QShortcut, QKeySequence
from typing import List, Dict, Optional, Callable
from views.shortcuts_dialog import ShortcutsDialog


class SuppliersTableWidget(QTableWidget):
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


class SuppliersView(QWidget):
    """Suppliers management GUI."""
    
    # Signals
    dashboard_requested = Signal()
    logout_requested = Signal()
    create_requested = Signal(str, str)
    update_requested = Signal(int, str, str)
    delete_requested = Signal(int)
    refresh_requested = Signal()
    
    def __init__(self):
        """Initialize the suppliers view."""
        super().__init__()
        self._create_widgets()
        self._setup_keyboard_navigation()
    
    def _create_widgets(self):
        """Create and layout UI widgets."""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Navigation panel (left sidebar) - same as dashboard
        nav_panel = QFrame()
        nav_panel.setObjectName("navPanel")
        nav_panel.setFixedWidth(180)
        nav_panel.setFrameShape(QFrame.Shape.StyledPanel)
        nav_panel.setFrameShadow(QFrame.Shadow.Raised)
        
        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setSpacing(10)
        nav_layout.setContentsMargins(15, 15, 15, 15)
        
        # Navigation title
        nav_title = QLabel("Navigation")
        nav_title.setStyleSheet("font-weight: bold; font-size: 12px;")
        nav_layout.addWidget(nav_title)
        
        nav_layout.addSpacing(10)
        
        # Dashboard menu item
        self.dashboard_button = QPushButton("Dashboard")
        self.dashboard_button.setMinimumHeight(30)
        self.dashboard_button.clicked.connect(self._handle_dashboard)
        nav_layout.addWidget(self.dashboard_button)
        
        # Suppliers menu item
        self.suppliers_button = QPushButton("Suppliers")
        self.suppliers_button.setMinimumHeight(30)
        self.suppliers_button.clicked.connect(self._handle_suppliers)
        nav_layout.addWidget(self.suppliers_button)
        
        nav_layout.addSpacing(15)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        nav_layout.addWidget(separator)
        
        nav_layout.addSpacing(15)
        
        # Logout menu item
        self.logout_button = QPushButton("Logout")
        self.logout_button.setMinimumHeight(30)
        self.logout_button.clicked.connect(self._handle_logout)
        nav_layout.addWidget(self.logout_button)
        
        nav_layout.addSpacing(15)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        nav_layout.addWidget(separator2)
        
        nav_layout.addSpacing(15)
        
        # Help/Shortcuts button
        self.help_button = QPushButton("Keyboard Shortcuts")
        self.help_button.setMinimumHeight(30)
        self.help_button.clicked.connect(self._handle_help)
        nav_layout.addWidget(self.help_button)
        
        nav_layout.addStretch()
        
        # Add navigation panel to main layout
        main_layout.addWidget(nav_panel)
        
        # Content area (right side)
        content_frame = QWidget()
        content_layout = QVBoxLayout(content_frame)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(40, 40, 40, 40)
        
        # Title and Add Supplier button
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("Suppliers")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        self.add_supplier_button = QPushButton("Add Supplier")
        self.add_supplier_button.setMinimumWidth(120)
        self.add_supplier_button.setMinimumHeight(30)
        self.add_supplier_button.clicked.connect(self._handle_add_supplier)
        title_layout.addWidget(self.add_supplier_button)
        
        content_layout.addLayout(title_layout)
        
        # Suppliers table
        self.suppliers_table = SuppliersTableWidget(self._open_selected_supplier)
        self.suppliers_table.setColumnCount(3)
        self.suppliers_table.setHorizontalHeaderLabels(["ID", "Account Number", "Name"])
        self.suppliers_table.horizontalHeader().setStretchLastSection(True)
        self.suppliers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.suppliers_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.suppliers_table.setAlternatingRowColors(True)
        self.suppliers_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Set column widths
        header = self.suppliers_table.horizontalHeader()
        header.resizeSection(0, 80)
        header.resizeSection(1, 200)
        
        # Enable keyboard navigation
        self.suppliers_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Double-click to edit
        self.suppliers_table.itemDoubleClicked.connect(self._on_table_double_click)
        
        content_layout.addWidget(self.suppliers_table)
        
        # Add content area to main layout
        main_layout.addWidget(content_frame, stretch=1)
    
    def _setup_keyboard_navigation(self):
        """Set up keyboard navigation."""
        # Tab order: Dashboard -> Suppliers -> Logout -> Help -> Add Supplier -> Table
        self.setTabOrder(self.dashboard_button, self.suppliers_button)
        self.setTabOrder(self.suppliers_button, self.logout_button)
        self.setTabOrder(self.logout_button, self.help_button)
        self.setTabOrder(self.help_button, self.add_supplier_button)
        self.setTabOrder(self.add_supplier_button, self.suppliers_table)
        
        # Arrow keys work automatically in QTableWidget
        # Enter key on table row opens details
        self.suppliers_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def _handle_dashboard(self):
        """Handle dashboard button click."""
        self.dashboard_requested.emit()
    
    def _handle_suppliers(self):
        """Handle suppliers button click."""
        # Already on suppliers page
        pass
    
    def _handle_logout(self):
        """Handle logout button click."""
        self.logout_requested.emit()
    
    def _handle_help(self):
        """Handle help button click."""
        dialog = ShortcutsDialog(self)
        dialog.exec()
    
    def _handle_add_supplier(self):
        """Handle Add Supplier button click."""
        self.add_supplier()
    
    def _on_table_double_click(self, item: QTableWidgetItem):
        """Handle double-click on table item."""
        self._open_selected_supplier()
    
    def _open_selected_supplier(self):
        """Open details for the currently selected supplier."""
        selected_items = self.suppliers_table.selectedItems()
        if not selected_items:
            return
        
        row = selected_items[0].row()
        supplier_id = int(self.suppliers_table.item(row, 0).text())
        account_number = self.suppliers_table.item(row, 1).text()
        name = self.suppliers_table.item(row, 2).text()
        self._show_supplier_details(supplier_id, account_number, name)
    
    def _show_supplier_details(self, supplier_id: int, account_number: str, name: str):
        """Show supplier details in a popup dialog with tabs."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Supplier Details")
        dialog.setModal(True)
        dialog.setMinimumSize(600, 500)
        dialog.resize(600, 500)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("Supplier Information")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Create notebook for tabs
        notebook = QTabWidget()
        
        # Info tab
        info_frame = QWidget()
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(15)
        info_layout.setContentsMargins(30, 30, 30, 30)
        
        # Supplier ID (read-only)
        id_layout = QHBoxLayout()
        id_label = QLabel("ID:")
        id_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        id_label.setMinimumWidth(150)
        id_layout.addWidget(id_label)
        id_value = QLabel(str(supplier_id))
        id_value.setStyleSheet("font-size: 12px;")
        id_layout.addWidget(id_value)
        id_layout.addStretch()
        info_layout.addLayout(id_layout)
        
        # Account Number (editable)
        account_layout = QHBoxLayout()
        account_label = QLabel("Account Number:")
        account_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        account_label.setMinimumWidth(150)
        account_layout.addWidget(account_label)
        account_entry = QLineEdit(account_number)
        account_entry.setStyleSheet("font-size: 12px;")
        account_layout.addWidget(account_entry, stretch=1)
        info_layout.addLayout(account_layout)
        
        # Name (editable)
        name_layout = QHBoxLayout()
        name_label = QLabel("Name:")
        name_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        name_label.setMinimumWidth(150)
        name_layout.addWidget(name_label)
        name_entry = QLineEdit(name)
        name_entry.setStyleSheet("font-size: 12px;")
        name_layout.addWidget(name_entry, stretch=1)
        info_layout.addLayout(name_layout)
        
        info_layout.addStretch()
        notebook.addTab(info_frame, "Info")
        
        # Actions tab
        actions_frame = QWidget()
        actions_layout = QVBoxLayout(actions_frame)
        actions_layout.setContentsMargins(30, 30, 30, 30)
        
        delete_btn = QPushButton("Delete Supplier")
        delete_btn.setMinimumHeight(35)
        delete_btn.clicked.connect(
            lambda: self._delete_from_details_dialog(dialog, supplier_id, name)
        )
        actions_layout.addWidget(delete_btn)
        actions_layout.addStretch()
        
        notebook.addTab(actions_frame, "Actions")
        
        layout.addWidget(notebook)
        
        # Button frame
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        def handle_save():
            new_account_number = account_entry.text().strip()
            new_name = name_entry.text().strip()
            
            if not new_account_number or not new_name:
                QMessageBox.critical(dialog, "Error", "Please fill in both account number and name")
                return
            
            self.update_requested.emit(supplier_id, new_account_number, new_name)
            dialog.accept()
        
        save_btn = QPushButton("Save Changes")
        save_btn.setMinimumWidth(120)
        save_btn.setMinimumHeight(30)
        save_btn.setDefault(True)
        save_btn.clicked.connect(handle_save)
        
        # Ctrl+Enter shortcut for save
        ctrl_enter_shortcut = QShortcut(QKeySequence("Ctrl+Return"), dialog)
        ctrl_enter_shortcut.activated.connect(handle_save)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumWidth(120)
        cancel_btn.setMinimumHeight(30)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Set focus to account entry
        account_entry.setFocus()
        account_entry.selectAll()
        
        # Show dialog
        dialog.exec()
    
    def _delete_from_details_dialog(self, dialog: QDialog, supplier_id: int, supplier_name: str):
        """Handle delete from details dialog."""
        reply = QMessageBox.question(
            dialog,
            "Confirm Delete",
            f"Are you sure you want to delete supplier '{supplier_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            dialog.accept()
            self.delete_requested.emit(supplier_id)
    
    def add_supplier(self):
        """Show dialog for adding a new supplier."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Supplier")
        dialog.setModal(True)
        dialog.setMinimumSize(500, 300)
        dialog.resize(500, 300)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("Add New Supplier")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Account Number
        account_layout = QHBoxLayout()
        account_label = QLabel("Account Number:")
        account_label.setMinimumWidth(150)
        account_label.setStyleSheet("font-size: 11px;")
        account_layout.addWidget(account_label)
        account_entry = QLineEdit()
        account_entry.setStyleSheet("font-size: 11px;")
        account_layout.addWidget(account_entry, stretch=1)
        layout.addLayout(account_layout)
        
        # Name
        name_layout = QHBoxLayout()
        name_label = QLabel("Name:")
        name_label.setMinimumWidth(150)
        name_label.setStyleSheet("font-size: 11px;")
        name_layout.addWidget(name_label)
        name_entry = QLineEdit()
        name_entry.setStyleSheet("font-size: 11px;")
        name_layout.addWidget(name_entry, stretch=1)
        layout.addLayout(name_layout)
        
        # Status label
        status_label = QLabel("")
        status_label.setStyleSheet("color: red; font-size: 9px;")
        layout.addWidget(status_label)
        
        layout.addStretch()
        
        # Button frame
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        def handle_save():
            acc_num = account_entry.text().strip()
            supplier_name = name_entry.text().strip()
            
            if not acc_num or not supplier_name:
                status_label.setText("Please fill in both fields")
                return
            
            self.create_requested.emit(acc_num, supplier_name)
            dialog.accept()
        
        save_btn = QPushButton("Save")
        save_btn.setMinimumWidth(100)
        save_btn.setMinimumHeight(30)
        save_btn.setDefault(True)
        save_btn.clicked.connect(handle_save)
        
        # Ctrl+Enter shortcut for save
        ctrl_enter_shortcut = QShortcut(QKeySequence("Ctrl+Return"), dialog)
        ctrl_enter_shortcut.activated.connect(handle_save)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setMinimumHeight(30)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Set focus to account entry
        account_entry.setFocus()
        
        # Show dialog
        dialog.exec()
    
    def load_suppliers(self, suppliers: List[Dict[str, any]]):
        """Load suppliers into the table."""
        self.suppliers_table.setRowCount(len(suppliers))
        
        for row, supplier in enumerate(suppliers):
            self.suppliers_table.setItem(row, 0, QTableWidgetItem(str(supplier['id'])))
            self.suppliers_table.setItem(row, 1, QTableWidgetItem(supplier['account_number']))
            self.suppliers_table.setItem(row, 2, QTableWidgetItem(supplier['name']))
        
        # Resize columns to content
        self.suppliers_table.resizeColumnsToContents()
        header = self.suppliers_table.horizontalHeader()
        header.resizeSection(0, 80)
        if len(suppliers) > 0:
            header.resizeSection(1, 200)
    
    def show_success(self, message: str):
        """Display a success message."""
        self.show_success_dialog(message)
    
    def show_error(self, message: str):
        """Display an error message."""
        self.show_error_dialog(message)
    
    def show_success_dialog(self, message: str):
        """Show a success dialog."""
        QMessageBox.information(self, "Success", message)
    
    def show_error_dialog(self, message: str):
        """Show an error dialog."""
        QMessageBox.critical(self, "Error", message)
