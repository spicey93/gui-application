"""Inventory view GUI."""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QKeyEvent
from typing import List, Dict
from views.navigation_panel import NavigationPanel


class InventoryTableWidget(QTableWidget):
    """Custom table widget for inventory display."""
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events."""
        # Allow standard table navigation
        super().keyPressEvent(event)


class InventoryView(QWidget):
    """Inventory management GUI."""
    
    # Signals
    dashboard_requested = Signal()
    suppliers_requested = Signal()
    products_requested = Signal()
    configuration_requested = Signal()
    logout_requested = Signal()
    refresh_requested = Signal()
    
    def __init__(self):
        """Initialize the inventory view."""
        super().__init__()
        self._create_widgets()
        self._setup_keyboard_navigation()
    
    def _create_widgets(self):
        """Create and layout UI widgets."""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Navigation panel (left sidebar)
        self.nav_panel = NavigationPanel(current_view="inventory")
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
        
        # Title and Refresh button
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("Inventory")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        self.refresh_button = QPushButton("Refresh (F5)")
        self.refresh_button.setMinimumWidth(140)
        self.refresh_button.setMinimumHeight(30)
        self.refresh_button.clicked.connect(self._handle_refresh)
        title_layout.addWidget(self.refresh_button)
        
        content_layout.addLayout(title_layout)
        
        # Inventory table
        self.inventory_table = InventoryTableWidget()
        self.inventory_table.setColumnCount(3)
        self.inventory_table.setHorizontalHeaderLabels(["Stock Number", "Description", "Stock Quantity"])
        self.inventory_table.horizontalHeader().setStretchLastSection(True)
        self.inventory_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.inventory_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.inventory_table.setAlternatingRowColors(True)
        self.inventory_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Set column widths
        header = self.inventory_table.horizontalHeader()
        header.resizeSection(0, 150)
        header.resizeSection(1, 300)
        header.resizeSection(2, 150)
        
        # Enable keyboard navigation
        self.inventory_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        content_layout.addWidget(self.inventory_table)
        
        # Add content area to main layout
        main_layout.addWidget(content_frame, stretch=1)
    
    def _setup_keyboard_navigation(self):
        """Set up keyboard navigation."""
        # Tab order: Table -> Refresh -> Navigation panel
        self.setTabOrder(self.inventory_table, self.refresh_button)
        self.setTabOrder(self.refresh_button, self.nav_panel.logout_button)
        
        # Arrow keys work automatically in QTableWidget
        self.inventory_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def showEvent(self, event: QEvent):
        """Handle show event - set focus to table if it has data."""
        super().showEvent(event)
        # Set focus to table if it has rows
        if self.inventory_table.rowCount() > 0:
            self.inventory_table.setFocus()
            # Ensure first row is selected if nothing is selected
            if not self.inventory_table.selectedItems():
                self.inventory_table.selectRow(0)
    
    def _handle_dashboard(self):
        """Handle dashboard button click."""
        self.dashboard_requested.emit()
    
    def _handle_suppliers(self):
        """Handle suppliers button click."""
        self.suppliers_requested.emit()
    
    def _handle_products(self):
        """Handle products button click."""
        self.products_requested.emit()
    
    def _handle_configuration(self):
        """Handle configuration button click."""
        self.configuration_requested.emit()
    
    def _handle_logout(self):
        """Handle logout button click."""
        self.logout_requested.emit()
    
    def _handle_refresh(self):
        """Handle refresh button click."""
        self.refresh_requested.emit()
    
    def load_inventory(self, inventory_items: List[Dict[str, any]]):
        """
        Load inventory items into the table.
        
        Args:
            inventory_items: List of inventory item dictionaries with stock_number, description, stock_quantity
        """
        self.inventory_table.setRowCount(len(inventory_items))
        
        for row, item in enumerate(inventory_items):
            self.inventory_table.setItem(row, 0, QTableWidgetItem(str(item.get('stock_number', ''))))
            self.inventory_table.setItem(row, 1, QTableWidgetItem(str(item.get('description', ''))))
            
            # Format stock quantity with 2 decimal places
            stock_qty = item.get('stock_quantity', 0.0)
            stock_qty_str = f"{stock_qty:.2f}" if isinstance(stock_qty, (int, float)) else str(stock_qty)
            self.inventory_table.setItem(row, 2, QTableWidgetItem(stock_qty_str))
        
        # Resize columns to content
        self.inventory_table.resizeColumnsToContents()
        header = self.inventory_table.horizontalHeader()
        header.resizeSection(0, 150)
        header.resizeSection(1, 300)
        header.resizeSection(2, 150)
        
        # Auto-select first row and set focus to table if data exists
        if len(inventory_items) > 0:
            self.inventory_table.selectRow(0)
            self.inventory_table.setFocus()
            # Ensure the first row is visible
            self.inventory_table.scrollToItem(self.inventory_table.item(0, 0))

