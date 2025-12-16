"""Inventory view GUI."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView
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
    
    def __init__(self):
        """Initialize the inventory view."""
        super().__init__(title="Inventory", current_view="inventory")
        self._create_widgets()
        self._setup_keyboard_navigation()
    
    def _create_widgets(self):
        """Create and layout UI widgets."""
        # Get content layout to add widgets directly (no tabs needed)
        content_layout = self.get_content_layout()
        
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
        
        content_layout.addWidget(self.inventory_table, stretch=1)
    
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

