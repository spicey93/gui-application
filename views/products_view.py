"""Products view GUI."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QDialog, QLineEdit, QComboBox, QMessageBox, QHeaderView, QLabel, QPushButton
)
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QKeyEvent, QShortcut, QKeySequence
from typing import List, Dict, Optional, Callable
from views.base_view import BaseTabbedView
from utils.styles import apply_theme


class ProductsTableWidget(QTableWidget):
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


class ProductsView(BaseTabbedView):
    """Products management GUI."""
    
    # Additional signals beyond base class
    create_requested = Signal(str, str, str)
    update_requested = Signal(int, str, str, str)
    delete_requested = Signal(int)
    refresh_requested = Signal()
    add_product_type_requested = Signal(str)  # Signal for adding product type
    
    def __init__(self):
        """Initialize the products view."""
        super().__init__(title="Products", current_view="products")
        self.available_types = []  # Store available product types
        self._create_widgets()
        self._setup_keyboard_navigation()
    
    def _create_widgets(self):
        """Create and layout UI widgets."""
        # Add action button using base class method
        # Note: Shortcut is handled globally in main.py, so we don't register it here
        # to avoid conflicts between WindowShortcut and ApplicationShortcut contexts
        self.add_product_button = self.add_action_button(
            "Add Product (Ctrl+N)",
            self._handle_add_product,
            None  # Shortcut handled globally in main.py
        )
        
        # Get content layout to add widgets directly (no tabs needed)
        content_layout = self.get_content_layout()
        
        # Products table
        self.products_table = ProductsTableWidget(self._open_selected_product)
        self.products_table.setColumnCount(4)
        self.products_table.setHorizontalHeaderLabels(["ID", "Stock Number", "Description", "Type"])
        self.products_table.horizontalHeader().setStretchLastSection(True)
        self.products_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.products_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.products_table.setAlternatingRowColors(True)
        self.products_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Set column widths
        header = self.products_table.horizontalHeader()
        header.resizeSection(0, 80)
        header.resizeSection(1, 150)
        header.resizeSection(2, 300)
        
        # Enable keyboard navigation
        self.products_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Double-click to edit
        self.products_table.itemDoubleClicked.connect(self._on_table_double_click)
        
        content_layout.addWidget(self.products_table, stretch=1)
    
    def _setup_keyboard_navigation(self):
        """Set up keyboard navigation."""
        # Tab order: Table -> Add Product -> Navigation panel
        # This makes the table the first focusable element
        self.setTabOrder(self.products_table, self.add_product_button)
        self.setTabOrder(self.add_product_button, self.nav_panel.logout_button)
        
        # Arrow keys work automatically in QTableWidget
        self.products_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def showEvent(self, event: QEvent):
        """Handle show event - set focus to table if it has data."""
        super().showEvent(event)
        # Set focus to table if it has rows
        if self.products_table.rowCount() > 0:
            self.products_table.setFocus()
            # Ensure first row is selected if nothing is selected
            if not self.products_table.selectedItems():
                self.products_table.selectRow(0)
    
    def _handle_add_product(self):
        """Handle Add Product button click."""
        self.add_product()
    
    def _on_table_double_click(self, item: QTableWidgetItem):
        """Handle double-click on table item."""
        self._open_selected_product()
    
    def _open_selected_product(self):
        """Open details for the currently selected product."""
        selected_items = self.products_table.selectedItems()
        if not selected_items:
            return
        
        row = selected_items[0].row()
        product_id = int(self.products_table.item(row, 0).text())
        stock_number = self.products_table.item(row, 1).text()
        description = self.products_table.item(row, 2).text()
        type = self.products_table.item(row, 3).text()
        
        self._show_product_details(product_id, stock_number, description, type)
    
    def _show_product_details(self, product_id: int, stock_number: str, description: str, type: str):
        """Show product details in a popup dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Product Details")
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
        title_label = QLabel("Product Information")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Product ID (read-only)
        id_layout = QHBoxLayout()
        id_label = QLabel("ID:")
        id_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        id_label.setMinimumWidth(150)
        id_layout.addWidget(id_label)
        id_value = QLabel(str(product_id))
        id_value.setStyleSheet("font-size: 12px;")
        id_layout.addWidget(id_value)
        id_layout.addStretch()
        layout.addLayout(id_layout)
        
        # Stock Number (editable)
        stock_layout = QHBoxLayout()
        stock_label = QLabel("Stock Number:")
        stock_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        stock_label.setMinimumWidth(150)
        stock_layout.addWidget(stock_label)
        stock_entry = QLineEdit(stock_number)
        stock_entry.setStyleSheet("font-size: 12px;")
        stock_layout.addWidget(stock_entry, stretch=1)
        layout.addLayout(stock_layout)
        
        # Description (editable)
        desc_layout = QHBoxLayout()
        desc_label = QLabel("Description:")
        desc_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        desc_label.setMinimumWidth(150)
        desc_layout.addWidget(desc_label)
        desc_entry = QLineEdit(description)
        desc_entry.setStyleSheet("font-size: 12px;")
        desc_layout.addWidget(desc_entry, stretch=1)
        layout.addLayout(desc_layout)
        
        # Type (dropdown)
        type_layout = QHBoxLayout()
        type_label = QLabel("Type:")
        type_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        type_label.setMinimumWidth(150)
        type_layout.addWidget(type_label)
        type_combo = QComboBox()
        type_combo.setStyleSheet("font-size: 12px;")
        type_combo.setEditable(True)  # Allow custom entry
        type_combo.addItem("")  # Empty option
        # Populate with available types
        self._populate_type_combo(type_combo, type)
        type_layout.addWidget(type_combo, stretch=1)
        layout.addLayout(type_layout)
        
        layout.addStretch()
        
        # Button frame
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        def handle_save():
            new_stock_number = stock_entry.text().strip()
            new_description = desc_entry.text().strip()
            new_type = type_combo.currentText().strip()
            
            if not new_stock_number:
                QMessageBox.critical(dialog, "Error", "Please enter a stock number")
                return
            
            self.update_requested.emit(product_id, new_stock_number, new_description, new_type)
            dialog.accept()
        
        def handle_delete():
            reply = QMessageBox.question(
                dialog,
                "Confirm Delete",
                f"Are you sure you want to delete product '{stock_entry.text()}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                dialog.accept()
                self.delete_requested.emit(product_id)
        
        save_btn = QPushButton("Save Changes (Ctrl+Enter)")
        save_btn.setMinimumWidth(200)
        save_btn.setMinimumHeight(30)
        save_btn.setDefault(True)
        save_btn.clicked.connect(handle_save)
        
        # Ctrl+Enter shortcut for save
        ctrl_enter_shortcut = QShortcut(QKeySequence("Ctrl+Return"), dialog)
        ctrl_enter_shortcut.activated.connect(handle_save)
        button_layout.addWidget(save_btn)
        
        delete_btn = QPushButton("Delete Product (Ctrl+Shift+D)")
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
        
        # Set focus to stock number entry
        stock_entry.setFocus()
        stock_entry.selectAll()
        
        # Show dialog
        dialog.exec()
    
    def add_product(self):
        """Show dialog for adding a new product."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Product")
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
        title_label = QLabel("Add New Product")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Stock Number
        stock_layout = QHBoxLayout()
        stock_label = QLabel("Stock Number:")
        stock_label.setMinimumWidth(150)
        stock_label.setStyleSheet("font-size: 11px;")
        stock_layout.addWidget(stock_label)
        stock_entry = QLineEdit()
        stock_entry.setStyleSheet("font-size: 11px;")
        stock_layout.addWidget(stock_entry, stretch=1)
        layout.addLayout(stock_layout)
        
        # Description
        desc_layout = QHBoxLayout()
        desc_label = QLabel("Description:")
        desc_label.setMinimumWidth(150)
        desc_label.setStyleSheet("font-size: 11px;")
        desc_layout.addWidget(desc_label)
        desc_entry = QLineEdit()
        desc_entry.setStyleSheet("font-size: 11px;")
        desc_layout.addWidget(desc_entry, stretch=1)
        layout.addLayout(desc_layout)
        
        # Type (dropdown)
        type_layout = QHBoxLayout()
        type_label = QLabel("Type:")
        type_label.setMinimumWidth(150)
        type_label.setStyleSheet("font-size: 11px;")
        type_layout.addWidget(type_label)
        
        type_combo = QComboBox()
        type_combo.setStyleSheet("font-size: 11px;")
        type_combo.setEditable(True)  # Allow custom entry
        # Populate with available types
        self._populate_type_combo(type_combo)
        type_layout.addWidget(type_combo, stretch=1)
        
        layout.addLayout(type_layout)
        
        # Status label
        status_label = QLabel("")
        status_label.setStyleSheet("color: red; font-size: 9px;")
        layout.addWidget(status_label)
        
        layout.addStretch()
        
        # Button frame
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        def handle_save():
            product_stock_number = stock_entry.text().strip()
            product_description = desc_entry.text().strip()
            product_type = type_combo.currentText().strip()
            
            if not product_stock_number:
                status_label.setText("Please enter a stock number")
                return
            
            # Type will be automatically created by controller if it doesn't exist
            self.create_requested.emit(product_stock_number, product_description, product_type)
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
        
        # Set focus to stock number entry
        stock_entry.setFocus()
        
        # Show dialog
        dialog.exec()
    
    def load_products(self, products: List[Dict[str, any]]):
        """Load products into the table."""
        self.products_table.setRowCount(len(products))
        
        for row, product in enumerate(products):
            self.products_table.setItem(row, 0, QTableWidgetItem(str(product['id'])))
            self.products_table.setItem(row, 1, QTableWidgetItem(product.get('stock_number', '')))
            self.products_table.setItem(row, 2, QTableWidgetItem(product.get('description', '')))
            self.products_table.setItem(row, 3, QTableWidgetItem(product.get('type', '')))
        
        # Resize columns to content
        self.products_table.resizeColumnsToContents()
        header = self.products_table.horizontalHeader()
        header.resizeSection(0, 80)
        if len(products) > 0:
            header.resizeSection(1, 150)
            header.resizeSection(2, 300)
        
        # Auto-select first row and set focus to table if data exists
        if len(products) > 0:
            self.products_table.selectRow(0)
            self.products_table.setFocus()
            # Ensure the first row is visible
            self.products_table.scrollToItem(self.products_table.item(0, 0))
    
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
    
    def load_product_types(self, types: List[str]):
        """Load product types into dropdowns."""
        # Store available types for use in dialogs
        self.available_types = types
    
    def _populate_type_combo(self, combo: QComboBox, current_value: str = ""):
        """Populate a type combobox with available types."""
        combo.clear()
        combo.addItem("")  # Empty option
        for type_name in getattr(self, 'available_types', []):
            combo.addItem(type_name)
        
        # Set current value
        if current_value:
            index = combo.findText(current_value)
            if index >= 0:
                combo.setCurrentIndex(index)
            else:
                combo.setCurrentText(current_value)  # Custom value

