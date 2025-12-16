"""Suppliers view GUI."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QLineEdit, 
    QTabWidget, QMessageBox, QHeaderView, QDateEdit, 
    QDoubleSpinBox, QSpinBox, QComboBox, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QDate, QEvent
from PySide6.QtGui import QKeyEvent, QShortcut, QKeySequence
from typing import List, Dict, Optional, Callable, TYPE_CHECKING
from views.base_view import BaseTabbedView
from utils.styles import apply_theme

if TYPE_CHECKING:
    from controllers.invoice_controller import InvoiceController
    from controllers.payment_controller import PaymentController
    from models.supplier import Supplier


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


class InvoicesTableWidget(QTableWidget):
    """Custom table widget for invoices with Enter key support."""
    
    def __init__(self, enter_callback: Callable[[int], None]):
        """Initialize the table widget."""
        super().__init__()
        self.enter_callback = enter_callback
        self.enter_callback = enter_callback
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.selectedItems():
                row = self.selectedItems()[0].row()
                self.enter_callback(row)
                event.accept()
                return
        super().keyPressEvent(event)


class PaymentsTableWidget(QTableWidget):
    """Custom table widget for payments with Enter key support."""
    
    def __init__(self, enter_callback: Callable[[int], None]):
        """Initialize the table widget."""
        super().__init__()
        self.enter_callback = enter_callback
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.selectedItems():
                row = self.selectedItems()[0].row()
                self.enter_callback(row)
                event.accept()
                return
        super().keyPressEvent(event)


class SuppliersView(BaseTabbedView):
    """Suppliers management GUI."""
    
    # Additional signals beyond base class
    create_requested = Signal(str, str)
    update_requested = Signal(int, str, str)
    delete_requested = Signal(int)
    refresh_requested = Signal()
    
    def __init__(self):
        """Initialize the suppliers view."""
        super().__init__(title="Suppliers", current_view="suppliers")
        self.invoice_controller: Optional["InvoiceController"] = None
        self.payment_controller: Optional["PaymentController"] = None
        self.supplier_model: Optional["Supplier"] = None
        self._create_widgets()
        self._setup_keyboard_navigation()
    
    def set_controllers(self, invoice_controller: "InvoiceController", 
                      payment_controller: "PaymentController",
                      supplier_model: "Supplier", user_id: int,
                      product_model=None):
        """Set the invoice and payment controllers."""
        self.invoice_controller = invoice_controller
        self.payment_controller = payment_controller
        self.supplier_model = supplier_model
        self._current_user_id = user_id
        self.product_model = product_model
    
    def _create_widgets(self):
        """Create and layout UI widgets."""
        # Add action buttons using base class method
        # Note: Ctrl+N shortcut is handled by main window, not here to avoid conflicts
        self.add_supplier_button = self.add_action_button(
            "Add Supplier (Ctrl+N)",
            self._handle_add_supplier,
            None  # No shortcut here - handled by main window
        )
        
        self.create_invoice_button = self.add_action_button(
            "Create Invoice (Ctrl+I)",
            self._handle_create_invoice_from_tab,
            "Ctrl+I"
        )
        
        self.create_payment_button = self.add_action_button(
            "Create Payment (Ctrl+P)",
            self._handle_create_payment_from_tab,
            "Ctrl+P"
        )
        
        # Create tabs widget
        self.tab_widget = self.create_tabs()
        
        # Connect tab change signal to update details when Details tab is selected
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        # Track selected supplier for details tab
        self.selected_supplier_id: Optional[int] = None
        
        # Tab 1: Suppliers
        suppliers_widget = QWidget()
        suppliers_layout = QVBoxLayout(suppliers_widget)
        suppliers_layout.setSpacing(20)
        suppliers_layout.setContentsMargins(0, 0, 0, 0)
        
        # Suppliers table
        self.suppliers_table = SuppliersTableWidget(self._switch_to_details_tab)
        self.suppliers_table.setColumnCount(4)
        self.suppliers_table.setHorizontalHeaderLabels(["ID", "Account Number", "Name", "Outstanding Balance"])
        self.suppliers_table.horizontalHeader().setStretchLastSection(True)
        self.suppliers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.suppliers_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.suppliers_table.setAlternatingRowColors(True)
        self.suppliers_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Set column widths
        header = self.suppliers_table.horizontalHeader()
        header.resizeSection(0, 80)
        header.resizeSection(1, 200)
        header.resizeSection(3, 150)
        
        # Enable keyboard navigation
        self.suppliers_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Selection changed - update selected supplier
        self.suppliers_table.itemSelectionChanged.connect(self._on_supplier_selection_changed)
        
        # Double-click to edit
        self.suppliers_table.itemDoubleClicked.connect(self._on_table_double_click)
        
        suppliers_layout.addWidget(self.suppliers_table)
        
        self.add_tab(suppliers_widget, "Suppliers (Ctrl+1)", "Ctrl+1")
        
        # Tab 2: Details
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setSpacing(20)
        details_layout.setContentsMargins(30, 30, 30, 30)
        
        # Details content (will be populated when supplier is selected)
        self.details_label = QLabel("Select a supplier from the Suppliers tab to view details.")
        self.details_label.setStyleSheet("font-size: 12px; color: gray;")
        details_layout.addWidget(self.details_label)
        
        # Details form (hidden until supplier selected)
        self.details_form = QWidget()
        details_form_layout = QVBoxLayout(self.details_form)
        details_form_layout.setSpacing(15)
        details_form_layout.setContentsMargins(0, 0, 0, 0)
        
        # Supplier ID (read-only)
        id_layout = QHBoxLayout()
        id_label = QLabel("ID:")
        id_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        id_label.setMinimumWidth(150)
        id_layout.addWidget(id_label)
        self.details_id_label = QLabel("")
        self.details_id_label.setStyleSheet("font-size: 12px;")
        id_layout.addWidget(self.details_id_label)
        id_layout.addStretch()
        details_form_layout.addLayout(id_layout)
        
        # Account Number (editable)
        account_layout = QHBoxLayout()
        account_label = QLabel("Account Number:")
        account_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        account_label.setMinimumWidth(150)
        account_layout.addWidget(account_label)
        self.details_account_entry = QLineEdit()
        self.details_account_entry.setStyleSheet("font-size: 12px;")
        account_layout.addWidget(self.details_account_entry, stretch=1)
        details_form_layout.addLayout(account_layout)
        
        # Name (editable)
        name_layout = QHBoxLayout()
        name_label = QLabel("Name:")
        name_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        name_label.setMinimumWidth(150)
        name_layout.addWidget(name_label)
        self.details_name_entry = QLineEdit()
        self.details_name_entry.setStyleSheet("font-size: 12px;")
        name_layout.addWidget(self.details_name_entry, stretch=1)
        details_form_layout.addLayout(name_layout)
        
        # Buttons
        details_buttons_layout = QHBoxLayout()
        details_buttons_layout.addStretch()
        
        self.details_save_button = QPushButton("Save Changes (Ctrl+Enter)")
        self.details_save_button.setMinimumWidth(200)
        self.details_save_button.setMinimumHeight(30)
        self.details_save_button.clicked.connect(self._handle_save_details)
        details_buttons_layout.addWidget(self.details_save_button)
        
        self.details_delete_button = QPushButton("Delete Supplier (Ctrl+Shift+D)")
        self.details_delete_button.setMinimumWidth(220)
        self.details_delete_button.setMinimumHeight(30)
        self.details_delete_button.clicked.connect(self._handle_delete_details)
        details_buttons_layout.addWidget(self.details_delete_button)
        
        details_form_layout.addLayout(details_buttons_layout)
        details_form_layout.addStretch()
        
        self.details_form.hide()
        details_layout.addWidget(self.details_form)
        details_layout.addStretch()
        
        self.add_tab(details_widget, "Details (Ctrl+2)", "Ctrl+2")
        
        # Tab 3: Invoices
        invoices_widget = QWidget()
        invoices_layout = QVBoxLayout(invoices_widget)
        invoices_layout.setSpacing(20)
        invoices_layout.setContentsMargins(0, 0, 0, 0)
        
        # Invoices table
        self.invoices_table = InvoicesTableWidget(self._handle_invoice_enter)
        self.invoices_table.setColumnCount(6)
        self.invoices_table.setHorizontalHeaderLabels(["Invoice #", "Date", "Supplier", "Total", "Outstanding", "Status"])
        self.invoices_table.horizontalHeader().setStretchLastSection(True)
        self.invoices_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.invoices_table.setAlternatingRowColors(True)
        self.invoices_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.invoices_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        invoices_layout.addWidget(self.invoices_table)
        
        self.add_tab(invoices_widget, "Invoices (Ctrl+3)", "Ctrl+3")
        
        # Tab 4: Payments
        payments_widget = QWidget()
        payments_layout = QVBoxLayout(payments_widget)
        payments_layout.setSpacing(20)
        payments_layout.setContentsMargins(0, 0, 0, 0)
        
        # Payments table
        self.payments_table = PaymentsTableWidget(self._handle_payment_enter)
        self.payments_table.setColumnCount(6)
        self.payments_table.setHorizontalHeaderLabels(["Date", "Amount", "Supplier", "Method", "Reference", "Unallocated"])
        self.payments_table.horizontalHeader().setStretchLastSection(True)
        self.payments_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.payments_table.setAlternatingRowColors(True)
        self.payments_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.payments_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        payments_layout.addWidget(self.payments_table)
        
        self.add_tab(payments_widget, "Payments (Ctrl+4)", "Ctrl+4")
        
        # Set Suppliers tab as default
        self.tab_widget.setCurrentIndex(0)
    
    def _setup_keyboard_navigation(self):
        """Set up keyboard navigation."""
        # Tab order: Table -> Add Supplier -> Navigation panel
        # This makes the table the first focusable element
        self.setTabOrder(self.suppliers_table, self.add_supplier_button)
        self.setTabOrder(self.add_supplier_button, self.nav_panel.logout_button)
        
        # Arrow keys work automatically in QTableWidget
        # Enter key on table row switches to details tab
        self.suppliers_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Add shortcuts for details tab
        save_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        save_shortcut.activated.connect(self._handle_save_details)
        
        delete_shortcut = QShortcut(QKeySequence("Ctrl+Shift+D"), self)
        delete_shortcut.activated.connect(self._handle_delete_details)
    
    def showEvent(self, event: QEvent):
        """Handle show event - set focus to table if it has data."""
        super().showEvent(event)
        # Ensure Suppliers tab is shown first
        self.tab_widget.setCurrentIndex(0)
        # Set focus to table if it has rows
        if self.suppliers_table.rowCount() > 0:
            self.suppliers_table.setFocus()
            # Ensure first row is selected if nothing is selected
            if not self.suppliers_table.selectedItems():
                self.suppliers_table.selectRow(0)
                self._on_supplier_selection_changed()
        
        # Refresh invoices and payments when view is shown (will be supplier-specific if supplier is selected)
        self.refresh_requested.emit()
        # If a supplier is selected, refresh the invoices and payments tabs
        if self.selected_supplier_id:
            if self.tab_widget.currentIndex() == 2:  # Invoices tab
                self._refresh_invoices_tab()
            elif self.tab_widget.currentIndex() == 3:  # Payments tab
                self._refresh_payments_tab()
    
    def _handle_add_supplier(self):
        """Handle Add Supplier button click."""
        self.add_supplier()
    
    def _on_table_double_click(self, item: QTableWidgetItem):
        """Handle double-click on table item."""
        self._switch_to_details_tab()
    
    def _on_supplier_selection_changed(self):
        """Handle supplier selection change - update selected supplier ID."""
        selected_items = self.suppliers_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            supplier_id = int(self.suppliers_table.item(row, 0).text())
            self.selected_supplier_id = supplier_id
            # Update current tab based on which one is active
            current_tab = self.tab_widget.currentIndex()
            if current_tab == 1:  # Details tab
                self._update_details_tab()
            elif current_tab == 2:  # Invoices tab
                self._refresh_invoices_tab()
            elif current_tab == 3:  # Payments tab
                self._refresh_payments_tab()
    
    def _on_tab_changed(self, index: int):
        """Handle tab change - update tab content based on selected supplier."""
        # Get the currently selected supplier from the table
        selected_items = self.suppliers_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            supplier_id = int(self.suppliers_table.item(row, 0).text())
            self.selected_supplier_id = supplier_id
        else:
            self.selected_supplier_id = None
        
        if index == 1:  # Details tab
            if self.selected_supplier_id:
                self._update_details_tab()
            else:
                # No supplier selected, show placeholder
                self.details_label.show()
                self.details_form.hide()
        elif index == 2:  # Invoices tab
            self._refresh_invoices_tab()
        elif index == 3:  # Payments tab
            self._refresh_payments_tab()
    
    def _refresh_invoices_tab(self):
        """Refresh the invoices tab with supplier-specific invoices."""
        if not self.selected_supplier_id or not self.invoice_controller:
            # Clear table if no supplier selected
            self.invoices_table.setRowCount(0)
            return
        
        invoices = self.invoice_controller.get_invoices(self.selected_supplier_id)
        self.load_invoices(invoices)
    
    def _refresh_payments_tab(self):
        """Refresh the payments tab with supplier-specific payments."""
        if not self.selected_supplier_id or not self.payment_controller:
            # Clear table if no supplier selected
            self.payments_table.setRowCount(0)
            return
        
        payments = self.payment_controller.get_payments(self.selected_supplier_id)
        self.load_payments(payments)
    
    def _switch_to_details_tab(self):
        """Switch to details tab for the currently selected supplier."""
        selected_items = self.suppliers_table.selectedItems()
        if not selected_items:
            return
        
        row = selected_items[0].row()
        supplier_id = int(self.suppliers_table.item(row, 0).text())
        self.selected_supplier_id = supplier_id
        self._update_details_tab()
        self.tab_widget.setCurrentIndex(1)
    
    def _update_details_tab(self):
        """Update the details tab with selected supplier information."""
        if not self.selected_supplier_id or not self.supplier_model:
            return
        
        supplier_data = self.supplier_model.get_by_id(self.selected_supplier_id, self._current_user_id)
        if not supplier_data:
            return
        
        self.details_id_label.setText(str(supplier_data['id']))
        self.details_account_entry.setText(supplier_data['account_number'])
        self.details_name_entry.setText(supplier_data['name'])
        
        self.details_label.hide()
        self.details_form.show()
    
    def _handle_save_details(self):
        """Handle save button in details tab."""
        if not self.selected_supplier_id:
            return
        
        new_account_number = self.details_account_entry.text().strip()
        new_name = self.details_name_entry.text().strip()
        
        if not new_account_number or not new_name:
            QMessageBox.critical(self, "Error", "Please fill in both account number and name")
            return
        
        self.update_requested.emit(self.selected_supplier_id, new_account_number, new_name)
    
    def _handle_delete_details(self):
        """Handle delete button in details tab."""
        if not self.selected_supplier_id:
            return
        
        supplier_name = self.details_name_entry.text()
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete supplier '{supplier_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_requested.emit(self.selected_supplier_id)
            self.selected_supplier_id = None
            self.details_label.show()
            self.details_form.hide()
    
    def _handle_create_invoice_from_tab(self):
        """Handle create invoice button from invoices tab."""
        if not self.invoice_controller:
            QMessageBox.warning(self, "Error", "Invoice controller not available")
            return
        
        # If a supplier is selected, use it; otherwise show dialog to select supplier
        if self.selected_supplier_id:
            self._create_invoice_dialog(None, self.selected_supplier_id)
        else:
            QMessageBox.information(self, "Info", "Please select a supplier first")
    
    def _handle_create_payment_from_tab(self):
        """Handle create payment button from payments tab."""
        if not self.payment_controller:
            QMessageBox.warning(self, "Error", "Payment controller not available")
            return
        
        # If a supplier is selected, use it; otherwise show dialog to select supplier
        if self.selected_supplier_id:
            self._create_payment_dialog(None, self.selected_supplier_id)
        else:
            QMessageBox.information(self, "Info", "Please select a supplier first")
    
    def _handle_invoice_enter(self, row: int):
        """Handle Enter key on invoice row."""
        if not self.invoice_controller or not self.selected_supplier_id:
            return
        
        invoice_id = self.invoices_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if invoice_id:
            self._view_invoice_dialog(None, self.selected_supplier_id, invoice_id)
    
    def _handle_payment_enter(self, row: int):
        """Handle Enter key on payment row."""
        if not self.payment_controller or not self.selected_supplier_id:
            return
        
        payment_id = self.payments_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if payment_id:
            self._allocate_payment_dialog(None, self.selected_supplier_id, payment_id)
    
    def _show_supplier_details(self, supplier_id: int, account_number: str, name: str):
        """Show supplier details in a popup dialog with tabs."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Supplier Details")
        dialog.setModal(True)
        dialog.setMinimumSize(600, 500)
        dialog.resize(600, 500)
        apply_theme(dialog)
        
        # Add Escape key shortcut for cancel
        from PySide6.QtGui import QShortcut, QKeySequence
        esc_shortcut = QShortcut(QKeySequence("Escape"), dialog)
        esc_shortcut.activated.connect(dialog.reject)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("Supplier Information")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Create notebook for tabs
        notebook = QTabWidget()
        notebook.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
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
        account_entry.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
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
        name_entry.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        name_layout.addWidget(name_entry, stretch=1)
        info_layout.addLayout(name_layout)
        
        info_layout.addStretch()
        notebook.addTab(info_frame, "Info (Ctrl+1)")
        
        # Invoices tab
        invoices_frame = QWidget()
        invoices_layout = QVBoxLayout(invoices_frame)
        invoices_layout.setContentsMargins(30, 30, 30, 30)
        invoices_layout.setSpacing(15)
        
        # Create Invoice button
        create_invoice_btn = QPushButton("Create Invoice")
        create_invoice_btn.setMinimumHeight(35)
        create_invoice_btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        create_invoice_btn.clicked.connect(
            lambda: self._create_invoice_dialog(dialog, supplier_id)
        )
        invoices_layout.addWidget(create_invoice_btn)
        
        # Invoices table
        invoices_list = []
        if self.invoice_controller:
            invoices_list = self.invoice_controller.get_invoices(supplier_id)
        
        def handle_invoice_enter(row):
            if row < len(invoices_list):
                self._view_invoice_dialog(dialog, supplier_id, invoices_list[row]['id'])
        
        invoices_table = InvoicesTableWidget(handle_invoice_enter)
        invoices_table.setColumnCount(6)
        invoices_table.setHorizontalHeaderLabels(["Invoice #", "Date", "Total", "Outstanding", "Status", "Delete"])
        invoices_table.horizontalHeader().setStretchLastSection(False)
        invoices_table.setColumnWidth(5, 80)  # Delete column width
        invoices_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        invoices_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        invoices_table.setAlternatingRowColors(True)
        invoices_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Load invoices
        if invoices_list:
            invoices_table.setRowCount(len(invoices_list))
            for row, invoice in enumerate(invoices_list):
                invoice_id = invoice['id']
                outstanding = self.invoice_controller.get_invoice_outstanding_balance(invoice_id)
                invoices_table.setItem(row, 0, QTableWidgetItem(invoice['invoice_number']))
                invoices_table.setItem(row, 1, QTableWidgetItem(invoice['invoice_date']))
                invoices_table.setItem(row, 2, QTableWidgetItem(f"£{invoice['total']:.2f}"))
                invoices_table.setItem(row, 3, QTableWidgetItem(f"£{outstanding:.2f}"))
                invoices_table.setItem(row, 4, QTableWidgetItem(invoice['status']))
                
                # Delete button
                delete_btn = QPushButton("Delete")
                delete_btn.setMaximumWidth(70)
                delete_btn.clicked.connect(
                    lambda checked, inv_id=invoice_id, inv_num=invoice['invoice_number']: 
                    self._delete_invoice_dialog(dialog, supplier_id, inv_id, inv_num)
                )
                invoices_table.setCellWidget(row, 5, delete_btn)
            
            # Double-click to view invoice
            invoices_table.itemDoubleClicked.connect(
                lambda item: self._view_invoice_dialog(dialog, supplier_id, invoices_list[item.row()]['id'])
            )
        
        invoices_table.resizeColumnsToContents()
        invoices_layout.addWidget(invoices_table)
        notebook.addTab(invoices_frame, "Invoices (Ctrl+2)")
        
        # Payments tab
        payments_frame = QWidget()
        payments_layout = QVBoxLayout(payments_frame)
        payments_layout.setContentsMargins(30, 30, 30, 30)
        payments_layout.setSpacing(15)
        
        # Create Payment button
        create_payment_btn = QPushButton("Create Payment")
        create_payment_btn.setMinimumHeight(35)
        create_payment_btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        create_payment_btn.clicked.connect(
            lambda: self._create_payment_dialog(dialog, supplier_id)
        )
        payments_layout.addWidget(create_payment_btn)
        
        # Payments table
        payments_list = []
        if self.payment_controller:
            payments_list = self.payment_controller.get_payments(supplier_id)
        
        def handle_payment_enter(row):
            if row < len(payments_list):
                self._allocate_payment_dialog(dialog, supplier_id, payments_list[row]['id'])
        
        payments_table = PaymentsTableWidget(handle_payment_enter)
        payments_table.setColumnCount(6)
        payments_table.setHorizontalHeaderLabels(["Date", "Amount", "Method", "Reference", "Unallocated", "Delete"])
        payments_table.horizontalHeader().setStretchLastSection(False)
        payments_table.setColumnWidth(5, 80)  # Delete column width
        payments_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        payments_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        payments_table.setAlternatingRowColors(True)
        payments_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Load payments
        if payments_list:
            payments_table.setRowCount(len(payments_list))
            for row, payment in enumerate(payments_list):
                payment_id = payment['id']
                unallocated = self.payment_controller.get_payment_unallocated_amount(payment_id)
                payments_table.setItem(row, 0, QTableWidgetItem(payment['payment_date']))
                payments_table.setItem(row, 1, QTableWidgetItem(f"£{payment['amount']:.2f}"))
                payments_table.setItem(row, 2, QTableWidgetItem(payment.get('payment_method', 'Cash')))
                payments_table.setItem(row, 3, QTableWidgetItem(payment.get('reference', '')))
                payments_table.setItem(row, 4, QTableWidgetItem(f"£{unallocated:.2f}"))
                
                # Delete button
                delete_btn = QPushButton("Delete")
                delete_btn.setMaximumWidth(70)
                delete_btn.clicked.connect(
                    lambda checked, pay_id=payment_id, pay_date=payment['payment_date'], pay_amt=payment['amount']: 
                    self._delete_payment_dialog(dialog, supplier_id, pay_id, pay_date, pay_amt)
                )
                payments_table.setCellWidget(row, 5, delete_btn)
            
            # Double-click to allocate payment
            payments_table.itemDoubleClicked.connect(
                lambda item: self._allocate_payment_dialog(dialog, supplier_id, payments_list[item.row()]['id'])
            )
        
        payments_table.resizeColumnsToContents()
        payments_layout.addWidget(payments_table)
        notebook.addTab(payments_frame, "Payments (Ctrl+3)")
        
        # Actions tab
        actions_frame = QWidget()
        actions_layout = QVBoxLayout(actions_frame)
        actions_layout.setContentsMargins(30, 30, 30, 30)
        
        delete_btn = QPushButton("Delete Supplier")
        delete_btn.setMinimumHeight(35)
        delete_btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        delete_btn.clicked.connect(
            lambda: self._delete_from_details_dialog(dialog, supplier_id, name)
        )
        actions_layout.addWidget(delete_btn)
        actions_layout.addStretch()
        
        notebook.addTab(actions_frame, "Actions (Ctrl+4)")
        
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
        
        save_btn = QPushButton("Save Changes (Ctrl+Enter)")
        save_btn.setMinimumWidth(200)
        save_btn.setMinimumHeight(30)
        save_btn.setDefault(True)
        save_btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        save_btn.clicked.connect(handle_save)
        
        # Ctrl+Enter shortcut for save
        ctrl_enter_shortcut = QShortcut(QKeySequence("Ctrl+Return"), dialog)
        ctrl_enter_shortcut.activated.connect(handle_save)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel (Esc)")
        cancel_btn.setMinimumWidth(140)
        cancel_btn.setMinimumHeight(30)
        cancel_btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Set up tab order for keyboard navigation
        # Tab order: TabWidget -> Account Entry -> Name Entry -> Save Button -> Cancel Button
        dialog.setTabOrder(notebook, account_entry)
        dialog.setTabOrder(account_entry, name_entry)
        dialog.setTabOrder(name_entry, save_btn)
        dialog.setTabOrder(save_btn, cancel_btn)
        
        # For tabs with tables, set tab order within those tabs
        # Invoices tab: Create Invoice Button -> Invoices Table
        dialog.setTabOrder(create_invoice_btn, invoices_table)
        # Payments tab: Create Payment Button -> Payments Table
        dialog.setTabOrder(create_payment_btn, payments_table)
        
        # Add keyboard shortcuts for tab navigation
        # Ctrl+1, Ctrl+2, etc. for tabs
        tab_shortcuts = [
            QShortcut(QKeySequence("Ctrl+1"), dialog),
            QShortcut(QKeySequence("Ctrl+2"), dialog),
            QShortcut(QKeySequence("Ctrl+3"), dialog),
            QShortcut(QKeySequence("Ctrl+4"), dialog),
        ]
        for i, shortcut in enumerate(tab_shortcuts):
            if i < notebook.count():
                shortcut.activated.connect(lambda idx=i: notebook.setCurrentIndex(idx))
        
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
    
    def _delete_invoice_dialog(self, parent_dialog: QDialog, supplier_id: int, invoice_id: int, invoice_number: str):
        """Handle delete invoice dialog."""
        if not self.invoice_controller:
            QMessageBox.warning(parent_dialog, "Error", "Invoice controller not available")
            return
        
        reply = QMessageBox.question(
            parent_dialog,
            "Confirm Delete",
            f"Are you sure you want to delete invoice '{invoice_number}'?\n\n"
            "Note: Invoices with allocated payments cannot be deleted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.invoice_controller.delete_invoice(invoice_id)
            if success:
                QMessageBox.information(parent_dialog, "Success", message)
                # Refresh the supplier details dialog
                parent_dialog.accept()
                # Reopen the dialog to show updated data
                supplier_data = self.supplier_model.get_by_id(supplier_id, self._current_user_id)
                if supplier_data:
                    self._show_supplier_details(supplier_id, supplier_data['account_number'], supplier_data['name'])
            else:
                QMessageBox.critical(parent_dialog, "Error", message)
    
    def _delete_payment_dialog(self, parent_dialog: QDialog, supplier_id: int, payment_id: int, 
                               payment_date: str, payment_amount: float):
        """Handle delete payment dialog."""
        if not self.payment_controller:
            QMessageBox.warning(parent_dialog, "Error", "Payment controller not available")
            return
        
        reply = QMessageBox.question(
            parent_dialog,
            "Confirm Delete",
            f"Are you sure you want to delete payment of £{payment_amount:.2f} from {payment_date}?\n\n"
            "This will also remove all payment allocations.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.payment_controller.delete_payment(payment_id)
            if success:
                QMessageBox.information(parent_dialog, "Success", message)
                # Refresh the supplier details dialog
                parent_dialog.accept()
                # Reopen the dialog to show updated data
                supplier_data = self.supplier_model.get_by_id(supplier_id, self._current_user_id)
                if supplier_data:
                    self._show_supplier_details(supplier_id, supplier_data['account_number'], supplier_data['name'])
            else:
                QMessageBox.critical(parent_dialog, "Error", message)
    
    def add_supplier(self):
        """Show dialog for adding a new supplier."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Supplier")
        dialog.setModal(True)
        dialog.setMinimumSize(500, 300)
        dialog.resize(500, 300)
        apply_theme(dialog)
        
        # Add Escape key shortcut for cancel
        esc_shortcut = QShortcut(QKeySequence("Escape"), dialog)
        esc_shortcut.activated.connect(dialog.reject)
        
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
            
            # Calculate outstanding balance
            if self.supplier_model and hasattr(self, '_current_user_id'):
                outstanding = self.supplier_model.get_outstanding_balance(supplier['id'], 
                                                                         self._current_user_id)
                self.suppliers_table.setItem(row, 3, QTableWidgetItem(f"£{outstanding:.2f}"))
            else:
                self.suppliers_table.setItem(row, 3, QTableWidgetItem("£0.00"))
        
        # Resize columns to content
        self.suppliers_table.resizeColumnsToContents()
        header = self.suppliers_table.horizontalHeader()
        header.resizeSection(0, 80)
        if len(suppliers) > 0:
            header.resizeSection(1, 200)
            header.resizeSection(3, 150)
        
        # Auto-select first row and set focus to table if data exists
        if len(suppliers) > 0:
            self.suppliers_table.selectRow(0)
            self.suppliers_table.setFocus()
            # Ensure the first row is visible
            self.suppliers_table.scrollToItem(self.suppliers_table.item(0, 0))
            # Trigger selection changed to update details tab
            self._on_supplier_selection_changed()
    
    def load_invoices(self, invoices: List[Dict[str, any]]):
        """Load invoices into the invoices table."""
        self.invoices_table.setRowCount(len(invoices))
        
        for row, invoice in enumerate(invoices):
            invoice_id = invoice['id']
            # Store invoice ID in first item's user data
            invoice_num_item = QTableWidgetItem(invoice.get('invoice_number', ''))
            invoice_num_item.setData(Qt.ItemDataRole.UserRole, invoice_id)
            self.invoices_table.setItem(row, 0, invoice_num_item)
            
            self.invoices_table.setItem(row, 1, QTableWidgetItem(invoice.get('invoice_date', '')))
            
            # Since invoices are now supplier-specific, we don't need to show supplier name
            # But we'll keep the column for consistency (or remove it if preferred)
            # For now, we'll show the selected supplier's name or leave it empty
            supplier_name = ""
            if self.selected_supplier_id and self.supplier_model and hasattr(self, '_current_user_id'):
                supplier_data = self.supplier_model.get_by_id(self.selected_supplier_id, self._current_user_id)
                if supplier_data:
                    supplier_name = supplier_data.get('name', '')
            self.invoices_table.setItem(row, 2, QTableWidgetItem(supplier_name))
            
            self.invoices_table.setItem(row, 3, QTableWidgetItem(f"£{invoice.get('total', 0.0):.2f}"))
            
            # Calculate outstanding balance
            outstanding = 0.0
            if self.invoice_controller:
                outstanding = self.invoice_controller.get_invoice_outstanding_balance(invoice_id)
            self.invoices_table.setItem(row, 4, QTableWidgetItem(f"£{outstanding:.2f}"))
            
            self.invoices_table.setItem(row, 5, QTableWidgetItem(invoice.get('status', '')))
        
        # Resize columns
        self.invoices_table.resizeColumnsToContents()
    
    def load_payments(self, payments: List[Dict[str, any]]):
        """Load payments into the payments table."""
        self.payments_table.setRowCount(len(payments))
        
        for row, payment in enumerate(payments):
            payment_id = payment['id']
            # Store payment ID in first item's user data
            date_item = QTableWidgetItem(payment.get('payment_date', ''))
            date_item.setData(Qt.ItemDataRole.UserRole, payment_id)
            self.payments_table.setItem(row, 0, date_item)
            
            self.payments_table.setItem(row, 1, QTableWidgetItem(f"£{payment.get('amount', 0.0):.2f}"))
            
            # Since payments are now supplier-specific, we don't need to show supplier name
            # But we'll keep the column for consistency (or remove it if preferred)
            # For now, we'll show the selected supplier's name or leave it empty
            supplier_name = ""
            if self.selected_supplier_id and self.supplier_model and hasattr(self, '_current_user_id'):
                supplier_data = self.supplier_model.get_by_id(self.selected_supplier_id, self._current_user_id)
                if supplier_data:
                    supplier_name = supplier_data.get('name', '')
            self.payments_table.setItem(row, 2, QTableWidgetItem(supplier_name))
            
            self.payments_table.setItem(row, 3, QTableWidgetItem(payment.get('payment_method', 'Cash')))
            self.payments_table.setItem(row, 4, QTableWidgetItem(payment.get('reference', '')))
            
            # Calculate unallocated amount
            unallocated = payment.get('amount', 0.0)
            if self.payment_controller:
                unallocated = self.payment_controller.get_payment_unallocated_amount(payment_id)
            self.payments_table.setItem(row, 5, QTableWidgetItem(f"£{unallocated:.2f}"))
        
        # Resize columns
        self.payments_table.resizeColumnsToContents()
    
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
    
    def _create_invoice_dialog(self, parent_dialog: QDialog, supplier_id: int):
        """Create invoice dialog."""
        if not self.invoice_controller:
            QMessageBox.warning(self, "Error", "Invoice controller not available")
            return
        
        dialog = QDialog(parent_dialog)
        dialog.setWindowTitle("Create Invoice")
        dialog.setModal(True)
        dialog.setMinimumSize(800, 600)
        dialog.resize(800, 600)
        apply_theme(dialog)
        
        esc_shortcut = QShortcut(QKeySequence("Escape"), dialog)
        esc_shortcut.activated.connect(dialog.reject)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Invoice header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(10)
        
        # Invoice Number
        inv_num_layout = QHBoxLayout()
        inv_num_label = QLabel("Invoice Number:")
        inv_num_label.setMinimumWidth(150)
        inv_num_layout.addWidget(inv_num_label)
        inv_num_entry = QLineEdit()
        inv_num_layout.addWidget(inv_num_entry, stretch=1)
        header_layout.addLayout(inv_num_layout)
        
        # Invoice Date
        date_layout = QHBoxLayout()
        date_label = QLabel("Invoice Date:")
        date_label.setMinimumWidth(150)
        date_layout.addWidget(date_label)
        date_entry = QDateEdit()
        date_entry.setDate(QDate.currentDate())
        date_entry.setCalendarPopup(True)
        date_entry.setStyleSheet("font-size: 12px;")
        date_layout.addWidget(date_entry, stretch=1)
        header_layout.addLayout(date_layout)
        
        layout.addLayout(header_layout)
        
        # Items table
        items_label = QLabel("Items:")
        items_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(items_label)
        
        items_table = QTableWidget()
        items_table.setColumnCount(6)
        items_table.setHorizontalHeaderLabels(["Stock #", "Description", "Quantity", "Unit Price", "VAT Code", "Line Total"])
        items_table.horizontalHeader().setStretchLastSection(True)
        items_table.setAlternatingRowColors(True)
        items_table.setMinimumHeight(200)
        items_table.setEditTriggers(QTableWidget.EditTrigger.AllEditTriggers)  # Allow editing VAT codes
        layout.addWidget(items_table)
        
        # Add Item button
        add_item_btn = QPushButton("Add Item (Ctrl+I)")
        add_item_btn.clicked.connect(
            lambda: self._add_invoice_item_dialog(dialog, items_table, supplier_id, update_totals)
        )
        layout.addWidget(add_item_btn)
        
        # Add Item shortcut
        add_item_shortcut = QShortcut(QKeySequence("Ctrl+I"), dialog)
        add_item_shortcut.activated.connect(
            lambda: self._add_invoice_item_dialog(dialog, items_table, supplier_id, update_totals)
        )
        
        # Totals
        totals_layout = QVBoxLayout()
        totals_layout.setSpacing(5)
        
        subtotal_label = QLabel("Subtotal: £0.00")
        subtotal_label.setStyleSheet("font-size: 12px;")
        totals_layout.addWidget(subtotal_label)
        
        vat_label = QLabel("VAT: £0.00")
        vat_label.setStyleSheet("font-size: 12px;")
        totals_layout.addWidget(vat_label)
        
        total_label = QLabel("Total: £0.00")
        total_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        totals_layout.addWidget(total_label)
        
        layout.addLayout(totals_layout)
        
        def update_totals():
            """Update totals from items."""
            subtotal = 0.0
            vat_amount = 0.0
            
            # VAT rates by code: S=Standard (20%), E=Exempt (0%), Z=Zero (0%)
            vat_rates = {'S': 20.0, 'E': 0.0, 'Z': 0.0}
            
            for row in range(items_table.rowCount()):
                qty_item = items_table.item(row, 2)
                price_item = items_table.item(row, 3)
                vat_code_item = items_table.item(row, 4)
                if qty_item and price_item:
                    try:
                        qty = float(qty_item.text())
                        price = float(price_item.text())
                        line_total = qty * price
                        subtotal += line_total
                        
                        # Calculate VAT for this line
                        # Check if VAT code is a widget (combobox) or item (text)
                        vat_code = 'S'  # Default
                        vat_widget = items_table.cellWidget(row, 4)
                        if vat_widget and isinstance(vat_widget, QComboBox):
                            vat_code = vat_widget.currentText().strip().upper()
                        elif vat_code_item:
                            vat_code = vat_code_item.text().strip().upper()
                        
                        vat_rate = vat_rates.get(vat_code, 20.0)  # Default to 20% if unknown code
                        line_vat = line_total * (vat_rate / 100.0)
                        vat_amount += line_vat
                        
                        items_table.setItem(row, 5, QTableWidgetItem(f"£{line_total:.2f}"))
                    except ValueError:
                        pass
            
            total = subtotal + vat_amount
            
            subtotal_label.setText(f"Subtotal: £{subtotal:.2f}")
            vat_label.setText(f"VAT: £{vat_amount:.2f}")
            total_label.setText(f"Total: £{total:.2f}")
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        def handle_save():
            if not inv_num_entry.text().strip():
                QMessageBox.warning(dialog, "Error", "Invoice number is required")
                return
            
            if items_table.rowCount() == 0:
                QMessageBox.warning(dialog, "Error", "At least one item is required")
                return
            
            invoice_date = date_entry.date().toString("yyyy-MM-dd")
            # VAT rate is now per-item, so pass 0.0 as default
            vat_rate = 0.0
            
            success, message, invoice_id = self.invoice_controller.create_invoice(
                supplier_id, inv_num_entry.text().strip(), invoice_date, vat_rate
            )
            
            if not success:
                QMessageBox.critical(dialog, "Error", message)
                return
            
            # Add items
            for row in range(items_table.rowCount()):
                stock_num = items_table.item(row, 0).text()
                desc = items_table.item(row, 1).text()
                qty = float(items_table.item(row, 2).text())
                price = float(items_table.item(row, 3).text())
                
                # Get VAT code from widget or item
                vat_widget = items_table.cellWidget(row, 4)
                if vat_widget and isinstance(vat_widget, QComboBox):
                    vat_code = vat_widget.currentText().strip().upper()
                else:
                    vat_code_item = items_table.item(row, 4)
                    vat_code = vat_code_item.text().strip().upper() if vat_code_item else 'S'
                
                # Try to find product by stock number
                product_id = None
                if self.invoice_controller and hasattr(self.invoice_controller, 'product_model'):
                    # This would need to be set up in the controller
                    pass
                
                self.invoice_controller.add_invoice_item(
                    invoice_id, product_id, stock_num, desc, qty, price
                )
            
            QMessageBox.information(dialog, "Success", "Invoice created successfully")
            dialog.accept()
            parent_dialog.accept()  # Close parent dialog to refresh
            
        save_btn = QPushButton("Save (Ctrl+Enter)")
        save_btn.setDefault(True)
        save_btn.clicked.connect(handle_save)
        ctrl_enter = QShortcut(QKeySequence("Ctrl+Return"), dialog)
        ctrl_enter.activated.connect(handle_save)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel (Esc)")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        inv_num_entry.setFocus()
        dialog.exec()
    
    def _add_invoice_item_dialog(self, parent_dialog: QDialog, items_table: QTableWidget, supplier_id: int, update_totals_callback=None):
        """Product search and basket dialog for adding items to invoice."""
        if not self.product_model:
            QMessageBox.warning(parent_dialog, "Error", "Product model not available")
            return
        
        dialog = QDialog(parent_dialog)
        dialog.setWindowTitle("Add Products to Invoice")
        dialog.setModal(True)
        dialog.setMinimumSize(900, 800)
        dialog.resize(900, 800)
        apply_theme(dialog)
        
        esc_shortcut = QShortcut(QKeySequence("Escape"), dialog)
        esc_shortcut.activated.connect(dialog.reject)
        
        main_layout = QVBoxLayout(dialog)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("Search Products and Add to Basket")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # Product search and selection section
        products_section = QWidget()
        products_layout = QVBoxLayout(products_section)
        products_layout.setSpacing(10)
        products_layout.setContentsMargins(0, 0, 0, 0)
        
        # Search field
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_label.setMinimumWidth(80)
        search_layout.addWidget(search_label)
        search_entry = QLineEdit()
        search_entry.setPlaceholderText("Search by stock number or description...")
        search_entry.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        search_layout.addWidget(search_entry, stretch=1)
        products_layout.addLayout(search_layout)
        
        # Products table with Enter key support
        class ProductSearchTableWidget(QTableWidget):
            def __init__(self, add_callback):
                super().__init__()
                self.add_callback = add_callback
            
            def keyPressEvent(self, event):
                if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                    if self.selectedItems():
                        row = self.selectedItems()[0].row()
                        self.add_callback(row)
                        event.accept()
                        return
                super().keyPressEvent(event)
        
        products_table = ProductSearchTableWidget(lambda row: add_to_basket_from_row(row))
        products_table.setColumnCount(4)
        products_table.setHorizontalHeaderLabels(["Stock #", "Description", "Type", "Action"])
        products_table.horizontalHeader().setStretchLastSection(True)
        products_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        products_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        products_table.setAlternatingRowColors(True)
        products_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        products_table.setMinimumHeight(300)
        products_layout.addWidget(products_table)
        
        # Store filtered products for Enter key
        filtered_products_list = []
        
        def add_to_basket_from_row(row):
            """Add product to basket from table row."""
            if 0 <= row < len(filtered_products_list):
                add_to_basket(filtered_products_list[row])
        
        main_layout.addWidget(products_section)
        
        # Basket section (below products)
        basket_label = QLabel("Basket")
        basket_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        main_layout.addWidget(basket_label)
        
        # Basket table
        basket_table = QTableWidget()
        basket_table.setColumnCount(6)
        basket_table.setHorizontalHeaderLabels(["Stock #", "Description", "Quantity", "Unit Price", "VAT Code", "Remove"])
        basket_table.horizontalHeader().setStretchLastSection(True)
        basket_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        basket_table.setAlternatingRowColors(True)
        basket_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        basket_table.setMinimumHeight(300)
        main_layout.addWidget(basket_table)
        
        # Basket data storage
        basket_items = []  # List of dicts: {product_id, stock_number, description, quantity, unit_price, vat_code}
        
        # Load all products
        all_products = self.product_model.get_all(self._current_user_id) if hasattr(self, '_current_user_id') else []
        
        def filter_products():
            """Filter products based on search text."""
            nonlocal filtered_products_list
            search_text = search_entry.text().lower().strip()
            if not search_text:
                filtered_products_list = all_products
            else:
                filtered_products_list = [
                    p for p in all_products
                    if search_text in p.get('stock_number', '').lower() or
                       search_text in p.get('description', '').lower()
                ]
            
            products_table.setRowCount(len(filtered_products_list))
            for row, product in enumerate(filtered_products_list):
                products_table.setItem(row, 0, QTableWidgetItem(product.get('stock_number', '')))
                products_table.setItem(row, 1, QTableWidgetItem(product.get('description', '')))
                products_table.setItem(row, 2, QTableWidgetItem(product.get('type', '')))
                
                # Add button
                add_btn = QPushButton("Add")
                add_btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                add_btn.clicked.connect(lambda checked, p=product: add_to_basket(p))
                products_table.setCellWidget(row, 3, add_btn)
            
            products_table.resizeColumnsToContents()
        
        def add_to_basket(product):
            """Add product to basket."""
            # Get product ID (could be 'id' or 'internal_id')
            product_id = product.get('internal_id') or product.get('id')
            
            # Check if already in basket
            for item in basket_items:
                if item['product_id'] == product_id:
                    QMessageBox.information(dialog, "Info", "Product already in basket")
                    return
            
            # Add to basket
            basket_items.append({
                'product_id': product_id,
                'stock_number': product.get('stock_number', ''),
                'description': product.get('description', ''),
                'quantity': 1.0,
                'unit_price': 0.0,
                'vat_code': 'S'  # Default to Standard VAT
            })
            update_basket_table()
        
        def remove_from_basket(row):
            """Remove item from basket."""
            if 0 <= row < len(basket_items):
                basket_items.pop(row)
                update_basket_table()
        
        def update_basket_table():
            """Update basket table display."""
            basket_table.setRowCount(len(basket_items))
            for row, item in enumerate(basket_items):
                basket_table.setItem(row, 0, QTableWidgetItem(item['stock_number']))
                basket_table.setItem(row, 1, QTableWidgetItem(item['description']))
                
                # Quantity spinbox
                qty_spin = QDoubleSpinBox()
                qty_spin.setRange(0.01, 999999)
                qty_spin.setValue(item['quantity'])
                qty_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                qty_spin.valueChanged.connect(lambda val, r=row: update_basket_item(r, 'quantity', val))
                basket_table.setCellWidget(row, 2, qty_spin)
                
                # Unit price spinbox
                price_spin = QDoubleSpinBox()
                price_spin.setRange(0, 999999)
                price_spin.setPrefix("£")
                price_spin.setValue(item['unit_price'])
                price_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                price_spin.valueChanged.connect(lambda val, r=row: update_basket_item(r, 'unit_price', val))
                basket_table.setCellWidget(row, 3, price_spin)
                
                # VAT Code combobox
                vat_combo = QComboBox()
                vat_combo.addItems(['S', 'E', 'Z'])
                vat_combo.setCurrentText(item.get('vat_code', 'S'))
                vat_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                vat_combo.currentTextChanged.connect(lambda val, r=row: update_basket_item(r, 'vat_code', val))
                basket_table.setCellWidget(row, 4, vat_combo)
                
                # Remove button
                remove_btn = QPushButton("Remove")
                remove_btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                remove_btn.clicked.connect(lambda checked, r=row: remove_from_basket(r))
                basket_table.setCellWidget(row, 5, remove_btn)
            
            basket_table.resizeColumnsToContents()
        
        def update_basket_item(row, field, value):
            """Update basket item field."""
            if 0 <= row < len(basket_items):
                basket_items[row][field] = value
        
        # Connect search field
        search_entry.textChanged.connect(filter_products)
        
        # Initial load
        filter_products()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        def handle_submit():
            """Submit basket to invoice items table."""
            if not basket_items:
                QMessageBox.warning(dialog, "Error", "Basket is empty")
                return
            
            # Validate all items have quantity and price
            for item in basket_items:
                if item['quantity'] <= 0:
                    QMessageBox.warning(dialog, "Error", f"Quantity must be greater than zero for {item['stock_number']}")
                    return
                if item['unit_price'] < 0:
                    QMessageBox.warning(dialog, "Error", f"Unit price cannot be negative for {item['stock_number']}")
                    return
            
            # Add all items to invoice items table
            for item in basket_items:
                row = items_table.rowCount()
                items_table.insertRow(row)
                items_table.setItem(row, 0, QTableWidgetItem(item['stock_number']))
                items_table.setItem(row, 1, QTableWidgetItem(item['description']))
                items_table.setItem(row, 2, QTableWidgetItem(str(item['quantity'])))
                items_table.setItem(row, 3, QTableWidgetItem(str(item['unit_price'])))
                
                # VAT Code combobox
                vat_combo = QComboBox()
                vat_combo.addItems(['S', 'E', 'Z'])
                vat_combo.setCurrentText(item.get('vat_code', 'S'))
                if update_totals_callback:
                    vat_combo.currentTextChanged.connect(update_totals_callback)
                items_table.setCellWidget(row, 4, vat_combo)
                
                items_table.setItem(row, 5, QTableWidgetItem(f"£{item['quantity'] * item['unit_price']:.2f}"))
            
            # Trigger totals update in parent dialog
            if update_totals_callback:
                update_totals_callback()
            
            dialog.accept()
        
        submit_btn = QPushButton("Add to Invoice (Ctrl+Enter)")
        submit_btn.setDefault(True)
        submit_btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        submit_btn.clicked.connect(handle_submit)
        ctrl_enter = QShortcut(QKeySequence("Ctrl+Return"), dialog)
        ctrl_enter.activated.connect(handle_submit)
        button_layout.addWidget(submit_btn)
        
        cancel_btn = QPushButton("Cancel (Esc)")
        cancel_btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(button_layout)
        
        # Set up tab order
        dialog.setTabOrder(search_entry, products_table)
        dialog.setTabOrder(products_table, basket_table)
        dialog.setTabOrder(basket_table, submit_btn)
        dialog.setTabOrder(submit_btn, cancel_btn)
        
        # Set focus to search field
        search_entry.setFocus()
        
        dialog.exec()
    
    def _view_invoice_dialog(self, parent_dialog: QDialog, supplier_id: int, invoice_id: int):
        """View invoice dialog - displays invoice details in read-only format."""
        if not self.invoice_controller:
            QMessageBox.warning(self, "Error", "Invoice controller not available")
            return
        
        # Get invoice details
        invoice = self.invoice_controller.get_invoice(invoice_id)
        if not invoice:
            QMessageBox.warning(self, "Error", "Invoice not found")
            return
        
        # Get invoice items
        invoice_items = self.invoice_controller.get_invoice_items(invoice_id)
        
        # Get outstanding balance
        outstanding = self.invoice_controller.get_invoice_outstanding_balance(invoice_id)
        
        dialog = QDialog(parent_dialog)
        dialog.setWindowTitle(f"Invoice {invoice['invoice_number']}")
        dialog.setModal(True)
        dialog.setMinimumSize(800, 600)
        dialog.resize(800, 600)
        apply_theme(dialog)
        
        esc_shortcut = QShortcut(QKeySequence("Escape"), dialog)
        esc_shortcut.activated.connect(dialog.reject)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Invoice header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(10)
        
        # Title
        title_label = QLabel(f"Invoice {invoice['invoice_number']}")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        # Invoice Number (read-only)
        inv_num_layout = QHBoxLayout()
        inv_num_label = QLabel("Invoice Number:")
        inv_num_label.setMinimumWidth(150)
        inv_num_label.setStyleSheet("font-weight: bold;")
        inv_num_layout.addWidget(inv_num_label)
        inv_num_value = QLabel(invoice['invoice_number'])
        inv_num_layout.addWidget(inv_num_value, stretch=1)
        header_layout.addLayout(inv_num_layout)
        
        # Invoice Date (read-only)
        date_layout = QHBoxLayout()
        date_label = QLabel("Invoice Date:")
        date_label.setMinimumWidth(150)
        date_label.setStyleSheet("font-weight: bold;")
        date_layout.addWidget(date_label)
        date_value = QLabel(invoice['invoice_date'])
        date_layout.addWidget(date_value, stretch=1)
        header_layout.addLayout(date_layout)
        
        # VAT Rate (read-only)
        vat_layout = QHBoxLayout()
        vat_label = QLabel("VAT Rate (%):")
        vat_label.setMinimumWidth(150)
        vat_label.setStyleSheet("font-weight: bold;")
        vat_layout.addWidget(vat_label)
        vat_value = QLabel(f"{invoice['vat_rate']:.2f}%")
        vat_layout.addWidget(vat_value, stretch=1)
        header_layout.addLayout(vat_layout)
        
        # Status (read-only)
        status_layout = QHBoxLayout()
        status_label = QLabel("Status:")
        status_label.setMinimumWidth(150)
        status_label.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(status_label)
        status_value = QLabel(invoice['status'])
        status_layout.addWidget(status_value, stretch=1)
        header_layout.addLayout(status_layout)
        
        layout.addLayout(header_layout)
        
        # Items table
        items_label = QLabel("Items:")
        items_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(items_label)
        
        items_table = QTableWidget()
        items_table.setColumnCount(5)
        items_table.setHorizontalHeaderLabels(["Stock #", "Description", "Quantity", "Unit Price", "Line Total"])
        items_table.horizontalHeader().setStretchLastSection(True)
        items_table.setAlternatingRowColors(True)
        items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        items_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        items_table.setMinimumHeight(200)
        
        # Load items
        if invoice_items:
            items_table.setRowCount(len(invoice_items))
            for row, item in enumerate(invoice_items):
                items_table.setItem(row, 0, QTableWidgetItem(item.get('stock_number', '')))
                items_table.setItem(row, 1, QTableWidgetItem(item.get('description', '')))
                items_table.setItem(row, 2, QTableWidgetItem(str(item.get('quantity', 0))))
                items_table.setItem(row, 3, QTableWidgetItem(f"£{item.get('unit_price', 0):.2f}"))
                line_total = item.get('quantity', 0) * item.get('unit_price', 0)
                items_table.setItem(row, 4, QTableWidgetItem(f"£{line_total:.2f}"))
        
        items_table.resizeColumnsToContents()
        layout.addWidget(items_table)
        
        # Totals
        totals_layout = QVBoxLayout()
        totals_layout.setSpacing(5)
        
        subtotal_label = QLabel(f"Subtotal: £{invoice.get('subtotal', 0):.2f}")
        subtotal_label.setStyleSheet("font-size: 12px;")
        totals_layout.addWidget(subtotal_label)
        
        vat_amount_label = QLabel(f"VAT: £{invoice.get('vat_amount', 0):.2f}")
        vat_amount_label.setStyleSheet("font-size: 12px;")
        totals_layout.addWidget(vat_amount_label)
        
        total_label = QLabel(f"Total: £{invoice.get('total', 0):.2f}")
        total_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        totals_layout.addWidget(total_label)
        
        outstanding_label = QLabel(f"Outstanding: £{outstanding:.2f}")
        outstanding_label.setStyleSheet("font-size: 12px; color: #d32f2f;")
        totals_layout.addWidget(outstanding_label)
        
        layout.addLayout(totals_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Close (Esc)")
        close_btn.setMinimumWidth(140)
        close_btn.setMinimumHeight(30)
        close_btn.setDefault(True)
        close_btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        close_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def _edit_invoice_dialog(self, parent_dialog: QDialog, supplier_id: int, invoice_id: int):
        """Edit invoice dialog - similar to create but pre-filled."""
        # Implementation similar to _create_invoice_dialog but loads existing invoice
        QMessageBox.information(self, "Info", "Edit invoice functionality - to be implemented")
    
    def _create_payment_dialog(self, parent_dialog: QDialog, supplier_id: int):
        """Create payment dialog."""
        if not self.payment_controller:
            QMessageBox.warning(self, "Error", "Payment controller not available")
            return
        
        dialog = QDialog(parent_dialog)
        dialog.setWindowTitle("Create Payment")
        dialog.setModal(True)
        dialog.setMinimumSize(500, 400)
        apply_theme(dialog)
        
        esc_shortcut = QShortcut(QKeySequence("Escape"), dialog)
        esc_shortcut.activated.connect(dialog.reject)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Payment Date
        date_layout = QHBoxLayout()
        date_label = QLabel("Payment Date:")
        date_label.setMinimumWidth(150)
        date_layout.addWidget(date_label)
        date_entry = QDateEdit()
        date_entry.setDate(QDate.currentDate())
        date_entry.setCalendarPopup(True)
        date_layout.addWidget(date_entry, stretch=1)
        layout.addLayout(date_layout)
        
        # Amount
        amount_layout = QHBoxLayout()
        amount_label = QLabel("Amount:")
        amount_label.setMinimumWidth(150)
        amount_layout.addWidget(amount_label)
        amount_entry = QDoubleSpinBox()
        amount_entry.setRange(0.01, 999999)
        amount_entry.setPrefix("£")
        amount_entry.setValue(0.0)
        amount_layout.addWidget(amount_entry, stretch=1)
        layout.addLayout(amount_layout)
        
        # Reference
        ref_layout = QHBoxLayout()
        ref_label = QLabel("Reference:")
        ref_label.setMinimumWidth(150)
        ref_layout.addWidget(ref_label)
        ref_entry = QLineEdit()
        ref_layout.addWidget(ref_entry, stretch=1)
        layout.addLayout(ref_layout)
        
        # Payment Method
        method_layout = QHBoxLayout()
        method_label = QLabel("Payment Method:")
        method_label.setMinimumWidth(150)
        method_layout.addWidget(method_label)
        method_combo = QComboBox()
        method_combo.addItems(["Cash", "Card", "Cheque", "BACS"])
        method_combo.setCurrentIndex(0)  # Default to Cash
        method_layout.addWidget(method_combo, stretch=1)
        layout.addLayout(method_layout)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        def handle_save():
            if amount_entry.value() <= 0:
                QMessageBox.warning(dialog, "Error", "Payment amount must be greater than zero")
                return
            
            payment_date = date_entry.date().toString("yyyy-MM-dd")
            payment_method = method_combo.currentText()
            success, message, payment_id = self.payment_controller.create_payment(
                supplier_id, payment_date, amount_entry.value(),
                ref_entry.text().strip(), payment_method
            )
            
            if not success:
                QMessageBox.critical(dialog, "Error", message)
                return
            
            dialog.accept()
            
            # Check if supplier has outstanding invoices and show allocation dialog
            outstanding_invoices = self.payment_controller.get_outstanding_invoices(supplier_id)
            if outstanding_invoices and payment_id:
                # Show allocation dialog (it will handle closing parent_dialog on success)
                # Pass a callback to close parent_dialog after successful allocation
                def allocation_callback():
                    parent_dialog.accept()  # Close parent to refresh
                self._allocate_payment_dialog(parent_dialog, supplier_id, payment_id, allocation_callback)
            else:
                # No outstanding invoices, show success and close parent to refresh
                QMessageBox.information(parent_dialog, "Success", "Payment created successfully")
                parent_dialog.accept()
        
        save_btn = QPushButton("Save (Ctrl+Enter)")
        save_btn.setDefault(True)
        save_btn.clicked.connect(handle_save)
        ctrl_enter = QShortcut(QKeySequence("Ctrl+Return"), dialog)
        ctrl_enter.activated.connect(handle_save)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel (Esc)")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        date_entry.setFocus()
        dialog.exec()
    
    def _allocate_payment_dialog(self, parent_dialog: QDialog, supplier_id: int, payment_id: int, 
                                 on_success_callback: Optional[Callable] = None):
        """
        Allocate payment to invoices dialog.
        
        Args:
            parent_dialog: Parent dialog
            supplier_id: Supplier ID
            payment_id: Payment ID
            on_success_callback: Optional callback to call after successful allocation
        """
        if not self.payment_controller:
            return
        
        dialog = QDialog(parent_dialog)
        dialog.setWindowTitle("Allocate Payment")
        dialog.setModal(True)
        dialog.setMinimumSize(600, 500)
        apply_theme(dialog)
        
        esc_shortcut = QShortcut(QKeySequence("Escape"), dialog)
        esc_shortcut.activated.connect(dialog.reject)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        payment = self.payment_controller.get_payment(payment_id)
        if not payment:
            QMessageBox.warning(dialog, "Error", "Payment not found")
            dialog.reject()
            return
        
        unallocated = self.payment_controller.get_payment_unallocated_amount(payment_id)
        
        info_label = QLabel(f"Payment Amount: £{payment['amount']:.2f}\nUnallocated: £{unallocated:.2f}")
        info_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(info_label)
        
        # Outstanding invoices
        invoices = self.payment_controller.get_outstanding_invoices(supplier_id)
        
        invoices_table = QTableWidget()
        invoices_table.setColumnCount(4)
        invoices_table.setHorizontalHeaderLabels(["Invoice #", "Date", "Outstanding", "Allocate"])
        invoices_table.horizontalHeader().setStretchLastSection(True)
        invoices_table.setAlternatingRowColors(True)
        invoices_table.setRowCount(len(invoices))
        
        allocation_entries = []
        for row, invoice in enumerate(invoices):
            invoices_table.setItem(row, 0, QTableWidgetItem(invoice['invoice_number']))
            invoices_table.setItem(row, 1, QTableWidgetItem(invoice['invoice_date']))
            invoices_table.setItem(row, 2, QTableWidgetItem(f"£{invoice['outstanding_balance']:.2f}"))
            
            # Allocation amount entry
            alloc_entry = QDoubleSpinBox()
            alloc_entry.setRange(0, min(unallocated, invoice['outstanding_balance']))
            alloc_entry.setPrefix("£")
            alloc_entry.setValue(0.0)
            allocation_entries.append((invoice['id'], alloc_entry))
            invoices_table.setCellWidget(row, 3, alloc_entry)
        
        layout.addWidget(invoices_table)
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        def handle_allocate():
            total_allocated = sum(entry.value() for _, entry in allocation_entries)
            if total_allocated > unallocated:
                QMessageBox.warning(dialog, "Error", f"Total allocation (£{total_allocated:.2f}) exceeds unallocated amount (£{unallocated:.2f})")
                return
            
            for invoice_id, entry in allocation_entries:
                if entry.value() > 0:
                    success, message, _ = self.payment_controller.allocate_payment(
                        payment_id, invoice_id, entry.value()
                    )
                    if not success:
                        QMessageBox.critical(dialog, "Error", message)
                        return
            
            QMessageBox.information(dialog, "Success", "Payment allocated successfully")
            dialog.accept()
            if on_success_callback:
                on_success_callback()
            else:
                parent_dialog.accept()
        
        allocate_btn = QPushButton("Allocate (Ctrl+Enter)")
        allocate_btn.setDefault(True)
        allocate_btn.clicked.connect(handle_allocate)
        ctrl_enter = QShortcut(QKeySequence("Ctrl+Return"), dialog)
        ctrl_enter.activated.connect(handle_allocate)
        button_layout.addWidget(allocate_btn)
        
        cancel_btn = QPushButton("Cancel (Esc)")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        dialog.exec()
