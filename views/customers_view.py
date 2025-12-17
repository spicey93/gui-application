"""Customers view for customer management."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QMessageBox, QDialog, QLabel, QLineEdit,
    QFormLayout, QDialogButtonBox
)
from PySide6.QtCore import Signal, Qt, QEvent
from PySide6.QtGui import QKeyEvent, QShortcut, QKeySequence
from typing import List, Dict, Optional, Callable
from views.base_view import BaseTabbedView


class CustomersTableWidget(QTableWidget):
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


class CustomerDialog(QDialog):
    """Dialog for creating/editing a customer."""
    
    def __init__(self, parent: Optional[QWidget] = None, 
                 customer: Optional[Dict] = None):
        """
        Initialize the customer dialog.
        
        Args:
            parent: Parent widget
            customer: Existing customer data for editing, or None for new
        """
        super().__init__(parent)
        self.customer = customer
        self.setWindowTitle("Edit Customer" if customer else "Add Customer")
        self.setMinimumWidth(400)
        self._create_widgets()
        
        if customer:
            self._populate_fields()
    
    def _create_widgets(self) -> None:
        """Create and layout dialog widgets."""
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter customer name")
        form_layout.addRow("Name*:", self.name_input)
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Enter phone number")
        form_layout.addRow("Phone:", self.phone_input)
        
        self.house_name_no_input = QLineEdit()
        self.house_name_no_input.setPlaceholderText("Enter house name/number")
        form_layout.addRow("House Name/No:", self.house_name_no_input)
        
        self.street_address_input = QLineEdit()
        self.street_address_input.setPlaceholderText("Enter street address")
        form_layout.addRow("Street Address:", self.street_address_input)
        
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("Enter city")
        form_layout.addRow("City:", self.city_input)
        
        self.county_input = QLineEdit()
        self.county_input.setPlaceholderText("Enter county")
        form_layout.addRow("County:", self.county_input)
        
        self.postcode_input = QLineEdit()
        self.postcode_input.setPlaceholderText("Enter postcode")
        form_layout.addRow("Postcode:", self.postcode_input)
        
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
        """Populate fields with existing customer data."""
        if self.customer:
            self.name_input.setText(self.customer.get("name", ""))
            self.phone_input.setText(self.customer.get("phone", ""))
            self.house_name_no_input.setText(self.customer.get("house_name_no", ""))
            self.street_address_input.setText(self.customer.get("street_address", ""))
            self.city_input.setText(self.customer.get("city", ""))
            self.county_input.setText(self.customer.get("county", ""))
            self.postcode_input.setText(self.customer.get("postcode", ""))
    
    def get_data(self) -> Dict[str, str]:
        """Get the dialog data."""
        return {
            "name": self.name_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "house_name_no": self.house_name_no_input.text().strip(),
            "street_address": self.street_address_input.text().strip(),
            "city": self.city_input.text().strip(),
            "county": self.county_input.text().strip(),
            "postcode": self.postcode_input.text().strip()
        }


class CustomersView(BaseTabbedView):
    """View for managing customers."""
    
    # Signals
    create_requested = Signal(str, str, str, str, str, str, str)
    update_requested = Signal(int, str, str, str, str, str, str, str)
    delete_requested = Signal(int)
    refresh_requested = Signal()
    
    def __init__(self):
        """Initialize the customers view."""
        super().__init__(title="Customers", current_view="customers")
        self._customers_data: List[Dict] = []
        self.selected_customer_id: Optional[int] = None
        self._create_widgets()
        self._setup_keyboard_navigation()
    
    def _create_widgets(self) -> None:
        """Create and layout UI widgets."""
        # Add action button
        self.add_customer_button = self.add_action_button(
            "Add Customer (Ctrl+N)", self.add_customer, None
        )
        
        # Create tabs widget
        self.tab_widget = self.create_tabs()
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        # Tab 1: Customers
        self._create_customers_tab()
        
        # Tab 2: Details
        self._create_details_tab()
        
        # Tab 3: Sales (placeholder)
        self._create_sales_tab()
        
        # Tab 4: Payments (placeholder)
        self._create_payments_tab()
        
        # Set Customers tab as default
        self.tab_widget.setCurrentIndex(0)
    
    def _create_customers_tab(self) -> None:
        """Create the customers list tab."""
        customers_widget = QWidget()
        customers_layout = QVBoxLayout(customers_widget)
        customers_layout.setSpacing(20)
        customers_layout.setContentsMargins(0, 0, 0, 0)
        
        # Customers table
        self.customers_table = CustomersTableWidget(self._switch_to_details_tab)
        self.customers_table.setColumnCount(5)
        self.customers_table.setHorizontalHeaderLabels(
            ["ID", "Name", "Phone", "City", "Postcode"]
        )
        self.customers_table.horizontalHeader().setStretchLastSection(True)
        self.customers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.customers_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.customers_table.setAlternatingRowColors(True)
        self.customers_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.customers_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Set column widths
        header = self.customers_table.horizontalHeader()
        header.resizeSection(0, 60)
        header.resizeSection(1, 200)
        header.resizeSection(2, 150)
        header.resizeSection(3, 150)
        
        # Selection changed
        self.customers_table.itemSelectionChanged.connect(
            self._on_customer_selection_changed
        )
        self.customers_table.itemDoubleClicked.connect(self._switch_to_details_tab)
        
        customers_layout.addWidget(self.customers_table)
        self.add_tab(customers_widget, "Customers (Ctrl+1)", "Ctrl+1")
    
    def _create_details_tab(self) -> None:
        """Create the details tab."""
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setSpacing(20)
        details_layout.setContentsMargins(30, 30, 30, 30)
        
        # Placeholder label
        self.details_label = QLabel(
            "Select a customer from the Customers tab to view details."
        )
        self.details_label.setStyleSheet("font-size: 12px; color: gray;")
        details_layout.addWidget(self.details_label)
        
        # Details form (hidden until customer selected)
        self.details_form = QWidget()
        details_form_layout = QVBoxLayout(self.details_form)
        details_form_layout.setSpacing(15)
        details_form_layout.setContentsMargins(0, 0, 0, 0)
        
        # ID (read-only)
        self.details_id_label = self._create_detail_row(
            details_form_layout, "ID:", read_only=True
        )
        
        # Name
        self.details_name_entry = self._create_detail_row(
            details_form_layout, "Name:"
        )
        
        # Phone
        self.details_phone_entry = self._create_detail_row(
            details_form_layout, "Phone:"
        )
        
        # House Name/No
        self.details_house_entry = self._create_detail_row(
            details_form_layout, "House Name/No:"
        )
        
        # Street Address
        self.details_street_entry = self._create_detail_row(
            details_form_layout, "Street Address:"
        )
        
        # City
        self.details_city_entry = self._create_detail_row(
            details_form_layout, "City:"
        )
        
        # County
        self.details_county_entry = self._create_detail_row(
            details_form_layout, "County:"
        )
        
        # Postcode
        self.details_postcode_entry = self._create_detail_row(
            details_form_layout, "Postcode:"
        )
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.details_save_button = QPushButton("Save Changes (Ctrl+Enter)")
        self.details_save_button.setMinimumWidth(200)
        self.details_save_button.setMinimumHeight(30)
        self.details_save_button.clicked.connect(self._handle_save_details)
        buttons_layout.addWidget(self.details_save_button)
        
        self.details_delete_button = QPushButton("Delete Customer (Ctrl+Shift+D)")
        self.details_delete_button.setMinimumWidth(220)
        self.details_delete_button.setMinimumHeight(30)
        self.details_delete_button.clicked.connect(self._handle_delete_details)
        buttons_layout.addWidget(self.details_delete_button)
        
        details_form_layout.addLayout(buttons_layout)
        details_form_layout.addStretch()
        
        self.details_form.hide()
        details_layout.addWidget(self.details_form)
        details_layout.addStretch()
        
        self.add_tab(details_widget, "Details (Ctrl+2)", "Ctrl+2")
    
    def _create_detail_row(self, layout: QVBoxLayout, label_text: str, 
                           read_only: bool = False) -> QLineEdit | QLabel:
        """Create a detail row with label and input."""
        row_layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setStyleSheet("font-weight: bold; font-size: 12px;")
        label.setMinimumWidth(150)
        row_layout.addWidget(label)
        
        if read_only:
            value_label = QLabel("")
            value_label.setStyleSheet("font-size: 12px;")
            row_layout.addWidget(value_label)
            row_layout.addStretch()
            layout.addLayout(row_layout)
            return value_label
        else:
            entry = QLineEdit()
            entry.setStyleSheet("font-size: 12px;")
            row_layout.addWidget(entry, stretch=1)
            layout.addLayout(row_layout)
            return entry
    
    def _create_sales_tab(self) -> None:
        """Create the sales tab (placeholder)."""
        sales_widget = QWidget()
        sales_layout = QVBoxLayout(sales_widget)
        sales_layout.setSpacing(20)
        sales_layout.setContentsMargins(30, 30, 30, 30)
        
        placeholder = QLabel("Sales functionality will be implemented later.")
        placeholder.setStyleSheet("font-size: 12px; color: gray;")
        sales_layout.addWidget(placeholder)
        sales_layout.addStretch()
        
        self.add_tab(sales_widget, "Sales (Ctrl+3)", "Ctrl+3")
    
    def _create_payments_tab(self) -> None:
        """Create the payments tab (placeholder)."""
        payments_widget = QWidget()
        payments_layout = QVBoxLayout(payments_widget)
        payments_layout.setSpacing(20)
        payments_layout.setContentsMargins(30, 30, 30, 30)
        
        placeholder = QLabel("Payments functionality will be implemented later.")
        placeholder.setStyleSheet("font-size: 12px; color: gray;")
        payments_layout.addWidget(placeholder)
        payments_layout.addStretch()
        
        self.add_tab(payments_widget, "Payments (Ctrl+4)", "Ctrl+4")
    
    def _setup_keyboard_navigation(self) -> None:
        """Set up keyboard navigation."""
        self.setTabOrder(self.customers_table, self.add_customer_button)
        self.customers_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Shortcuts for details tab
        save_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        save_shortcut.activated.connect(self._handle_save_details)
        
        delete_shortcut = QShortcut(QKeySequence("Ctrl+Shift+D"), self)
        delete_shortcut.activated.connect(self._handle_delete_details)
    
    def showEvent(self, event: QEvent) -> None:
        """Handle show event - set focus to table and select first row."""
        super().showEvent(event)
        self.tab_widget.setCurrentIndex(0)
        if self.customers_table.rowCount() > 0:
            self.customers_table.setFocus()
            if not self.customers_table.selectedItems():
                self.customers_table.selectRow(0)
                self._on_customer_selection_changed()
    
    def _on_tab_changed(self, index: int) -> None:
        """Handle tab change."""
        if index == 1:  # Details tab
            self._update_details_tab()
    
    def _on_customer_selection_changed(self) -> None:
        """Handle customer selection change."""
        selected_items = self.customers_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            customer_id = int(self.customers_table.item(row, 0).text())
            self.selected_customer_id = customer_id
            if self.tab_widget.currentIndex() == 1:
                self._update_details_tab()
    
    def _switch_to_details_tab(self) -> None:
        """Switch to the details tab."""
        if self.selected_customer_id is not None:
            self.tab_widget.setCurrentIndex(1)
    
    def _update_details_tab(self) -> None:
        """Update the details tab with selected customer data."""
        if self.selected_customer_id is None:
            self.details_label.show()
            self.details_form.hide()
            return
        
        # Find customer data
        customer = None
        for c in self._customers_data:
            if c.get("id") == self.selected_customer_id:
                customer = c
                break
        
        if customer is None:
            self.details_label.show()
            self.details_form.hide()
            return
        
        self.details_label.hide()
        self.details_form.show()
        
        self.details_id_label.setText(str(customer.get("id", "")))
        self.details_name_entry.setText(customer.get("name", ""))
        self.details_phone_entry.setText(customer.get("phone", ""))
        self.details_house_entry.setText(customer.get("house_name_no", ""))
        self.details_street_entry.setText(customer.get("street_address", ""))
        self.details_city_entry.setText(customer.get("city", ""))
        self.details_county_entry.setText(customer.get("county", ""))
        self.details_postcode_entry.setText(customer.get("postcode", ""))
    
    def _handle_save_details(self) -> None:
        """Handle save details button click."""
        if self.selected_customer_id is None:
            return
        
        if self.tab_widget.currentIndex() != 1:
            return
        
        name = self.details_name_entry.text().strip()
        if not name:
            self.show_error_dialog("Name is required")
            return
        
        self.update_requested.emit(
            self.selected_customer_id,
            name,
            self.details_phone_entry.text().strip(),
            self.details_house_entry.text().strip(),
            self.details_street_entry.text().strip(),
            self.details_city_entry.text().strip(),
            self.details_county_entry.text().strip(),
            self.details_postcode_entry.text().strip()
        )
    
    def _handle_delete_details(self) -> None:
        """Handle delete button click from details tab."""
        if self.selected_customer_id is None:
            return
        
        if self.tab_widget.currentIndex() != 1:
            return
        
        customer_name = self.details_name_entry.text()
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete customer '{customer_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_requested.emit(self.selected_customer_id)
            self.selected_customer_id = None
            self.tab_widget.setCurrentIndex(0)
    
    def load_customers(self, customers: List[Dict]) -> None:
        """Load customers into the table."""
        self._customers_data = customers
        self.customers_table.setRowCount(len(customers))
        
        for row, customer in enumerate(customers):
            self.customers_table.setItem(
                row, 0, QTableWidgetItem(str(customer.get("id", "")))
            )
            self.customers_table.setItem(
                row, 1, QTableWidgetItem(customer.get("name", ""))
            )
            self.customers_table.setItem(
                row, 2, QTableWidgetItem(customer.get("phone", ""))
            )
            self.customers_table.setItem(
                row, 3, QTableWidgetItem(customer.get("city", ""))
            )
            self.customers_table.setItem(
                row, 4, QTableWidgetItem(customer.get("postcode", ""))
            )
        
        # Auto-select first row if data exists
        if customers and self.customers_table.rowCount() > 0:
            self.customers_table.selectRow(0)
            self._on_customer_selection_changed()
    
    def add_customer(self) -> None:
        """Show dialog to add a new customer."""
        dialog = CustomerDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if data["name"]:
                self.create_requested.emit(
                    data["name"], data["phone"], data["house_name_no"],
                    data["street_address"], data["city"], data["county"],
                    data["postcode"]
                )
            else:
                self.show_error_dialog("Name is required")
    
    def show_success_dialog(self, message: str) -> None:
        """Show a success message dialog."""
        QMessageBox.information(self, "Success", message)
    
    def show_error_dialog(self, message: str) -> None:
        """Show an error message dialog."""
        QMessageBox.warning(self, "Error", message)
