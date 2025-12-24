"""Vehicles view GUI."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QGroupBox, QTextEdit, QScrollArea, QFormLayout,
    QTabWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QShortcut, QKeySequence, QKeyEvent
from views.base_view import BaseTabbedView
from typing import List, Dict, Any, Optional, Callable


class VehiclesTableWidget(QTableWidget):
    """Custom table widget with Enter key support."""
    
    def __init__(self, enter_callback: Callable[[], None]):
        """Initialize the table widget."""
        super().__init__()
        self.enter_callback = enter_callback
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # Check if we have a selected row
            current_row = self.currentRow()
            if current_row >= 0:
                self.enter_callback()
                event.accept()
                return
        super().keyPressEvent(event)


class VehiclesView(BaseTabbedView):
    """Vehicles view GUI."""
    
    # Signals
    vehicle_lookup_requested = Signal(str)  # vrm
    vehicle_api_lookup_requested = Signal(str)  # vrm
    vehicle_selected = Signal(int)  # vehicle_id
    vehicle_delete_requested = Signal(int)  # vehicle_id
    
    def __init__(self):
        """Initialize the vehicles view."""
        super().__init__(title="Vehicles", current_view="vehicles")
        self._all_vehicles_data: List[Dict] = []  # Store all vehicles for filtering
        self._create_widgets()
        self._setup_keyboard_navigation()
    
    def _create_widgets(self) -> None:
        """Create and layout UI widgets."""
        self.create_tabs()
        
        # Create list tab
        list_tab = self._create_list_tab()
        self.add_tab(list_tab, "Vehicles (Ctrl+1)", "Ctrl+1")
        
        # Create details tab
        details_tab = self._create_details_tab()
        self.add_tab(details_tab, "Details (Ctrl+2)", "Ctrl+2")
        
        # Create customer tab
        customer_tab = self._create_customer_tab()
        self.add_tab(customer_tab, "Customer (Ctrl+3)", "Ctrl+3")
        
        # Create sales history tab
        sales_history_tab = self._create_sales_history_tab()
        self.add_tab(sales_history_tab, "Sales History (Ctrl+4)", "Ctrl+4")
    
    def _create_list_tab(self) -> QWidget:
        """Create the vehicles list tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # VRM Search section
        lookup_group = QGroupBox("Vehicle Search")
        lookup_layout = QHBoxLayout(lookup_group)
        
        self.vrm_input = QLineEdit()
        self.vrm_input.setPlaceholderText("Enter VRM (e.g., LD, AB12)")
        self.vrm_input.setMaximumWidth(200)
        self.vrm_input.returnPressed.connect(self._on_search_clicked)
        lookup_layout.addWidget(QLabel("VRM:"))
        lookup_layout.addWidget(self.vrm_input)
        
        self.search_btn = QPushButton("Search (Enter)")
        self.search_btn.clicked.connect(self._on_search_clicked)
        lookup_layout.addWidget(self.search_btn)
        
        self.api_lookup_btn = QPushButton("API Lookup")
        self.api_lookup_btn.clicked.connect(self._on_api_lookup_clicked)
        lookup_layout.addWidget(self.api_lookup_btn)
        lookup_layout.addStretch()
        
        layout.addWidget(lookup_group)
        
        # Search box
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_label.setMinimumWidth(60)
        self.vehicles_search_box = QLineEdit()
        self.vehicles_search_box.setPlaceholderText("Search vehicles...")
        self.vehicles_search_box.textChanged.connect(self._filter_vehicles)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.vehicles_search_box)
        layout.addLayout(search_layout)
        
        # Vehicles table
        self.vehicles_table = VehiclesTableWidget(self._on_view_details)
        self.vehicles_table.setColumnCount(5)
        self.vehicles_table.setHorizontalHeaderLabels([
            "VRM", "Make", "Model", "Year", "Last Updated"
        ])
        self.vehicles_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.vehicles_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.vehicles_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.vehicles_table.setAlternatingRowColors(True)
        self.vehicles_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.vehicles_table.doubleClicked.connect(self._on_vehicle_double_clicked)
        
        layout.addWidget(self.vehicles_table, stretch=1)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.view_details_btn = QPushButton("View Details (Enter)")
        self.view_details_btn.clicked.connect(self._on_view_details)
        button_layout.addWidget(self.view_details_btn)
        
        self.delete_btn = QPushButton("Delete (Del)")
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        button_layout.addWidget(self.delete_btn)
        
        layout.addLayout(button_layout)
        
        return tab
    
    def _create_details_tab(self) -> QWidget:
        """Create the vehicle details tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Vehicle info header
        self.details_header = QLabel("Select a vehicle to view details")
        self.details_header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.details_header)
        
        # Scroll area for details
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        scroll_content = QWidget()
        details_layout = QVBoxLayout(scroll_content)
        details_layout.setSpacing(15)
        
        # Basic info group
        self.basic_group = QGroupBox("Vehicle Information")
        self.basic_layout = QFormLayout(self.basic_group)
        self.vrm_label = QLabel("-")
        self.make_label = QLabel("-")
        self.model_label = QLabel("-")
        self.year_label = QLabel("-")
        self.basic_layout.addRow("VRM:", self.vrm_label)
        self.basic_layout.addRow("Make:", self.make_label)
        self.basic_layout.addRow("Model:", self.model_label)
        self.basic_layout.addRow("Build Year:", self.year_label)
        details_layout.addWidget(self.basic_group)
        
        # Tyre info group
        self.tyre_group = QGroupBox("Tyre Information")
        self.tyre_layout = QVBoxLayout(self.tyre_group)
        self.tyre_table = QTableWidget()
        self.tyre_table.setColumnCount(8)
        self.tyre_table.setHorizontalHeaderLabels([
            "Position", "Size", "Load Index", "Speed Index", 
            "Pressure (Bar)", "Pressure (PSI)", "Rim Size", "Run Flat"
        ])
        self.tyre_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.tyre_table.setAlternatingRowColors(True)
        self.tyre_layout.addWidget(self.tyre_table, stretch=1)
        details_layout.addWidget(self.tyre_group)
        
        # Hub/Fixing info
        self.hub_group = QGroupBox("Hub & Fixing Information")
        self.hub_layout = QFormLayout(self.hub_group)
        self.center_bore_label = QLabel("-")
        self.pcd_label = QLabel("-")
        self.thread_type_label = QLabel("-")
        self.torque_label = QLabel("-")
        self.hub_layout.addRow("Center Bore:", self.center_bore_label)
        self.hub_layout.addRow("PCD:", self.pcd_label)
        self.hub_layout.addRow("Thread Type:", self.thread_type_label)
        self.hub_layout.addRow("Torque (Nm):", self.torque_label)
        details_layout.addWidget(self.hub_group)
        
        details_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Back button
        back_layout = QHBoxLayout()
        self.back_btn = QPushButton("Back to List (Ctrl+1)")
        self.back_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(0))
        back_layout.addWidget(self.back_btn)
        back_layout.addStretch()
        layout.addLayout(back_layout)
        
        return tab
    
    def _create_customer_tab(self) -> QWidget:
        """Create the customer tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Vehicle info header
        self.customer_header = QLabel("Select a vehicle to view customer information")
        self.customer_header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.customer_header)
        
        # Customer info group
        self.customer_group = QGroupBox("Customer Information")
        self.customer_layout = QFormLayout(self.customer_group)
        self.customer_name_label = QLabel("-")
        self.customer_phone_label = QLabel("-")
        self.customer_address_label = QLabel("-")
        self.customer_layout.addRow("Name:", self.customer_name_label)
        self.customer_layout.addRow("Phone:", self.customer_phone_label)
        self.customer_layout.addRow("Address:", self.customer_address_label)
        layout.addWidget(self.customer_group)
        
        layout.addStretch()
        
        # Back button
        back_layout = QHBoxLayout()
        back_btn = QPushButton("Back to List (Ctrl+1)")
        back_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(0))
        back_layout.addWidget(back_btn)
        back_layout.addStretch()
        layout.addLayout(back_layout)
        
        return tab
    
    def _create_sales_history_tab(self) -> QWidget:
        """Create the sales history tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Vehicle info header
        self.sales_history_header = QLabel("Select a vehicle to view sales history")
        self.sales_history_header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.sales_history_header)
        
        # Sales history table
        self.sales_history_table = QTableWidget()
        self.sales_history_table.setColumnCount(7)
        self.sales_history_table.setHorizontalHeaderLabels([
            "Document Number", "Date", "Type", "Status", "Subtotal", "VAT", "Total"
        ])
        self.sales_history_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.sales_history_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.sales_history_table.setAlternatingRowColors(True)
        layout.addWidget(self.sales_history_table, stretch=1)
        
        # Back button
        back_layout = QHBoxLayout()
        back_btn = QPushButton("Back to List (Ctrl+1)")
        back_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(0))
        back_layout.addWidget(back_btn)
        back_layout.addStretch()
        layout.addLayout(back_layout)
        
        return tab
    
    def _setup_keyboard_navigation(self) -> None:
        """Set up keyboard navigation."""
        delete_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)
        delete_shortcut.activated.connect(self._on_delete_clicked)
    
    def _on_search_clicked(self) -> None:
        """Handle search button click."""
        vrm = self.vrm_input.text().strip()
        if not vrm:
            QMessageBox.warning(self, "Warning", "Please enter a VRM to search")
            return
        
        self.vehicle_lookup_requested.emit(vrm.upper())
    
    def _on_api_lookup_clicked(self) -> None:
        """Handle API lookup button click."""
        vrm = self.vrm_input.text().strip().upper()
        if vrm:
            self.vehicle_api_lookup_requested.emit(vrm)
        else:
            QMessageBox.warning(self, "Warning", "Please enter a VRM for API lookup")
    
    def _on_vehicle_double_clicked(self) -> None:
        """Handle vehicle double click."""
        self._on_view_details()
    
    def _on_view_details(self) -> None:
        """Handle view details button click."""
        vehicle_id = self._get_selected_vehicle_id()
        if vehicle_id:
            self.vehicle_selected.emit(vehicle_id)
    
    def _on_delete_clicked(self) -> None:
        """Handle delete button click."""
        vehicle_id = self._get_selected_vehicle_id()
        if vehicle_id:
            reply = QMessageBox.question(
                self, "Confirm Delete",
                "Are you sure you want to delete this vehicle?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.vehicle_delete_requested.emit(vehicle_id)
    
    def _get_selected_vehicle_id(self) -> Optional[int]:
        """Get the selected vehicle ID."""
        selected = self.vehicles_table.selectedItems()
        if selected:
            row = selected[0].row()
            id_item = self.vehicles_table.item(row, 0)
            if id_item:
                return id_item.data(Qt.ItemDataRole.UserRole)
        return None
    
    def populate_vehicles(self, vehicles: List[Dict[str, Any]]) -> None:
        """Populate the vehicles table."""
        # Store all vehicles for filtering
        self._all_vehicles_data = vehicles
        # Apply current filter
        self._filter_vehicles()
    
    def _filter_vehicles(self) -> None:
        """Filter vehicles based on search text."""
        search_text = self.vehicles_search_box.text().strip().lower()
        
        if not search_text:
            filtered_vehicles = self._all_vehicles_data
        else:
            filtered_vehicles = [
                v for v in self._all_vehicles_data
                if search_text in str(v.get('id', '')).lower()
                or search_text in v.get('vrm', '').lower()
                or search_text in v.get('make', '').lower()
                or search_text in v.get('model', '').lower()
                or search_text in str(v.get('build_year', '')).lower()
            ]
        
        self.vehicles_table.setRowCount(len(filtered_vehicles))
        
        for row, vehicle in enumerate(filtered_vehicles):
            vrm_item = QTableWidgetItem(vehicle.get('vrm', ''))
            vrm_item.setData(Qt.ItemDataRole.UserRole, vehicle.get('id'))
            self.vehicles_table.setItem(row, 0, vrm_item)
            self.vehicles_table.setItem(
                row, 1, QTableWidgetItem(vehicle.get('make', ''))
            )
            self.vehicles_table.setItem(
                row, 2, QTableWidgetItem(vehicle.get('model', ''))
            )
            self.vehicles_table.setItem(
                row, 3, QTableWidgetItem(vehicle.get('build_year', ''))
            )
            updated = vehicle.get('updated_at', '')[:10] if vehicle.get('updated_at') else ''
            self.vehicles_table.setItem(row, 4, QTableWidgetItem(updated))
        
        # Select first row if there are results and set focus
        if filtered_vehicles:
            self.vehicles_table.selectRow(0)
            self.vehicles_table.setFocus()
    
    def focus_vrm_input(self) -> None:
        """Focus the VRM input field."""
        self.vrm_input.setFocus()
        self.vrm_input.selectAll()
    
    def show_vehicle_details(
        self, 
        vehicle: Dict[str, Any], 
        customer: Optional[Dict[str, Any]] = None,
        sales_history: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Display vehicle details in the details tab."""
        # Update header
        vrm = vehicle.get('vrm', 'Unknown')
        make = vehicle.get('make', '')
        model = vehicle.get('model', '')
        self.details_header.setText(f"{vrm} - {make} {model}")
        
        # Update basic info
        self.vrm_label.setText(vrm)
        self.make_label.setText(make or "-")
        self.model_label.setText(model or "-")
        self.year_label.setText(vehicle.get('build_year', '-') or "-")
        
        # Update tyre info
        tyre_data = vehicle.get('tyre_data', {})
        record_list = tyre_data.get('RecordList', []) if tyre_data else []
        
        # Calculate rows: each record has front and rear tyres
        total_rows = len(record_list) * 2
        self.tyre_table.setRowCount(total_rows)
        
        row = 0
        for idx, record in enumerate(record_list):
            # Front tyre
            front = record.get('Front', {})
            front_tyre = front.get('Tyre', {})
            front_rim = front.get('Rim', {})
            front_pressure = front_tyre.get('Pressure', {})
            
            self.tyre_table.setItem(row, 0, QTableWidgetItem(f"Front (Option {idx+1})"))
            self.tyre_table.setItem(row, 1, QTableWidgetItem(front_tyre.get('Size', '-')))
            self.tyre_table.setItem(row, 2, QTableWidgetItem(str(front_tyre.get('LoadIndex', '-'))))
            self.tyre_table.setItem(row, 3, QTableWidgetItem(str(front_tyre.get('SpeedIndex', '-'))))
            self.tyre_table.setItem(row, 4, QTableWidgetItem(str(front_pressure.get('Bar', '-'))))
            self.tyre_table.setItem(row, 5, QTableWidgetItem(str(front_pressure.get('Psi', '-'))))
            self.tyre_table.setItem(row, 6, QTableWidgetItem(front_rim.get('Size', '-')))
            self.tyre_table.setItem(row, 7, QTableWidgetItem(
                "Yes" if front_tyre.get('RunFlat') else "No"
            ))
            row += 1
            
            # Rear tyre
            rear = record.get('Rear', {})
            rear_tyre = rear.get('Tyre', {})
            rear_rim = rear.get('Rim', {})
            rear_pressure = rear_tyre.get('Pressure', {})
            
            self.tyre_table.setItem(row, 0, QTableWidgetItem(f"Rear (Option {idx+1})"))
            self.tyre_table.setItem(row, 1, QTableWidgetItem(rear_tyre.get('Size', '-')))
            self.tyre_table.setItem(row, 2, QTableWidgetItem(str(rear_tyre.get('LoadIndex', '-'))))
            self.tyre_table.setItem(row, 3, QTableWidgetItem(str(rear_tyre.get('SpeedIndex', '-'))))
            self.tyre_table.setItem(row, 4, QTableWidgetItem(str(rear_pressure.get('Bar', '-'))))
            self.tyre_table.setItem(row, 5, QTableWidgetItem(str(rear_pressure.get('Psi', '-'))))
            self.tyre_table.setItem(row, 6, QTableWidgetItem(rear_rim.get('Size', '-')))
            self.tyre_table.setItem(row, 7, QTableWidgetItem(
                "Yes" if rear_tyre.get('RunFlat') else "No"
            ))
            row += 1
        
        # Hub/Fixing info from first record
        if record_list:
            first_record = record_list[0]
            hub = first_record.get('Hub', {})
            fixing = first_record.get('Fixing', {})
            
            self.center_bore_label.setText(str(hub.get('CenterBore', '-')))
            self.pcd_label.setText(str(hub.get('PCD', '-')))
            self.thread_type_label.setText(str(fixing.get('ThreadType', '-')))
            self.torque_label.setText(str(fixing.get('Torque', '-')))
        else:
            self.center_bore_label.setText("-")
            self.pcd_label.setText("-")
            self.thread_type_label.setText("-")
            self.torque_label.setText("-")
        
        # Update customer tab header and info
        vrm = vehicle.get('vrm', 'Unknown')
        make = vehicle.get('make', '')
        model = vehicle.get('model', '')
        self.customer_header.setText(f"{vrm} - {make} {model} - Customer")
        
        if customer:
            self.customer_name_label.setText(customer.get('name', '-'))
            self.customer_phone_label.setText(customer.get('phone', '-') or "-")
            # Format address
            address_parts = []
            if customer.get('house_name_no'):
                address_parts.append(customer.get('house_name_no'))
            if customer.get('street_address'):
                address_parts.append(customer.get('street_address'))
            if customer.get('city'):
                address_parts.append(customer.get('city'))
            if customer.get('county'):
                address_parts.append(customer.get('county'))
            if customer.get('postcode'):
                address_parts.append(customer.get('postcode'))
            self.customer_address_label.setText(", ".join(address_parts) if address_parts else "-")
        else:
            self.customer_name_label.setText("-")
            self.customer_phone_label.setText("-")
            self.customer_address_label.setText("No customer associated with this vehicle")
        
        # Update sales history tab header and table
        self.sales_history_header.setText(f"{vrm} - {make} {model} - Sales History")
        
        if sales_history:
            self.sales_history_table.setRowCount(len(sales_history))
            for row, sale in enumerate(sales_history):
                self.sales_history_table.setItem(
                    row, 0, QTableWidgetItem(sale.get('document_number', '-'))
                )
                date_str = sale.get('document_date', '')[:10] if sale.get('document_date') else '-'
                self.sales_history_table.setItem(row, 1, QTableWidgetItem(date_str))
                doc_type = sale.get('document_type', '-').capitalize()
                self.sales_history_table.setItem(row, 2, QTableWidgetItem(doc_type))
                status = sale.get('status', '-').capitalize()
                self.sales_history_table.setItem(row, 3, QTableWidgetItem(status))
                self.sales_history_table.setItem(
                    row, 4, QTableWidgetItem(f"£{sale.get('subtotal', 0.0):.2f}")
                )
                self.sales_history_table.setItem(
                    row, 5, QTableWidgetItem(f"£{sale.get('vat_amount', 0.0):.2f}")
                )
                self.sales_history_table.setItem(
                    row, 6, QTableWidgetItem(f"£{sale.get('total', 0.0):.2f}")
                )
        else:
            self.sales_history_table.setRowCount(0)
        
        # Switch to details tab
        self.tab_widget.setCurrentIndex(1)
    
    def clear_vrm_input(self) -> None:
        """Clear the VRM input field."""
        self.vrm_input.clear()
    
    def show_message(self, title: str, message: str, is_error: bool = False) -> None:
        """Show a message dialog."""
        if is_error:
            QMessageBox.warning(self, title, message)
        else:
            QMessageBox.information(self, title, message)
    
    def confirm_api_lookup(self, vrm: str, message: Optional[str] = None) -> bool:
        """
        Ask user to confirm API lookup.
        
        Args:
            vrm: The VRM being looked up
            message: Optional custom message to display
        
        Returns:
            True if user confirms, False otherwise
        """
        if message is None:
            message = (
                f"Perform API lookup for vehicle '{vrm}'?\n\n"
                "(This will use API credits)"
            )
        
        reply = QMessageBox.question(
            self,
            "Confirm API Lookup",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes

