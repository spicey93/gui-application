"""Suppliers view GUI."""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QDialog, QLineEdit, QTabWidget, QMessageBox, QHeaderView,
    QDateEdit, QDoubleSpinBox, QSpinBox, QComboBox, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QDate, QEvent
from PySide6.QtGui import QKeyEvent, QShortcut, QKeySequence
from typing import List, Dict, Optional, Callable, TYPE_CHECKING
from views.navigation_panel import NavigationPanel

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


class SuppliersView(QWidget):
    """Suppliers management GUI."""
    
    # Signals
    dashboard_requested = Signal()
    configuration_requested = Signal()
    logout_requested = Signal()
    create_requested = Signal(str, str)
    update_requested = Signal(int, str, str)
    delete_requested = Signal(int)
    refresh_requested = Signal()
    
    def __init__(self):
        """Initialize the suppliers view."""
        super().__init__()
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
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Navigation panel (left sidebar)
        self.nav_panel = NavigationPanel(current_view="suppliers")
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
        
        # Title and Add Supplier button
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("Suppliers")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        self.add_supplier_button = QPushButton("Add Supplier (Ctrl+N)")
        self.add_supplier_button.setMinimumWidth(180)
        self.add_supplier_button.setMinimumHeight(30)
        self.add_supplier_button.clicked.connect(self._handle_add_supplier)
        title_layout.addWidget(self.add_supplier_button)
        
        content_layout.addLayout(title_layout)
        
        # Suppliers table
        self.suppliers_table = SuppliersTableWidget(self._open_selected_supplier)
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
        
        # Double-click to edit
        self.suppliers_table.itemDoubleClicked.connect(self._on_table_double_click)
        
        content_layout.addWidget(self.suppliers_table)
        
        # Add content area to main layout
        main_layout.addWidget(content_frame, stretch=1)
    
    def _setup_keyboard_navigation(self):
        """Set up keyboard navigation."""
        # Tab order: Table -> Add Supplier -> Navigation panel
        # This makes the table the first focusable element
        self.setTabOrder(self.suppliers_table, self.add_supplier_button)
        self.setTabOrder(self.add_supplier_button, self.nav_panel.logout_button)
        
        # Arrow keys work automatically in QTableWidget
        # Enter key on table row opens details
        self.suppliers_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def showEvent(self, event: QEvent):
        """Handle show event - set focus to table if it has data."""
        super().showEvent(event)
        # Set focus to table if it has rows
        if self.suppliers_table.rowCount() > 0:
            self.suppliers_table.setFocus()
            # Ensure first row is selected if nothing is selected
            if not self.suppliers_table.selectedItems():
                self.suppliers_table.selectRow(0)
    
    def _handle_dashboard(self):
        """Handle dashboard button click."""
        self.dashboard_requested.emit()
    
    def _handle_suppliers(self):
        """Handle suppliers button click."""
        # Already on suppliers page
        pass
    
    def _handle_products(self):
        """Handle products button click."""
        # Navigation handled by main app
        pass
    
    def _handle_configuration(self):
        """Handle configuration button click."""
        self.configuration_requested.emit()
    
    def _handle_logout(self):
        """Handle logout button click."""
        self.logout_requested.emit()
    
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
                self._edit_invoice_dialog(dialog, supplier_id, invoices_list[row]['id'])
        
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
            
            # Double-click to edit invoice
            invoices_table.itemDoubleClicked.connect(
                lambda item: self._edit_invoice_dialog(dialog, supplier_id, invoices_list[item.row()]['id'])
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
                supplier_data = self.supplier_model.get_by_id(supplier_id, self.user_id)
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
                supplier_data = self.supplier_model.get_by_id(supplier_id, self.user_id)
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
        date_layout.addWidget(date_entry, stretch=1)
        header_layout.addLayout(date_layout)
        
        # VAT Rate
        vat_layout = QHBoxLayout()
        vat_label = QLabel("VAT Rate (%):")
        vat_label.setMinimumWidth(150)
        vat_layout.addWidget(vat_label)
        vat_entry = QDoubleSpinBox()
        vat_entry.setRange(0, 100)
        vat_entry.setValue(20.0)
        vat_entry.setSuffix("%")
        vat_layout.addWidget(vat_entry, stretch=1)
        header_layout.addLayout(vat_layout)
        
        layout.addLayout(header_layout)
        
        # Items table
        items_label = QLabel("Items:")
        items_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(items_label)
        
        items_table = QTableWidget()
        items_table.setColumnCount(5)
        items_table.setHorizontalHeaderLabels(["Stock #", "Description", "Quantity", "Unit Price", "Line Total"])
        items_table.horizontalHeader().setStretchLastSection(True)
        items_table.setAlternatingRowColors(True)
        items_table.setMinimumHeight(200)
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
            for row in range(items_table.rowCount()):
                qty_item = items_table.item(row, 2)
                price_item = items_table.item(row, 3)
                if qty_item and price_item:
                    try:
                        qty = float(qty_item.text())
                        price = float(price_item.text())
                        line_total = qty * price
                        subtotal += line_total
                        items_table.setItem(row, 4, QTableWidgetItem(f"£{line_total:.2f}"))
                    except ValueError:
                        pass
            
            vat_rate = vat_entry.value()
            vat_amount = subtotal * (vat_rate / 100.0)
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
            vat_rate = vat_entry.value()
            
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
        basket_table.setColumnCount(5)
        basket_table.setHorizontalHeaderLabels(["Stock #", "Description", "Quantity", "Unit Price", "Remove"])
        basket_table.horizontalHeader().setStretchLastSection(True)
        basket_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        basket_table.setAlternatingRowColors(True)
        basket_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        basket_table.setMinimumHeight(300)
        main_layout.addWidget(basket_table)
        
        # Basket data storage
        basket_items = []  # List of dicts: {product_id, stock_number, description, quantity, unit_price}
        
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
                'unit_price': 0.0
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
                
                # Remove button
                remove_btn = QPushButton("Remove")
                remove_btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                remove_btn.clicked.connect(lambda checked, r=row: remove_from_basket(r))
                basket_table.setCellWidget(row, 4, remove_btn)
            
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
                items_table.setItem(row, 4, QTableWidgetItem(f"£{item['quantity'] * item['unit_price']:.2f}"))
            
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
