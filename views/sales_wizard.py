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
                 vehicles: List[Dict] = None):
        """
        Initialize the sales wizard dialog.
        
        Args:
            parent: Parent widget
            customers: List of customers
            products: List of products
            services: List of services
            vehicles: List of vehicles
        """
        super().__init__(parent)
        self.customers = customers or []
        self.products = products or []
        self.services = services or []
        self.vehicles = vehicles or []
        
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
        """Create customer selection step."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        
        title = QLabel("Step 1: Select Customer")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        form_layout = QFormLayout()
        
        # Customer selector
        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(False)
        self.customer_combo.addItem("-- Select Customer --", None)
        for customer in self.customers:
            self.customer_combo.addItem(
                f"{customer.get('id', '')} - {customer.get('name', '')}",
                customer.get('internal_id')
            )
        form_layout.addRow("Customer*:", self.customer_combo)
        
        # Add Customer button
        add_customer_btn = QPushButton("Add New Customer")
        add_customer_btn.clicked.connect(self._add_customer)
        form_layout.addRow("", add_customer_btn)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
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
        
        # Items table
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels(
            ["Type", "Stock/Code", "Description", "Qty", "Price", "Total"]
        )
        self.items_table.horizontalHeader().setStretchLastSection(True)
        self.items_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
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
    
    def _add_customer(self):
        """Show dialog to add new customer."""
        # Simple customer creation dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Customer")
        layout = QVBoxLayout(dialog)
        
        form_layout = QFormLayout()
        name_input = QLineEdit()
        phone_input = QLineEdit()
        address_input = QLineEdit()
        
        form_layout.addRow("Name*:", name_input)
        form_layout.addRow("Phone:", phone_input)
        form_layout.addRow("Address:", address_input)
        
        layout.addLayout(form_layout)
        
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Emit signal to create customer (will be handled by controller)
            # For now, just show message
            QMessageBox.information(self, "Info", "Customer creation will be handled by the controller")
    
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
        """Show dialog to add product."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Product")
        layout = QVBoxLayout(dialog)
        
        form_layout = QFormLayout()
        
        product_combo = QComboBox()
        product_combo.addItem("-- Select Product --", None)
        for product in self.products:
            product_combo.addItem(
                f"{product.get('id', '')} - {product.get('stock_number', '')}",
                product
            )
        form_layout.addRow("Product*:", product_combo)
        
        quantity_input = QDoubleSpinBox()
        quantity_input.setMinimum(0.01)
        quantity_input.setMaximum(999999.99)
        quantity_input.setValue(1.0)
        form_layout.addRow("Quantity*:", quantity_input)
        
        price_input = QDoubleSpinBox()
        price_input.setMinimum(0.0)
        price_input.setMaximum(999999.99)
        price_input.setDecimals(2)
        price_input.setPrefix("£")
        form_layout.addRow("Unit Price*:", price_input)
        
        vat_combo = QComboBox()
        vat_combo.addItems(["S", "E", "Z"])
        form_layout.addRow("VAT Code:", vat_combo)
        
        layout.addLayout(form_layout)
        
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            product = product_combo.currentData()
            if product:
                quantity = quantity_input.value()
                price = price_input.value()
                total = quantity * price
                vat_code = vat_combo.currentText()
                
                item = {
                    'type': 'product',
                    'product_id': product.get('id'),
                    'service_id': None,
                    'stock_number': product.get('stock_number', ''),
                    'description': product.get('description', ''),
                    'quantity': quantity,
                    'unit_price': price,
                    'line_total': total,
                    'vat_code': vat_code
                }
                self.items.append(item)
                self._refresh_items_table()
    
    def _add_service(self):
        """Show dialog to add service."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Service")
        layout = QVBoxLayout(dialog)
        
        form_layout = QFormLayout()
        
        service_combo = QComboBox()
        service_combo.addItem("-- Select Service --", None)
        for service in self.services:
            service_combo.addItem(
                f"{service.get('id', '')} - {service.get('name', '')}",
                service
            )
        form_layout.addRow("Service*:", service_combo)
        
        quantity_input = QDoubleSpinBox()
        quantity_input.setMinimum(0.01)
        quantity_input.setMaximum(999999.99)
        quantity_input.setValue(1.0)
        form_layout.addRow("Quantity*:", quantity_input)
        
        price_input = QDoubleSpinBox()
        price_input.setMinimum(0.0)
        price_input.setMaximum(999999.99)
        price_input.setDecimals(2)
        price_input.setPrefix("£")
        form_layout.addRow("Unit Price*:", price_input)
        
        vat_combo = QComboBox()
        vat_combo.addItems(["S", "E", "Z"])
        form_layout.addRow("VAT Code:", vat_combo)
        
        layout.addLayout(form_layout)
        
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            service = service_combo.currentData()
            if service:
                quantity = quantity_input.value()
                price = price_input.value()
                total = quantity * price
                vat_code = vat_combo.currentText()
                
                item = {
                    'type': 'service',
                    'product_id': None,
                    'service_id': service.get('id'),
                    'stock_number': service.get('code', ''),
                    'description': service.get('name', ''),
                    'quantity': quantity,
                    'unit_price': price,
                    'line_total': total,
                    'vat_code': vat_code
                }
                self.items.append(item)
                self._refresh_items_table()
    
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
        self.items_table.setRowCount(len(self.items))
        
        total = 0.0
        for row, item in enumerate(self.items):
            self.items_table.setItem(row, 0, QTableWidgetItem(item.get('type', '').upper()))
            self.items_table.setItem(row, 1, QTableWidgetItem(item.get('stock_number', '')))
            self.items_table.setItem(row, 2, QTableWidgetItem(item.get('description', '')))
            self.items_table.setItem(row, 3, QTableWidgetItem(str(item.get('quantity', 0.0))))
            self.items_table.setItem(row, 4, QTableWidgetItem(f"£{item.get('unit_price', 0.0):.2f}"))
            self.items_table.setItem(row, 5, QTableWidgetItem(f"£{item.get('line_total', 0.0):.2f}"))
            total += item.get('line_total', 0.0)
        
        self.items_total_label.setText(f"Total: £{total:.2f}")
    
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
            # Customer selection
            customer_id = self.customer_combo.currentData()
            if not customer_id:
                QMessageBox.warning(self, "Validation", "Please select a customer")
                return False
            self.selected_customer_id = customer_id
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
            # Final step validation
            if not self.selected_customer_id:
                QMessageBox.warning(self, "Validation", "Customer is required")
                return False
        
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
        
        # Get final values
        customer_id = self.selected_customer_id
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
        return {
            'customer_id': self.selected_customer_id,
            'vehicle_id': self.selected_vehicle_id,
            'document_date': self.document_date_input.date().toString(Qt.DateFormat.ISODate),
            'document_type': self.document_type_combo.currentText(),
            'status': self.status_combo.currentText(),
            'notes': self.notes_input.toPlainText().strip(),
            'items': self.items
        }

