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
from views.widgets.table_config import TableConfig
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
        self._all_services_data: List[Dict] = []  # Store all services for filtering
        self.selected_service_id: Optional[int] = None
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
        
        # Create tabs widget
        self.tab_widget = self.create_tabs()
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        # Tab 1: Services
        self._create_services_tab()
        
        # Tab 2: Details
        self._create_details_tab()
        
        # Tab 3: Sales History
        self._create_sales_history_tab()
        
        # Set Services tab as default
        self.tab_widget.setCurrentIndex(0)
    
    def _create_services_tab(self):
        """Create the services list tab."""
        services_widget = QWidget()
        services_layout = QVBoxLayout(services_widget)
        services_layout.setSpacing(20)
        services_layout.setContentsMargins(10, 10, 10, 10)
        
        # Search box
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_label.setMinimumWidth(60)
        self.services_search_box = QLineEdit()
        self.services_search_box.setPlaceholderText("Search services...")
        self.services_search_box.textChanged.connect(self._filter_services)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.services_search_box)
        services_layout.addLayout(search_layout)
        
        # Services table
        self.services_table = ServicesTableWidget(self._switch_to_details_tab)
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
        
        # Enable keyboard navigation
        self.services_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Selection changed - update selected service
        self.services_table.itemSelectionChanged.connect(self._on_service_selection_changed)
        
        # Double-click to edit
        self.services_table.itemDoubleClicked.connect(self._on_table_double_click)
        
        services_layout.addWidget(self.services_table, stretch=1)
        self.add_tab(services_widget, "Services (Ctrl+1)", "Ctrl+1")
    
    def _create_details_tab(self):
        """Create the details tab."""
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setSpacing(20)
        details_layout.setContentsMargins(10, 10, 10, 10)
        
        # Placeholder label
        self.details_label = QLabel(
            "Select a service from the Services tab to view details."
        )
        self.details_label.setStyleSheet("font-size: 12px; color: gray;")
        details_layout.addWidget(self.details_label)
        
        # Details form (hidden until service selected)
        self.details_form = QWidget()
        details_form_layout = QVBoxLayout(self.details_form)
        details_form_layout.setSpacing(15)
        details_form_layout.setContentsMargins(0, 0, 0, 0)
        
        # Store form widgets for later use
        self.details_id_label = QLabel("")
        self.details_name_entry = QLineEdit()
        self.details_code_entry = QLineEdit()
        self.details_group_entry = QLineEdit()
        self.details_desc_entry = QTextEdit()
        self.details_desc_entry.setMaximumHeight(100)
        self.details_est_cost_entry = QDoubleSpinBox()
        self.details_est_cost_entry.setMaximum(999999.99)
        self.details_est_cost_entry.setDecimals(2)
        self.details_est_cost_entry.setPrefix("£")
        self.details_vat_entry = QLineEdit()
        self.details_vat_entry.setMaxLength(10)
        self.details_income_combo = QComboBox()
        self.details_retail_entry = QDoubleSpinBox()
        self.details_retail_entry.setMaximum(999999.99)
        self.details_retail_entry.setDecimals(2)
        self.details_retail_entry.setPrefix("£")
        self.details_trade_entry = QDoubleSpinBox()
        self.details_trade_entry.setMaximum(999999.99)
        self.details_trade_entry.setDecimals(2)
        self.details_trade_entry.setPrefix("£")
        
        # Add form rows
        self._create_detail_row(details_form_layout, "ID:", self.details_id_label, read_only=True)
        self._create_detail_row(details_form_layout, "Name:", self.details_name_entry)
        self._create_detail_row(details_form_layout, "Code:", self.details_code_entry)
        self._create_detail_row(details_form_layout, "Group:", self.details_group_entry)
        
        # Description row
        desc_row = QHBoxLayout()
        desc_label = QLabel("Description:")
        desc_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        desc_label.setMinimumWidth(150)
        desc_row.addWidget(desc_label)
        desc_row.addWidget(self.details_desc_entry, stretch=1)
        details_form_layout.addLayout(desc_row)
        
        self._create_detail_row(details_form_layout, "Estimated Cost:", self.details_est_cost_entry)
        self._create_detail_row(details_form_layout, "VAT Code:", self.details_vat_entry)
        
        # Income Account row
        income_row = QHBoxLayout()
        income_label = QLabel("Income Account:")
        income_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        income_label.setMinimumWidth(150)
        income_row.addWidget(income_label)
        income_row.addWidget(self.details_income_combo, stretch=1)
        details_form_layout.addLayout(income_row)
        
        self._create_detail_row(details_form_layout, "Retail Price:", self.details_retail_entry)
        self._create_detail_row(details_form_layout, "Trade Price:", self.details_trade_entry)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.details_save_button = QPushButton("Save Changes (Ctrl+Enter)")
        self.details_save_button.setMinimumWidth(200)
        self.details_save_button.setMinimumHeight(30)
        self.details_save_button.clicked.connect(self._handle_save_details)
        buttons_layout.addWidget(self.details_save_button)
        
        self.details_delete_button = QPushButton("Delete Service (Ctrl+Shift+D)")
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
    
    def _create_detail_row(self, layout: QVBoxLayout, label_text: str, widget: QWidget, read_only: bool = False):
        """Create a detail row with label and widget."""
        row_layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setStyleSheet("font-weight: bold; font-size: 12px;")
        label.setMinimumWidth(150)
        row_layout.addWidget(label)
        row_layout.addWidget(widget, stretch=1)
        layout.addLayout(row_layout)
    
    def _create_sales_history_tab(self):
        """Create the sales history tab."""
        sales_widget = QWidget()
        sales_layout = QVBoxLayout(sales_widget)
        sales_layout.setSpacing(20)
        sales_layout.setContentsMargins(10, 10, 10, 10)
        
        # Placeholder label
        self.sales_history_label = QLabel(
            "Select a service from the Services tab to view sales history."
        )
        self.sales_history_label.setStyleSheet("font-size: 12px; color: gray;")
        sales_layout.addWidget(self.sales_history_label)
        
        # Sales history table
        self.sales_history_table = QTableWidget()
        self.sales_history_table.setColumnCount(7)
        self.sales_history_table.setHorizontalHeaderLabels([
            "Document Number", "Date", "Customer", "Quantity", "Unit Price", "VAT", "Total"
        ])
        self.sales_history_table.horizontalHeader().setStretchLastSection(True)
        self.sales_history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sales_history_table.setAlternatingRowColors(True)
        self.sales_history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.sales_history_table.hide()
        
        sales_layout.addWidget(self.sales_history_table, stretch=1)
        self.add_tab(sales_widget, "Sales History (Ctrl+3)", "Ctrl+3")
    
    def _setup_keyboard_navigation(self):
        """Set up keyboard navigation."""
        # Tab order: Table -> Add Service -> Navigation panel
        self.setTabOrder(self.services_table, self.add_service_button)
        self.setTabOrder(self.add_service_button, self.nav_panel.logout_button)
        
        # Arrow keys work automatically in QTableWidget
        self.services_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Shortcuts for details tab
        save_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        save_shortcut.activated.connect(self._handle_save_details)
        
        delete_shortcut = QShortcut(QKeySequence("Ctrl+Shift+D"), self)
        delete_shortcut.activated.connect(self._handle_delete_details)
    
    def showEvent(self, event: QEvent):
        """Handle show event - set focus to table if it has data."""
        super().showEvent(event)
        # Set focus to table if it has rows and we're on the services tab
        if self.tab_widget.currentIndex() == 0 and self.services_table.rowCount() > 0:
            self.services_table.setFocus()
            # Ensure first row is selected if nothing is selected
            if not self.services_table.selectedItems():
                self.services_table.selectRow(0)
                self._on_service_selection_changed()
    
    def _handle_add_service(self):
        """Handle Add Service button click."""
        self.add_service()
    
    def _on_table_double_click(self, item: QTableWidgetItem):
        """Handle double-click on table item."""
        self._open_selected_service()
    
    def _open_selected_service(self):
        """Open details for the currently selected service."""
        self._switch_to_details_tab()
    
    def _switch_to_details_tab(self):
        """Switch to the details tab."""
        if self.selected_service_id is not None:
            self.tab_widget.setCurrentIndex(1)
    
    def _on_service_selection_changed(self):
        """Handle service selection change."""
        selected_items = self.services_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            service_id = int(self.services_table.item(row, 0).text())
            self.selected_service_id = service_id
            if self.tab_widget.currentIndex() == 1:
                # Request full service details from controller
                self.get_service_details_requested.emit(service_id)
    
    def _on_tab_changed(self, index: int):
        """Handle tab change."""
        if index == 1:  # Details tab
            if self.selected_service_id:
                self.get_service_details_requested.emit(self.selected_service_id)
        elif index == 2:  # Sales History tab
            if self.selected_service_id:
                # TODO: Request sales history from controller
                pass
    
    def load_services(self, services: List[Dict[str, any]]):
        """Load services into the table."""
        # Store all services for filtering
        self._all_services_data = services
        # Apply current filter
        self._filter_services()
    
    def _filter_services(self):
        """Filter services based on search text."""
        search_text = self.services_search_box.text().strip().lower()
        
        if not search_text:
            filtered_services = self._all_services_data
        else:
            filtered_services = [
                s for s in self._all_services_data
                if search_text in str(s.get('id', '')).lower()
                or search_text in s.get('code', '').lower()
                or search_text in s.get('name', '').lower()
                or search_text in (s.get('group_name', '') or '').lower()
                or search_text in (s.get('description', '') or '').lower()
            ]
        
        self.services_table.setRowCount(len(filtered_services))
        
        for row, service in enumerate(filtered_services):
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
        
        # Distribute columns proportionally based on content
        TableConfig.distribute_columns_proportionally(self.services_table)
    
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
        default_income_index = 0  # Default to empty option
        # Populate with Income type accounts
        if self.nominal_account_model and self._current_user_id:
            accounts = self.nominal_account_model.get_all(self._current_user_id)
            for account in accounts:
                if account.get('account_type') == 'Income':
                    display_text = f"{account.get('account_code')} - {account.get('account_name')}"
                    account_id = account.get('id')
                    account_code = account.get('account_code')
                    income_combo.addItem(display_text, account_id)
                    # Default to account code 4100 if it exists
                    if account_code == 4100:
                        default_income_index = income_combo.count() - 1
        income_combo.setCurrentIndex(default_income_index)
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
        """Show service details in the details tab."""
        self._update_details_tab(service)
    
    def _update_details_tab(self, service: Dict[str, any]):
        """Update the details tab with selected service data."""
        if not service:
            self.details_label.show()
            self.details_form.hide()
            return
        
        self.details_label.hide()
        self.details_form.show()
        
        # Populate form fields
        self.details_id_label.setText(str(service.get('id', '')))
        self.details_name_entry.setText(service.get('name', ''))
        self.details_code_entry.setText(service.get('code', ''))
        self.details_group_entry.setText(service.get('group_name', '') or '')
        self.details_desc_entry.setPlainText(service.get('description', '') or '')
        self.details_est_cost_entry.setValue(service.get('estimated_cost', 0.0) or 0.0)
        self.details_vat_entry.setText(service.get('vat_code', 'S'))
        self.details_retail_entry.setValue(service.get('retail_price', 0.0) or 0.0)
        self.details_trade_entry.setValue(service.get('trade_price', 0.0) or 0.0)
        
        # Populate income account combo
        self.details_income_combo.clear()
        self.details_income_combo.addItem("")  # Empty option
        current_income_account_id = service.get('income_account_id')
        current_index = 0
        if self.nominal_account_model and self._current_user_id:
            accounts = self.nominal_account_model.get_all(self._current_user_id)
            for idx, account in enumerate(accounts):
                if account.get('account_type') == 'Income':
                    display_text = f"{account.get('account_code')} - {account.get('account_name')}"
                    account_id = account.get('id')
                    self.details_income_combo.addItem(display_text, account_id)
                    if account_id == current_income_account_id:
                        current_index = idx + 1  # +1 for empty option
        self.details_income_combo.setCurrentIndex(current_index)
    
    def _handle_save_details(self):
        """Handle save details button click."""
        if self.selected_service_id is None:
            return
        
        if self.tab_widget.currentIndex() != 1:
            return
        
        name = self.details_name_entry.text().strip()
        code = self.details_code_entry.text().strip()
        if not name or not code:
            self.show_error_dialog("Name and code are required")
            return
        
        self.update_requested.emit(
            self.selected_service_id,
            name,
            code,
            self.details_group_entry.text().strip(),
            self.details_desc_entry.toPlainText().strip(),
            self.details_est_cost_entry.value(),
            self.details_vat_entry.text().strip() or 'S',
            self.details_income_combo.currentData() if self.details_income_combo.currentData() else 0,
            self.details_retail_entry.value(),
            self.details_trade_entry.value()
        )
    
    def _handle_delete_details(self):
        """Handle delete button click from details tab."""
        if self.selected_service_id is None:
            return
        
        if self.tab_widget.currentIndex() != 1:
            return
        
        service_name = self.details_name_entry.text()
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete service '{service_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_requested.emit(self.selected_service_id)
            self.selected_service_id = None
            self.tab_widget.setCurrentIndex(0)
    
    def show_service_details_dialog(self, service: Dict[str, any]):
        """Show service details dialog with full service data (legacy method for backward compatibility)."""
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

