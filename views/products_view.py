"""Products view GUI."""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QDialog, QLineEdit, QComboBox, QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QShortcut, QKeySequence
from typing import List, Dict, Optional, Callable
from views.navigation_panel import NavigationPanel


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


class ProductsView(QWidget):
    """Products management GUI."""
    
    # Signals
    dashboard_requested = Signal()
    suppliers_requested = Signal()
    configuration_requested = Signal()
    logout_requested = Signal()
    create_requested = Signal(str, str, str)
    update_requested = Signal(int, str, str, str)
    delete_requested = Signal(int)
    refresh_requested = Signal()
    add_product_type_requested = Signal(str)  # Signal for adding product type
    
    def __init__(self):
        """Initialize the products view."""
        super().__init__()
        self.available_types = []  # Store available product types
        self._create_widgets()
        self._setup_keyboard_navigation()
    
    def _create_widgets(self):
        """Create and layout UI widgets."""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Navigation panel (left sidebar)
        self.nav_panel = NavigationPanel(current_view="products")
        self.nav_panel.dashboard_requested.connect(self._handle_dashboard)
        self.nav_panel.suppliers_requested.connect(self._handle_suppliers)
        self.nav_panel.products_requested.connect(self._handle_products)
        self.nav_panel.configuration_requested.connect(self._handle_configuration)
        self.nav_panel.logout_requested.connect(self._handle_logout)
        
        # Add navigation panel to main layout
        main_layout.addWidget(self.nav_panel)
        
        # Content area (right side)
        content_frame = QWidget()
        content_layout = QVBoxLayout(content_frame)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(40, 40, 40, 40)
        
        # Title and Add Product button
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("Products")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        self.add_product_button = QPushButton("Add Product (Ctrl+N)")
        self.add_product_button.setMinimumWidth(180)
        self.add_product_button.setMinimumHeight(30)
        self.add_product_button.clicked.connect(self._handle_add_product)
        title_layout.addWidget(self.add_product_button)
        
        content_layout.addLayout(title_layout)
        
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
        
        content_layout.addWidget(self.products_table)
        
        # Add content area to main layout
        main_layout.addWidget(content_frame, stretch=1)
    
    def _setup_keyboard_navigation(self):
        """Set up keyboard navigation."""
        # Tab order: Navigation panel -> Add Product -> Table
        self.setTabOrder(self.nav_panel.logout_button, self.add_product_button)
        self.setTabOrder(self.add_product_button, self.products_table)
        
        # Arrow keys work automatically in QTableWidget
        self.products_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def _handle_dashboard(self):
        """Handle dashboard button click."""
        self.dashboard_requested.emit()
    
    def _handle_suppliers(self):
        """Handle suppliers button click."""
        self.suppliers_requested.emit()
    
    def _handle_products(self):
        """Handle products button click."""
        # Already on products page
        pass
    
    def _handle_configuration(self):
        """Handle configuration button click."""
        self.configuration_requested.emit()
    
    def _handle_logout(self):
        """Handle logout button click."""
        self.logout_requested.emit()
    
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
        
        delete_btn = QPushButton("Delete Product")
        delete_btn.setMinimumWidth(120)
        delete_btn.setMinimumHeight(30)
        delete_btn.clicked.connect(handle_delete)
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
        
        # Type (dropdown) with add button
        type_layout = QHBoxLayout()
        type_label = QLabel("Type:")
        type_label.setMinimumWidth(150)
        type_label.setStyleSheet("font-size: 11px;")
        type_layout.addWidget(type_label)
        
        # Container for combo and button
        type_input_layout = QHBoxLayout()
        type_input_layout.setSpacing(5)
        type_input_layout.setContentsMargins(0, 0, 0, 0)
        
        type_combo = QComboBox()
        type_combo.setStyleSheet("font-size: 11px;")
        type_combo.setEditable(True)  # Allow custom entry
        # Populate with available types
        self._populate_type_combo(type_combo)
        type_input_layout.addWidget(type_combo, stretch=1)
        
        # Add button for new product type
        add_type_btn = QPushButton("+")
        add_type_btn.setMinimumWidth(35)
        add_type_btn.setMaximumWidth(35)
        add_type_btn.setMinimumHeight(30)
        add_type_btn.setMaximumHeight(30)
        add_type_btn.setToolTip("Add new product type")
        add_type_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
        add_type_btn.clicked.connect(lambda: self._handle_add_product_type_dialog(type_combo))
        type_input_layout.addWidget(add_type_btn)
        
        type_widget = QWidget()
        type_widget.setLayout(type_input_layout)
        type_layout.addWidget(type_widget, stretch=1)
        
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
    
    def _handle_add_product_type_dialog(self, type_combo: QComboBox):
        """Handle add product type button click - opens dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Product Type")
        dialog.setModal(True)
        dialog.setMinimumSize(400, 180)
        dialog.resize(400, 180)
        
        # Add Escape key shortcut for cancel
        esc_shortcut = QShortcut(QKeySequence("Escape"), dialog)
        esc_shortcut.activated.connect(dialog.reject)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("Add New Product Type")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Name input
        name_layout = QHBoxLayout()
        name_label = QLabel("Name:")
        name_label.setMinimumWidth(100)
        name_label.setStyleSheet("font-size: 12px;")
        name_layout.addWidget(name_label)
        name_entry = QLineEdit()
        name_entry.setStyleSheet("font-size: 12px; padding: 5px;")
        name_entry.setPlaceholderText("Enter product type name")
        name_entry.setMinimumHeight(30)
        name_layout.addWidget(name_entry, stretch=1)
        layout.addLayout(name_layout)
        
        # Status label
        status_label = QLabel("")
        status_label.setStyleSheet("color: red; font-size: 10px;")
        status_label.setMinimumHeight(15)
        layout.addWidget(status_label)
        
        layout.addStretch()
        
        # Button frame
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        def handle_save():
            type_name = name_entry.text().strip()
            
            if not type_name:
                status_label.setText("Please enter a product type name")
                return
            
            # Emit signal to add product type
            self.add_product_type_requested.emit(type_name)
            # Refresh the combo box with new types (will be updated by controller)
            # The controller will call refresh_types which updates available_types
            # We'll refresh the combo after the dialog closes
            dialog.accept()
            # Refresh combo box after dialog closes
            self._populate_type_combo(type_combo, type_name)
        
        save_btn = QPushButton("Save (Ctrl+Enter)")
        save_btn.setMinimumWidth(140)
        save_btn.setMinimumHeight(35)
        save_btn.setDefault(True)
        save_btn.clicked.connect(handle_save)
        
        # Ctrl+Enter shortcut for save
        ctrl_enter_shortcut = QShortcut(QKeySequence("Ctrl+Return"), dialog)
        ctrl_enter_shortcut.activated.connect(handle_save)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel (Esc)")
        cancel_btn.setMinimumWidth(120)
        cancel_btn.setMinimumHeight(35)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Set focus to name entry
        name_entry.setFocus()
        
        # Show dialog
        dialog.exec()

