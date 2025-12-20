"""Suppliers view GUI."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QLineEdit, 
    QTabWidget, QMessageBox, QHeaderView, QDateEdit, 
    QDoubleSpinBox, QSpinBox, QComboBox, QTextEdit, QCompleter
)
from PySide6.QtCore import Qt, Signal, QDate, QEvent, QStringListModel
from PySide6.QtGui import QKeyEvent, QShortcut, QKeySequence, QCloseEvent
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
                      product_model=None, tyre_model=None):
        """Set the invoice and payment controllers."""
        self.invoice_controller = invoice_controller
        self.payment_controller = payment_controller
        self.supplier_model = supplier_model
        self._current_user_id = user_id
        self.product_model = product_model
        self.tyre_model = tyre_model
    
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
        
        # Set column resize modes - ID fixed, Name stretches, others resize to contents
        header = self.suppliers_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.resizeSection(0, 80)
        
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
        header = self.invoices_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
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
        header = self.payments_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
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
            # Force table to recalculate column widths when tab becomes visible
            self._resize_invoices_table()
        elif index == 3:  # Payments tab
            self._refresh_payments_tab()
            # Force table to recalculate column widths when tab becomes visible
            self._resize_payments_table()
    
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
    
    def _show_supplier_details(self, supplier_id: int, account_number: str, name: str, initial_tab: int = 0):
        """Show supplier details in a popup dialog with tabs.
        
        Args:
            supplier_id: Supplier ID
            account_number: Supplier account number
            name: Supplier name
            initial_tab: Initial tab index to show (0=Info, 1=Invoices, 2=Payments, 3=Actions)
        """
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
        
        # Select first row if available
        if invoices_list:
            invoices_table.selectRow(0)
        
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
        payments_table.setColumnCount(7)
        payments_table.setHorizontalHeaderLabels(["Date", "Amount", "Method", "Reference", "Unallocated", "Allocations", "Delete"])
        payments_table.horizontalHeader().setStretchLastSection(False)
        payments_table.setColumnWidth(5, 100)  # Allocations column width
        payments_table.setColumnWidth(6, 80)  # Delete column width
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
                allocations = self.payment_controller.get_payment_allocations(payment_id)
                
                payments_table.setItem(row, 0, QTableWidgetItem(payment['payment_date']))
                payments_table.setItem(row, 1, QTableWidgetItem(f"£{payment['amount']:.2f}"))
                payments_table.setItem(row, 2, QTableWidgetItem(payment.get('payment_method', 'Cash')))
                payments_table.setItem(row, 3, QTableWidgetItem(payment.get('reference', '')))
                payments_table.setItem(row, 4, QTableWidgetItem(f"£{unallocated:.2f}"))
                
                # Allocations button/view
                if allocations:
                    alloc_btn = QPushButton(f"View ({len(allocations)})")
                    alloc_btn.setMaximumWidth(90)
                    alloc_btn.clicked.connect(
                        lambda checked, pay_id=payment_id: 
                        self._view_payment_allocations_dialog(dialog, supplier_id, pay_id)
                    )
                    payments_table.setCellWidget(row, 5, alloc_btn)
                else:
                    payments_table.setItem(row, 5, QTableWidgetItem("None"))
                
                # Delete button (disabled if allocated)
                delete_btn = QPushButton("Delete")
                delete_btn.setMaximumWidth(70)
                if allocations:
                    delete_btn.setEnabled(False)
                    delete_btn.setToolTip("Cannot delete payment with allocations. Unallocate first.")
                delete_btn.clicked.connect(
                    lambda checked, pay_id=payment_id, pay_date=payment['payment_date'], pay_amt=payment['amount']: 
                    self._delete_payment_dialog(dialog, supplier_id, pay_id, pay_date, pay_amt)
                )
                payments_table.setCellWidget(row, 6, delete_btn)
            
            # Double-click to allocate payment
            payments_table.itemDoubleClicked.connect(
                lambda item: self._allocate_payment_dialog(dialog, supplier_id, payments_list[item.row()]['id'])
            )
        
        # Select first row if available
        if payments_list:
            payments_table.selectRow(0)
        
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
        
        # Set initial tab
        notebook.setCurrentIndex(initial_tab)
        
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
        
        # Select first row if available
        if len(invoices) > 0:
            self.invoices_table.selectRow(0)
        
        # Trigger resize to ensure columns fill available space
        self._resize_invoices_table()
    
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
        
        # Select first row if available
        if len(payments) > 0:
            self.payments_table.selectRow(0)
        
        # Trigger resize to ensure columns fill available space
        self._resize_payments_table()
    
    def _resize_invoices_table(self):
        """Resize invoices table columns to fill available space."""
        if not self.invoices_table.isVisible():
            # Table is not visible, schedule resize for when it becomes visible
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, self._resize_invoices_table)
            return
        
        header = self.invoices_table.horizontalHeader()
        # Resize ResizeToContents columns to their optimal size
        # This forces Qt to recalculate column widths
        header.resizeSections(QHeaderView.ResizeMode.ResizeToContents)
        # Restore the stretch mode for column 2 (Supplier)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        # Force the table to update its layout
        self.invoices_table.doItemsLayout()
    
    def _resize_payments_table(self):
        """Resize payments table columns to fill available space."""
        if not self.payments_table.isVisible():
            # Table is not visible, schedule resize for when it becomes visible
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, self._resize_payments_table)
            return
        
        header = self.payments_table.horizontalHeader()
        # Resize ResizeToContents columns to their optimal size
        # This forces Qt to recalculate column widths
        header.resizeSections(QHeaderView.ResizeMode.ResizeToContents)
        # Restore the stretch mode for column 2 (Supplier)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        # Force the table to update its layout
        self.payments_table.doItemsLayout()
    
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
        
        # Override closeEvent to show confirmation
        def handle_close_event(event: QCloseEvent):
            """Handle close event with confirmation."""
            reply = QMessageBox.question(
                dialog,
                "Confirm Close",
                "Are you sure you want to close? Any unsaved changes will be lost.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()
        
        dialog.closeEvent = handle_close_event
        
        # Handle Escape key with confirmation
        def handle_escape():
            """Handle Escape key with confirmation."""
            reply = QMessageBox.question(
                dialog,
                "Confirm Close",
                "Are you sure you want to close? Any unsaved changes will be lost.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                dialog.reject()
        
        esc_shortcut = QShortcut(QKeySequence("Escape"), dialog)
        esc_shortcut.activated.connect(handle_escape)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Invoice header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(10)
        
        # Supplier dropdown
        supplier_layout = QHBoxLayout()
        supplier_label = QLabel("Supplier:")
        supplier_label.setMinimumWidth(150)
        supplier_layout.addWidget(supplier_label)
        supplier_combo = QComboBox()
        supplier_combo.setStyleSheet("font-size: 12px;")
        
        # Populate suppliers dropdown
        suppliers = []
        if self.supplier_model and hasattr(self, '_current_user_id'):
            suppliers = self.supplier_model.get_all(self._current_user_id)
        
        if not suppliers:
            QMessageBox.warning(dialog, "Error", "No suppliers available. Please create a supplier first.")
            dialog.reject()
            return
        
        selected_supplier_index = 0
        for idx, supplier in enumerate(suppliers):
            account_num = supplier.get('account_number', '')
            name = supplier.get('name', '')
            # Format: "Account Number - Name" or just "Name" if no account number
            if account_num:
                display_text = f"{account_num} - {name}"
            else:
                display_text = name
            supplier_combo.addItem(display_text, supplier.get('id'))
            # Pre-select the supplier that was passed in
            if supplier.get('id') == supplier_id:
                selected_supplier_index = idx
        
        supplier_combo.setCurrentIndex(selected_supplier_index)
        supplier_layout.addWidget(supplier_combo, stretch=1)
        header_layout.addLayout(supplier_layout)
        
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
        
        # Custom table widget with Enter key and double-click support
        class InvoiceItemsTableWidget(QTableWidget):
            def __init__(self, edit_callback):
                super().__init__()
                self.edit_callback = edit_callback
            
            def keyPressEvent(self, event):
                """Handle Enter key to edit selected item."""
                if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                    if self.selectedItems():
                        row = self.selectedItems()[0].row()
                        self.edit_callback(row)
                        event.accept()
                        return
                super().keyPressEvent(event)
        
        items_table = InvoiceItemsTableWidget(lambda row: edit_invoice_item(row))
        items_table.setColumnCount(6)
        items_table.setHorizontalHeaderLabels(["Stock #", "Description", "Quantity", "Unit Price", "VAT Code", "Line Total"])
        header = items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        items_table.setAlternatingRowColors(True)
        items_table.setMinimumHeight(200)
        items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Read-only
        items_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        items_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        items_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        items_table.itemDoubleClicked.connect(lambda item, row=0: edit_invoice_item(item.row()))
        layout.addWidget(items_table)
        
        # Store invoice items data
        invoice_items_data = []  # List of dicts: {stock_number, description, quantity, unit_price, vat_code}
        
        # Add Item button
        def open_add_item_dialog():
            """Open add item dialog with current supplier selection."""
            current_supplier_id = supplier_combo.currentData()
            if current_supplier_id is None:
                current_supplier_id = supplier_id  # Fallback to original
            self._add_invoice_item_dialog(dialog, items_table, current_supplier_id, update_totals, invoice_items_data=invoice_items_data, update_table=update_invoice_table)
        
        add_item_btn = QPushButton("Add Item (Ctrl+I)")
        add_item_btn.clicked.connect(open_add_item_dialog)
        layout.addWidget(add_item_btn)
        
        # Add Item shortcut
        add_item_shortcut = QShortcut(QKeySequence("Ctrl+I"), dialog)
        add_item_shortcut.activated.connect(open_add_item_dialog)
        
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
        
        def update_invoice_table():
            """Update the invoice items table from invoice_items_data."""
            items_table.setRowCount(len(invoice_items_data))
            for row, item in enumerate(invoice_items_data):
                items_table.setItem(row, 0, QTableWidgetItem(item['stock_number']))
                items_table.setItem(row, 1, QTableWidgetItem(item['description']))
                items_table.setItem(row, 2, QTableWidgetItem(str(item['quantity'])))
                items_table.setItem(row, 3, QTableWidgetItem(str(item['unit_price'])))
                items_table.setItem(row, 4, QTableWidgetItem(item['vat_code']))
                line_total = item['quantity'] * item['unit_price']
                items_table.setItem(row, 5, QTableWidgetItem(f"£{line_total:.2f}"))
            update_totals()
        
        def update_totals():
            """Update totals from items."""
            subtotal = 0.0
            vat_amount = 0.0
            
            # VAT rates by code: S=Standard (20%), E=Exempt (0%), Z=Zero (0%)
            vat_rates = {'S': 20.0, 'E': 0.0, 'Z': 0.0}
            
            for item in invoice_items_data:
                line_total = item['quantity'] * item['unit_price']
                subtotal += line_total
                
                vat_code = item.get('vat_code', 'S').strip().upper()
                vat_rate = vat_rates.get(vat_code, 20.0)
                line_vat = line_total * (vat_rate / 100.0)
                vat_amount += line_vat
            
            total = subtotal + vat_amount
            
            subtotal_label.setText(f"Subtotal: £{subtotal:.2f}")
            vat_label.setText(f"VAT: £{vat_amount:.2f}")
            total_label.setText(f"Total: £{total:.2f}")
        
        def edit_invoice_item(row):
            """Open basket dialog to edit/delete an invoice item."""
            if 0 <= row < len(invoice_items_data):
                item_to_edit = invoice_items_data[row]
                # Get current supplier from dropdown
                current_supplier_id = supplier_combo.currentData()
                if current_supplier_id is None:
                    current_supplier_id = supplier_id  # Fallback to original
                # Open basket dialog in edit mode
                self._add_invoice_item_dialog(dialog, items_table, current_supplier_id, update_totals, invoice_items_data=invoice_items_data, update_table=update_invoice_table, edit_item=item_to_edit, edit_row=row)
        
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
            
            # Get selected supplier from dropdown
            selected_supplier_id = supplier_combo.currentData()
            if selected_supplier_id is None:
                QMessageBox.warning(dialog, "Error", "Please select a supplier")
                return
            
            invoice_date = date_entry.date().toString("yyyy-MM-dd")
            # VAT rate is now per-item, so pass 0.0 as default
            vat_rate = 0.0
            
            success, message, invoice_id = self.invoice_controller.create_invoice(
                selected_supplier_id, inv_num_entry.text().strip(), invoice_date, vat_rate
            )
            
            if not success:
                QMessageBox.critical(dialog, "Error", message)
                return
            
            # Add items from invoice_items_data
            for item in invoice_items_data:
                stock_num = item['stock_number']
                desc = item['description']
                qty = item['quantity']
                price = item['unit_price']
                vat_code = item.get('vat_code', 'S')
                
                # Get product_id from item (stored when adding to basket)
                product_id = item.get('product_id')
                
                self.invoice_controller.add_invoice_item(
                    invoice_id, product_id, stock_num, desc, qty, price, vat_code
                )
            
            QMessageBox.information(dialog, "Success", "Invoice created successfully")
            dialog.accept()
            if parent_dialog is not None:
                parent_dialog.accept()  # Close parent dialog to refresh
            
        save_btn = QPushButton("Save (Ctrl+Enter)")
        save_btn.setDefault(True)
        save_btn.clicked.connect(handle_save)
        ctrl_enter = QShortcut(QKeySequence("Ctrl+Return"), dialog)
        ctrl_enter.activated.connect(handle_save)
        button_layout.addWidget(save_btn)
        
        def handle_cancel():
            """Handle cancel button with confirmation."""
            reply = QMessageBox.question(
                dialog,
                "Confirm Close",
                "Are you sure you want to close? Any unsaved changes will be lost.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                dialog.reject()
        
        cancel_btn = QPushButton("Cancel (Esc)")
        cancel_btn.clicked.connect(handle_cancel)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        inv_num_entry.setFocus()
        dialog.exec()
    
    def _add_invoice_item_dialog(self, parent_dialog: QDialog, items_table: QTableWidget, supplier_id: int, update_totals_callback=None, invoice_items_data=None, update_table=None, edit_item=None, edit_row=None):
        """Product search and basket dialog for adding/editing items to invoice."""
        if not self.product_model:
            QMessageBox.warning(parent_dialog, "Error", "Product model not available")
            return
        
        dialog = QDialog(parent_dialog)
        if edit_item is not None:
            dialog.setWindowTitle("Edit Invoice Item")
        else:
            dialog.setWindowTitle("Add Products to Invoice")
        dialog.setModal(True)
        dialog.setMinimumSize(900, 800)
        dialog.resize(900, 800)
        apply_theme(dialog)
        
        # Override closeEvent to show confirmation
        def handle_close_event(event: QCloseEvent):
            """Handle close event with confirmation."""
            reply = QMessageBox.question(
                dialog,
                "Confirm Close",
                "Are you sure you want to close? Any unsaved changes will be lost.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()
        
        dialog.closeEvent = handle_close_event
        
        # Handle Escape key with confirmation
        def handle_escape():
            """Handle Escape key with confirmation."""
            reply = QMessageBox.question(
                dialog,
                "Confirm Close",
                "Are you sure you want to close? Any unsaved changes will be lost.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                dialog.reject()
        
        esc_shortcut = QShortcut(QKeySequence("Escape"), dialog)
        esc_shortcut.activated.connect(handle_escape)
        
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
        
        # Search field with custom key handling
        class SearchLineEdit(QLineEdit):
            def keyPressEvent(self, event):
                """Override to prevent Enter from triggering default button."""
                if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                    # Emit returnPressed signal and accept the event
                    self.returnPressed.emit()
                    event.accept()
                    return
                super().keyPressEvent(event)
        
        # Create two-column grid layout for filters
        from PySide6.QtWidgets import QGridLayout
        filter_grid = QGridLayout()
        filter_grid.setColumnStretch(0, 0)  # Label column - fixed width
        filter_grid.setColumnStretch(1, 1)   # Input column - stretches
        filter_grid.setSpacing(10)
        filter_grid.setColumnMinimumWidth(0, 100)  # Minimum width for label column
        
        row = 0
        
        # Search field
        search_label = QLabel("Search:")
        search_label.setStyleSheet("font-size: 11px;")
        filter_grid.addWidget(search_label, row, 0)
        search_entry = SearchLineEdit()
        search_entry.setPlaceholderText("Search by stock number or description...")
        search_entry.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        filter_grid.addWidget(search_entry, row, 1)
        row += 1
        
        # Brand filter - editable with autocomplete
        brand_label = QLabel("Brand:")
        brand_label.setStyleSheet("font-size: 11px;")
        filter_grid.addWidget(brand_label, row, 0)
        brand_combo = QComboBox()
        brand_combo.setEditable(True)
        brand_combo.addItem("")  # Empty option
        filter_grid.addWidget(brand_combo, row, 1)
        row += 1
        
        # Model filter - editable with autocomplete
        model_label = QLabel("Model:")
        model_label.setStyleSheet("font-size: 11px;")
        filter_grid.addWidget(model_label, row, 0)
        model_combo = QComboBox()
        model_combo.setEditable(True)
        model_combo.addItem("")  # Empty option
        filter_grid.addWidget(model_combo, row, 1)
        row += 1
        
        products_layout.addLayout(filter_grid)
        
        # Search and Clear buttons (will be connected after filter_products is defined)
        button_row_layout = QHBoxLayout()
        button_row_layout.setSpacing(10)
        
        search_button = QPushButton("Search")
        search_button.setMinimumHeight(30)
        button_row_layout.addWidget(search_button)
        
        clear_button = QPushButton("Clear")
        clear_button.setMinimumHeight(30)
        button_row_layout.addWidget(clear_button)
        button_row_layout.addStretch()
        
        products_layout.addLayout(button_row_layout)
        
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
        
        # Message label for no results
        no_results_label = QLabel()
        no_results_label.setStyleSheet("color: red; font-size: 12px; padding: 10px;")
        no_results_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        no_results_label.hide()
        products_layout.addWidget(no_results_label)
        
        products_table = ProductSearchTableWidget(lambda row: add_to_basket_from_row(row))
        products_table.setColumnCount(1)
        products_table.setHorizontalHeaderLabels(["Description"])
        # Set column resize modes - Description stretches
        header = products_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        products_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        products_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        products_table.setAlternatingRowColors(True)
        products_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        products_table.setMinimumHeight(300)
        products_layout.addWidget(products_table)
        
        # Store filtered products for Enter key (includes both products and catalogue tyres)
        filtered_products_list = []
        
        # Check if tyre_model is available
        tyre_model = getattr(self, 'tyre_model', None)
        
        def load_brand_dropdowns():
            """Load brand dropdown with values from both products and catalogue."""
            brands = set()
            
            # Get brands from products
            if self.product_model:
                tyre_products = self.product_model.get_tyre_products(self._current_user_id) if hasattr(self, '_current_user_id') else []
                for product in tyre_products:
                    if product.get('tyre_brand'):
                        brands.add(product['tyre_brand'])
            
            # Get brands from catalogue
            if tyre_model:
                catalogue_brands = tyre_model.get_unique_brands()
                brands.update(catalogue_brands)
            
            # Set up autocomplete for brand
            brand_list = sorted(brands)
            brand_completer = QCompleter(brand_list, brand_combo)
            brand_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            brand_completer.setFilterMode(Qt.MatchFlag.MatchContains)
            brand_combo.setCompleter(brand_completer)
            
            # Add items to combo for dropdown
            brand_combo.clear()
            brand_combo.addItem("")  # Empty option
            for brand in brand_list:
                brand_combo.addItem(brand)
        
        def load_model_dropdown():
            """Load model dropdown based on selected brand."""
            selected_brand = brand_combo.currentText().strip()
            
            models = set()
            
            # Get models from products
            if self.product_model:
                tyre_products = self.product_model.get_tyre_products(self._current_user_id) if hasattr(self, '_current_user_id') else []
                for product in tyre_products:
                    product_brand = product.get('tyre_brand', '').strip()
                    if (not selected_brand or product_brand == selected_brand) and product.get('tyre_model'):
                        models.add(product['tyre_model'])
            
            # Get models from catalogue
            if tyre_model:
                if selected_brand:
                    catalogue_tyres = tyre_model.search(brand=selected_brand, limit=10000)
                else:
                    # If no brand selected, get all models (limited)
                    catalogue_tyres = tyre_model.search(limit=10000)
                for tyre in catalogue_tyres:
                    if tyre.get('model'):
                        models.add(tyre['model'])
            
            # Set up autocomplete for model
            model_list = sorted(models)
            model_completer = QCompleter(model_list, model_combo)
            model_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            model_completer.setFilterMode(Qt.MatchFlag.MatchContains)
            model_combo.setCompleter(model_completer)
            
            # Add items to combo for dropdown
            model_combo.clear()
            model_combo.addItem("")  # Empty option
            for model in model_list:
                model_combo.addItem(model)
        
        # Connect brand dropdown to update model dropdown
        brand_combo.currentTextChanged.connect(lambda: load_model_dropdown())
        
        # Initial load of brand dropdown
        load_brand_dropdowns()
        
        # Set up Enter key handlers for brand and model
        def handle_brand_enter():
            """Handle Enter key in brand field."""
            filter_products()
        
        def handle_model_enter():
            """Handle Enter key in model field."""
            filter_products()
        
        # Custom line edit class to prevent Enter from triggering default button
        class ComboLineEdit(QLineEdit):
            def keyPressEvent(self, event):
                """Override to prevent Enter from triggering default button."""
                if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                    self.returnPressed.emit()
                    event.accept()
                    return
                super().keyPressEvent(event)
        
        # Replace line edits with custom ones
        brand_line_edit = ComboLineEdit()
        brand_combo.setLineEdit(brand_line_edit)
        brand_line_edit.returnPressed.connect(handle_brand_enter)
        
        model_line_edit = ComboLineEdit()
        model_combo.setLineEdit(model_line_edit)
        model_line_edit.returnPressed.connect(handle_model_enter)
        
        def show_add_product_dialog(product):
            """Show dialog to enter unit cost, VAT code, and quantity."""
            # If this is a catalogue tyre, create a product from it first
            if product.get('_source') == 'catalogue':
                if not self.product_model or not hasattr(self, '_current_user_id'):
                    QMessageBox.warning(dialog, "Error", "Cannot add catalogue tyre: product model not available")
                    return
                
                # Create product from catalogue tyre
                success, message, internal_product_id = self.product_model.create_from_tyre_catalogue(
                    product, self._current_user_id
                )
                
                if not success:
                    QMessageBox.warning(dialog, "Error", f"Failed to create product from catalogue: {message}")
                    return
                
                # Get the newly created product
                new_product = self.product_model.get_by_internal_id(internal_product_id)
                if not new_product:
                    QMessageBox.warning(dialog, "Error", "Product created but could not be retrieved")
                    return
                
                # Update product to use the created product
                product = new_product.copy()
                product['_source'] = 'product'
                product['internal_id'] = internal_product_id
                
                # Refresh products list
                all_products.clear()
                all_products.extend(self.product_model.get_all(self._current_user_id))
            
            item_dialog = QDialog(dialog)
            item_dialog.setWindowTitle("Add Product to Basket")
            item_dialog.setModal(True)
            item_dialog.setMinimumSize(400, 250)
            apply_theme(item_dialog)
            
            layout = QVBoxLayout(item_dialog)
            layout.setSpacing(15)
            layout.setContentsMargins(20, 20, 20, 20)
            
            # Product info (read-only)
            info_label = QLabel(f"Product: {product.get('stock_number', '')} - {product.get('description', '')}")
            info_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            layout.addWidget(info_label)
            
            # Unit cost
            cost_layout = QHBoxLayout()
            cost_label = QLabel("Unit Cost:")
            cost_label.setMinimumWidth(100)
            cost_layout.addWidget(cost_label)
            cost_spin = QDoubleSpinBox()
            cost_spin.setRange(0, 999999)
            cost_spin.setPrefix("£")
            cost_spin.setValue(0.0)
            cost_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            cost_layout.addWidget(cost_spin, stretch=1)
            layout.addLayout(cost_layout)
            
            # VAT Code
            vat_layout = QHBoxLayout()
            vat_label = QLabel("VAT Code:")
            vat_label.setMinimumWidth(100)
            vat_layout.addWidget(vat_label)
            vat_combo = QComboBox()
            vat_combo.addItems(['S', 'E', 'Z'])
            vat_combo.setCurrentText('S')
            vat_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            vat_layout.addWidget(vat_combo, stretch=1)
            layout.addLayout(vat_layout)
            
            # Quantity
            qty_layout = QHBoxLayout()
            qty_label = QLabel("Quantity:")
            qty_label.setMinimumWidth(100)
            qty_layout.addWidget(qty_label)
            qty_spin = QDoubleSpinBox()
            qty_spin.setRange(0.01, 999999)
            qty_spin.setValue(1.0)
            qty_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            qty_layout.addWidget(qty_spin, stretch=1)
            layout.addLayout(qty_layout)
            
            # Buttons
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            def handle_add():
                """Add product with entered values."""
                unit_price = cost_spin.value()
                vat_code = vat_combo.currentText()
                quantity = qty_spin.value()
                
                if quantity <= 0:
                    QMessageBox.warning(item_dialog, "Error", "Quantity must be greater than zero")
                    return
                
                if unit_price < 0:
                    QMessageBox.warning(item_dialog, "Error", "Unit cost cannot be negative")
                    return
                
                # Add to basket with entered values
                product_id = product.get('internal_id') or product.get('id')
                
                # If editing, replace the item; otherwise check for duplicates
                if edit_item is not None and len(basket_items) > 0:
                    # Replace the existing item, preserve product_id if it exists
                    basket_items[0] = {
                        'product_id': product_id,
                        'stock_number': product.get('stock_number', ''),
                        'description': product.get('description', ''),
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'vat_code': vat_code
                    }
                    # Preserve original product_id if it was set
                    if 'product_id' in edit_item and edit_item['product_id'] is not None:
                        basket_items[0]['product_id'] = edit_item['product_id']
                else:
                    # Check if already in basket
                    for item in basket_items:
                        if item.get('product_id') == product_id:
                            QMessageBox.information(item_dialog, "Info", "Product already in basket")
                            return
                    
                    basket_items.append({
                        'product_id': product_id,
                        'stock_number': product.get('stock_number', ''),
                        'description': product.get('description', ''),
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'vat_code': vat_code
                    })
                update_basket_table()
                item_dialog.accept()
                
                # Clear search fields and results table
                search_entry.clear()
                brand_combo.setCurrentIndex(0)
                brand_combo.lineEdit().clear()
                model_combo.setCurrentIndex(0)
                model_combo.lineEdit().clear()
                products_table.setRowCount(0)
                filtered_products_list.clear()
                no_results_label.hide()
                
                # Return focus to search field for next search
                search_entry.setFocus()
            
            add_btn = QPushButton("Add to Basket")
            add_btn.setDefault(True)
            add_btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            add_btn.clicked.connect(handle_add)
            button_layout.addWidget(add_btn)
            
            cancel_btn = QPushButton("Cancel")
            cancel_btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            cancel_btn.clicked.connect(item_dialog.reject)
            button_layout.addWidget(cancel_btn)
            
            layout.addLayout(button_layout)
            
            # Set focus to unit cost
            cost_spin.setFocus()
            
            item_dialog.exec()
        
        def add_to_basket_from_row(row):
            """Add product to basket from table row."""
            if 0 <= row < len(filtered_products_list):
                show_add_product_dialog(filtered_products_list[row])
        
        main_layout.addWidget(products_section)
        
        # Basket section (below products)
        basket_label = QLabel("Basket")
        basket_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        main_layout.addWidget(basket_label)
        
        # Basket table
        basket_table = QTableWidget()
        if edit_item is not None:
            # When editing, show delete button instead of remove
            basket_table.setColumnCount(6)
            basket_table.setHorizontalHeaderLabels(["Stock #", "Description", "Quantity", "Unit Price", "VAT Code", "Delete"])
        else:
            basket_table.setColumnCount(6)
            basket_table.setHorizontalHeaderLabels(["Stock #", "Description", "Quantity", "Unit Price", "VAT Code", "Remove"])
        basket_table.horizontalHeader().setStretchLastSection(False)
        basket_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        basket_table.setAlternatingRowColors(True)
        basket_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        basket_table.setMinimumHeight(300)
        # Set fixed column widths for consistency
        basket_table.setColumnWidth(0, 120)  # Stock #
        basket_table.setColumnWidth(1, 300)  # Description
        basket_table.setColumnWidth(2, 100)  # Quantity
        basket_table.setColumnWidth(3, 120)  # Unit Price
        basket_table.setColumnWidth(4, 100)  # VAT Code
        basket_table.setColumnWidth(5, 100)  # Remove/Delete
        basket_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        basket_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        basket_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        basket_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        basket_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        basket_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        main_layout.addWidget(basket_table)
        
        # Basket data storage
        basket_items = []  # List of dicts: {product_id, stock_number, description, quantity, unit_price, vat_code}
        
        # Load all products
        all_products = self.product_model.get_all(self._current_user_id) if hasattr(self, '_current_user_id') else []
        
        def filter_products():
            """Filter products and catalogue tyres based on search text and filters."""
            nonlocal filtered_products_list
            search_text = search_entry.text().lower().strip()
            selected_brand = brand_combo.currentText().strip()
            selected_model = model_combo.currentText().strip()
            
            results = []
            
            # Always search both products and catalogue
            # Search products
            product_list = all_products
            
            # Apply brand filter for tyre products (case-insensitive partial match)
            if selected_brand:
                brand_lower = selected_brand.lower()
                product_list = [
                    p for p in product_list
                    if not p.get('is_tyre') or (p.get('tyre_brand', '') or '').lower().find(brand_lower) != -1
                ]
            
            # Apply model filter for tyre products (case-insensitive partial match)
            if selected_model:
                model_lower = selected_model.lower()
                product_list = [
                    p for p in product_list
                    if not p.get('is_tyre') or (p.get('tyre_model', '') or '').lower().find(model_lower) != -1
                ]
            
            # Apply search text filter
            if search_text:
                product_list = [
                    p for p in product_list
                    if search_text in p.get('stock_number', '').lower() or
                       search_text in p.get('description', '').lower()
                ]
            
            # Add products to results with source indicator
            for product in product_list:
                product_copy = product.copy()
                product_copy['_source'] = 'product'
                results.append(product_copy)
            
            # Search catalogue tyres (always enabled)
            if tyre_model:
                # Build catalogue search filters
                catalogue_filters = {}
                # For brand, use exact match if it's in the dropdown, otherwise search pattern
                if selected_brand:
                    # Check if it's an exact match from dropdown
                    brand_items = [brand_combo.itemText(i) for i in range(brand_combo.count())]
                    if selected_brand in brand_items:
                        catalogue_filters['brand'] = selected_brand
                    else:
                        # Partial match - will filter after search
                        pass
                
                # Search catalogue
                catalogue_tyres = tyre_model.search(
                    pattern=search_text if search_text else None,
                    limit=1000,
                    **catalogue_filters
                )
                
                # Apply brand filter if specified (partial match)
                if selected_brand:
                    brand_lower = selected_brand.lower()
                    catalogue_tyres = [
                        t for t in catalogue_tyres
                        if (t.get('brand', '') or '').lower().find(brand_lower) != -1
                    ]
                
                # Apply model filter if specified (partial match)
                if selected_model:
                    model_lower = selected_model.lower()
                    catalogue_tyres = [
                        t for t in catalogue_tyres
                        if (t.get('model', '') or '').lower().find(model_lower) != -1
                    ]
                
                # Add catalogue tyres to results
                for tyre in catalogue_tyres:
                    tyre_copy = tyre.copy()
                    tyre_copy['_source'] = 'catalogue'
                    # Map catalogue fields to product-like structure
                    tyre_copy['stock_number'] = tyre.get('ean', '') or tyre.get('description', '')[:50]
                    tyre_copy['description'] = tyre.get('description', '')
                    tyre_copy['type'] = tyre.get('product_type', '')
                    results.append(tyre_copy)
            
            filtered_products_list = results
            
            # Always show table, just populate it (empty if no results)
            products_table.setRowCount(len(filtered_products_list))
            
            if len(filtered_products_list) == 0:
                no_results_label.setText("No products or tyres exist that match the search.")
                no_results_label.show()
            else:
                no_results_label.hide()
                
                for row, item in enumerate(filtered_products_list):
                    products_table.setItem(row, 0, QTableWidgetItem(item.get('description', '')))
                
                # Select and highlight first row if results exist
                products_table.selectRow(0)
                products_table.setFocus()
        
        def add_to_basket(product):
            """Add product to basket (used by Add button)."""
            show_add_product_dialog(product)
        
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
        
        def update_basket_item(row, field, value):
            """Update basket item field."""
            if 0 <= row < len(basket_items):
                basket_items[row][field] = value
        
        # If editing, pre-populate basket with the item being edited
        if edit_item is not None:
            basket_items.append(edit_item.copy())
            update_basket_table()
        
        # Connect search field and filters - trigger search
        def handle_search_enter():
            """Handle Enter key in search field."""
            filter_products()
        
        search_entry.returnPressed.connect(handle_search_enter)
        # Connect buttons to filter_products (defined above)
        search_button.clicked.connect(filter_products)
        clear_button.clicked.connect(lambda: (
            search_entry.clear(),
            brand_combo.setCurrentIndex(0),
            model_combo.setCurrentIndex(0),
            filter_products()
        ))
        # Note: Removed auto-search on filter change - user must click Search button
        # brand_combo.currentTextChanged.connect(filter_products)
        # model_combo.currentTextChanged.connect(filter_products)
        
        # Don't load all products initially - wait for search
        filtered_products_list = []
        products_table.setRowCount(0)
        no_results_label.hide()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        def handle_submit():
            """Submit basket to invoice items table."""
            # If editing and basket is empty, delete the item
            if edit_item is not None and edit_row is not None and invoice_items_data is not None and update_table is not None:
                if not basket_items:
                    # Delete the item
                    invoice_items_data.pop(edit_row)
                    update_table()
                    dialog.accept()
                    return
            
            # For adding new items, check basket is not empty
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
            
            # If editing, replace the item at edit_row; otherwise add new items
            if edit_item is not None and edit_row is not None and invoice_items_data is not None and update_table is not None:
                # Edit mode: replace the item
                if len(basket_items) > 0:
                    invoice_items_data[edit_row] = basket_items[0]
                    update_table()
            elif invoice_items_data is not None and update_table is not None:
                # Add mode: add all items to invoice_items_data
                for item in basket_items:
                    invoice_items_data.append(item)
                update_table()
            else:
                # Legacy mode: directly modify items_table
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
        
        # Change button text based on edit mode
        if edit_item is not None:
            submit_btn_text = "Update Item (Ctrl+Enter)"
        else:
            submit_btn_text = "Add to Invoice (Ctrl+Enter)"
        
        submit_btn = QPushButton(submit_btn_text)
        submit_btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        submit_btn.setAutoDefault(False)  # Prevent Enter key from triggering this button
        submit_btn.setDefault(False)  # Explicitly not default
        submit_btn.clicked.connect(handle_submit)
        ctrl_enter = QShortcut(QKeySequence("Ctrl+Return"), dialog)
        ctrl_enter.activated.connect(handle_submit)
        button_layout.addWidget(submit_btn)
        
        def handle_cancel():
            """Handle cancel button with confirmation."""
            reply = QMessageBox.question(
                dialog,
                "Confirm Close",
                "Are you sure you want to close? Any unsaved changes will be lost.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                dialog.reject()
        
        cancel_btn = QPushButton("Cancel (Esc)")
        cancel_btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        cancel_btn.clicked.connect(handle_cancel)
        button_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(button_layout)
        
        # Set up tab order: Search -> Brand -> Model -> Products Table -> Basket -> Submit -> Cancel
        dialog.setTabOrder(search_entry, brand_combo)
        dialog.setTabOrder(brand_combo, model_combo)
        dialog.setTabOrder(model_combo, products_table)
        dialog.setTabOrder(products_table, basket_table)
        dialog.setTabOrder(basket_table, submit_btn)
        dialog.setTabOrder(submit_btn, cancel_btn)
        
        # Set focus to search field
        search_entry.setFocus()
        
        dialog.exec()
    
    def _view_payment_allocations_dialog(self, parent_dialog: QDialog, supplier_id: int, payment_id: int):
        """View and manage payment allocations dialog."""
        if not self.payment_controller:
            return
        
        dialog = QDialog(parent_dialog)
        dialog.setWindowTitle("Payment Allocations")
        dialog.setModal(True)
        dialog.setMinimumSize(600, 400)
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
        
        info_label = QLabel(f"Payment: £{payment['amount']:.2f} on {payment['payment_date']}")
        info_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(info_label)
        
        allocations = self.payment_controller.get_payment_allocations(payment_id)
        
        if not allocations:
            no_alloc_label = QLabel("No allocations found.")
            layout.addWidget(no_alloc_label)
        else:
            allocations_table = QTableWidget()
            allocations_table.setColumnCount(4)
            allocations_table.setHorizontalHeaderLabels(["Invoice #", "Date", "Amount Allocated", "Unallocate"])
            allocations_table.horizontalHeader().setStretchLastSection(False)
            allocations_table.setColumnWidth(3, 100)
            allocations_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            allocations_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            allocations_table.setAlternatingRowColors(True)
            allocations_table.setRowCount(len(allocations))
            
            for row, allocation in enumerate(allocations):
                # Get invoice details
                invoice_id = allocation['invoice_id']
                invoice = self.invoice_controller.get_invoice(invoice_id) if self.invoice_controller else None
                
                if invoice:
                    allocations_table.setItem(row, 0, QTableWidgetItem(invoice.get('invoice_number', 'N/A')))
                    allocations_table.setItem(row, 1, QTableWidgetItem(invoice.get('invoice_date', 'N/A')))
                else:
                    allocations_table.setItem(row, 0, QTableWidgetItem(f"Invoice #{invoice_id}"))
                    allocations_table.setItem(row, 1, QTableWidgetItem("N/A"))
                
                allocations_table.setItem(row, 2, QTableWidgetItem(f"£{allocation['amount_allocated']:.2f}"))
                
                # Unallocate button
                unalloc_btn = QPushButton("Unallocate")
                unalloc_btn.setMaximumWidth(90)
                unalloc_btn.clicked.connect(
                    lambda checked, alloc_id=allocation['id']: self._unallocate_payment(dialog, supplier_id, alloc_id)
                )
                allocations_table.setCellWidget(row, 3, unalloc_btn)
            
            layout.addWidget(allocations_table)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_btn = QPushButton("Close (Esc)")
        close_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def _unallocate_payment(self, parent_dialog: QDialog, supplier_id: int, allocation_id: int):
        """Unallocate a payment from an invoice."""
        reply = QMessageBox.question(
            parent_dialog,
            "Confirm Unallocate",
            "Are you sure you want to unallocate this payment?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.payment_controller.delete_allocation(allocation_id)
            if success:
                QMessageBox.information(parent_dialog, "Success", message)
                # Refresh the dialog
                parent_dialog.accept()
                # Reopen supplier details to refresh
                supplier_data = self.supplier_model.get_by_id(supplier_id, self._current_user_id)
                if supplier_data:
                    self._show_supplier_details(supplier_id, supplier_data['account_number'], supplier_data['name'])
            else:
                QMessageBox.warning(parent_dialog, "Error", message)
    
    def _view_invoice_dialog(self, parent_dialog: QDialog, supplier_id: int, invoice_id: int):
        """Edit invoice dialog - allows editing invoice details and items."""
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
        dialog.setWindowTitle(f"Edit Invoice {invoice['invoice_number']}")
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
        
        # Supplier dropdown
        supplier_layout = QHBoxLayout()
        supplier_label = QLabel("Supplier:")
        supplier_label.setMinimumWidth(150)
        supplier_layout.addWidget(supplier_label)
        supplier_combo = QComboBox()
        supplier_combo.setStyleSheet("font-size: 12px;")
        
        # Populate suppliers dropdown
        suppliers = []
        if self.supplier_model and hasattr(self, '_current_user_id'):
            suppliers = self.supplier_model.get_all(self._current_user_id)
        
        selected_supplier_index = 0
        # Get internal supplier ID from invoice
        invoice_supplier_internal_id = invoice.get('supplier_id')
        for idx, supp in enumerate(suppliers):
            account_num = supp.get('account_number', '')
            name = supp.get('name', '')
            if account_num:
                display_text = f"{account_num} - {name}"
            else:
                display_text = name
            supplier_combo.addItem(display_text, supp.get('id'))
            # Pre-select the invoice's supplier (compare internal_id)
            if supp.get('internal_id') == invoice_supplier_internal_id:
                selected_supplier_index = idx
        
        supplier_combo.setCurrentIndex(selected_supplier_index)
        supplier_layout.addWidget(supplier_combo, stretch=1)
        header_layout.addLayout(supplier_layout)
        
        # Invoice Number (editable)
        inv_num_layout = QHBoxLayout()
        inv_num_label = QLabel("Invoice Number:")
        inv_num_label.setMinimumWidth(150)
        inv_num_layout.addWidget(inv_num_label)
        inv_num_entry = QLineEdit(invoice['invoice_number'])
        inv_num_layout.addWidget(inv_num_entry, stretch=1)
        header_layout.addLayout(inv_num_layout)
        
        # Invoice Date (editable)
        date_layout = QHBoxLayout()
        date_label = QLabel("Invoice Date:")
        date_label.setMinimumWidth(150)
        date_layout.addWidget(date_label)
        date_entry = QDateEdit()
        invoice_date = QDate.fromString(invoice['invoice_date'], "yyyy-MM-dd")
        date_entry.setDate(invoice_date)
        date_entry.setCalendarPopup(True)
        date_entry.setStyleSheet("font-size: 12px;")
        date_layout.addWidget(date_entry, stretch=1)
        header_layout.addLayout(date_layout)
        
        layout.addLayout(header_layout)
        
        # Items table - use same structure as create invoice
        items_label = QLabel("Items:")
        items_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(items_label)
        
        # Custom table widget with Enter key and double-click support
        class InvoiceItemsTableWidget(QTableWidget):
            def __init__(self, edit_callback):
                super().__init__()
                self.edit_callback = edit_callback
            
            def keyPressEvent(self, event):
                """Handle Enter key to edit selected item."""
                if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                    if self.selectedItems():
                        row = self.selectedItems()[0].row()
                        self.edit_callback(row)
                        event.accept()
                        return
                super().keyPressEvent(event)
        
        items_table = InvoiceItemsTableWidget(lambda row: edit_invoice_item(row))
        items_table.setColumnCount(6)
        items_table.setHorizontalHeaderLabels(["Stock #", "Description", "Quantity", "Unit Price", "VAT Code", "Line Total"])
        header = items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        items_table.setAlternatingRowColors(True)
        items_table.setMinimumHeight(200)
        items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Read-only
        items_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        items_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        items_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        items_table.itemDoubleClicked.connect(lambda item, row=0: edit_invoice_item(item.row()))
        layout.addWidget(items_table)
        
        # Store invoice items data
        invoice_items_data = []
        
        # Load existing items into invoice_items_data
        for item in invoice_items:
            invoice_items_data.append({
                'item_id': item.get('id'),  # Store item ID for updates/deletes
                'product_id': item.get('product_id'),
                'stock_number': item.get('stock_number', ''),
                'description': item.get('description', ''),
                'quantity': item.get('quantity', 0),
                'unit_price': item.get('unit_price', 0),
                'vat_code': item.get('vat_code', 'S')  # Get from database
            })
        
        def update_invoice_table():
            """Update the invoice items table from invoice_items_data."""
            items_table.setRowCount(len(invoice_items_data))
            for row, item in enumerate(invoice_items_data):
                items_table.setItem(row, 0, QTableWidgetItem(item['stock_number']))
                items_table.setItem(row, 1, QTableWidgetItem(item['description']))
                items_table.setItem(row, 2, QTableWidgetItem(str(item['quantity'])))
                items_table.setItem(row, 3, QTableWidgetItem(str(item['unit_price'])))
                items_table.setItem(row, 4, QTableWidgetItem(item.get('vat_code', 'S')))
                line_total = item['quantity'] * item['unit_price']
                items_table.setItem(row, 5, QTableWidgetItem(f"£{line_total:.2f}"))
            update_totals()
        
        def update_totals():
            """Update totals from items."""
            subtotal = 0.0
            vat_amount = 0.0
            
            # VAT rates by code: S=Standard (20%), E=Exempt (0%), Z=Zero (0%)
            vat_rates = {'S': 20.0, 'E': 0.0, 'Z': 0.0}
            
            for item in invoice_items_data:
                line_total = item['quantity'] * item['unit_price']
                subtotal += line_total
                
                vat_code = item.get('vat_code', 'S').strip().upper()
                vat_rate = vat_rates.get(vat_code, 20.0)
                line_vat = line_total * (vat_rate / 100.0)
                vat_amount += line_vat
            
            total = subtotal + vat_amount
            
            subtotal_label.setText(f"Subtotal: £{subtotal:.2f}")
            vat_label.setText(f"VAT: £{vat_amount:.2f}")
            total_label.setText(f"Total: £{total:.2f}")
        
        def edit_invoice_item(row):
            """Open basket dialog to edit/delete an invoice item."""
            if 0 <= row < len(invoice_items_data):
                item_to_edit = invoice_items_data[row]
                # Open basket dialog in edit mode
                current_supplier_id = supplier_combo.currentData()
                if current_supplier_id is None:
                    current_supplier_id = supplier_id
                self._add_invoice_item_dialog(dialog, items_table, current_supplier_id, update_totals, invoice_items_data=invoice_items_data, update_table=update_invoice_table, edit_item=item_to_edit, edit_row=row)
        
        # Add Item button
        def open_add_item_dialog():
            """Open add item dialog with current supplier selection."""
            current_supplier_id = supplier_combo.currentData()
            if current_supplier_id is None:
                current_supplier_id = supplier_id
            self._add_invoice_item_dialog(dialog, items_table, current_supplier_id, update_totals, invoice_items_data=invoice_items_data, update_table=update_invoice_table)
        
        add_item_btn = QPushButton("Add Item (Ctrl+I)")
        add_item_btn.clicked.connect(open_add_item_dialog)
        layout.addWidget(add_item_btn)
        
        # Add Item shortcut
        add_item_shortcut = QShortcut(QKeySequence("Ctrl+I"), dialog)
        add_item_shortcut.activated.connect(open_add_item_dialog)
        
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
        
        # Initial table update
        update_invoice_table()
        
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
            
            # Get selected supplier from dropdown
            selected_supplier_id = supplier_combo.currentData()
            if selected_supplier_id is None:
                QMessageBox.warning(dialog, "Error", "Please select a supplier")
                return
            
            invoice_date = date_entry.date().toString("yyyy-MM-dd")
            vat_rate = 0.0  # Per-item VAT now
            
            # Get existing invoice items to compare
            existing_items = self.invoice_controller.get_invoice_items(invoice_id)
            existing_item_map = {item.get('id'): item for item in existing_items if item.get('id')}
            
            # Get current item IDs from invoice_items_data
            current_item_ids = {item.get('item_id') for item in invoice_items_data if item.get('item_id')}
            
            # Delete items that were removed (not in current list)
            for existing_item_id, existing_item in existing_item_map.items():
                if existing_item_id not in current_item_ids:
                    self.invoice_controller.delete_invoice_item(existing_item_id)
            
            # Update or add items
            for item in invoice_items_data:
                stock_num = item['stock_number']
                desc = item['description']
                qty = item['quantity']
                price = item['unit_price']
                product_id = item.get('product_id')
                item_id = item.get('item_id')
                
                if item_id and item_id in existing_item_map:
                    # Check if item actually changed
                    existing_item = existing_item_map[item_id]
                    vat_code = item.get('vat_code', 'S')
                    if (existing_item.get('quantity') != qty or 
                        existing_item.get('unit_price') != price or
                        existing_item.get('stock_number') != stock_num or
                        existing_item.get('description') != desc or
                        existing_item.get('vat_code', 'S') != vat_code):
                        # Item changed - delete old (reverses stock) and add new
                        self.invoice_controller.delete_invoice_item(item_id)
                        self.invoice_controller.add_invoice_item(
                            invoice_id, product_id, stock_num, desc, qty, price, vat_code
                        )
                    # If unchanged, do nothing
                else:
                    # New item - add it
                    vat_code = item.get('vat_code', 'S')
                    self.invoice_controller.add_invoice_item(
                        invoice_id, product_id, stock_num, desc, qty, price, vat_code
                    )
            
            # Update invoice (supplier change not supported in update method, so skip for now)
            success, message = self.invoice_controller.update_invoice(
                invoice_id, inv_num_entry.text().strip(), invoice_date, vat_rate, invoice.get('status', 'pending')
            )
            
            if not success:
                QMessageBox.critical(dialog, "Error", message)
                return
            
            QMessageBox.information(dialog, "Success", "Invoice updated successfully")
            dialog.accept()
            if parent_dialog is not None:
                parent_dialog.accept()  # Close parent dialog to refresh
        
        def handle_delete():
            """Delete the invoice."""
            reply = QMessageBox.question(
                dialog,
                "Confirm Delete",
                f"Are you sure you want to delete invoice '{inv_num_entry.text()}'? This will reverse stock changes.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                success, message = self.invoice_controller.delete_invoice(invoice_id)
                if success:
                    QMessageBox.information(dialog, "Success", "Invoice deleted successfully")
                    dialog.accept()
                    if parent_dialog is not None:
                        parent_dialog.accept()  # Close parent dialog to refresh
                else:
                    QMessageBox.critical(dialog, "Error", message)
        
        save_btn = QPushButton("Save Changes (Ctrl+Enter)")
        save_btn.setDefault(True)
        save_btn.clicked.connect(handle_save)
        ctrl_enter = QShortcut(QKeySequence("Ctrl+Return"), dialog)
        ctrl_enter.activated.connect(handle_save)
        button_layout.addWidget(save_btn)
        
        delete_btn = QPushButton("Delete Invoice")
        delete_btn.setStyleSheet("background-color: #d32f2f; color: white;")
        delete_btn.clicked.connect(handle_delete)
        button_layout.addWidget(delete_btn)
        
        cancel_btn = QPushButton("Cancel (Esc)")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
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
                    if parent_dialog is not None:
                        parent_dialog.accept()  # Close parent to refresh
                self._allocate_payment_dialog(parent_dialog, supplier_id, payment_id, allocation_callback)
            else:
                # No outstanding invoices, show success and close parent to refresh
                if parent_dialog is not None:
                    QMessageBox.information(parent_dialog, "Success", "Payment created successfully")
                    parent_dialog.accept()
                else:
                    QMessageBox.information(self, "Success", "Payment created successfully")
        
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
        current_allocations = self.payment_controller.get_payment_allocations(payment_id)
        
        info_label = QLabel(f"Payment Amount: £{payment['amount']:.2f}\nUnallocated: £{unallocated:.2f}")
        info_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(info_label)
        
        # Current allocations section (if any exist)
        if current_allocations:
            allocations_label = QLabel("Current Allocations:")
            allocations_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            layout.addWidget(allocations_label)
            
            allocations_table = QTableWidget()
            allocations_table.setColumnCount(4)
            allocations_table.setHorizontalHeaderLabels(["Invoice #", "Date", "Amount Allocated", "Unallocate"])
            allocations_table.horizontalHeader().setStretchLastSection(False)
            allocations_table.setColumnWidth(3, 100)
            allocations_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            allocations_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            allocations_table.setAlternatingRowColors(True)
            allocations_table.setRowCount(len(current_allocations))
            
            for row, allocation in enumerate(current_allocations):
                # Get invoice details
                invoice_id = allocation['invoice_id']
                invoice = self.invoice_controller.get_invoice(invoice_id) if self.invoice_controller else None
                
                if invoice:
                    allocations_table.setItem(row, 0, QTableWidgetItem(invoice.get('invoice_number', 'N/A')))
                    allocations_table.setItem(row, 1, QTableWidgetItem(invoice.get('invoice_date', 'N/A')))
                else:
                    allocations_table.setItem(row, 0, QTableWidgetItem(f"Invoice #{invoice_id}"))
                    allocations_table.setItem(row, 1, QTableWidgetItem("N/A"))
                
                allocations_table.setItem(row, 2, QTableWidgetItem(f"£{allocation['amount_allocated']:.2f}"))
                
                # Unallocate button
                unalloc_btn = QPushButton("Unallocate")
                unalloc_btn.setMaximumWidth(90)
                unalloc_btn.clicked.connect(
                    lambda checked, alloc_id=allocation['id']: self._handle_unallocate_from_allocate_dialog(
                        dialog, supplier_id, payment_id, alloc_id, parent_dialog, on_success_callback
                    )
                )
                allocations_table.setCellWidget(row, 3, unalloc_btn)
            
            layout.addWidget(allocations_table)
            
            separator = QLabel("─" * 50)
            separator.setStyleSheet("color: #999;")
            layout.addWidget(separator)
        
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
            elif parent_dialog is not None:
                parent_dialog.accept()
        
        def handle_delete():
            """Handle delete payment button."""
            allocations = self.payment_controller.get_payment_allocations(payment_id)
            if allocations:
                QMessageBox.warning(
                    dialog,
                    "Cannot Delete",
                    f"Cannot delete payment: payment has {len(allocations)} allocation(s).\n"
                    "Please unallocate the payment first."
                )
                return
            
            reply = QMessageBox.question(
                dialog,
                "Confirm Delete",
                f"Are you sure you want to delete payment of £{payment['amount']:.2f} from {payment['payment_date']}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                success, message = self.payment_controller.delete_payment(payment_id)
                if success:
                    QMessageBox.information(dialog, "Success", message)
                    dialog.accept()
                    # Close parent dialog if it exists
                    if parent_dialog is not None:
                        parent_dialog.accept()
                    # Reopen supplier details dialog to show updated payments, on payments tab
                    supplier_data = self.supplier_model.get_by_id(supplier_id, self._current_user_id)
                    if supplier_data:
                        # Use QTimer to ensure dialog is closed before reopening
                        from PySide6.QtCore import QTimer
                        def show_supplier_with_payments_tab():
                            self._show_supplier_details(supplier_id, supplier_data['account_number'], supplier_data['name'], initial_tab=2)
                        QTimer.singleShot(100, show_supplier_with_payments_tab)
                    elif on_success_callback:
                        on_success_callback()
                else:
                    QMessageBox.warning(dialog, "Error", message)
        
        allocate_btn = QPushButton("Allocate (Ctrl+Enter)")
        allocate_btn.setDefault(True)
        allocate_btn.clicked.connect(handle_allocate)
        ctrl_enter = QShortcut(QKeySequence("Ctrl+Return"), dialog)
        ctrl_enter.activated.connect(handle_allocate)
        button_layout.addWidget(allocate_btn)
        
        delete_btn = QPushButton("Delete Payment")
        delete_btn.clicked.connect(handle_delete)
        button_layout.addWidget(delete_btn)
        
        cancel_btn = QPushButton("Cancel (Esc)")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        dialog.exec()
    
    def _handle_unallocate_from_allocate_dialog(self, dialog: QDialog, supplier_id: int, payment_id: int, 
                                                allocation_id: int, parent_dialog: Optional[QDialog], 
                                                on_success_callback: Optional[Callable]):
        """Handle unallocate from allocate payment dialog."""
        reply = QMessageBox.question(
            dialog,
            "Confirm Unallocate",
            "Are you sure you want to unallocate this payment?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.payment_controller.delete_allocation(allocation_id)
            if success:
                QMessageBox.information(dialog, "Success", message)
                # Close and reopen the allocate dialog to refresh
                dialog.accept()
                # Reopen allocate dialog
                self._allocate_payment_dialog(parent_dialog, supplier_id, payment_id, on_success_callback)
            else:
                QMessageBox.warning(dialog, "Error", message)
    