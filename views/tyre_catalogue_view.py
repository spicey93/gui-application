"""Tyre catalogue view for searching and filtering tyres."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QComboBox, QCheckBox, QLabel, QPushButton, QScrollArea,
    QWidget, QHeaderView, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QShortcut, QKeySequence
from typing import TYPE_CHECKING, Optional, Dict
from utils.styles import apply_theme

if TYPE_CHECKING:
    from models.tyre import Tyre


class TyreCatalogueView(QDialog):
    """Dialog for searching and viewing tyre catalogue."""
    
    def __init__(self, tyre_model: "Tyre", parent=None):
        """Initialize the tyre catalogue view."""
        super().__init__(parent)
        self.tyre_model = tyre_model
        self.setWindowTitle("Tyre Catalogue")
        self.setModal(True)
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        apply_theme(self)
        
        # Add Escape key shortcut for close
        esc_shortcut = QShortcut(QKeySequence("Escape"), self)
        esc_shortcut.activated.connect(self.reject)
        
        self._create_widgets()
        self._load_dropdown_values()
        # Initialize with empty state - no results until filters are applied
        self.results_table.setRowCount(0)
        self.results_count_label.setText("Results: Please apply filters to search")
        self.message_label.setText("Please apply at least one filter to search the catalogue. Results will be shown when filters return less than 1000 results.")
    
    def _create_widgets(self):
        """Create and layout UI widgets."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Tyre Catalogue")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Main content area with filters and table
        main_layout = QHBoxLayout()
        main_layout.setSpacing(15)
        
        # Left side: Filters
        filters_widget = QWidget()
        filters_widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                border-radius: 5px;
            }
        """)
        filters_layout = QVBoxLayout(filters_widget)
        filters_layout.setSpacing(10)
        filters_layout.setContentsMargins(15, 15, 15, 15)
        
        filters_label = QLabel("Search Filters")
        filters_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #000;")
        filters_layout.addWidget(filters_label)
        
        # Scroll area for filters
        filters_scroll = QScrollArea()
        filters_scroll.setWidgetResizable(True)
        filters_scroll.setMaximumWidth(400)
        filters_scroll.setMinimumWidth(350)
        filters_scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)
        
        filters_content = QWidget()
        filters_content.setStyleSheet("background-color: transparent;")
        filters_content_layout = QVBoxLayout(filters_content)
        filters_content_layout.setSpacing(10)
        filters_content_layout.setContentsMargins(10, 10, 10, 10)
        
        # Pattern (text entry)
        pattern_layout = QHBoxLayout()
        pattern_label = QLabel("Pattern:")
        pattern_label.setMinimumWidth(120)
        pattern_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #000;")
        pattern_layout.addWidget(pattern_label)
        self.pattern_entry = QLineEdit()
        self.pattern_entry.setPlaceholderText("Enter pattern...")
        self.pattern_entry.setStyleSheet("background-color: white; color: black;")
        self.pattern_entry.returnPressed.connect(self._apply_filters)
        pattern_layout.addWidget(self.pattern_entry)
        filters_content_layout.addLayout(pattern_layout)
        
        # Brand (dropdown)
        brand_layout = QHBoxLayout()
        brand_label = QLabel("Brand:")
        brand_label.setMinimumWidth(120)
        brand_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #000;")
        brand_layout.addWidget(brand_label)
        self.brand_combo = QComboBox()
        self.brand_combo.setEditable(False)
        self.brand_combo.setStyleSheet("background-color: white; color: black;")
        self.brand_combo.addItem("")  # Empty option
        brand_layout.addWidget(self.brand_combo)
        filters_content_layout.addLayout(brand_layout)
        
        # OE Fitment (dropdown)
        oe_layout = QHBoxLayout()
        oe_label = QLabel("OE Fitment:")
        oe_label.setMinimumWidth(120)
        oe_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #000;")
        oe_layout.addWidget(oe_label)
        self.oe_combo = QComboBox()
        self.oe_combo.setEditable(False)
        self.oe_combo.setStyleSheet("background-color: white; color: black;")
        self.oe_combo.addItem("")  # Empty option
        oe_layout.addWidget(self.oe_combo)
        filters_content_layout.addLayout(oe_layout)
        
        # Run Flat (checkbox)
        runflat_layout = QHBoxLayout()
        runflat_label = QLabel("Run Flat:")
        runflat_label.setMinimumWidth(120)
        runflat_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #000;")
        runflat_layout.addWidget(runflat_label)
        self.runflat_checkbox = QCheckBox()
        runflat_layout.addWidget(self.runflat_checkbox)
        runflat_layout.addStretch()
        filters_content_layout.addLayout(runflat_layout)
        
        # Width (text entry)
        width_layout = QHBoxLayout()
        width_label = QLabel("Width:")
        width_label.setMinimumWidth(120)
        width_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #000;")
        width_layout.addWidget(width_label)
        self.width_entry = QLineEdit()
        self.width_entry.setPlaceholderText("Enter width...")
        self.width_entry.setStyleSheet("background-color: white; color: black;")
        self.width_entry.returnPressed.connect(self._apply_filters)
        width_layout.addWidget(self.width_entry)
        filters_content_layout.addLayout(width_layout)
        
        # Profile (text entry)
        profile_layout = QHBoxLayout()
        profile_label = QLabel("Profile:")
        profile_label.setMinimumWidth(120)
        profile_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #000;")
        profile_layout.addWidget(profile_label)
        self.profile_entry = QLineEdit()
        self.profile_entry.setPlaceholderText("Enter profile...")
        self.profile_entry.setStyleSheet("background-color: white; color: black;")
        self.profile_entry.returnPressed.connect(self._apply_filters)
        profile_layout.addWidget(self.profile_entry)
        filters_content_layout.addLayout(profile_layout)
        
        # Diameter (text entry)
        diameter_layout = QHBoxLayout()
        diameter_label = QLabel("Diameter:")
        diameter_label.setMinimumWidth(120)
        diameter_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #000;")
        diameter_layout.addWidget(diameter_label)
        self.diameter_entry = QLineEdit()
        self.diameter_entry.setPlaceholderText("Enter diameter...")
        self.diameter_entry.setStyleSheet("background-color: white; color: black;")
        self.diameter_entry.returnPressed.connect(self._apply_filters)
        diameter_layout.addWidget(self.diameter_entry)
        filters_content_layout.addLayout(diameter_layout)
        
        # Vehicle Type (dropdown)
        vehicle_type_layout = QHBoxLayout()
        vehicle_type_label = QLabel("Vehicle Type:")
        vehicle_type_label.setMinimumWidth(120)
        vehicle_type_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #000;")
        vehicle_type_layout.addWidget(vehicle_type_label)
        self.vehicle_type_combo = QComboBox()
        self.vehicle_type_combo.setEditable(False)
        self.vehicle_type_combo.setStyleSheet("background-color: white; color: black;")
        self.vehicle_type_combo.addItem("")  # Empty option
        vehicle_type_layout.addWidget(self.vehicle_type_combo)
        filters_content_layout.addLayout(vehicle_type_layout)
        
        # Product Type (dropdown)
        product_type_layout = QHBoxLayout()
        product_type_label = QLabel("Product Type:")
        product_type_label.setMinimumWidth(120)
        product_type_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #000;")
        product_type_layout.addWidget(product_type_label)
        self.product_type_combo = QComboBox()
        self.product_type_combo.setEditable(False)
        self.product_type_combo.setStyleSheet("background-color: white; color: black;")
        self.product_type_combo.addItem("")  # Empty option
        product_type_layout.addWidget(self.product_type_combo)
        filters_content_layout.addLayout(product_type_layout)
        
        # EAN (text entry)
        ean_layout = QHBoxLayout()
        ean_label = QLabel("EAN:")
        ean_label.setMinimumWidth(120)
        ean_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #000;")
        ean_layout.addWidget(ean_label)
        self.ean_entry = QLineEdit()
        self.ean_entry.setPlaceholderText("Enter EAN...")
        self.ean_entry.setStyleSheet("background-color: white; color: black;")
        self.ean_entry.returnPressed.connect(self._apply_filters)
        ean_layout.addWidget(self.ean_entry)
        filters_content_layout.addLayout(ean_layout)
        
        # Speed Rating (dropdown)
        speed_rating_layout = QHBoxLayout()
        speed_rating_label = QLabel("Speed Rating:")
        speed_rating_label.setMinimumWidth(120)
        speed_rating_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #000;")
        speed_rating_layout.addWidget(speed_rating_label)
        self.speed_rating_combo = QComboBox()
        self.speed_rating_combo.setEditable(False)
        self.speed_rating_combo.setStyleSheet("background-color: white; color: black;")
        self.speed_rating_combo.addItem("")  # Empty option
        speed_rating_layout.addWidget(self.speed_rating_combo)
        filters_content_layout.addLayout(speed_rating_layout)
        
        # Load Rating (dropdown)
        load_rating_layout = QHBoxLayout()
        load_rating_label = QLabel("Load Rating:")
        load_rating_label.setMinimumWidth(120)
        load_rating_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #000;")
        load_rating_layout.addWidget(load_rating_label)
        self.load_rating_combo = QComboBox()
        self.load_rating_combo.setEditable(False)
        self.load_rating_combo.setStyleSheet("background-color: white; color: black;")
        self.load_rating_combo.addItem("")  # Empty option
        load_rating_layout.addWidget(self.load_rating_combo)
        filters_content_layout.addLayout(load_rating_layout)
        
        # Rolling Resistance (dropdown)
        rolling_resistance_layout = QHBoxLayout()
        rolling_resistance_label = QLabel("Rolling Resistance:")
        rolling_resistance_label.setMinimumWidth(120)
        rolling_resistance_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #000;")
        rolling_resistance_layout.addWidget(rolling_resistance_label)
        self.rolling_resistance_combo = QComboBox()
        self.rolling_resistance_combo.setEditable(False)
        self.rolling_resistance_combo.setStyleSheet("background-color: white; color: black;")
        self.rolling_resistance_combo.addItem("")  # Empty option
        rolling_resistance_layout.addWidget(self.rolling_resistance_combo)
        filters_content_layout.addLayout(rolling_resistance_layout)
        
        # Wet Grip (dropdown)
        wet_grip_layout = QHBoxLayout()
        wet_grip_label = QLabel("Wet Grip:")
        wet_grip_label.setMinimumWidth(120)
        wet_grip_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #000;")
        wet_grip_layout.addWidget(wet_grip_label)
        self.wet_grip_combo = QComboBox()
        self.wet_grip_combo.setEditable(False)
        self.wet_grip_combo.setStyleSheet("background-color: white; color: black;")
        self.wet_grip_combo.addItem("")  # Empty option
        wet_grip_layout.addWidget(self.wet_grip_combo)
        filters_content_layout.addLayout(wet_grip_layout)
        
        filters_content_layout.addStretch()
        
        filters_scroll.setWidget(filters_content)
        filters_layout.addWidget(filters_scroll)
        
        # Search button
        search_button = QPushButton("Search")
        search_button.setMinimumHeight(30)
        search_button.setDefault(True)
        search_button.clicked.connect(self._apply_filters)
        filters_layout.addWidget(search_button)
        
        # Clear button
        clear_button = QPushButton("Clear Filters")
        clear_button.setMinimumHeight(30)
        clear_button.clicked.connect(self._clear_filters)
        filters_layout.addWidget(clear_button)
        
        main_layout.addWidget(filters_widget)
        
        # Right side: Results table
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        results_layout.setSpacing(10)
        results_layout.setContentsMargins(0, 0, 0, 0)
        
        # Results count label
        self.results_count_label = QLabel("Results: 0")
        self.results_count_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        results_layout.addWidget(self.results_count_label)
        
        # Message label for filter requirements
        self.message_label = QLabel("")
        self.message_label.setStyleSheet("font-size: 12px; color: #666; font-style: italic;")
        self.message_label.setWordWrap(True)
        results_layout.addWidget(self.message_label)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels([
            "Description", "Brand", "Pattern", "Size", "Speed", "Load", "Run Flat", "EAN"
        ])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.setSortingEnabled(True)
        
        # Connect double-click to show details
        self.results_table.itemDoubleClicked.connect(self._on_tyre_double_clicked)
        
        # Set column resize modes - Description stretches, others resize to contents
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        
        results_layout.addWidget(self.results_table, stretch=1)
        
        main_layout.addWidget(results_widget, stretch=2)
        
        layout.addLayout(main_layout)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_button = QPushButton("Close (Esc)")
        close_button.setMinimumWidth(120)
        close_button.setMinimumHeight(30)
        close_button.clicked.connect(self.reject)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        # Store current results for double-click access
        self._current_results = []
    
    def _load_dropdown_values(self):
        """Load unique values for dropdowns from database."""
        # Brand
        brands = self.tyre_model.get_unique_brands()
        for brand in brands:
            self.brand_combo.addItem(brand)
        
        # OE Fitment
        oe_fitments = self.tyre_model.get_unique_oe_fitments()
        for oe in oe_fitments:
            self.oe_combo.addItem(oe)
        
        # Vehicle Type
        vehicle_types = self.tyre_model.get_unique_vehicle_types()
        for vt in vehicle_types:
            self.vehicle_type_combo.addItem(vt)
        
        # Product Type
        product_types = self.tyre_model.get_unique_product_types()
        for pt in product_types:
            self.product_type_combo.addItem(pt)
        
        # Speed Rating
        speed_ratings = self.tyre_model.get_unique_speed_ratings()
        for sr in speed_ratings:
            self.speed_rating_combo.addItem(sr)
        
        # Load Index
        load_indices = self.tyre_model.get_unique_load_indices()
        for li in load_indices:
            self.load_rating_combo.addItem(li)
        
        # Rolling Resistance
        rolling_resistances = self.tyre_model.get_unique_rolling_resistances()
        for rr in rolling_resistances:
            self.rolling_resistance_combo.addItem(rr)
        
        # Wet Grip
        wet_grips = self.tyre_model.get_unique_wet_grips()
        for wg in wet_grips:
            self.wet_grip_combo.addItem(wg)
    
    def _clear_filters(self):
        """Clear all filter fields."""
        self.pattern_entry.clear()
        self.brand_combo.setCurrentIndex(0)
        self.oe_combo.setCurrentIndex(0)
        self.runflat_checkbox.setChecked(False)
        self.width_entry.clear()
        self.profile_entry.clear()
        self.diameter_entry.clear()
        self.vehicle_type_combo.setCurrentIndex(0)
        self.product_type_combo.setCurrentIndex(0)
        self.ean_entry.clear()
        self.speed_rating_combo.setCurrentIndex(0)
        self.load_rating_combo.setCurrentIndex(0)
        self.rolling_resistance_combo.setCurrentIndex(0)
        self.wet_grip_combo.setCurrentIndex(0)
        # Clear results but don't search automatically
        self.results_table.setRowCount(0)
        self._current_results = []
        self.results_count_label.setText("Results: Please apply filters to search")
        self.message_label.setText("Please apply at least one filter to search the catalogue. Results will be shown when filters return less than 1000 results.")
    
    def _has_active_filters(self) -> bool:
        """Check if any filters are currently active."""
        return (
            bool(self.pattern_entry.text().strip()) or
            bool(self.brand_combo.currentText().strip()) or
            bool(self.oe_combo.currentText().strip()) or
            self.runflat_checkbox.isChecked() or
            bool(self.width_entry.text().strip()) or
            bool(self.profile_entry.text().strip()) or
            bool(self.diameter_entry.text().strip()) or
            bool(self.vehicle_type_combo.currentText().strip()) or
            bool(self.product_type_combo.currentText().strip()) or
            bool(self.ean_entry.text().strip()) or
            bool(self.speed_rating_combo.currentText().strip()) or
            bool(self.load_rating_combo.currentText().strip()) or
            bool(self.rolling_resistance_combo.currentText().strip()) or
            bool(self.wet_grip_combo.currentText().strip())
        )
    
    def _apply_filters(self):
        """Apply current filters and update results table."""
        # Get filter values
        pattern = self.pattern_entry.text().strip() or None
        brand = self.brand_combo.currentText().strip() or None
        oe_fitment = self.oe_combo.currentText().strip() or None
        run_flat = self.runflat_checkbox.isChecked() or None
        width = self.width_entry.text().strip() or None
        profile = self.profile_entry.text().strip() or None
        diameter = self.diameter_entry.text().strip() or None
        vehicle_type = self.vehicle_type_combo.currentText().strip() or None
        product_type = self.product_type_combo.currentText().strip() or None
        ean = self.ean_entry.text().strip() or None
        speed_rating = self.speed_rating_combo.currentText().strip() or None
        load_index = self.load_rating_combo.currentText().strip() or None
        rolling_resistance = self.rolling_resistance_combo.currentText().strip() or None
        wet_grip = self.wet_grip_combo.currentText().strip() or None
        
        # Check if any filters are active
        has_filters = self._has_active_filters()
        
        if not has_filters:
            # No filters applied - don't show results
            self.results_table.setRowCount(0)
            self._current_results = []
            self.results_count_label.setText("Results: Please apply filters to search")
            self.message_label.setText("Please apply at least one filter to search the catalogue. Results will be shown when filters return less than 1000 results.")
            return
        
        # Search tyres with limit of 1001 to check if we exceed 1000
        results = self.tyre_model.search(
            pattern=pattern,
            brand=brand,
            oe_fitment=oe_fitment,
            run_flat=run_flat,
            width=width,
            profile=profile,
            diameter=diameter,
            vehicle_type=vehicle_type,
            product_type=product_type,
            ean=ean,
            speed_rating=speed_rating,
            load_index=load_index,
            rolling_resistance=rolling_resistance,
            wet_grip=wet_grip,
            limit=1001  # Check if we have more than 1000 results
        )
        
        result_count = len(results)
        
        # Only show results if we have less than 1000
        if result_count >= 1000:
            # Too many results - don't show them
            self.results_table.setRowCount(0)
            self._current_results = []
            self.results_count_label.setText(f"Results: {result_count}+ (too many to display)")
            self.message_label.setText(f"Your search returned {result_count}+ results. Please apply more specific filters to narrow down the results to less than 1000.")
        else:
            # Show results
            self.results_count_label.setText(f"Results: {result_count}")
            self.message_label.setText("")
            
            # Store results for access on double-click
            self._current_results = results
            
            # Populate table
            self.results_table.setRowCount(result_count)
            for row, tyre in enumerate(results):
                # Description
                desc = tyre.get('description', '')
                desc_item = QTableWidgetItem(desc)
                desc_item.setData(Qt.ItemDataRole.UserRole, tyre)  # Store full tyre data
                self.results_table.setItem(row, 0, desc_item)
                
                # Brand
                brand_val = tyre.get('brand', '')
                self.results_table.setItem(row, 1, QTableWidgetItem(brand_val))
                
                # Pattern
                pattern_val = tyre.get('pattern', '')
                self.results_table.setItem(row, 2, QTableWidgetItem(pattern_val))
                
                # Size (Width/Profile/Diameter)
                width_val = tyre.get('width', '')
                profile_val = tyre.get('profile', '')
                diameter_val = tyre.get('diameter', '')
                size_str = f"{width_val}/{profile_val}R{diameter_val}" if width_val and profile_val and diameter_val else ""
                self.results_table.setItem(row, 3, QTableWidgetItem(size_str))
                
                # Speed Rating
                speed_val = tyre.get('speed_rating', '')
                self.results_table.setItem(row, 4, QTableWidgetItem(speed_val))
                
                # Load Index
                load_val = tyre.get('load_index', '')
                self.results_table.setItem(row, 5, QTableWidgetItem(load_val))
                
                # Run Flat
                run_flat_val = tyre.get('run_flat', '')
                self.results_table.setItem(row, 6, QTableWidgetItem(run_flat_val))
                
                # EAN
                ean_val = tyre.get('ean', '')
                self.results_table.setItem(row, 7, QTableWidgetItem(ean_val))
            
            # Resize columns to content
            # Columns will auto-resize based on their resize modes
    
    def _on_tyre_double_clicked(self, item: QTableWidgetItem):
        """Handle double-click on tyre row to show details."""
        row = item.row()
        if row < len(self._current_results):
            tyre = self._current_results[row]
            self._show_tyre_details(tyre)
    
    def _show_tyre_details(self, tyre: Dict[str, any]):
        """Show tyre details in a popup dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Tyre Details")
        dialog.setModal(True)
        dialog.setMinimumSize(700, 800)
        dialog.resize(800, 900)
        apply_theme(dialog)
        
        # Add Escape key shortcut for close
        esc_shortcut = QShortcut(QKeySequence("Escape"), dialog)
        esc_shortcut.activated.connect(dialog.reject)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("Tyre Information")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Scroll area for all details
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(10)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        def add_detail_row(label_text: str, value: str, copyable: bool = False):
            """Helper to add a detail row."""
            row_layout = QHBoxLayout()
            label = QLabel(f"{label_text}:")
            label.setStyleSheet("font-weight: bold; font-size: 12px;")
            label.setMinimumWidth(180)
            row_layout.addWidget(label)
            
            if copyable:
                # Use QLineEdit for copyable fields
                value_entry = QLineEdit(value or "")
                value_entry.setReadOnly(True)
                value_entry.setStyleSheet("font-size: 12px; background-color: #f0f0f0;")
                value_entry.setCursorPosition(0)  # Select all on focus
                row_layout.addWidget(value_entry, stretch=1)
                
                # Copy button
                copy_button = QPushButton("Copy")
                copy_button.setMinimumWidth(60)
                copy_button.setMinimumHeight(25)
                copy_button.setStyleSheet("font-size: 10px;")
                copy_button.clicked.connect(lambda checked=False, text=value or "": self._copy_to_clipboard(text, dialog))
                row_layout.addWidget(copy_button)
            else:
                value_label = QLabel(value or "")
                value_label.setStyleSheet("font-size: 12px;")
                value_label.setWordWrap(True)
                row_layout.addWidget(value_label, stretch=1)
            
            scroll_layout.addLayout(row_layout)
        
        # Add all tyre details
        add_detail_row("Description", tyre.get('description', ''), copyable=True)
        add_detail_row("Brand", tyre.get('brand', ''))
        add_detail_row("Model", tyre.get('model', ''))
        add_detail_row("Pattern", tyre.get('pattern', ''))
        add_detail_row("Width", tyre.get('width', ''))
        add_detail_row("Profile", tyre.get('profile', ''))
        add_detail_row("Diameter", tyre.get('diameter', ''))
        add_detail_row("Speed Rating", tyre.get('speed_rating', ''))
        add_detail_row("Load Index", tyre.get('load_index', ''))
        add_detail_row("OE Fitment", tyre.get('oe_fitment', ''))
        add_detail_row("EAN", tyre.get('ean', ''), copyable=True)
        add_detail_row("Manufacturer Code", tyre.get('manufacturer_code', ''), copyable=True)
        add_detail_row("Product Type", tyre.get('product_type', ''))
        add_detail_row("Vehicle Type", tyre.get('vehicle_type', ''))
        add_detail_row("Rolling Resistance", tyre.get('rolling_resistance', ''))
        add_detail_row("Wet Grip", tyre.get('wet_grip', ''))
        add_detail_row("Noise Class", tyre.get('noise_class', ''))
        add_detail_row("Noise Performance", tyre.get('noise_performance', ''))
        add_detail_row("Vehicle Class", tyre.get('vehicle_class', ''))
        add_detail_row("Run Flat", tyre.get('run_flat', ''))
        add_detail_row("Created Date", tyre.get('created_date', ''))
        add_detail_row("Updated Date", tyre.get('updated_date', ''))
        
        # URLs
        tyre_url = tyre.get('tyre_url', '')
        if tyre_url:
            add_detail_row("Tyre URL", tyre_url, copyable=True)
        
        brand_url = tyre.get('brand_url', '')
        if brand_url:
            add_detail_row("Brand URL", brand_url, copyable=True)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll, stretch=1)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_button = QPushButton("Close (Esc)")
        close_button.setMinimumWidth(120)
        close_button.setMinimumHeight(30)
        close_button.clicked.connect(dialog.reject)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        # Show dialog
        dialog.exec()
    
    def _copy_to_clipboard(self, text: str, parent_dialog: QDialog):
        """Copy text to clipboard."""
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            QMessageBox.information(parent_dialog, "Copied", f"Copied to clipboard:\n{text[:50]}{'...' if len(text) > 50 else ''}")

