"""Products view GUI."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QDialog, QLineEdit, QComboBox, QMessageBox, QHeaderView, QLabel, QPushButton,
    QScrollArea, QCheckBox, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QKeyEvent, QShortcut, QKeySequence
from typing import List, Dict, Optional, Callable
from views.base_view import BaseTabbedView
from utils.styles import apply_theme
from utils.tyre_parser import extract_tyre_specs, validate_tyre_description


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
    create_tyre_requested = Signal(str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str)  # All tyre fields
    update_requested = Signal(int, str, str, str)
    update_tyre_requested = Signal(int, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str)  # All tyre fields including noise
    delete_requested = Signal(int)
    refresh_requested = Signal()
    add_product_type_requested = Signal(str)  # Signal for adding product type
    catalogue_requested = Signal()  # Signal for opening tyre catalogue
    get_product_details_requested = Signal(int)  # Request full product details
    stock_audit_requested = Signal(int)  # Request stock audit for a product
    check_product_history_requested = Signal(int)  # Check if product has history
    
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
        
        # Add View Catalogue button
        self.view_catalogue_button = self.add_action_button(
            "View Catalogue (Ctrl+Shift+C)",
            self._handle_view_catalogue,
            None  # Shortcut handled globally in main.py
        )
        
        # Create tabs widget
        self.tab_widget = self.create_tabs()
        
        # Connect tab change signal to update stock audit when tab is selected
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        # Track selected product for stock audit tab
        self.selected_product_id: Optional[int] = None
        self._all_products_data: List[Dict] = []  # Store all products for filtering
        
        # Tab 1: Products
        products_widget = QWidget()
        products_layout = QVBoxLayout(products_widget)
        products_layout.setSpacing(20)
        products_layout.setContentsMargins(10, 10, 10, 10)
        
        # Search box
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_label.setMinimumWidth(60)
        self.products_search_box = QLineEdit()
        self.products_search_box.setPlaceholderText("Search products...")
        self.products_search_box.textChanged.connect(self._filter_products)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.products_search_box)
        products_layout.addLayout(search_layout)
        
        # Products table
        self.products_table = ProductsTableWidget(self._open_selected_product)
        self.products_table.setColumnCount(4)
        self.products_table.setHorizontalHeaderLabels(["ID", "Stock Number", "Description", "Type"])
        self.products_table.horizontalHeader().setStretchLastSection(True)
        self.products_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.products_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.products_table.setAlternatingRowColors(True)
        self.products_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Set column resize modes - ID fixed, others stretch
        header = self.products_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.resizeSection(0, 80)
        
        # Enable keyboard navigation
        self.products_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Selection changed - update selected product
        self.products_table.itemSelectionChanged.connect(self._on_product_selection_changed)
        
        # Double-click to edit
        self.products_table.itemDoubleClicked.connect(self._on_table_double_click)
        
        products_layout.addWidget(self.products_table, stretch=1)
        
        self.add_tab(products_widget, "Products (Ctrl+1)", "Ctrl+1")
        
        # Tab 2: Details
        self._create_product_details_tab()
        
        # Tab 3: Stock Audit
        audit_widget = QWidget()
        audit_layout = QVBoxLayout(audit_widget)
        audit_layout.setSpacing(20)
        audit_layout.setContentsMargins(10, 10, 10, 10)
        
        # Instructions label
        self.audit_label = QLabel("Select a product from the Products tab to view stock audit history.")
        self.audit_label.setStyleSheet("font-size: 12px; color: gray;")
        audit_layout.addWidget(self.audit_label)
        
        # Stock audit table
        self.audit_table = QTableWidget()
        self.audit_table.setColumnCount(7)
        self.audit_table.setHorizontalHeaderLabels(["Type", "Document Number", "Date", "Supplier/Customer", "Quantity", "Unit Price", "Total"])
        self.audit_table.horizontalHeader().setStretchLastSection(True)
        self.audit_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.audit_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.audit_table.setAlternatingRowColors(True)
        self.audit_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Set column resize modes
        audit_header = self.audit_table.horizontalHeader()
        audit_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        audit_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        audit_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        audit_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        audit_header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        audit_header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        audit_header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        
        audit_layout.addWidget(self.audit_table, stretch=1)
        
        self.add_tab(audit_widget, "Stock Audit (Ctrl+3)", "Ctrl+3")
    
    def _create_product_details_tab(self):
        """Create the product details tab."""
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setSpacing(20)
        details_layout.setContentsMargins(10, 10, 10, 10)
        
        # Placeholder label
        self.product_details_label = QLabel(
            "Select a product from the Products tab to view details."
        )
        self.product_details_label.setStyleSheet("font-size: 12px; color: gray;")
        details_layout.addWidget(self.product_details_label)
        
        # Details form (hidden until product selected)
        self.product_details_form = QWidget()
        details_form_layout = QVBoxLayout(self.product_details_form)
        details_form_layout.setSpacing(15)
        details_form_layout.setContentsMargins(0, 0, 0, 0)
        
        # Store form widgets for later use
        self.product_details_id_label = QLabel("")
        self.product_details_stock_entry = QLineEdit()
        self.product_details_desc_entry = QLineEdit()
        self.product_details_type_combo = QComboBox()
        self.product_details_type_combo.setEditable(True)
        
        # Add form rows
        self._create_product_detail_row(details_form_layout, "ID:", self.product_details_id_label, read_only=True)
        self._create_product_detail_row(details_form_layout, "Stock Number:", self.product_details_stock_entry)
        self._create_product_detail_row(details_form_layout, "Description:", self.product_details_desc_entry)
        self._create_product_detail_row(details_form_layout, "Type:", self.product_details_type_combo)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.product_details_save_button = QPushButton("Save Changes (Ctrl+Enter)")
        self.product_details_save_button.setMinimumWidth(200)
        self.product_details_save_button.setMinimumHeight(30)
        self.product_details_save_button.clicked.connect(self._handle_save_product_details)
        buttons_layout.addWidget(self.product_details_save_button)
        
        self.product_details_delete_button = QPushButton("Delete Product (Ctrl+Shift+D)")
        self.product_details_delete_button.setMinimumWidth(220)
        self.product_details_delete_button.setMinimumHeight(30)
        self.product_details_delete_button.clicked.connect(self._handle_delete_product_details)
        buttons_layout.addWidget(self.product_details_delete_button)
        
        details_form_layout.addLayout(buttons_layout)
        details_form_layout.addStretch()
        
        self.product_details_form.hide()
        details_layout.addWidget(self.product_details_form)
        details_layout.addStretch()
        
        self.add_tab(details_widget, "Details (Ctrl+2)", "Ctrl+2")
    
    def _create_product_detail_row(self, layout: QVBoxLayout, label_text: str, widget: QWidget, read_only: bool = False):
        """Create a detail row with label and widget."""
        row_layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setStyleSheet("font-weight: bold; font-size: 12px;")
        label.setMinimumWidth(150)
        row_layout.addWidget(label)
        row_layout.addWidget(widget, stretch=1)
        layout.addLayout(row_layout)
    
    def _setup_keyboard_navigation(self):
        """Set up keyboard navigation."""
        # Tab order: Table -> Add Product -> Navigation panel
        # This makes the table the first focusable element
        self.setTabOrder(self.products_table, self.add_product_button)
        self.setTabOrder(self.add_product_button, self.nav_panel.logout_button)
        
        # Arrow keys work automatically in QTableWidget
        self.products_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Shortcuts for details tab
        save_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        save_shortcut.activated.connect(self._handle_save_product_details)
        
        delete_shortcut = QShortcut(QKeySequence("Ctrl+Shift+D"), self)
        delete_shortcut.activated.connect(self._handle_delete_product_details)
    
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
    
    def _handle_view_catalogue(self):
        """Handle View Catalogue button click."""
        self.catalogue_requested.emit()
    
    def _on_table_double_click(self, item: QTableWidgetItem):
        """Handle double-click on table item."""
        self._open_selected_product()
    
    def _on_product_selection_changed(self):
        """Handle product selection change - update details or stock audit if on those tabs."""
        selected_items = self.products_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            product_id = int(self.products_table.item(row, 0).text())
            self.selected_product_id = product_id
            # If on details tab, refresh details
            if self.tab_widget.currentIndex() == 1:
                self.get_product_details_requested.emit(product_id)
            # If on stock audit tab, refresh audit data
            elif self.tab_widget.currentIndex() == 2:
                self.stock_audit_requested.emit(product_id)
    
    def _on_tab_changed(self, index: int):
        """Handle tab change - refresh details or stock audit if switching to those tabs."""
        if index == 1 and self.selected_product_id:  # Details tab
            self.get_product_details_requested.emit(self.selected_product_id)
        elif index == 2 and self.selected_product_id:  # Stock Audit tab
            self.stock_audit_requested.emit(self.selected_product_id)
    
    def _open_selected_product(self):
        """Open details for the currently selected product."""
        if self.selected_product_id is not None:
            self.tab_widget.setCurrentIndex(1)
            self.get_product_details_requested.emit(self.selected_product_id)
    
    def show_product_details(self, product: Dict[str, any], has_history: bool = False):
        """Show product details in the details tab."""
        self._update_product_details_tab(product, has_history)
    
    def _update_product_details_tab(self, product: Dict[str, any], has_history: bool = False):
        """Update the details tab with selected product data."""
        if not product:
            self.product_details_label.show()
            self.product_details_form.hide()
            return
        
        self.product_details_label.hide()
        self.product_details_form.show()
        
        # Populate form fields
        self.product_details_id_label.setText(str(product.get('id', '')))
        self.product_details_stock_entry.setText(product.get('stock_number', ''))
        self.product_details_desc_entry.setText(product.get('description', ''))
        
        # Populate type combo
        self.product_details_type_combo.clear()
        self.product_details_type_combo.addItem("")
        for type_name in getattr(self, 'available_types', []):
            self.product_details_type_combo.addItem(type_name)
        product_type = product.get('type', '')
        if product_type:
            index = self.product_details_type_combo.findText(product_type)
            if index >= 0:
                self.product_details_type_combo.setCurrentIndex(index)
            else:
                self.product_details_type_combo.setCurrentText(product_type)
        
        # Enable/disable delete button based on history
        if has_history:
            self.product_details_delete_button.setEnabled(False)
            self.product_details_delete_button.setToolTip("Cannot delete product with transaction history")
        else:
            self.product_details_delete_button.setEnabled(True)
            self.product_details_delete_button.setToolTip("")
    
    def _handle_save_product_details(self):
        """Handle save product details button click."""
        if self.selected_product_id is None:
            return
        
        if self.tab_widget.currentIndex() != 1:
            return
        
        stock_number = self.product_details_stock_entry.text().strip()
        if not stock_number:
            self.show_error_dialog("Stock number is required")
            return
        
        description = self.product_details_desc_entry.text().strip()
        product_type = self.product_details_type_combo.currentText().strip()
        
        # Check if it's a tyre product - if so, we need to use update_tyre_requested
        # For now, use standard update - controller can handle it
        self.update_requested.emit(
            self.selected_product_id,
            stock_number,
            description,
            product_type
        )
    
    def _handle_delete_product_details(self):
        """Handle delete product button click from details tab."""
        if self.selected_product_id is None:
            return
        
        if self.tab_widget.currentIndex() != 1:
            return
        
        product_name = self.product_details_stock_entry.text()
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete product '{product_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_requested.emit(self.selected_product_id)
            self.selected_product_id = None
            self.tab_widget.setCurrentIndex(0)
    
    def _show_product_details(self, product: Dict[str, any], has_history: bool = False):
        """Show product details in a popup dialog."""
        product_id = product.get('id')
        stock_number = product.get('stock_number', '')
        description = product.get('description', '')
        type = product.get('type', '')
        is_tyre = product.get('is_tyre', 0) == 1
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Product Details")
        dialog.setModal(True)
        if is_tyre:
            dialog.setMinimumSize(700, 800)
            dialog.resize(700, 800)
        else:
            dialog.setMinimumSize(600, 500)
            dialog.resize(600, 500)
        apply_theme(dialog)
        
        # Add Escape key shortcut for cancel
        esc_shortcut = QShortcut(QKeySequence("Escape"), dialog)
        esc_shortcut.activated.connect(dialog.reject)
        
        # Scroll area for long forms (especially tyre products)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: #ffffff;")
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background-color: #ffffff;")
        layout = QVBoxLayout(scroll_widget)
        layout.setSpacing(15)
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
        
        # Tyre fields (only if is_tyre = 1)
        tyre_widgets = {}
        if is_tyre:
            tyre_model = getattr(self, 'tyre_model', None)
            
            # Brand
            brand_layout = QHBoxLayout()
            brand_label = QLabel("Brand:")
            brand_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            brand_label.setMinimumWidth(150)
            brand_layout.addWidget(brand_label)
            brand_combo = QComboBox()
            brand_combo.setStyleSheet("font-size: 12px;")
            brand_combo.setEditable(True)
            brand_combo.addItem("")
            if tyre_model:
                for brand in tyre_model.get_unique_brands():
                    brand_combo.addItem(brand)
            brand_combo.setCurrentText(product.get('tyre_brand', '') or '')
            brand_layout.addWidget(brand_combo, stretch=1)
            layout.addLayout(brand_layout)
            tyre_widgets['brand'] = brand_combo
            
            # Model
            model_layout = QHBoxLayout()
            model_label = QLabel("Model:")
            model_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            model_label.setMinimumWidth(150)
            model_layout.addWidget(model_label)
            model_entry = QLineEdit(product.get('tyre_model', '') or '')
            model_entry.setStyleSheet("font-size: 12px;")
            model_layout.addWidget(model_entry, stretch=1)
            layout.addLayout(model_layout)
            tyre_widgets['model'] = model_entry
            
            # Pattern
            pattern_layout = QHBoxLayout()
            pattern_label = QLabel("Pattern:")
            pattern_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            pattern_label.setMinimumWidth(150)
            pattern_layout.addWidget(pattern_label)
            pattern_entry = QLineEdit(product.get('tyre_pattern', '') or '')
            pattern_entry.setStyleSheet("font-size: 12px;")
            pattern_layout.addWidget(pattern_entry, stretch=1)
            layout.addLayout(pattern_layout)
            tyre_widgets['pattern'] = pattern_entry
            
            # Width, Profile, Diameter
            size_layout = QHBoxLayout()
            width_label = QLabel("Width:")
            width_label.setMinimumWidth(60)
            width_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            size_layout.addWidget(width_label)
            width_entry = QLineEdit(product.get('tyre_width', '') or '')
            width_entry.setStyleSheet("font-size: 12px;")
            size_layout.addWidget(width_entry)
            tyre_widgets['width'] = width_entry
            
            profile_label = QLabel("Profile:")
            profile_label.setMinimumWidth(60)
            profile_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            size_layout.addWidget(profile_label)
            profile_entry = QLineEdit(product.get('tyre_profile', '') or '')
            profile_entry.setStyleSheet("font-size: 12px;")
            size_layout.addWidget(profile_entry)
            tyre_widgets['profile'] = profile_entry
            
            diameter_label = QLabel("Diameter:")
            diameter_label.setMinimumWidth(70)
            diameter_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            size_layout.addWidget(diameter_label)
            diameter_entry = QLineEdit(product.get('tyre_diameter', '') or '')
            diameter_entry.setStyleSheet("font-size: 12px;")
            size_layout.addWidget(diameter_entry, stretch=1)
            layout.addLayout(size_layout)
            tyre_widgets['diameter'] = diameter_entry
            
            # Speed Rating, Load Index
            rating_layout = QHBoxLayout()
            speed_label = QLabel("Speed Rating:")
            speed_label.setMinimumWidth(100)
            speed_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            rating_layout.addWidget(speed_label)
            speed_combo = QComboBox()
            speed_combo.setStyleSheet("font-size: 12px;")
            speed_combo.setEditable(True)
            speed_combo.addItem("")
            if tyre_model:
                for rating in tyre_model.get_unique_speed_ratings():
                    speed_combo.addItem(rating)
            speed_combo.setCurrentText(product.get('tyre_speed_rating', '') or '')
            rating_layout.addWidget(speed_combo)
            tyre_widgets['speed_rating'] = speed_combo
            
            load_label = QLabel("Load Index:")
            load_label.setMinimumWidth(100)
            load_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            rating_layout.addWidget(load_label)
            load_combo = QComboBox()
            load_combo.setStyleSheet("font-size: 12px;")
            load_combo.setEditable(True)
            load_combo.addItem("")
            if tyre_model:
                for load in tyre_model.get_unique_load_indices():
                    load_combo.addItem(load)
            load_combo.setCurrentText(product.get('tyre_load_index', '') or '')
            rating_layout.addWidget(load_combo, stretch=1)
            layout.addLayout(rating_layout)
            tyre_widgets['load_index'] = load_combo
            
            # OE Fitment
            oe_layout = QHBoxLayout()
            oe_label = QLabel("OE Fitment:")
            oe_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            oe_label.setMinimumWidth(150)
            oe_layout.addWidget(oe_label)
            oe_combo = QComboBox()
            oe_combo.setStyleSheet("font-size: 12px;")
            oe_combo.setEditable(True)
            oe_combo.addItem("")
            if tyre_model:
                for fitment in tyre_model.get_unique_oe_fitments():
                    oe_combo.addItem(fitment)
            oe_combo.setCurrentText(product.get('tyre_oe_fitment', '') or '')
            oe_layout.addWidget(oe_combo, stretch=1)
            layout.addLayout(oe_layout)
            tyre_widgets['oe_fitment'] = oe_combo
            
            # EAN, Manufacturer Code
            code_layout = QHBoxLayout()
            ean_label = QLabel("EAN:")
            ean_label.setMinimumWidth(100)
            ean_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            code_layout.addWidget(ean_label)
            ean_entry = QLineEdit(product.get('tyre_ean', '') or '')
            ean_entry.setStyleSheet("font-size: 12px;")
            code_layout.addWidget(ean_entry)
            tyre_widgets['ean'] = ean_entry
            
            mfg_label = QLabel("Manufacturer Code:")
            mfg_label.setMinimumWidth(130)
            mfg_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            code_layout.addWidget(mfg_label)
            mfg_entry = QLineEdit(product.get('tyre_manufacturer_code', '') or '')
            mfg_entry.setStyleSheet("font-size: 12px;")
            code_layout.addWidget(mfg_entry, stretch=1)
            layout.addLayout(code_layout)
            tyre_widgets['manufacturer_code'] = mfg_entry
            
            # Vehicle Type, Product Type
            type2_layout = QHBoxLayout()
            vtype_label = QLabel("Vehicle Type:")
            vtype_label.setMinimumWidth(100)
            vtype_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            type2_layout.addWidget(vtype_label)
            vtype_combo = QComboBox()
            vtype_combo.setStyleSheet("font-size: 12px;")
            vtype_combo.setEditable(True)
            vtype_combo.addItem("")
            if tyre_model:
                for vtype in tyre_model.get_unique_vehicle_types():
                    vtype_combo.addItem(vtype)
            vtype_combo.setCurrentText(product.get('tyre_vehicle_type', '') or '')
            type2_layout.addWidget(vtype_combo)
            tyre_widgets['vehicle_type'] = vtype_combo
            
            ptype_label = QLabel("Product Type:")
            ptype_label.setMinimumWidth(100)
            ptype_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            type2_layout.addWidget(ptype_label)
            ptype_combo = QComboBox()
            ptype_combo.setStyleSheet("font-size: 12px;")
            ptype_combo.setEditable(True)
            ptype_combo.addItem("")
            if tyre_model:
                for ptype in tyre_model.get_unique_product_types():
                    ptype_combo.addItem(ptype)
            ptype_combo.setCurrentText(product.get('tyre_product_type', '') or '')
            type2_layout.addWidget(ptype_combo, stretch=1)
            layout.addLayout(type2_layout)
            tyre_widgets['product_type'] = ptype_combo
            
            # Rolling Resistance, Wet Grip
            perf_layout = QHBoxLayout()
            rr_label = QLabel("Rolling Resistance:")
            rr_label.setMinimumWidth(120)
            rr_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            perf_layout.addWidget(rr_label)
            rr_combo = QComboBox()
            rr_combo.setStyleSheet("font-size: 12px;")
            rr_combo.setEditable(True)
            rr_combo.addItem("")
            if tyre_model:
                for rr in tyre_model.get_unique_rolling_resistances():
                    rr_combo.addItem(rr)
            rr_combo.setCurrentText(product.get('tyre_rolling_resistance', '') or '')
            perf_layout.addWidget(rr_combo)
            tyre_widgets['rolling_resistance'] = rr_combo
            
            wg_label = QLabel("Wet Grip:")
            wg_label.setMinimumWidth(100)
            wg_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            perf_layout.addWidget(wg_label)
            wg_combo = QComboBox()
            wg_combo.setStyleSheet("font-size: 12px;")
            wg_combo.setEditable(True)
            wg_combo.addItem("")
            if tyre_model:
                for wg in tyre_model.get_unique_wet_grips():
                    wg_combo.addItem(wg)
            wg_combo.setCurrentText(product.get('tyre_wet_grip', '') or '')
            perf_layout.addWidget(wg_combo, stretch=1)
            layout.addLayout(perf_layout)
            tyre_widgets['wet_grip'] = wg_combo
            
            # Noise Class, Noise Performance
            noise_layout = QHBoxLayout()
            noise_class_label = QLabel("Noise Class:")
            noise_class_label.setMinimumWidth(120)
            noise_class_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            noise_layout.addWidget(noise_class_label)
            noise_class_combo = QComboBox()
            noise_class_combo.setStyleSheet("font-size: 12px;")
            noise_class_combo.setEditable(True)
            noise_class_combo.addItem("")
            noise_class_combo.setCurrentText(product.get('tyre_noise_class', '') or '')
            noise_layout.addWidget(noise_class_combo)
            tyre_widgets['noise_class'] = noise_class_combo
            
            noise_perf_label = QLabel("Noise Performance:")
            noise_perf_label.setMinimumWidth(120)
            noise_perf_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            noise_layout.addWidget(noise_perf_label)
            noise_perf_combo = QComboBox()
            noise_perf_combo.setStyleSheet("font-size: 12px;")
            noise_perf_combo.setEditable(True)
            noise_perf_combo.addItem("")
            noise_perf_combo.setCurrentText(product.get('tyre_noise_performance', '') or '')
            noise_layout.addWidget(noise_perf_combo, stretch=1)
            layout.addLayout(noise_layout)
            tyre_widgets['noise_performance'] = noise_perf_combo
            
            # Run Flat
            runflat_layout = QHBoxLayout()
            runflat_label = QLabel("Run Flat:")
            runflat_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            runflat_label.setMinimumWidth(150)
            runflat_layout.addWidget(runflat_label)
            runflat_check = QCheckBox()
            runflat_check.setChecked(product.get('tyre_run_flat', '') == 'Yes')
            runflat_layout.addWidget(runflat_check)
            runflat_layout.addStretch()
            layout.addLayout(runflat_layout)
            tyre_widgets['run_flat'] = runflat_check
            
            # URLs
            url_layout = QHBoxLayout()
            url_label = QLabel("Tyre URL:")
            url_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            url_label.setMinimumWidth(150)
            url_layout.addWidget(url_label)
            url_entry = QLineEdit(product.get('tyre_url', '') or '')
            url_entry.setStyleSheet("font-size: 12px;")
            url_layout.addWidget(url_entry, stretch=1)
            layout.addLayout(url_layout)
            tyre_widgets['tyre_url'] = url_entry
            
            brand_url_layout = QHBoxLayout()
            brand_url_label = QLabel("Brand URL:")
            brand_url_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            brand_url_label.setMinimumWidth(150)
            brand_url_layout.addWidget(brand_url_label)
            brand_url_entry = QLineEdit(product.get('tyre_brand_url', '') or '')
            brand_url_entry.setStyleSheet("font-size: 12px;")
            brand_url_layout.addWidget(brand_url_entry, stretch=1)
            layout.addLayout(brand_url_layout)
            tyre_widgets['brand_url'] = brand_url_entry
        
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
            
            if is_tyre:
                # Emit tyre update signal
                self.update_tyre_requested.emit(
                    product_id, new_stock_number, new_description, new_type,
                    tyre_widgets['brand'].currentText().strip(),
                    tyre_widgets['model'].text().strip(),
                    tyre_widgets['pattern'].text().strip(),
                    tyre_widgets['width'].text().strip(),
                    tyre_widgets['profile'].text().strip(),
                    tyre_widgets['diameter'].text().strip(),
                    tyre_widgets['speed_rating'].currentText().strip(),
                    tyre_widgets['load_index'].currentText().strip(),
                    tyre_widgets['oe_fitment'].currentText().strip(),
                    tyre_widgets['ean'].text().strip(),
                    tyre_widgets['manufacturer_code'].text().strip(),
                    tyre_widgets['vehicle_type'].currentText().strip(),
                    tyre_widgets['product_type'].currentText().strip(),
                    tyre_widgets['rolling_resistance'].currentText().strip(),
                    tyre_widgets['wet_grip'].currentText().strip(),
                    tyre_widgets['noise_class'].currentText().strip(),
                    tyre_widgets['noise_performance'].currentText().strip(),
                    "Yes" if tyre_widgets['run_flat'].isChecked() else "",
                    tyre_widgets['tyre_url'].text().strip(),
                    tyre_widgets['brand_url'].text().strip()
                )
            else:
                # Emit standard update signal
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
        
        # Disable delete button if product has history
        if has_history:
            delete_btn.setEnabled(False)
            delete_btn.setToolTip("Cannot delete product with transaction history")
        
        # Ctrl+Shift+D shortcut for delete
        delete_shortcut = QShortcut(QKeySequence("Ctrl+Shift+D"), dialog)
        delete_shortcut.activated.connect(handle_delete)
        if has_history:
            delete_shortcut.setEnabled(False)
        button_layout.addWidget(delete_btn)
        
        cancel_btn = QPushButton("Cancel (Esc)")
        cancel_btn.setMinimumWidth(140)
        cancel_btn.setMinimumHeight(30)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        scroll.setWidget(scroll_widget)
        
        main_layout = QVBoxLayout(dialog)
        main_layout.addWidget(scroll)
        
        # Set focus to stock number entry
        stock_entry.setFocus()
        stock_entry.selectAll()
        
        # Show dialog
        dialog.exec()
    
    def add_product(self):
        """Show dialog for adding a new product."""
        # First ask if this is a tyre product
        ask_dialog = QDialog(self)
        ask_dialog.setWindowTitle("Add Product")
        ask_dialog.setModal(True)
        ask_dialog.setMinimumSize(400, 150)
        apply_theme(ask_dialog)
        
        ask_layout = QVBoxLayout(ask_dialog)
        ask_layout.setSpacing(20)
        ask_layout.setContentsMargins(30, 30, 30, 30)
        
        ask_label = QLabel("Is this a tyre product?")
        ask_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        ask_layout.addWidget(ask_label)
        
        ask_button_layout = QHBoxLayout()
        ask_button_layout.addStretch()
        
        def handle_yes():
            ask_dialog.accept()
            self._show_add_tyre_product_dialog()
        
        def handle_no():
            ask_dialog.accept()
            self._show_add_standard_product_dialog()
        
        yes_btn = QPushButton("Yes")
        yes_btn.clicked.connect(handle_yes)
        yes_btn.setDefault(True)  # Make Yes the default button (Enter key)
        ask_button_layout.addWidget(yes_btn)
        
        no_btn = QPushButton("No")
        no_btn.clicked.connect(handle_no)
        ask_button_layout.addWidget(no_btn)
        
        ask_layout.addLayout(ask_button_layout)
        
        # Set focus on Yes button so user can press Enter immediately
        yes_btn.setFocus()
        
        if ask_dialog.exec() == QDialog.DialogCode.Rejected:
            return
    
    def _show_add_standard_product_dialog(self):
        """Show dialog for adding a standard (non-tyre) product."""
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
    
    def _show_add_tyre_product_dialog(self):
        """Show dialog for adding a tyre product with all tyre fields."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Tyre Product")
        dialog.setModal(True)
        dialog.setMinimumSize(700, 800)
        dialog.resize(700, 800)
        apply_theme(dialog)
        
        # Add Escape key shortcut for cancel
        esc_shortcut = QShortcut(QKeySequence("Escape"), dialog)
        esc_shortcut.activated.connect(dialog.reject)
        
        # Scroll area for long form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: #ffffff;")
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background-color: #ffffff;")
        layout = QVBoxLayout(scroll_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("Add New Tyre Product")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Create two-column grid layout
        grid_layout = QGridLayout()
        grid_layout.setColumnStretch(0, 0)  # Label column - fixed width
        grid_layout.setColumnStretch(1, 1)   # Input column - stretches
        grid_layout.setSpacing(10)
        grid_layout.setColumnMinimumWidth(0, 150)  # Minimum width for label column
        
        row = 0
        
        # Stock Number
        stock_label = QLabel("Stock Number:")
        stock_label.setStyleSheet("font-size: 11px;")
        grid_layout.addWidget(stock_label, row, 0)
        stock_entry = QLineEdit()
        stock_entry.setStyleSheet("font-size: 11px;")
        grid_layout.addWidget(stock_entry, row, 1)
        row += 1
        
        # Description
        desc_label = QLabel("Description:")
        desc_label.setStyleSheet("font-size: 11px;")
        grid_layout.addWidget(desc_label, row, 0)
        desc_entry = QLineEdit()
        desc_entry.setStyleSheet("font-size: 11px;")
        desc_entry.setPlaceholderText("e.g., 225/45R17 91W")
        grid_layout.addWidget(desc_entry, row, 1)
        row += 1
        
        # Validation status label (spans both columns)
        validation_label = QLabel("")
        validation_label.setStyleSheet("font-size: 10px; color: red;")
        validation_label.setWordWrap(True)
        grid_layout.addWidget(validation_label, row, 0, 1, 2)
        row += 1
        
        # Get tyre_model if available (for brand/model dropdowns)
        tyre_model = getattr(self, 'tyre_model', None)
        
        # Brand
        brand_label = QLabel("Brand:")
        brand_label.setStyleSheet("font-size: 11px;")
        grid_layout.addWidget(brand_label, row, 0)
        brand_combo = QComboBox()
        brand_combo.setStyleSheet("font-size: 11px;")
        brand_combo.setEditable(True)
        brand_combo.addItem("")
        if tyre_model:
            for brand in tyre_model.get_unique_brands():
                brand_combo.addItem(brand)
        grid_layout.addWidget(brand_combo, row, 1)
        row += 1
        
        # Model (dropdown that updates based on brand)
        model_label = QLabel("Model:")
        model_label.setStyleSheet("font-size: 11px;")
        grid_layout.addWidget(model_label, row, 0)
        model_combo = QComboBox()
        model_combo.setStyleSheet("font-size: 11px;")
        model_combo.setEditable(True)
        model_combo.addItem("")
        grid_layout.addWidget(model_combo, row, 1)
        row += 1
        
        # Function to update model dropdown based on brand selection
        def update_model_dropdown():
            """Update model dropdown based on selected brand."""
            brand = brand_combo.currentText().strip()
            model_combo.clear()
            model_combo.addItem("")
            if brand and tyre_model:
                models = tyre_model.get_unique_models_by_brand(brand)
                for model in models:
                    model_combo.addItem(model)
        
        # Connect brand change to model update
        brand_combo.currentTextChanged.connect(update_model_dropdown)
        brand_combo.editTextChanged.connect(update_model_dropdown)
        
        # OE Fitment
        oe_label = QLabel("OE Fitment:")
        oe_label.setStyleSheet("font-size: 11px;")
        grid_layout.addWidget(oe_label, row, 0)
        oe_combo = QComboBox()
        oe_combo.setStyleSheet("font-size: 11px;")
        oe_combo.setEditable(True)
        oe_combo.addItem("")
        if tyre_model:
            for fitment in tyre_model.get_unique_oe_fitments():
                oe_combo.addItem(fitment)
        grid_layout.addWidget(oe_combo, row, 1)
        row += 1
        
        # Note: Pattern, Width, Profile, Diameter, Speed Rating, and Load Index
        # are automatically extracted from the description field
        note_label = QLabel("Note: Pattern, Width, Profile, Diameter, Speed Rating, and Load Index are automatically extracted from the description.")
        note_label.setStyleSheet("font-size: 10px; color: gray; font-style: italic;")
        note_label.setWordWrap(True)
        grid_layout.addWidget(note_label, row, 0, 1, 2)
        row += 1
        
        # EAN
        ean_label = QLabel("EAN:")
        ean_label.setStyleSheet("font-size: 11px;")
        grid_layout.addWidget(ean_label, row, 0)
        ean_entry = QLineEdit()
        ean_entry.setStyleSheet("font-size: 11px;")
        grid_layout.addWidget(ean_entry, row, 1)
        row += 1
        
        # Manufacturer Code
        mfg_label = QLabel("Manufacturer Code:")
        mfg_label.setStyleSheet("font-size: 11px;")
        grid_layout.addWidget(mfg_label, row, 0)
        mfg_entry = QLineEdit()
        mfg_entry.setStyleSheet("font-size: 11px;")
        grid_layout.addWidget(mfg_entry, row, 1)
        row += 1
        
        # Vehicle Type
        vtype_label = QLabel("Vehicle Type:")
        vtype_label.setStyleSheet("font-size: 11px;")
        grid_layout.addWidget(vtype_label, row, 0)
        vtype_combo = QComboBox()
        vtype_combo.setStyleSheet("font-size: 11px;")
        vtype_combo.setEditable(True)
        vtype_combo.addItem("")
        if tyre_model:
            for vtype in tyre_model.get_unique_vehicle_types():
                vtype_combo.addItem(vtype)
        grid_layout.addWidget(vtype_combo, row, 1)
        row += 1
        
        # Product Type
        ptype_label = QLabel("Product Type:")
        ptype_label.setStyleSheet("font-size: 11px;")
        grid_layout.addWidget(ptype_label, row, 0)
        ptype_combo = QComboBox()
        ptype_combo.setStyleSheet("font-size: 11px;")
        ptype_combo.setEditable(True)
        ptype_combo.addItem("")
        if tyre_model:
            for ptype in tyre_model.get_unique_product_types():
                ptype_combo.addItem(ptype)
        grid_layout.addWidget(ptype_combo, row, 1)
        row += 1
        
        # Rolling Resistance
        rr_label = QLabel("Rolling Resistance:")
        rr_label.setStyleSheet("font-size: 11px;")
        grid_layout.addWidget(rr_label, row, 0)
        rr_combo = QComboBox()
        rr_combo.setStyleSheet("font-size: 11px;")
        rr_combo.setEditable(True)
        rr_combo.addItem("")
        if tyre_model:
            for rr in tyre_model.get_unique_rolling_resistances():
                rr_combo.addItem(rr)
        grid_layout.addWidget(rr_combo, row, 1)
        row += 1
        
        # Wet Grip
        wg_label = QLabel("Wet Grip:")
        wg_label.setStyleSheet("font-size: 11px;")
        grid_layout.addWidget(wg_label, row, 0)
        wg_combo = QComboBox()
        wg_combo.setStyleSheet("font-size: 11px;")
        wg_combo.setEditable(True)
        wg_combo.addItem("")
        if tyre_model:
            for wg in tyre_model.get_unique_wet_grips():
                wg_combo.addItem(wg)
        grid_layout.addWidget(wg_combo, row, 1)
        row += 1
        
        # Run Flat
        runflat_label = QLabel("Run Flat:")
        runflat_label.setStyleSheet("font-size: 11px;")
        grid_layout.addWidget(runflat_label, row, 0)
        runflat_check = QCheckBox()
        grid_layout.addWidget(runflat_check, row, 1, Qt.AlignmentFlag.AlignLeft)
        row += 1
        
        # Note: Tyre URL and Brand URL are automatically fetched from the database
        # based on brand and model selection
        
        layout.addLayout(grid_layout)
        
        layout.addStretch()
        
        # Status label
        status_label = QLabel("")
        status_label.setStyleSheet("color: red; font-size: 9px;")
        layout.addWidget(status_label)
        
        # Store extracted specs for use in save handler
        extracted_specs = {'pattern': '', 'width': '', 'profile': '', 'diameter': '', 
                          'speed_rating': '', 'load_index': ''}
        
        # Store fetched URLs (automatically populated from database)
        fetched_urls = {'tyre_url': '', 'brand_url': ''}
        
        # Function to fetch URLs from database based on brand/model
        def fetch_urls_from_database():
            """Fetch tyre URL and brand URL from database based on brand/model selection."""
            brand = brand_combo.currentText().strip()
            model = model_combo.currentText().strip()
            
            if not brand:
                fetched_urls['tyre_url'] = ''
                fetched_urls['brand_url'] = ''
                return
            
            if tyre_model:
                tyre_url, brand_url = tyre_model.get_urls_by_brand_model(brand, model if model else None)
                fetched_urls['tyre_url'] = tyre_url
                fetched_urls['brand_url'] = brand_url
            else:
                fetched_urls['tyre_url'] = ''
                fetched_urls['brand_url'] = ''
        
        # Connect brand and model changes to URL fetching
        brand_combo.currentTextChanged.connect(fetch_urls_from_database)
        brand_combo.editTextChanged.connect(fetch_urls_from_database)
        model_combo.currentTextChanged.connect(fetch_urls_from_database)
        model_combo.editTextChanged.connect(fetch_urls_from_database)
        
        # Auto-extract specs from description
        def extract_specs_from_description():
            """Extract tyre specifications from description."""
            description = desc_entry.text().strip()
            
            # Reset extracted specs
            extracted_specs.update({'pattern': '', 'width': '', 'profile': '', 'diameter': '', 
                                  'speed_rating': '', 'load_index': ''})
            
            if not description:
                validation_label.setText("")
                return
            
            # Validate description format
            is_valid, error_msg = validate_tyre_description(description)
            if not is_valid:
                validation_label.setText(f"⚠ {error_msg}")
                validation_label.setStyleSheet("font-size: 10px; color: red;")
                return
            
            # Clear validation error
            validation_label.setText("✓ Valid format - specs extracted")
            validation_label.setStyleSheet("font-size: 10px; color: green;")
            
            # Extract specs (OE fitment is not extracted, user selects from dropdown)
            specs = extract_tyre_specs(description)
            if specs:
                width, profile, diameter, speed_rating, load_index, _ = specs  # Ignore OE fitment
                
                # Store extracted values
                extracted_specs['width'] = width
                extracted_specs['profile'] = profile
                extracted_specs['diameter'] = diameter
                extracted_specs['speed_rating'] = speed_rating
                extracted_specs['load_index'] = load_index
                
                # Generate pattern code: width + profile + diameter + speed_rating
                if width and profile and diameter and speed_rating:
                    extracted_specs['pattern'] = f"{width}{profile}{diameter}{speed_rating}"
        
        # Connect description field to auto-extraction
        desc_entry.textChanged.connect(extract_specs_from_description)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Flag to prevent multiple save attempts
        _saving = False
        
        def handle_save():
            nonlocal _saving
            # Prevent multiple simultaneous save attempts
            if _saving:
                return
            _saving = True
            
            try:
                product_stock_number = stock_entry.text().strip()
                product_description = desc_entry.text().strip()
                # Type is automatically "Tyre" for tyre products
                product_type = "Tyre"
                
                if not product_stock_number:
                    status_label.setText("Please enter a stock number")
                    _saving = False
                    return
                
                # Validate description format if provided
                if product_description:
                    is_valid, error_msg = validate_tyre_description(product_description)
                    if not is_valid:
                        status_label.setText(f"Invalid description format: {error_msg}")
                        _saving = False
                        return
                    
                    # Re-extract specs to ensure we have the latest values
                    extract_specs_from_description()
                
                # Re-fetch URLs to ensure we have the latest values
                fetch_urls_from_database()
                
                # Emit signal with all tyre fields (using extracted specs and dropdown values)
                self.create_tyre_requested.emit(
                    product_stock_number, product_description, product_type,
                    brand_combo.currentText().strip(),
                    model_combo.currentText().strip(),
                    extracted_specs['pattern'],
                    extracted_specs['width'],
                    extracted_specs['profile'],
                    extracted_specs['diameter'],
                    extracted_specs['speed_rating'],
                    extracted_specs['load_index'],
                    oe_combo.currentText().strip(),  # Use dropdown value instead of extracted
                    ean_entry.text().strip(),
                    mfg_entry.text().strip(),
                    vtype_combo.currentText().strip(),
                    ptype_combo.currentText().strip(),
                    rr_combo.currentText().strip(),
                    wg_combo.currentText().strip(),
                    "Yes" if runflat_check.isChecked() else "",
                    fetched_urls['tyre_url'],  # Use fetched URL from database
                    fetched_urls['brand_url']  # Use fetched URL from database
                )
                dialog.accept()
            except Exception:
                _saving = False
                raise
        
        save_btn = QPushButton("Save (Ctrl+Enter)")
        save_btn.setMinimumWidth(160)
        save_btn.setMinimumHeight(30)
        save_btn.setDefault(True)
        save_btn.clicked.connect(handle_save)
        
        ctrl_enter_shortcut = QShortcut(QKeySequence("Ctrl+Return"), dialog)
        ctrl_enter_shortcut.activated.connect(handle_save)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel (Esc)")
        cancel_btn.setMinimumWidth(140)
        cancel_btn.setMinimumHeight(30)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        scroll.setWidget(scroll_widget)
        
        main_layout = QVBoxLayout(dialog)
        main_layout.addWidget(scroll)
        
        stock_entry.setFocus()
        dialog.exec()
    
    def load_products(self, products: List[Dict[str, any]]):
        """Load products into the table."""
        # Store all products for filtering
        self._all_products_data = products
        # Apply current filter
        self._filter_products()
    
    def _filter_products(self):
        """Filter products based on search text."""
        search_text = self.products_search_box.text().strip().lower()
        
        if not search_text:
            filtered_products = self._all_products_data
        else:
            filtered_products = [
                p for p in self._all_products_data
                if search_text in str(p.get('id', '')).lower()
                or search_text in p.get('stock_number', '').lower()
                or search_text in p.get('description', '').lower()
                or search_text in p.get('type', '').lower()
            ]
        
        self.products_table.setRowCount(len(filtered_products))
        
        for row, product in enumerate(filtered_products):
            self.products_table.setItem(row, 0, QTableWidgetItem(str(product['id'])))
            self.products_table.setItem(row, 1, QTableWidgetItem(product.get('stock_number', '')))
            self.products_table.setItem(row, 2, QTableWidgetItem(product.get('description', '')))
            self.products_table.setItem(row, 3, QTableWidgetItem(product.get('type', '')))
        
        # Resize columns to content
        self.products_table.resizeColumnsToContents()
        header = self.products_table.horizontalHeader()
        header.resizeSection(0, 80)
        if len(filtered_products) > 0:
            header.resizeSection(1, 150)
            header.resizeSection(2, 300)
        
        # Auto-select first row and set focus to table if data exists
        if len(filtered_products) > 0:
            self.products_table.selectRow(0)
            self.products_table.setFocus()
            # Ensure the first row is visible
            self.products_table.scrollToItem(self.products_table.item(0, 0))
            # Update selected product ID
            self.selected_product_id = filtered_products[0]['id']
    
    def load_stock_audit(self, history: Dict[str, List[Dict]]):
        """Load stock audit history into the audit table."""
        invoices = history.get('invoices', [])
        sales = history.get('sales', [])
        
        # Combine invoices and sales into single list
        all_transactions = []
        for inv in invoices:
            all_transactions.append({
                'type': 'Invoice',
                'document_number': inv.get('invoice_number', ''),
                'date': inv.get('invoice_date', ''),
                'supplier_customer': inv.get('supplier_name', ''),
                'quantity': inv.get('quantity', 0),
                'unit_price': inv.get('unit_price', 0),
                'total': inv.get('line_total', 0)
            })
        for sale in sales:
            all_transactions.append({
                'type': 'Sale',
                'document_number': sale.get('invoice_number', ''),
                'date': sale.get('invoice_date', ''),
                'supplier_customer': sale.get('customer_name', ''),
                'quantity': sale.get('quantity', 0),
                'unit_price': sale.get('unit_price', 0),
                'total': sale.get('line_total', 0)
            })
        
        # Sort by date descending
        all_transactions.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        self.audit_table.setRowCount(len(all_transactions))
        
        for row, transaction in enumerate(all_transactions):
            self.audit_table.setItem(row, 0, QTableWidgetItem(transaction.get('type', '')))
            self.audit_table.setItem(row, 1, QTableWidgetItem(str(transaction.get('document_number', ''))))
            self.audit_table.setItem(row, 2, QTableWidgetItem(str(transaction.get('date', ''))))
            self.audit_table.setItem(row, 3, QTableWidgetItem(transaction.get('supplier_customer', '')))
            
            # Format quantity
            qty = transaction.get('quantity', 0)
            qty_str = f"{qty:.2f}" if isinstance(qty, (int, float)) else str(qty)
            self.audit_table.setItem(row, 4, QTableWidgetItem(qty_str))
            
            # Format unit price
            price = transaction.get('unit_price', 0)
            price_str = f"£{price:.2f}" if isinstance(price, (int, float)) else str(price)
            self.audit_table.setItem(row, 5, QTableWidgetItem(price_str))
            
            # Format total
            total = transaction.get('total', 0)
            total_str = f"£{total:.2f}" if isinstance(total, (int, float)) else str(total)
            self.audit_table.setItem(row, 6, QTableWidgetItem(total_str))
        
        # Update label
        if self.selected_product_id:
            if len(all_transactions) > 0:
                self.audit_label.setText(f"Stock audit history for product ID {self.selected_product_id} ({len(all_transactions)} transactions)")
            else:
                self.audit_label.setText(f"No transaction history found for product ID {self.selected_product_id}")
        else:
            self.audit_label.setText("Select a product from the Products tab to view stock audit history.")
    
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

