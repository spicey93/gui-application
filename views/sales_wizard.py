"""Sales wizard dialog for creating new sales documents."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QComboBox, QTableWidget, QTableWidgetItem, QDateEdit, QTextEdit,
    QFormLayout, QDialogButtonBox, QWidget, QStackedWidget, QMessageBox,
    QHeaderView, QDoubleSpinBox
)
from PySide6.QtCore import Qt, QDate, Signal
from typing import List, Dict, Optional
from views.widgets.common_dialogs import show_confirmation_dialog


class SalesWizardDialog(QDialog):
    """Multi-step wizard dialog for creating sales documents."""
    
    def __init__(self, parent=None, customers: List[Dict] = None,
                 products: List[Dict] = None, services: List[Dict] = None,
                 vehicles: List[Dict] = None, customer_model=None, user_id: Optional[int] = None,
                 refresh_customers_callback=None):
        """
        Initialize the sales wizard dialog.
        
        Args:
            parent: Parent widget
            customers: List of customers
            products: List of products
            services: List of services
            vehicles: List of vehicles
            customer_model: Customer model instance for searching
            user_id: Current user ID
            refresh_customers_callback: Callback to refresh customer list after creation
        """
        super().__init__(parent)
        self.customers = customers or []
        self.products = products or []
        self.services = services or []
        self.vehicles = vehicles or []
        self.customer_model = customer_model
        self.user_id = user_id
        self.refresh_customers_callback = refresh_customers_callback
        
        self.selected_customer_id: Optional[int] = None
        self.selected_vehicle_id: Optional[int] = None
        self.document_type: str = "order"  # Default to order
        self.document_status: str = "draft"
        self.items: List[Dict] = []  # List of items to add
        
        self.setWindowTitle("Create New Sale")
        self.setMinimumSize(700, 600)
        self._create_widgets()
    
    def _create_widgets(self):
        """Create and layout wizard widgets."""
        layout = QVBoxLayout(self)
        
        # Create stacked widget for steps
        self.stacked_widget = QStackedWidget()
        
        # Step 1: Customer Selection
        self.step1_widget = self._create_customer_step()
        self.stacked_widget.addWidget(self.step1_widget)
        
        # Step 2: Vehicle Selection
        self.step2_widget = self._create_vehicle_step()
        self.stacked_widget.addWidget(self.step2_widget)
        
        # Step 3: Products/Services
        self.step3_widget = self._create_items_step()
        self.stacked_widget.addWidget(self.step3_widget)
        
        # Step 4: Notes and Final
        self.step4_widget = self._create_final_step()
        self.stacked_widget.addWidget(self.step4_widget)
        
        layout.addWidget(self.stacked_widget)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self._previous_step)
        self.back_button.setEnabled(False)
        
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self._next_step)
        
        nav_layout.addWidget(self.back_button)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_button)
        
        layout.addLayout(nav_layout)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.current_step = 0
        self._update_navigation()
    
    def _create_customer_step(self) -> QWidget:
        """Create customer entry step with lookup option."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("Step 1: Customer Details (Optional)")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Lookup Customer button at the top
        lookup_layout = QHBoxLayout()
        lookup_customer_btn = QPushButton("🔍 Lookup Customer")
        lookup_customer_btn.setMinimumHeight(35)
        lookup_customer_btn.clicked.connect(self._lookup_customer)
        lookup_layout.addWidget(lookup_customer_btn)
        lookup_layout.addStretch()
        layout.addLayout(lookup_layout)
        
        # Contact Information section
        contact_group = QWidget()
        contact_layout = QVBoxLayout(contact_group)
        contact_layout.setContentsMargins(0, 0, 0, 0)
        contact_layout.setSpacing(10)
        
        contact_label = QLabel("Contact Information")
        contact_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")
        contact_layout.addWidget(contact_label)
        
        # Name and Phone in a horizontal layout
        name_phone_layout = QHBoxLayout()
        name_phone_layout.setSpacing(15)
        
        name_label = QLabel("Name:")
        name_label.setMinimumWidth(80)
        self.customer_name_input = QLineEdit()
        self.customer_name_input.setPlaceholderText("Enter customer name (optional)")
        name_phone_layout.addWidget(name_label)
        name_phone_layout.addWidget(self.customer_name_input, stretch=2)
        
        phone_label = QLabel("Phone:")
        phone_label.setMinimumWidth(80)
        self.customer_phone_input = QLineEdit()
        self.customer_phone_input.setPlaceholderText("Enter phone number")
        name_phone_layout.addWidget(phone_label)
        name_phone_layout.addWidget(self.customer_phone_input, stretch=1)
        
        contact_layout.addLayout(name_phone_layout)
        layout.addWidget(contact_group)
        
        # Address section
        address_group = QWidget()
        address_layout = QVBoxLayout(address_group)
        address_layout.setContentsMargins(0, 0, 0, 0)
        address_layout.setSpacing(10)
        
        address_label = QLabel("Address")
        address_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")
        address_layout.addWidget(address_label)
        
        # Address line 1: House name/number
        house_label = QLabel("House Name/No:")
        house_label.setMinimumWidth(80)
        self.customer_house_input = QLineEdit()
        self.customer_house_input.setPlaceholderText("House name/number")
        house_layout = QHBoxLayout()
        house_layout.addWidget(house_label)
        house_layout.addWidget(self.customer_house_input)
        address_layout.addLayout(house_layout)
        
        # Address line 2: Street
        street_label = QLabel("Street:")
        street_label.setMinimumWidth(80)
        self.customer_street_input = QLineEdit()
        self.customer_street_input.setPlaceholderText("Street address")
        street_layout = QHBoxLayout()
        street_layout.addWidget(street_label)
        street_layout.addWidget(self.customer_street_input)
        address_layout.addLayout(street_layout)
        
        # City, County, Postcode in a horizontal layout
        city_county_postcode_layout = QHBoxLayout()
        city_county_postcode_layout.setSpacing(15)
        
        city_label = QLabel("City:")
        city_label.setMinimumWidth(80)
        self.customer_city_input = QLineEdit()
        self.customer_city_input.setPlaceholderText("City")
        city_county_postcode_layout.addWidget(city_label)
        city_county_postcode_layout.addWidget(self.customer_city_input, stretch=2)
        
        county_label = QLabel("County:")
        county_label.setMinimumWidth(80)
        self.customer_county_input = QLineEdit()
        self.customer_county_input.setPlaceholderText("County")
        city_county_postcode_layout.addWidget(county_label)
        city_county_postcode_layout.addWidget(self.customer_county_input, stretch=2)
        
        postcode_label = QLabel("Postcode:")
        postcode_label.setMinimumWidth(80)
        self.customer_postcode_input = QLineEdit()
        self.customer_postcode_input.setPlaceholderText("Postcode")
        city_county_postcode_layout.addWidget(postcode_label)
        city_county_postcode_layout.addWidget(self.customer_postcode_input, stretch=1)
        
        address_layout.addLayout(city_county_postcode_layout)
        layout.addWidget(address_group)
        
        layout.addStretch()
        
        # Set focus to name field
        self.customer_name_input.setFocus()
        
        return widget
    
    def _create_vehicle_step(self) -> QWidget:
        """Create vehicle selection step."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        
        title = QLabel("Step 2: Select Vehicle (Optional)")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        form_layout = QFormLayout()
        
        # VRM lookup
        vrm_layout = QHBoxLayout()
        self.vrm_input = QLineEdit()
        self.vrm_input.setPlaceholderText("Enter VRM")
        lookup_btn = QPushButton("Lookup VRM")
        lookup_btn.clicked.connect(self._lookup_vrm)
        vrm_layout.addWidget(self.vrm_input)
        vrm_layout.addWidget(lookup_btn)
        form_layout.addRow("VRM:", vrm_layout)
        
        # Vehicle selector
        self.vehicle_combo = QComboBox()
        self.vehicle_combo.setEditable(False)
        self.vehicle_combo.addItem("-- No Vehicle --", None)
        for vehicle in self.vehicles:
            vrm = vehicle.get('vrm', '')
            make = vehicle.get('make', '')
            model = vehicle.get('model', '')
            display = f"{vrm} - {make} {model}".strip()
            self.vehicle_combo.addItem(display, vehicle.get('id'))
        form_layout.addRow("Vehicle:", self.vehicle_combo)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        return widget
    
    def _create_items_step(self) -> QWidget:
        """Create products/services selection step."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        
        title = QLabel("Step 3: Add Products & Services")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Items table - editable for quantity and price
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels(
            ["Type", "Stock/Code", "Description", "Qty", "Price", "Total"]
        )
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Stock/Code
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Description
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Qty
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Price
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Total
        self.items_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.items_table.setAlternatingRowColors(True)
        # Enable editing for quantity and price columns only
        self.items_table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.SelectedClicked)
        # Connect cell changed signal for editing quantity/price
        self.items_table.cellChanged.connect(self._on_item_cell_changed)
        layout.addWidget(self.items_table, stretch=1)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        add_product_btn = QPushButton("Add Product (Ctrl+P)")
        add_product_btn.clicked.connect(self._add_product)
        add_service_btn = QPushButton("Add Service (Ctrl+S)")
        add_service_btn.clicked.connect(self._add_service)
        remove_item_btn = QPushButton("Remove Item")
        remove_item_btn.clicked.connect(self._remove_item)
        
        actions_layout.addWidget(add_product_btn)
        actions_layout.addWidget(add_service_btn)
        actions_layout.addWidget(remove_item_btn)
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
        
        # Totals
        self.items_total_label = QLabel("Total: £0.00")
        self.items_total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.items_total_label)
        
        layout.addStretch()
        
        return widget
    
    def _create_final_step(self) -> QWidget:
        """Create final step with notes and document type."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        
        title = QLabel("Step 4: Final Details")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        form_layout = QFormLayout()
        
        # Document date
        self.document_date_input = QDateEdit()
        self.document_date_input.setDate(QDate.currentDate())
        self.document_date_input.setCalendarPopup(True)
        form_layout.addRow("Document Date*:", self.document_date_input)
        
        # Document type
        self.document_type_combo = QComboBox()
        self.document_type_combo.addItems(["quote", "order", "invoice"])
        self.document_type_combo.setCurrentText("order")  # Default to order
        self.document_type_combo.currentTextChanged.connect(self._on_document_type_changed)
        form_layout.addRow("Document Type*:", self.document_type_combo)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(["draft", "sent", "finalized"])
        form_layout.addRow("Status:", self.status_combo)
        
        # Generated document number (read-only)
        self.document_number_label = QLabel("")
        self.document_number_label.setStyleSheet("font-weight: bold; color: blue;")
        form_layout.addRow("Document Number:", self.document_number_label)
        self._update_document_number_preview()
        
        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(150)
        self.notes_input.setPlaceholderText("Enter notes (optional)")
        form_layout.addRow("Notes:", self.notes_input)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        return widget
    
    def _lookup_customer(self):
        """Show customer lookup/search dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Lookup Customer")
        dialog.setMinimumSize(700, 500)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Search fields
        search_group = QWidget()
        search_layout = QVBoxLayout(search_group)
        search_layout.setSpacing(10)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        search_label = QLabel("Search by:")
        search_label.setStyleSheet("font-weight: bold;")
        search_layout.addWidget(search_label)
        
        # Search fields in a horizontal layout
        search_grid = QHBoxLayout()
        search_grid.setSpacing(15)
        
        name_search = QLineEdit()
        name_search.setPlaceholderText("Name...")
        name_label = QLabel("Name:")
        name_label.setMinimumWidth(80)
        name_layout = QHBoxLayout()
        name_layout.addWidget(name_label)
        name_layout.addWidget(name_search)
        search_grid.addLayout(name_layout)
        
        postcode_search = QLineEdit()
        postcode_search.setPlaceholderText("Postcode...")
        postcode_label = QLabel("Postcode:")
        postcode_label.setMinimumWidth(80)
        postcode_layout = QHBoxLayout()
        postcode_layout.addWidget(postcode_label)
        postcode_layout.addWidget(postcode_search)
        search_grid.addLayout(postcode_layout)
        
        phone_search = QLineEdit()
        phone_search.setPlaceholderText("Phone...")
        phone_label = QLabel("Phone:")
        phone_label.setMinimumWidth(80)
        phone_layout = QHBoxLayout()
        phone_layout.addWidget(phone_label)
        phone_layout.addWidget(phone_search)
        search_grid.addLayout(phone_layout)
        
        search_layout.addLayout(search_grid)
        layout.addWidget(search_group)
        
        # Custom table widget with Enter key support
        class CustomerSearchTableWidget(QTableWidget):
            def __init__(self, select_callback):
                super().__init__()
                self.select_callback = select_callback
            
            def keyPressEvent(self, event):
                """Handle Enter key to select customer."""
                if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                    if self.selectedItems():
                        row = self.selectedItems()[0].row()
                        self.select_callback(row)
                        event.accept()
                        return
                super().keyPressEvent(event)
        
        # Results table
        results_table = CustomerSearchTableWidget(lambda row: select_customer_from_row(row))
        results_table.setColumnCount(4)
        results_table.setHorizontalHeaderLabels(["ID", "Name", "Phone", "Postcode"])
        header = results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        results_table.setAlternatingRowColors(True)
        results_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        layout.addWidget(results_table, stretch=1)
        
        # Store filtered customers
        filtered_customers = []
        
        def perform_search():
            """Perform customer search on the existing customers list."""
            nonlocal filtered_customers
            name_text = name_search.text().lower().strip()
            postcode_text = postcode_search.text().lower().strip()
            phone_text = phone_search.text().lower().strip()
            
            if not name_text and not postcode_text and not phone_text:
                # Show all customers
                filtered_customers = self.customers
            else:
                # Filter customers by search criteria
                filtered_customers = [
                    c for c in self.customers
                    if (not name_text or name_text in c.get('name', '').lower()) and
                       (not postcode_text or postcode_text in c.get('postcode', '').lower()) and
                       (not phone_text or phone_text in c.get('phone', '').lower())
                ]
            
            results_table.setRowCount(len(filtered_customers))
            for row, customer in enumerate(filtered_customers):
                results_table.setItem(row, 0, QTableWidgetItem(str(customer.get('id', ''))))
                results_table.setItem(row, 1, QTableWidgetItem(customer.get('name', '')))
                results_table.setItem(row, 2, QTableWidgetItem(customer.get('phone', '')))
                results_table.setItem(row, 3, QTableWidgetItem(customer.get('postcode', '')))
            
            # Select first row if results exist
            if filtered_customers:
                results_table.selectRow(0)
                results_table.setFocus()
        
        def select_customer_from_row(row: int):
            """Select customer from table row and populate fields."""
            if 0 <= row < len(filtered_customers):
                customer = filtered_customers[row]
                
                # Populate fields
                self.customer_name_input.setText(customer.get('name', ''))
                self.customer_phone_input.setText(customer.get('phone', ''))
                self.customer_house_input.setText(customer.get('house_name_no', ''))
                self.customer_street_input.setText(customer.get('street_address', ''))
                self.customer_city_input.setText(customer.get('city', ''))
                self.customer_county_input.setText(customer.get('county', ''))
                self.customer_postcode_input.setText(customer.get('postcode', ''))
                self.selected_customer_id = customer.get('internal_id')
                dialog.accept()
        
        # Connect search fields - search as you type
        name_search.textChanged.connect(perform_search)
        postcode_search.textChanged.connect(perform_search)
        phone_search.textChanged.connect(perform_search)
        name_search.returnPressed.connect(perform_search)
        postcode_search.returnPressed.connect(perform_search)
        phone_search.returnPressed.connect(perform_search)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        
        def handle_ok():
            """Handle OK button - select highlighted customer."""
            selected_items = results_table.selectedItems()
            if selected_items:
                row = selected_items[0].row()
                select_customer_from_row(row)
            else:
                QMessageBox.warning(dialog, "Warning", "Please select a customer")
        
        button_box.accepted.connect(handle_ok)
        button_box.rejected.connect(dialog.reject)
        button_layout.addWidget(button_box)
        layout.addLayout(button_layout)
        
        # Perform initial search to show all customers
        perform_search()
        
        # Set focus to name search field
        name_search.setFocus()
        
        dialog.exec()
    
    def _lookup_vrm(self):
        """Lookup vehicle by VRM."""
        vrm = self.vrm_input.text().strip().upper()
        if not vrm:
            QMessageBox.warning(self, "Warning", "Please enter a VRM")
            return
        
        # Find vehicle in list
        for vehicle in self.vehicles:
            if vehicle.get('vrm', '').upper() == vrm:
                # Select in combo
                for i in range(self.vehicle_combo.count()):
                    if self.vehicle_combo.itemData(i) == vehicle.get('id'):
                        self.vehicle_combo.setCurrentIndex(i)
                        break
                return
        
        QMessageBox.information(self, "Info", f"Vehicle with VRM {vrm} not found. VRM lookup will be implemented in the future.")
    
    def _add_product(self):
        """Show search dialog to add product."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Search Products")
        dialog.setMinimumSize(600, 500)
        layout = QVBoxLayout(dialog)
        
        # Search entry
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_entry = QLineEdit()
        search_entry.setPlaceholderText("Enter stock number or description...")
        search_entry.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        search_layout.addWidget(search_label)
        search_layout.addWidget(search_entry)
        layout.addLayout(search_layout)
        
        # Custom table widget with Enter key support
        class ProductSearchTableWidget(QTableWidget):
            def __init__(self, select_callback):
                super().__init__()
                self.select_callback = select_callback
            
            def keyPressEvent(self, event):
                """Handle Enter key to select product."""
                if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                    if self.selectedItems():
                        row = self.selectedItems()[0].row()
                        self.select_callback(row)
                        event.accept()
                        return
                super().keyPressEvent(event)
        
        results_table = ProductSearchTableWidget(lambda row: select_product(row))
        results_table.setColumnCount(3)
        results_table.setHorizontalHeaderLabels(["Stock #", "Description", "Type"])
        header = results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        results_table.setAlternatingRowColors(True)
        results_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        layout.addWidget(results_table, stretch=1)
        
        # Store filtered products
        filtered_products = []
        
        def perform_search():
            """Perform product search."""
            nonlocal filtered_products
            search_text = search_entry.text().lower().strip()
            
            if not search_text:
                # Show all products
                filtered_products = self.products
            else:
                # Filter products by stock number or description
                filtered_products = [
                    p for p in self.products
                    if search_text in p.get('stock_number', '').lower() or
                       search_text in p.get('description', '').lower()
                ]
            
            results_table.setRowCount(len(filtered_products))
            for row, product in enumerate(filtered_products):
                results_table.setItem(row, 0, QTableWidgetItem(product.get('stock_number', '')))
                results_table.setItem(row, 1, QTableWidgetItem(product.get('description', '')))
                results_table.setItem(row, 2, QTableWidgetItem(product.get('type', '')))
            
            # Select first row if results exist
            if filtered_products:
                results_table.selectRow(0)
                results_table.setFocus()
        
        def select_product(row: int):
            """Select product and add to items."""
            if 0 <= row < len(filtered_products):
                product = filtered_products[row]
                
                item = {
                    'type': 'product',
                    'product_id': product.get('id'),
                    'service_id': None,
                    'stock_number': product.get('stock_number', ''),
                    'description': product.get('description', ''),
                    'quantity': 1.0,  # Default quantity
                    'unit_price': 0.0,  # Default price (user can edit)
                    'line_total': 0.0,
                    'vat_code': 'S'  # Default VAT code
                }
                self.items.append(item)
                self._refresh_items_table()
                dialog.accept()
        
        # Connect search
        search_entry.textChanged.connect(perform_search)
        search_entry.returnPressed.connect(perform_search)
        
        # Perform initial search to show all products
        perform_search()
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        
        def handle_ok():
            """Handle OK button - select highlighted product."""
            selected_items = results_table.selectedItems()
            if selected_items:
                row = selected_items[0].row()
                select_product(row)
            else:
                QMessageBox.warning(dialog, "Warning", "Please select a product")
        
        button_box.accepted.connect(handle_ok)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Set focus to search entry
        search_entry.setFocus()
        
        dialog.exec()
    
    def _add_service(self):
        """Show search dialog to add service."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Search Services")
        dialog.setMinimumSize(600, 500)
        layout = QVBoxLayout(dialog)
        
        # Search entry
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_entry = QLineEdit()
        search_entry.setPlaceholderText("Enter service code or name...")
        search_entry.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        search_layout.addWidget(search_label)
        search_layout.addWidget(search_entry)
        layout.addLayout(search_layout)
        
        # Results table
        # Custom table widget with Enter key support
        class ServiceSearchTableWidget(QTableWidget):
            def __init__(self, select_callback):
                super().__init__()
                self.select_callback = select_callback
            
            def keyPressEvent(self, event):
                """Handle Enter key to select service."""
                if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                    if self.selectedItems():
                        row = self.selectedItems()[0].row()
                        self.select_callback(row)
                        event.accept()
                        return
                super().keyPressEvent(event)
        
        results_table = ServiceSearchTableWidget(lambda row: select_service(row))
        results_table.setColumnCount(3)
        results_table.setHorizontalHeaderLabels(["Code", "Name", "Group"])
        header = results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        results_table.setAlternatingRowColors(True)
        results_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        layout.addWidget(results_table, stretch=1)
        
        # Store filtered services
        filtered_services = []
        
        def perform_search():
            """Perform service search."""
            nonlocal filtered_services
            search_text = search_entry.text().lower().strip()
            
            if not search_text:
                # Show all services
                filtered_services = self.services
            else:
                # Filter services by code or name
                filtered_services = [
                    s for s in self.services
                    if search_text in s.get('code', '').lower() or
                       search_text in s.get('name', '').lower()
                ]
            
            results_table.setRowCount(len(filtered_services))
            for row, service in enumerate(filtered_services):
                results_table.setItem(row, 0, QTableWidgetItem(service.get('code', '')))
                results_table.setItem(row, 1, QTableWidgetItem(service.get('name', '')))
                results_table.setItem(row, 2, QTableWidgetItem(service.get('group_name', '')))
            
            # Select first row if results exist
            if filtered_services:
                results_table.selectRow(0)
                results_table.setFocus()
        
        def select_service(row: int):
            """Select service and add to items."""
            if 0 <= row < len(filtered_services):
                service = filtered_services[row]
                
                item = {
                    'type': 'service',
                    'product_id': None,
                    'service_id': service.get('id'),
                    'stock_number': service.get('code', ''),
                    'description': service.get('name', ''),
                    'quantity': 1.0,  # Default quantity
                    'unit_price': 0.0,  # Default price (user can edit)
                    'line_total': 0.0,
                    'vat_code': 'S'  # Default VAT code
                }
                self.items.append(item)
                self._refresh_items_table()
                dialog.accept()
        
        # Connect search
        search_entry.textChanged.connect(perform_search)
        search_entry.returnPressed.connect(perform_search)
        
        # Perform initial search to show all services
        perform_search()
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        
        def handle_ok():
            """Handle OK button - select highlighted service."""
            selected_items = results_table.selectedItems()
            if selected_items:
                row = selected_items[0].row()
                select_service(row)
            else:
                QMessageBox.warning(dialog, "Warning", "Please select a service")
        
        button_box.accepted.connect(handle_ok)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Set focus to search entry
        search_entry.setFocus()
        
        dialog.exec()
    
    def _remove_item(self):
        """Remove selected item."""
        selected = self.items_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Warning", "Please select an item to remove")
            return
        
        row = selected[0].row()
        if 0 <= row < len(self.items):
            self.items.pop(row)
            self._refresh_items_table()
    
    def _refresh_items_table(self):
        """Refresh the items table."""
        # Disconnect cell changed signal temporarily to avoid recursive updates
        try:
            self.items_table.cellChanged.disconnect()
        except TypeError:
            pass
        
        self.items_table.setRowCount(len(self.items))
        
        total = 0.0
        for row, item in enumerate(self.items):
            # Type (read-only)
            self.items_table.setItem(row, 0, QTableWidgetItem(item.get('type', '').upper()))
            self.items_table.item(row, 0).setFlags(self.items_table.item(row, 0).flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # Stock/Code (read-only)
            self.items_table.setItem(row, 1, QTableWidgetItem(item.get('stock_number', '')))
            self.items_table.item(row, 1).setFlags(self.items_table.item(row, 1).flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # Description (read-only)
            self.items_table.setItem(row, 2, QTableWidgetItem(item.get('description', '')))
            self.items_table.item(row, 2).setFlags(self.items_table.item(row, 2).flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # Quantity (editable)
            qty_item = QTableWidgetItem(str(item.get('quantity', 1.0)))
            self.items_table.setItem(row, 3, qty_item)
            
            # Price (editable)
            price_item = QTableWidgetItem(str(item.get('unit_price', 0.0)))
            self.items_table.setItem(row, 4, price_item)
            
            # Total (read-only, calculated)
            line_total = item.get('quantity', 1.0) * item.get('unit_price', 0.0)
            total_item = QTableWidgetItem(f"£{line_total:.2f}")
            total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.items_table.setItem(row, 5, total_item)
            
            total += line_total
        
        self.items_total_label.setText(f"Total: £{total:.2f}")
        
        # Reconnect cell changed signal
        self.items_table.cellChanged.connect(self._on_item_cell_changed)
    
    def _on_item_cell_changed(self, row: int, column: int):
        """Handle cell change in items table (quantity or price edited)."""
        if row < 0 or row >= len(self.items):
            return
        
        item = self.items[row]
        
        if column == 3:  # Quantity column
            try:
                new_qty = float(self.items_table.item(row, column).text())
                if new_qty <= 0:
                    # Revert to old value
                    self.items_table.item(row, column).setText(str(item.get('quantity', 1.0)))
                    return
                item['quantity'] = new_qty
            except ValueError:
                # Revert to old value
                self.items_table.item(row, column).setText(str(item.get('quantity', 1.0)))
                return
        elif column == 4:  # Price column
            try:
                new_price = float(self.items_table.item(row, column).text())
                if new_price < 0:
                    # Revert to old value
                    self.items_table.item(row, column).setText(str(item.get('unit_price', 0.0)))
                    return
                item['unit_price'] = new_price
            except ValueError:
                # Revert to old value
                self.items_table.item(row, column).setText(str(item.get('unit_price', 0.0)))
                return
        else:
            return
        
        # Update line total
        item['line_total'] = item['quantity'] * item['unit_price']
        total_item = self.items_table.item(row, 5)
        if total_item:
            total_item.setText(f"£{item['line_total']:.2f}")
        
        # Update grand total
        grand_total = sum(i.get('quantity', 0.0) * i.get('unit_price', 0.0) for i in self.items)
        self.items_total_label.setText(f"Total: £{grand_total:.2f}")
    
    def _on_document_type_changed(self, text: str):
        """Handle document type change."""
        self.document_type = text
        self._update_document_number_preview()
    
    def _update_document_number_preview(self):
        """Update document number preview label."""
        doc_type = self.document_type_combo.currentText()
        if doc_type == 'quote':
            prefix = 'QU'
            format_str = 'QU000001'
        elif doc_type == 'order':
            prefix = 'ORD'
            format_str = 'ORD000001'
        else:
            prefix = 'INV'
            format_str = 'INV001'
        self.document_number_label.setText(f"{format_str} (auto-generated)")
    
    def set_document_number_preview(self, preview: str):
        """Set the document number preview from controller."""
        self.document_number_label.setText(f"{preview} (auto-generated)")
    
    def _previous_step(self):
        """Go to previous step."""
        if self.current_step > 0:
            self.current_step -= 1
            self.stacked_widget.setCurrentIndex(self.current_step)
            self._update_navigation()
    
    def _next_step(self):
        """Go to next step or finish."""
        # Validate current step
        if not self._validate_current_step():
            return
        
        if self.current_step < 3:
            self.current_step += 1
            self.stacked_widget.setCurrentIndex(self.current_step)
            self._update_navigation()
        else:
            # Final step - complete wizard
            self._complete_wizard()
    
    def _validate_current_step(self) -> bool:
        """Validate current step before proceeding."""
        if self.current_step == 0:
            # Customer details entry - optional, can skip
            # Customer will be created or found in final step if details provided
            pass
        elif self.current_step == 1:
            # Vehicle selection (optional, always valid)
            self.selected_vehicle_id = self.vehicle_combo.currentData()
        elif self.current_step == 2:
            # Items (optional but recommended)
            if not self.items:
                reply = QMessageBox.question(
                    self, "No Items", 
                    "No items have been added. Continue anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return False
        elif self.current_step == 3:
            # Final step validation - customer is optional
            pass
        
        return True
    
    def _update_navigation(self):
        """Update navigation button states."""
        self.back_button.setEnabled(self.current_step > 0)
        if self.current_step == 3:
            self.next_button.setText("Save")
        else:
            self.next_button.setText("Next")
    
    def _complete_wizard(self):
        """Complete the wizard and emit signal."""
        if not self._validate_current_step():
            return
        
        # Ensure customer exists or create it if details provided
        customer_id = self.selected_customer_id
        customer_name = self.customer_name_input.text().strip()
        
        if not customer_id and customer_name:
            # Create customer from entered details if name is provided
            if not self.customer_model or not self.user_id:
                QMessageBox.warning(self, "Error", "Cannot create customer: model or user ID not available")
                return
            
            success, message = self.customer_model.create(
                name=customer_name,
                phone=self.customer_phone_input.text().strip(),
                house_name_no=self.customer_house_input.text().strip(),
                street_address=self.customer_street_input.text().strip(),
                city=self.customer_city_input.text().strip(),
                county=self.customer_county_input.text().strip(),
                postcode=self.customer_postcode_input.text().strip(),
                user_id=self.user_id
            )
            
            if not success:
                QMessageBox.warning(self, "Error", f"Failed to create customer: {message}")
                return
            
            # Refresh customers list if callback provided
            if self.refresh_customers_callback:
                self.refresh_customers_callback()
            
            # Find the newly created customer's ID by searching
            customers = self.customer_model.search(
                self.user_id,
                name=customer_name
            )
            
            # Find exact match
            for customer in customers:
                if customer.get('name', '').strip() == customer_name:
                    customer_id = customer.get('internal_id')
                    break
            
            if not customer_id:
                QMessageBox.warning(self, "Error", "Customer was created but could not be found")
                return
        # If no customer_id and no name provided, customer_id will be None (optional)
        
        vehicle_id = self.selected_vehicle_id
        document_date = self.document_date_input.date().toString(Qt.DateFormat.ISODate)
        document_type = self.document_type_combo.currentText()
        status = self.status_combo.currentText()
        notes = self.notes_input.toPlainText().strip()
        
        # Store data for retrieval
        self._wizard_result = {
            'customer_id': customer_id,
            'vehicle_id': vehicle_id,
            'document_date': document_date,
            'document_type': document_type,
            'notes': notes,
            'status': status,
            'items': self.items
        }
        self.accept()
    
    def get_wizard_data(self) -> Dict:
        """Get all wizard data as a dictionary."""
        if hasattr(self, '_wizard_result'):
            return self._wizard_result
        
        return {
            'customer_id': self.selected_customer_id,
            'vehicle_id': self.selected_vehicle_id,
            'document_date': self.document_date_input.date().toString(Qt.DateFormat.ISODate),
            'document_type': self.document_type_combo.currentText(),
            'status': self.status_combo.currentText(),
            'notes': self.notes_input.toPlainText().strip(),
            'items': self.items
        }

