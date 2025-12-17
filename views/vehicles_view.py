"""Vehicles view GUI."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QGroupBox, QTextEdit, QScrollArea, QFormLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QShortcut, QKeySequence
from views.base_view import BaseTabbedView
from typing import List, Dict, Any, Optional


class VehiclesView(BaseTabbedView):
    """Vehicles view GUI."""
    
    # Signals
    vehicle_lookup_requested = Signal(str)  # vrm
    vehicle_selected = Signal(int)  # vehicle_id
    vehicle_delete_requested = Signal(int)  # vehicle_id
    
    def __init__(self):
        """Initialize the vehicles view."""
        super().__init__(title="Vehicles", current_view="vehicles")
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
    
    def _create_list_tab(self) -> QWidget:
        """Create the vehicles list tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # VRM Lookup section
        lookup_group = QGroupBox("Vehicle Lookup")
        lookup_layout = QHBoxLayout(lookup_group)
        
        self.vrm_input = QLineEdit()
        self.vrm_input.setPlaceholderText("Enter VRM (e.g., AB12 CDE)")
        self.vrm_input.setMaximumWidth(200)
        self.vrm_input.returnPressed.connect(self._on_lookup_clicked)
        lookup_layout.addWidget(QLabel("VRM:"))
        lookup_layout.addWidget(self.vrm_input)
        
        self.lookup_btn = QPushButton("Lookup (Enter)")
        self.lookup_btn.clicked.connect(self._on_lookup_clicked)
        lookup_layout.addWidget(self.lookup_btn)
        lookup_layout.addStretch()
        
        layout.addWidget(lookup_group)
        
        # Vehicles table
        self.vehicles_table = QTableWidget()
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
        self.vehicles_table.doubleClicked.connect(self._on_vehicle_double_clicked)
        
        layout.addWidget(self.vehicles_table)
        
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
        self.details_layout = QVBoxLayout(scroll_content)
        self.details_layout.setSpacing(15)
        
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
        self.details_layout.addWidget(self.basic_group)
        
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
        self.tyre_layout.addWidget(self.tyre_table)
        self.details_layout.addWidget(self.tyre_group)
        
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
        self.details_layout.addWidget(self.hub_group)
        
        self.details_layout.addStretch()
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
    
    def _setup_keyboard_navigation(self) -> None:
        """Set up keyboard navigation."""
        delete_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)
        delete_shortcut.activated.connect(self._on_delete_clicked)
        
        # Enter to view details when table focused
        enter_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Return), self.vehicles_table)
        enter_shortcut.activated.connect(self._on_view_details)
    
    def _on_lookup_clicked(self) -> None:
        """Handle lookup button click."""
        vrm = self.vrm_input.text().strip().upper()
        if vrm:
            self.vehicle_lookup_requested.emit(vrm)
        else:
            QMessageBox.warning(self, "Warning", "Please enter a VRM")
    
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
        self.vehicles_table.setRowCount(len(vehicles))
        
        for row, vehicle in enumerate(vehicles):
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
    
    def show_vehicle_details(self, vehicle: Dict[str, Any]) -> None:
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
    
    def confirm_api_lookup(self, vrm: str) -> bool:
        """Ask user to confirm API lookup for a VRM not in database."""
        reply = QMessageBox.question(
            self,
            "Vehicle Not Found",
            f"Vehicle '{vrm}' is not in your database.\n\n"
            "Would you like to perform an API lookup?\n"
            "(This will use API credits)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
