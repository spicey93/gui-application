"""Services view GUI."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QLineEdit, 
    QMessageBox, QHeaderView, QDoubleSpinBox, QComboBox, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QKeyEvent, QShortcut, QKeySequence
from typing import List, Dict, Optional, Callable, TYPE_CHECKING
from views.base_view import BaseTabbedView
from utils.styles import apply_theme

if TYPE_CHECKING:
    from models.nominal_account import NominalAccount


class ServicesTableWidget(QTableWidget):
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


class ServicesView(BaseTabbedView):
    """Services management GUI."""
    
    # Additional signals beyond base class
    create_requested = Signal(str, str, str, str, float, str, int, float, float)
    update_requested = Signal(int, str, str, str, str, float, str, int, float, float)
    delete_requested = Signal(int)
    refresh_requested = Signal()
    get_service_details_requested = Signal(int)  # Request full service details
    
    def __init__(self):
        """Initialize the services view."""
        super().__init__(title="Services", current_view="services")
        self.nominal_account_model: Optional["NominalAccount"] = None
        self._current_user_id: Optional[int] = None
        self._create_widgets()
        self._setup_keyboard_navigation()
    
    def set_models(self, nominal_account_model: "NominalAccount", user_id: int):
        """Set the nominal account model and user ID."""
        self.nominal_account_model = nominal_account_model
        self._current_user_id = user_id
    
    def _create_widgets(self):
        """Create and layout UI widgets."""
        # Add action button using base class method
        self.add_service_button = self.add_action_button(
            "Add Service (Ctrl+N)",
            self._handle_add_service,
            None  # Shortcut handled globally in main.py
        )
        
        # Get content layout to add widgets directly (no tabs needed)
        content_layout = self.get_content_layout()
        
        # Services table
        self.services_table = ServicesTableWidget(self._open_selected_service)
        self.services_table.setColumnCount(9)
        self.services_table.setHorizontalHeaderLabels([
            "ID", "Code", "Name", "Group", "Description", 
            "Retail Price", "Trade Price", "Est. Cost", "VAT Code"
        ])
        self.services_table.horizontalHeader().setStretchLastSection(True)
        self.services_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.services_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.services_table.setAlternatingRowColors(True)
        self.services_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Set column resize modes
        header = self.services_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        header.resizeSection(0, 80)
        
        # Enable keyboard navigation
        self.services_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Double-click to edit
        self.services_table.itemDoubleClicked.connect(self._on_table_double_click)
        
        content_layout.addWidget(self.services_table, stretch=1)
    
    def _setup_keyboard_navigation(self):
        """Set up keyboard navigation."""
        # Tab order: Table -> Add Service -> Navigation panel
        self.setTabOrder(self.services_table, self.add_service_button)
        self.setTabOrder(self.add_service_button, self.nav_panel.logout_button)
        
        # Arrow keys work automatically in QTableWidget
        self.services_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def showEvent(self, event: QEvent):
        """Handle show event - set focus to table if it has data."""
        super().showEvent(event)
        # Set focus to table if it has rows
        if self.services_table.rowCount() > 0:
            self.services_table.setFocus()
            # Ensure first row is selected if nothing is selected
            if not self.services_table.selectedItems():
                self.services_table.selectRow(0)
    
    def _handle_add_service(self):
        """Handle Add Service button click."""
        self.add_service()
    
    def _on_table_double_click(self, item: QTableWidgetItem):
        """Handle double-click on table item."""
        self._open_selected_service()
    
    def _open_selected_service(self):
        """Open details for the currently selected service."""
        selected_items = self.services_table.selectedItems()
        if not selected_items:
            return
        
        row = selected_items[0].row()
        service_id = int(self.services_table.item(row, 0).text())
        # Request full service details from controller
        self.get_service_details_requested.emit(service_id)
    
    def load_services(self, services: List[Dict[str, any]]):
        """Load services into the table."""
        self.services_table.setRowCount(len(services))
        
        for row, service in enumerate(services):
            # ID
            id_item = QTableWidgetItem(str(service.get('id', '')))
            id_item.setData(Qt.ItemDataRole.UserRole, service.get('id'))
            self.services_table.setItem(row, 0, id_item)
            
            # Code
            self.services_table.setItem(row, 1, QTableWidgetItem(service.get('code', '')))
            
            # Name
            self.services_table.setItem(row, 2, QTableWidgetItem(service.get('name', '')))
            
            # Group
            self.services_table.setItem(row, 3, QTableWidgetItem(service.get('group_name', '') or ''))
            
            # Description
            desc = service.get('description', '') or ''
            # Truncate long descriptions for display
            if len(desc) > 50:
                desc = desc[:47] + '...'
            self.services_table.setItem(row, 4, QTableWidgetItem(desc))
            
            # Retail Price
            retail_price = service.get('retail_price', 0.0) or 0.0
            self.services_table.setItem(row, 5, QTableWidgetItem(f"£{retail_price:.2f}"))
            
            # Trade Price
            trade_price = service.get('trade_price', 0.0) or 0.0
            self.services_table.setItem(row, 6, QTableWidgetItem(f"£{trade_price:.2f}"))
            
            # Estimated Cost
            est_cost = service.get('estimated_cost', 0.0) or 0.0
            self.services_table.setItem(row, 7, QTableWidgetItem(f"£{est_cost:.2f}"))
            
            # VAT Code
            self.services_table.setItem(row, 8, QTableWidgetItem(service.get('vat_code', 'S')))
    
    def add_service(self):
        """Show dialog to add a new service."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Service")
        dialog.setModal(True)
        dialog.setMinimumSize(600, 700)
        dialog.resize(600, 700)
        apply_theme(dialog)
        
        # Add Escape key shortcut for cancel
        esc_shortcut = QShortcut(QKeySequence("Escape"), dialog)
        esc_shortcut.activated.connect(dialog.reject)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("Add New Service")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Name
        name_layout = QHBoxLayout()
        name_label = QLabel("Name:")
        name_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        name_label.setMinimumWidth(150)
        name_layout.addWidget(name_label)
        name_entry = QLineEdit()
        name_entry.setStyleSheet("font-size: 12px;")
        name_layout.addWidget(name_entry, stretch=1)
        layout.addLayout(name_layout)
        
        # Code
        code_layout = QHBoxLayout()
        code_label = QLabel("Code:")
        code_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        code_label.setMinimumWidth(150)
        code_layout.addWidget(code_label)
        code_entry = QLineEdit()
        code_entry.setStyleSheet("font-size: 12px;")
        code_layout.addWidget(code_entry, stretch=1)
        layout.addLayout(code_layout)
        
        # Group
        group_layout = QHBoxLayout()
        group_label = QLabel("Group:")
        group_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        group_label.setMinimumWidth(150)
        group_layout.addWidget(group_label)
        group_entry = QLineEdit()
        group_entry.setStyleSheet("font-size: 12px;")
        group_layout.addWidget(group_entry, stretch=1)
        layout.addLayout(group_layout)
        
        # Description
        desc_layout = QHBoxLayout()
        desc_label = QLabel("Description:")
        desc_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        desc_label.setMinimumWidth(150)
        desc_layout.addWidget(desc_label)
        desc_entry = QTextEdit()
        desc_entry.setMaximumHeight(100)
        desc_entry.setStyleSheet("font-size: 12px;")
        desc_layout.addWidget(desc_entry, stretch=1)
        layout.addLayout(desc_layout)
        
        # Estimated Cost
        est_cost_layout = QHBoxLayout()
        est_cost_label = QLabel("Estimated Cost:")
        est_cost_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        est_cost_label.setMinimumWidth(150)
        est_cost_layout.addWidget(est_cost_label)
        est_cost_entry = QDoubleSpinBox()
        est_cost_entry.setStyleSheet("font-size: 12px;")
        est_cost_entry.setMaximum(999999.99)
        est_cost_entry.setDecimals(2)
        est_cost_entry.setPrefix("£")
        est_cost_entry.setValue(0.0)
        est_cost_layout.addWidget(est_cost_entry, stretch=1)
        layout.addLayout(est_cost_layout)
        
        # VAT Code
        vat_layout = QHBoxLayout()
        vat_label = QLabel("VAT Code:")
        vat_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        vat_label.setMinimumWidth(150)
        vat_layout.addWidget(vat_label)
        vat_entry = QLineEdit("S")
        vat_entry.setStyleSheet("font-size: 12px;")
        vat_entry.setMaxLength(10)
        vat_layout.addWidget(vat_entry, stretch=1)
        layout.addLayout(vat_layout)
        
        # Income Account
        income_layout = QHBoxLayout()
        income_label = QLabel("Income Account:")
        income_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        income_label.setMinimumWidth(150)
        income_layout.addWidget(income_label)
        income_combo = QComboBox()
        income_combo.setStyleSheet("font-size: 12px;")
        income_combo.addItem("")  # Empty option
        # Populate with Income type accounts
        if self.nominal_account_model and self._current_user_id:
            accounts = self.nominal_account_model.get_all(self._current_user_id)
            for account in accounts:
                if account.get('account_type') == 'Income':
                    display_text = f"{account.get('account_code')} - {account.get('account_name')}"
                    income_combo.addItem(display_text, account.get('id'))
        income_layout.addWidget(income_combo, stretch=1)
        layout.addLayout(income_layout)
        
        # Retail Price
        retail_layout = QHBoxLayout()
        retail_label = QLabel("Retail Price:")
        retail_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        retail_label.setMinimumWidth(150)
        retail_layout.addWidget(retail_label)
        retail_entry = QDoubleSpinBox()
        retail_entry.setStyleSheet("font-size: 12px;")
        retail_entry.setMaximum(999999.99)
        retail_entry.setDecimals(2)
        retail_entry.setPrefix("£")
        retail_entry.setValue(0.0)
        retail_layout.addWidget(retail_entry, stretch=1)
        layout.addLayout(retail_layout)
        
        # Trade Price
        trade_layout = QHBoxLayout()
        trade_label = QLabel("Trade Price:")
        trade_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        trade_label.setMinimumWidth(150)
        trade_layout.addWidget(trade_label)
        trade_entry = QDoubleSpinBox()
        trade_entry.setStyleSheet("font-size: 12px;")
        trade_entry.setMaximum(999999.99)
        trade_entry.setDecimals(2)
        trade_entry.setPrefix("£")
        trade_entry.setValue(0.0)
        trade_layout.addWidget(trade_entry, stretch=1)
        layout.addLayout(trade_layout)
        
        layout.addStretch()
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setMinimumWidth(100)
        cancel_button.clicked.connect(dialog.reject)
        buttons_layout.addWidget(cancel_button)
        
        save_button = QPushButton("Save")
        save_button.setMinimumWidth(100)
        buttons_layout.addWidget(save_button)
        
        layout.addLayout(buttons_layout)
        
        def handle_save():
            name = name_entry.text().strip()
            code = code_entry.text().strip()
            group = group_entry.text().strip()
            description = desc_entry.toPlainText().strip()
            estimated_cost = est_cost_entry.value()
            vat_code = vat_entry.text().strip() or 'S'
            income_account_id = income_combo.currentData()
            retail_price = retail_entry.value()
            trade_price = trade_entry.value()
            
            if not name or not code:
                QMessageBox.critical(dialog, "Error", "Name and code are required")
                return
            
            self.create_requested.emit(
                name, code, group, description, estimated_cost, vat_code,
                income_account_id if income_account_id else 0, retail_price, trade_price
            )
            dialog.accept()
        
        save_button.clicked.connect(handle_save)
        
        # Ctrl+Enter shortcut for save
        ctrl_enter_shortcut = QShortcut(QKeySequence("Ctrl+Return"), dialog)
        ctrl_enter_shortcut.activated.connect(handle_save)
        
        dialog.exec()
    
    def show_service_details(self, service: Dict[str, any]):
        """Show service details dialog with full service data."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Service Details")
        dialog.setModal(True)
        dialog.setMinimumSize(600, 700)
        dialog.resize(600, 700)
        apply_theme(dialog)
        
        # Add Escape key shortcut for cancel
        esc_shortcut = QShortcut(QKeySequence("Escape"), dialog)
        esc_shortcut.activated.connect(dialog.reject)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("Service Information")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title_label)
        
        service_id = service.get('id')
        
        # ID (read-only)
        id_layout = QHBoxLayout()
        id_label = QLabel("ID:")
        id_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        id_label.setMinimumWidth(150)
        id_layout.addWidget(id_label)
        id_value = QLabel(str(service_id))
        id_value.setStyleSheet("font-size: 12px;")
        id_layout.addWidget(id_value)
        id_layout.addStretch()
        layout.addLayout(id_layout)
        
        # Name
        name_layout = QHBoxLayout()
        name_label = QLabel("Name:")
        name_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        name_label.setMinimumWidth(150)
        name_layout.addWidget(name_label)
        name_entry = QLineEdit(service.get('name', ''))
        name_entry.setStyleSheet("font-size: 12px;")
        name_layout.addWidget(name_entry, stretch=1)
        layout.addLayout(name_layout)
        
        # Code
        code_layout = QHBoxLayout()
        code_label = QLabel("Code:")
        code_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        code_label.setMinimumWidth(150)
        code_layout.addWidget(code_label)
        code_entry = QLineEdit(service.get('code', ''))
        code_entry.setStyleSheet("font-size: 12px;")
        code_layout.addWidget(code_entry, stretch=1)
        layout.addLayout(code_layout)
        
        # Group
        group_layout = QHBoxLayout()
        group_label = QLabel("Group:")
        group_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        group_label.setMinimumWidth(150)
        group_layout.addWidget(group_label)
        group_entry = QLineEdit(service.get('group_name', '') or '')
        group_entry.setStyleSheet("font-size: 12px;")
        group_layout.addWidget(group_entry, stretch=1)
        layout.addLayout(group_layout)
        
        # Description
        desc_layout = QHBoxLayout()
        desc_label = QLabel("Description:")
        desc_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        desc_label.setMinimumWidth(150)
        desc_layout.addWidget(desc_label)
        desc_entry = QTextEdit(service.get('description', '') or '')
        desc_entry.setMaximumHeight(100)
        desc_entry.setStyleSheet("font-size: 12px;")
        desc_layout.addWidget(desc_entry, stretch=1)
        layout.addLayout(desc_layout)
        
        # Estimated Cost
        est_cost_layout = QHBoxLayout()
        est_cost_label = QLabel("Estimated Cost:")
        est_cost_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        est_cost_label.setMinimumWidth(150)
        est_cost_layout.addWidget(est_cost_label)
        est_cost_entry = QDoubleSpinBox()
        est_cost_entry.setStyleSheet("font-size: 12px;")
        est_cost_entry.setMaximum(999999.99)
        est_cost_entry.setDecimals(2)
        est_cost_entry.setPrefix("£")
        est_cost_entry.setValue(service.get('estimated_cost', 0.0) or 0.0)
        est_cost_layout.addWidget(est_cost_entry, stretch=1)
        layout.addLayout(est_cost_layout)
        
        # VAT Code
        vat_layout = QHBoxLayout()
        vat_label = QLabel("VAT Code:")
        vat_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        vat_label.setMinimumWidth(150)
        vat_layout.addWidget(vat_label)
        vat_entry = QLineEdit(service.get('vat_code', 'S'))
        vat_entry.setStyleSheet("font-size: 12px;")
        vat_entry.setMaxLength(10)
        vat_layout.addWidget(vat_entry, stretch=1)
        layout.addLayout(vat_layout)
        
        # Income Account
        income_layout = QHBoxLayout()
        income_label = QLabel("Income Account:")
        income_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        income_label.setMinimumWidth(150)
        income_layout.addWidget(income_label)
        income_combo = QComboBox()
        income_combo.setStyleSheet("font-size: 12px;")
        income_combo.addItem("")  # Empty option
        current_income_account_id = service.get('income_account_id')
        current_index = 0
        # Populate with Income type accounts
        if self.nominal_account_model and self._current_user_id:
            accounts = self.nominal_account_model.get_all(self._current_user_id)
            for idx, account in enumerate(accounts):
                if account.get('account_type') == 'Income':
                    display_text = f"{account.get('account_code')} - {account.get('account_name')}"
                    account_id = account.get('id')
                    income_combo.addItem(display_text, account_id)
                    if account_id == current_income_account_id:
                        current_index = idx + 1  # +1 for empty option
        income_combo.setCurrentIndex(current_index)
        income_layout.addWidget(income_combo, stretch=1)
        layout.addLayout(income_layout)
        
        # Retail Price
        retail_layout = QHBoxLayout()
        retail_label = QLabel("Retail Price:")
        retail_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        retail_label.setMinimumWidth(150)
        retail_layout.addWidget(retail_label)
        retail_entry = QDoubleSpinBox()
        retail_entry.setStyleSheet("font-size: 12px;")
        retail_entry.setMaximum(999999.99)
        retail_entry.setDecimals(2)
        retail_entry.setPrefix("£")
        retail_entry.setValue(service.get('retail_price', 0.0) or 0.0)
        retail_layout.addWidget(retail_entry, stretch=1)
        layout.addLayout(retail_layout)
        
        # Trade Price
        trade_layout = QHBoxLayout()
        trade_label = QLabel("Trade Price:")
        trade_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        trade_label.setMinimumWidth(150)
        trade_layout.addWidget(trade_label)
        trade_entry = QDoubleSpinBox()
        trade_entry.setStyleSheet("font-size: 12px;")
        trade_entry.setMaximum(999999.99)
        trade_entry.setDecimals(2)
        trade_entry.setPrefix("£")
        trade_entry.setValue(service.get('trade_price', 0.0) or 0.0)
        trade_layout.addWidget(trade_entry, stretch=1)
        layout.addLayout(trade_layout)
        
        layout.addStretch()
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        delete_button = QPushButton("Delete")
        delete_button.setMinimumWidth(100)
        buttons_layout.addWidget(delete_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setMinimumWidth(100)
        cancel_button.clicked.connect(dialog.reject)
        buttons_layout.addWidget(cancel_button)
        
        save_button = QPushButton("Save")
        save_button.setMinimumWidth(100)
        buttons_layout.addWidget(save_button)
        
        layout.addLayout(buttons_layout)
        
        def handle_save():
            name = name_entry.text().strip()
            code = code_entry.text().strip()
            group = group_entry.text().strip()
            description = desc_entry.toPlainText().strip()
            estimated_cost = est_cost_entry.value()
            vat_code = vat_entry.text().strip() or 'S'
            income_account_id = income_combo.currentData()
            retail_price = retail_entry.value()
            trade_price = trade_entry.value()
            
            if not name or not code:
                QMessageBox.critical(dialog, "Error", "Name and code are required")
                return
            
            self.update_requested.emit(
                service_id, name, code, group, description, estimated_cost, vat_code,
                income_account_id if income_account_id else 0, retail_price, trade_price
            )
            dialog.accept()
        
        def handle_delete():
            reply = QMessageBox.question(
                dialog,
                "Confirm Delete",
                f"Are you sure you want to delete service '{name_entry.text()}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.delete_requested.emit(service_id)
                dialog.accept()
        
        save_button.clicked.connect(handle_save)
        delete_button.clicked.connect(handle_delete)
        
        # Ctrl+Enter shortcut for save
        ctrl_enter_shortcut = QShortcut(QKeySequence("Ctrl+Return"), dialog)
        ctrl_enter_shortcut.activated.connect(handle_save)
        
        # Delete shortcut
        delete_shortcut = QShortcut(QKeySequence("Ctrl+Shift+D"), dialog)
        delete_shortcut.activated.connect(handle_delete)
        
        dialog.exec()
    
    def show_success_dialog(self, message: str):
        """Show success message dialog."""
        QMessageBox.information(self, "Success", message)
    
    def show_error_dialog(self, message: str):
        """Show error message dialog."""
        QMessageBox.critical(self, "Error", message)

