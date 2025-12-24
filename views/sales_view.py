"""Sales view for managing sales documents and customer payments."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QMessageBox, QDialog, QLabel, QLineEdit,
    QFormLayout, QDialogButtonBox, QComboBox, QTextEdit, QDateEdit, QDoubleSpinBox,
    QSpinBox, QSplitter
)
from PySide6.QtCore import Signal, Qt, QDate
from PySide6.QtGui import QKeyEvent, QShortcut, QKeySequence
from typing import List, Dict, Optional, Callable
from views.base_view import BaseTabbedView
from views.widgets.common_dialogs import show_confirmation_dialog


class SalesDocumentsTableWidget(QTableWidget):
    """Custom table widget with Enter key support."""
    
    def __init__(self, enter_callback: Callable[[], None]):
        """Initialize the table widget."""
        super().__init__()
        self.enter_callback = enter_callback
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.selectedItems():
                self.enter_callback()
                event.accept()
                return
        super().keyPressEvent(event)


class SalesDocumentDialog(QDialog):
    """Dialog for creating/editing a sales document."""
    
    def __init__(self, parent: Optional[QWidget] = None, 
                 document: Optional[Dict] = None,
                 customers: List[Dict] = None):
        """
        Initialize the sales document dialog.
        
        Args:
            parent: Parent widget
            document: Existing document data for editing, or None for new
            customers: List of customers for dropdown
        """
        super().__init__(parent)
        self.document = document
        self.customers = customers or []
        self.setWindowTitle("Edit Sales Document" if document else "Add Sales Document")
        self.setMinimumWidth(500)
        self._create_widgets()
        
        if document:
            self._populate_fields()
    
    def _create_widgets(self) -> None:
        """Create and layout dialog widgets."""
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # Customer selector
        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(False)
        for customer in self.customers:
            self.customer_combo.addItem(f"{customer.get('id', '')} - {customer.get('name', '')}", customer.get('id'))
        form_layout.addRow("Customer*:", self.customer_combo)
        
        # Document number
        self.document_number_input = QLineEdit()
        self.document_number_input.setPlaceholderText("Enter document number")
        form_layout.addRow("Document Number*:", self.document_number_input)
        
        # Document date
        self.document_date_input = QDateEdit()
        self.document_date_input.setDate(QDate.currentDate())
        self.document_date_input.setCalendarPopup(True)
        form_layout.addRow("Document Date*:", self.document_date_input)
        
        # Document type
        self.document_type_combo = QComboBox()
        self.document_type_combo.addItems(["quote", "order", "invoice"])
        form_layout.addRow("Document Type*:", self.document_type_combo)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(["draft", "sent", "finalized", "paid", "cancelled"])
        form_layout.addRow("Status:", self.status_combo)
        
        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(100)
        self.notes_input.setPlaceholderText("Enter notes (optional)")
        form_layout.addRow("Notes:", self.notes_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _populate_fields(self) -> None:
        """Populate fields with existing document data."""
        if self.document:
            # Find customer index
            customer_id = self.document.get("customer_id")
            for i in range(self.customer_combo.count()):
                if self.customer_combo.itemData(i) == customer_id:
                    self.customer_combo.setCurrentIndex(i)
                    break
            
            self.document_number_input.setText(self.document.get("document_number", ""))
            
            # Set date
            date_str = self.document.get("document_date", "")
            if date_str:
                date = QDate.fromString(date_str, Qt.DateFormat.ISODate)
                if date.isValid():
                    self.document_date_input.setDate(date)
            
            # Set document type
            doc_type = self.document.get("document_type", "quote")
            index = self.document_type_combo.findText(doc_type)
            if index >= 0:
                self.document_type_combo.setCurrentIndex(index)
            
            # Set status
            status = self.document.get("status", "draft")
            index = self.status_combo.findText(status)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
            
            self.notes_input.setPlainText(self.document.get("notes", ""))
    
    def get_data(self) -> Dict:
        """Get the dialog data."""
        customer_id = self.customer_combo.currentData()
        return {
            "customer_id": customer_id,
            "document_number": self.document_number_input.text().strip(),
            "document_date": self.document_date_input.date().toString(Qt.DateFormat.ISODate),
            "document_type": self.document_type_combo.currentText(),
            "status": self.status_combo.currentText(),
            "notes": self.notes_input.toPlainText().strip()
        }


class SalesItemDialog(QDialog):
    """Dialog for adding/editing a sales item."""
    
    def __init__(self, parent: Optional[QWidget] = None,
                 item: Optional[Dict] = None,
                 products: List[Dict] = None,
                 services: List[Dict] = None):
        """
        Initialize the sales item dialog.
        
        Args:
            parent: Parent widget
            item: Existing item data for editing, or None for new
            products: List of products for dropdown
            services: List of services for dropdown
        """
        super().__init__(parent)
        self.item = item
        self.products = products or []
        self.services = services or []
        self.setWindowTitle("Edit Item" if item else "Add Item")
        self.setMinimumWidth(500)
        self._create_widgets()
        
        if item:
            self._populate_fields()
    
    def _create_widgets(self) -> None:
        """Create and layout dialog widgets."""
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # Product selector
        self.product_combo = QComboBox()
        self.product_combo.setEditable(False)
        self.product_combo.addItem("None", None)
        for product in self.products:
            self.product_combo.addItem(
                f"{product.get('id', '')} - {product.get('stock_number', '')}",
                product.get('id')
            )
        form_layout.addRow("Product:", self.product_combo)
        
        # Service selector
        self.service_combo = QComboBox()
        self.service_combo.setEditable(False)
        self.service_combo.addItem("None", None)
        for service in self.services:
            self.service_combo.addItem(
                f"{service.get('id', '')} - {service.get('name', '')}",
                service.get('id')
            )
        form_layout.addRow("Service:", self.service_combo)
        
        # Stock number
        self.stock_number_input = QLineEdit()
        self.stock_number_input.setPlaceholderText("Enter stock number")
        form_layout.addRow("Stock Number*:", self.stock_number_input)
        
        # Description
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Enter description")
        form_layout.addRow("Description:", self.description_input)
        
        # Quantity
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setMinimum(0.01)
        self.quantity_input.setMaximum(999999.99)
        self.quantity_input.setValue(1.0)
        form_layout.addRow("Quantity*:", self.quantity_input)
        
        # Unit price
        self.unit_price_input = QDoubleSpinBox()
        self.unit_price_input.setMinimum(0.0)
        self.unit_price_input.setMaximum(999999.99)
        self.unit_price_input.setDecimals(2)
        self.unit_price_input.setPrefix("£")
        form_layout.addRow("Unit Price*:", self.unit_price_input)
        
        # VAT code
        self.vat_code_combo = QComboBox()
        self.vat_code_combo.addItems(["S", "E", "Z"])
        form_layout.addRow("VAT Code:", self.vat_code_combo)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _populate_fields(self) -> None:
        """Populate fields with existing item data."""
        if self.item:
            # Set product
            product_id = self.item.get("product_id")
            if product_id:
                for i in range(self.product_combo.count()):
                    if self.product_combo.itemData(i) == product_id:
                        self.product_combo.setCurrentIndex(i)
                        break
            
            # Set service
            service_id = self.item.get("service_id")
            if service_id:
                for i in range(self.service_combo.count()):
                    if self.service_combo.itemData(i) == service_id:
                        self.service_combo.setCurrentIndex(i)
                        break
            
            self.stock_number_input.setText(self.item.get("stock_number", ""))
            self.description_input.setText(self.item.get("description", ""))
            self.quantity_input.setValue(self.item.get("quantity", 1.0))
            self.unit_price_input.setValue(self.item.get("unit_price", 0.0))
            
            vat_code = self.item.get("vat_code", "S")
            index = self.vat_code_combo.findText(vat_code)
            if index >= 0:
                self.vat_code_combo.setCurrentIndex(index)
    
    def get_data(self) -> Dict:
        """Get the dialog data."""
        product_id = self.product_combo.currentData()
        service_id = self.service_combo.currentData()
        return {
            "product_id": product_id if product_id else None,
            "service_id": service_id if service_id else None,
            "stock_number": self.stock_number_input.text().strip(),
            "description": self.description_input.text().strip(),
            "quantity": self.quantity_input.value(),
            "unit_price": self.unit_price_input.value(),
            "vat_code": self.vat_code_combo.currentText()
        }


class SalesView(BaseTabbedView):
    """View for managing sales documents and customer payments."""
    
    # Navigation signals (inherited from BaseTabbedView)
    
    # Sales document signals
    create_document_requested = Signal(object)  # Emits dict with all wizard data
    update_document_requested = Signal(int, str, str, str, str, str)
    delete_document_requested = Signal(int)
    change_document_type_requested = Signal(int, str)
    refresh_documents_requested = Signal()
    
    # Item signals
    add_item_requested = Signal(int, object, object, str, str, float, float, str)
    update_item_requested = Signal(int, float, float)
    delete_item_requested = Signal(int)
    
    # Payment signals
    create_payment_requested = Signal(int, str, float, str, str)
    allocate_payment_requested = Signal(int, int, float)
    delete_payment_requested = Signal(int)
    delete_allocation_requested = Signal(int)
    
    # Customer creation signal
    create_customer_requested = Signal(str, str, str, str, str, str, str)
    
    # Document selection signal
    document_selected = Signal(int)
    
    def __init__(self):
        """Initialize the sales view."""
        super().__init__(title="Sales", current_view="sales")
        self._documents_data: List[Dict] = []
        self._customers_data: List[Dict] = []
        self._products_data: List[Dict] = []
        self._services_data: List[Dict] = []
        self.selected_document_id: Optional[int] = None
        self._create_widgets()
        self._setup_keyboard_navigation()
    
    def _create_widgets(self) -> None:
        """Create and layout UI widgets."""
        # Add action buttons
        self.add_document_button = self.add_action_button(
            "Add Document (Ctrl+N)", self.add_document, None
        )
        
        # Create tabs widget
        self.tab_widget = self.create_tabs()
        
        # Tab 1: Documents
        self._create_documents_tab()
        
        # Tab 2: Document Details
        self._create_document_details_tab()
        
        # Set Documents tab as default
        self.tab_widget.setCurrentIndex(0)
    
    def _create_documents_tab(self) -> None:
        """Create the documents list tab."""
        documents_widget = QWidget()
        documents_layout = QVBoxLayout(documents_widget)
        documents_layout.setSpacing(20)
        documents_layout.setContentsMargins(0, 0, 0, 0)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        # Customer filter
        filter_layout.addWidget(QLabel("Filter by Customer:"))
        self.customer_filter_combo = QComboBox()
        self.customer_filter_combo.setEditable(False)
        self.customer_filter_combo.addItem("All Customers", None)
        self.customer_filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.customer_filter_combo)
        
        # Document type filter
        filter_layout.addWidget(QLabel("Filter by Type:"))
        self.type_filter_combo = QComboBox()
        self.type_filter_combo.setEditable(False)
        self.type_filter_combo.addItem("All Types", None)
        self.type_filter_combo.addItems(["quote", "order", "invoice"])
        self.type_filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.type_filter_combo)
        
        filter_layout.addStretch()
        documents_layout.addLayout(filter_layout)
        
        # Documents table
        self.documents_table = SalesDocumentsTableWidget(self._switch_to_details_tab)
        self.documents_table.setColumnCount(7)
        self.documents_table.setHorizontalHeaderLabels(
            ["ID", "Customer", "Number", "Date", "Type", "Status", "Total"]
        )
        self.documents_table.horizontalHeader().setStretchLastSection(True)
        self.documents_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.documents_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.documents_table.setAlternatingRowColors(True)
        self.documents_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.documents_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Set column resize modes
        header = self.documents_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.resizeSection(0, 60)
        
        # Selection changed
        self.documents_table.itemSelectionChanged.connect(self._on_document_selection_changed)
        self.documents_table.itemDoubleClicked.connect(self._switch_to_details_tab)
        
        documents_layout.addWidget(self.documents_table, stretch=1)
        self.add_tab(documents_widget, "Documents (Ctrl+1)", "Ctrl+1")
    
    def _create_document_details_tab(self) -> None:
        """Create the document details tab."""
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setSpacing(20)
        details_layout.setContentsMargins(0, 0, 0, 0)
        
        # Document info section
        info_group = QWidget()
        info_layout = QFormLayout(info_group)
        
        self.document_info_label = QLabel("Select a document to view details")
        info_layout.addRow("Document:", self.document_info_label)
        
        # Action buttons for document
        doc_actions_layout = QHBoxLayout()
        self.edit_document_button = QPushButton("Edit Document")
        self.edit_document_button.clicked.connect(self.edit_document)
        self.delete_document_button = QPushButton("Delete Document")
        self.delete_document_button.clicked.connect(self.delete_document)
        self.change_type_button = QPushButton("Change Type")
        self.change_type_button.clicked.connect(self.change_document_type)
        doc_actions_layout.addWidget(self.edit_document_button)
        doc_actions_layout.addWidget(self.delete_document_button)
        doc_actions_layout.addWidget(self.change_type_button)
        doc_actions_layout.addStretch()
        info_layout.addRow("Actions:", doc_actions_layout)
        
        details_layout.addWidget(info_group)
        
        # Items section
        items_label = QLabel("Items:")
        items_label.setStyleSheet("font-weight: bold;")
        details_layout.addWidget(items_label)
        
        # Items table
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels(
            ["ID", "Stock Number", "Description", "Qty", "Unit Price", "VAT", "Total"]
        )
        self.items_table.horizontalHeader().setStretchLastSection(True)
        self.items_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Items action buttons
        items_actions_layout = QHBoxLayout()
        self.add_item_button = QPushButton("Add Item")
        self.add_item_button.clicked.connect(self.add_item)
        self.edit_item_button = QPushButton("Edit Item")
        self.edit_item_button.clicked.connect(self.edit_item)
        self.delete_item_button = QPushButton("Delete Item")
        self.delete_item_button.clicked.connect(self.delete_item)
        items_actions_layout.addWidget(self.add_item_button)
        items_actions_layout.addWidget(self.edit_item_button)
        items_actions_layout.addWidget(self.delete_item_button)
        items_actions_layout.addStretch()
        
        details_layout.addLayout(items_actions_layout)
        details_layout.addWidget(self.items_table, stretch=1)
        
        # Totals section
        totals_layout = QHBoxLayout()
        totals_layout.addStretch()
        self.totals_label = QLabel("Subtotal: £0.00 | VAT: £0.00 | Total: £0.00")
        totals_layout.addWidget(self.totals_label)
        details_layout.addLayout(totals_layout)
        
        details_layout.addStretch()
        self.add_tab(details_widget, "Document Details (Ctrl+2)", "Ctrl+2")
    
    def _setup_keyboard_navigation(self) -> None:
        """Set up keyboard navigation."""
        # Ctrl+N shortcut handled by action button
        pass
    
    def _on_filter_changed(self) -> None:
        """Handle filter changes."""
        # Just reload the documents that are already loaded with the new filters
        if self._documents_data:
            self.load_documents(self._documents_data)
    
    def _on_document_selection_changed(self) -> None:
        """Handle document selection change."""
        selected_items = self.documents_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            document_id_item = self.documents_table.item(row, 0)
            if document_id_item:
                self.selected_document_id = int(document_id_item.text())
                self.document_selected.emit(self.selected_document_id)
                self._load_document_details()
    
    def _switch_to_details_tab(self) -> None:
        """Switch to details tab and load document."""
        if self.selected_document_id:
            self.tab_widget.setCurrentIndex(1)
            self._load_document_details()
    
    def _load_document_details(self) -> None:
        """Load details for selected document."""
        if not self.selected_document_id:
            return
        
        # Find document
        document = None
        for doc in self._documents_data:
            if doc.get('id') == self.selected_document_id:
                document = doc
                break
        
        if not document:
            return
        
        # Update document info label
        customer_name = "Unknown"
        for customer in self._customers_data:
            if customer.get('internal_id') == document.get('customer_id'):
                customer_name = customer.get('name', 'Unknown')
                break
        
        self.document_info_label.setText(
            f"{document.get('document_number', '')} - {customer_name} "
            f"({document.get('document_type', '')}) - {document.get('status', '')}"
        )
        
        # Items will be loaded via document_selected signal
    
    def add_document(self) -> None:
        """Show sales wizard dialog."""
        from views.sales_wizard import SalesWizardDialog
        
        # Request vehicles from controller (will be empty for now)
        vehicles = []
        
        # Get customer model and user_id from controller if available
        customer_model = None
        user_id = None
        refresh_callback = None
        if hasattr(self, 'sales_controller') and self.sales_controller:
            customer_model = getattr(self.sales_controller, 'customer_model', None)
            user_id = getattr(self.sales_controller, 'user_id', None)
            refresh_callback = lambda: self.sales_controller.refresh_customers() if hasattr(self.sales_controller, 'refresh_customers') else None
        
        dialog = SalesWizardDialog(
            self, 
            customers=self._customers_data,
            products=self._products_data,
            services=self._services_data,
            vehicles=vehicles,
            customer_model=customer_model,
            user_id=user_id,
            refresh_customers_callback=refresh_callback
        )
        
        # Update document number preview when type changes
        dialog.document_type_combo.currentTextChanged.connect(
            lambda: self._update_wizard_document_preview(dialog)
        )
        self._update_wizard_document_preview(dialog)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_wizard_data()
            # Emit signal with wizard data as dict
            self.create_document_requested.emit(data)
    
    def _update_wizard_document_preview(self, dialog):
        """Update document number preview in wizard."""
        # This will be called when document type changes
        # The preview is already handled in the wizard itself
        pass
    
    def edit_document(self) -> None:
        """Show edit document dialog."""
        if not self.selected_document_id:
            self.show_error_dialog("Please select a document to edit")
            return
        
        # Find document
        document = None
        for doc in self._documents_data:
            if doc.get('id') == self.selected_document_id:
                document = doc
                break
        
        if not document:
            self.show_error_dialog("Document not found")
            return
        
        dialog = SalesDocumentDialog(self, document=document, customers=self._customers_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.update_document_requested.emit(
                self.selected_document_id,
                data['document_number'],
                data['document_date'],
                data['document_type'],
                data['notes'],
                data['status']
            )
    
    def delete_document(self) -> None:
        """Delete selected document."""
        if not self.selected_document_id:
            self.show_error_dialog("Please select a document to delete")
            return
        
        if show_confirmation_dialog(
            self, "Delete Document", 
            "Are you sure you want to delete this document?"
        ):
            self.delete_document_requested.emit(self.selected_document_id)
    
    def change_document_type(self) -> None:
        """Change document type."""
        if not self.selected_document_id:
            self.show_error_dialog("Please select a document")
            return
        
        # Show type selection dialog
        types = ["quote", "order", "invoice"]
        current_type = None
        for doc in self._documents_data:
            if doc.get('id') == self.selected_document_id:
                current_type = doc.get('document_type')
                break
        
        if not current_type:
            return
        
        # Simple dialog for type selection
        dialog = QDialog(self)
        dialog.setWindowTitle("Change Document Type")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(f"Current type: {current_type}"))
        layout.addWidget(QLabel("New type:"))
        
        type_combo = QComboBox()
        type_combo.addItems([t for t in types if t != current_type])
        layout.addWidget(type_combo)
        
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_type = type_combo.currentText()
            self.change_document_type_requested.emit(self.selected_document_id, new_type)
    
    def add_item(self) -> None:
        """Show add item dialog."""
        if not self.selected_document_id:
            self.show_error_dialog("Please select a document to add items to")
            return
        
        dialog = SalesItemDialog(self, products=self._products_data, services=self._services_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.add_item_requested.emit(
                self.selected_document_id,
                data['product_id'],
                data['service_id'],
                data['stock_number'],
                data['description'],
                data['quantity'],
                data['unit_price'],
                data['vat_code']
            )
    
    def edit_item(self) -> None:
        """Show edit item dialog."""
        selected_items = self.items_table.selectedItems()
        if not selected_items:
            self.show_error_dialog("Please select an item to edit")
            return
        
        row = selected_items[0].row()
        item_id_item = self.items_table.item(row, 0)
        if not item_id_item:
            return
        
        item_id = int(item_id_item.text())
        
        # Find item data
        item_data = None
        # We'll need to get this from controller
        # For now, create empty item
        dialog = SalesItemDialog(self, item=None, products=self._products_data, services=self._services_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.update_item_requested.emit(item_id, data['quantity'], data['unit_price'])
    
    def delete_item(self) -> None:
        """Delete selected item."""
        selected_items = self.items_table.selectedItems()
        if not selected_items:
            self.show_error_dialog("Please select an item to delete")
            return
        
        row = selected_items[0].row()
        item_id_item = self.items_table.item(row, 0)
        if not item_id_item:
            return
        
        item_id = int(item_id_item.text())
        
        if show_confirmation_dialog(self, "Delete Item", "Are you sure you want to delete this item?"):
            self.delete_item_requested.emit(item_id)
    
    def load_documents(self, documents: List[Dict]) -> None:
        """Load documents into the table."""
        self._documents_data = documents
        
        # Apply filters
        customer_filter = self.customer_filter_combo.currentData()
        type_filter = self.type_filter_combo.currentData()
        
        filtered_documents = documents
        if customer_filter:
            filtered_documents = [d for d in filtered_documents if d.get('customer_id') == customer_filter]
        if type_filter:
            filtered_documents = [d for d in filtered_documents if d.get('document_type') == type_filter]
        
        self.documents_table.setRowCount(len(filtered_documents))
        
        for row, document in enumerate(filtered_documents):
            # Get customer name
            customer_name = "Unknown"
            for customer in self._customers_data:
                if customer.get('internal_id') == document.get('customer_id'):
                    customer_name = customer.get('name', 'Unknown')
                    break
            
            self.documents_table.setItem(row, 0, QTableWidgetItem(str(document.get('id', ''))))
            self.documents_table.setItem(row, 1, QTableWidgetItem(customer_name))
            self.documents_table.setItem(row, 2, QTableWidgetItem(document.get('document_number', '')))
            self.documents_table.setItem(row, 3, QTableWidgetItem(document.get('document_date', '')))
            self.documents_table.setItem(row, 4, QTableWidgetItem(document.get('document_type', '')))
            self.documents_table.setItem(row, 5, QTableWidgetItem(document.get('status', '')))
            self.documents_table.setItem(row, 6, QTableWidgetItem(f"£{document.get('total', 0.0):.2f}"))
    
    def load_items(self, items: List[Dict], document: Optional[Dict] = None) -> None:
        """Load items into the items table."""
        self.items_table.setRowCount(len(items))
        
        subtotal = 0.0
        vat_amount = 0.0
        
        for row, item in enumerate(items):
            self.items_table.setItem(row, 0, QTableWidgetItem(str(item.get('id', ''))))
            self.items_table.setItem(row, 1, QTableWidgetItem(item.get('stock_number', '')))
            self.items_table.setItem(row, 2, QTableWidgetItem(item.get('description', '')))
            self.items_table.setItem(row, 3, QTableWidgetItem(str(item.get('quantity', 0.0))))
            self.items_table.setItem(row, 4, QTableWidgetItem(f"£{item.get('unit_price', 0.0):.2f}"))
            self.items_table.setItem(row, 5, QTableWidgetItem(item.get('vat_code', 'S')))
            self.items_table.setItem(row, 6, QTableWidgetItem(f"£{item.get('line_total', 0.0):.2f}"))
            
            subtotal += item.get('line_total', 0.0)
            # Calculate VAT (simplified - assumes 20% for S, 0% for E/Z)
            vat_code = item.get('vat_code', 'S')
            if vat_code == 'S':
                vat_amount += item.get('line_total', 0.0) * 0.20
        
        # Update totals label
        if document:
            self.totals_label.setText(
                f"Subtotal: £{document.get('subtotal', 0.0):.2f} | "
                f"VAT: £{document.get('vat_amount', 0.0):.2f} | "
                f"Total: £{document.get('total', 0.0):.2f}"
            )
        else:
            self.totals_label.setText(
                f"Subtotal: £{subtotal:.2f} | VAT: £{vat_amount:.2f} | Total: £{subtotal + vat_amount:.2f}"
            )
    
    def load_customers(self, customers: List[Dict]) -> None:
        """Load customers for dropdowns."""
        self._customers_data = customers
        
        # Update customer filter combo
        self.customer_filter_combo.clear()
        self.customer_filter_combo.addItem("All Customers", None)
        for customer in customers:
            self.customer_filter_combo.addItem(
                f"{customer.get('id', '')} - {customer.get('name', '')}",
                customer.get('internal_id')
            )
    
    def load_products(self, products: List[Dict]) -> None:
        """Load products for dropdowns."""
        self._products_data = products
    
    def load_services(self, services: List[Dict]) -> None:
        """Load services for dropdowns."""
        self._services_data = services
    
    def show_success_dialog(self, message: str) -> None:
        """Show success message."""
        QMessageBox.information(self, "Success", message)
    
    def show_error_dialog(self, message: str) -> None:
        """Show error message."""
        QMessageBox.critical(self, "Error", message)

