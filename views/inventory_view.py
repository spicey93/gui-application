"""Inventory view GUI."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QKeyEvent
from typing import List, Dict
from views.base_view import BaseTabbedView


class InventoryTableWidget(QTableWidget):
    """Custom table widget for inventory display."""
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events."""
        # Allow standard table navigation
        super().keyPressEvent(event)


class InventoryView(BaseTabbedView):
    """Inventory management GUI."""
    
    # Additional signals beyond base class
    filter_changed = Signal(bool)  # Signal when filter checkbox changes
    
    def __init__(self):
        """Initialize the inventory view."""
        super().__init__(title="Inventory", current_view="inventory")
        self._create_widgets()
        self._setup_keyboard_navigation()
    
    def _create_widgets(self):
        """Create and layout UI widgets."""
        # Get content layout to add widgets directly (no tabs needed)
        content_layout = self.get_content_layout()
        
        # Filter checkbox
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        self.show_out_of_stock_checkbox = QCheckBox("Show out of stock items")
        self.show_out_of_stock_checkbox.setChecked(False)  # Default to unchecked (hide out-of-stock)
        self.show_out_of_stock_checkbox.stateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.show_out_of_stock_checkbox)
        filter_layout.addStretch()
        content_layout.addLayout(filter_layout)
        
        # Inventory table
        self.inventory_table = InventoryTableWidget()
        self.inventory_table.setColumnCount(3)
        self.inventory_table.setHorizontalHeaderLabels(["Stock Number", "Description", "Stock Quantity"])
        self.inventory_table.horizontalHeader().setStretchLastSection(True)
        self.inventory_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.inventory_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.inventory_table.setAlternatingRowColors(True)
        self.inventory_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Set column resize modes - Description stretches, others resize to contents
        header = self.inventory_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        # Enable keyboard navigation
        self.inventory_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        content_layout.addWidget(self.inventory_table, stretch=1)
    
    def _on_filter_changed(self, state: int):
        """Handle filter checkbox state change."""
        show_out_of_stock = state == Qt.CheckState.Checked
        self.filter_changed.emit(show_out_of_stock)
    
    def _setup_keyboard_navigation(self):
        """Set up keyboard navigation."""
        # Tab order: Table -> Navigation panel
        self.setTabOrder(self.inventory_table, self.nav_panel.logout_button)
        
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
    
    def load_inventory(self, inventory_items: List[Dict[str, any]], include_out_of_stock: bool = False):
        """
        Load inventory items into the table.
        
        Args:
            inventory_items: List of inventory item dictionaries with stock_number, description, stock_quantity
            include_out_of_stock: If False, filter out items with stock_quantity <= 0
        """
        # Filter out out-of-stock items if not including them
        if not include_out_of_stock:
            inventory_items = [
                item for item in inventory_items 
                if item.get('stock_quantity', 0.0) > 0
            ]
        
        self.inventory_table.setRowCount(len(inventory_items))
        
        for row, item in enumerate(inventory_items):
            self.inventory_table.setItem(row, 0, QTableWidgetItem(str(item.get('stock_number', ''))))
            self.inventory_table.setItem(row, 1, QTableWidgetItem(str(item.get('description', ''))))
            
            # Format stock quantity with 2 decimal places
            stock_qty = item.get('stock_quantity', 0.0)
            stock_qty_str = f"{stock_qty:.2f}" if isinstance(stock_qty, (int, float)) else str(stock_qty)
            self.inventory_table.setItem(row, 2, QTableWidgetItem(stock_qty_str))
        
        # Columns will auto-resize based on their resize modes
        
        # Auto-select first row and set focus to table if data exists
        if len(inventory_items) > 0:
            self.inventory_table.selectRow(0)
            self.inventory_table.setFocus()
            # Ensure the first row is visible
            self.inventory_table.scrollToItem(self.inventory_table.item(0, 0))

