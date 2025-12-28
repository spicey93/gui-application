"""Table configuration helper utilities."""
from PySide6.QtWidgets import QTableWidget, QHeaderView, QSizePolicy, QTableWidgetItem
from PySide6.QtCore import Qt, QTimer
from typing import List, Dict, Optional, Union
from PySide6.QtGui import QFontMetrics


class TableConfig:
    """Helper class for configuring QTableWidget instances."""
    
    @staticmethod
    def configure_table(
        table: QTableWidget,
        columns: List[str],
        column_widths: Optional[Dict[int, int]] = None,
        resize_modes: Optional[Dict[int, QHeaderView.ResizeMode]] = None,
        stretch_last: bool = True,
        alternating_rows: bool = True,
        selection_behavior: QTableWidget.SelectionBehavior = QTableWidget.SelectionBehavior.SelectRows,
        selection_mode: QTableWidget.SelectionMode = QTableWidget.SelectionMode.SingleSelection,
        edit_triggers: QTableWidget.EditTrigger = QTableWidget.EditTrigger.NoEditTriggers,
        focus_policy: Qt.FocusPolicy = Qt.FocusPolicy.StrongFocus,
        size_policy: Optional[QSizePolicy] = None
    ) -> None:
        """
        Configure a table widget with common settings.
        
        Args:
            table: The QTableWidget to configure
            columns: List of column header labels
            column_widths: Optional dict mapping column index to width
            resize_modes: Optional dict mapping column index to resize mode
            stretch_last: Whether to stretch the last column
            alternating_rows: Whether to use alternating row colors
            selection_behavior: Selection behavior mode
            selection_mode: Selection mode
            edit_triggers: Edit trigger mode
            focus_policy: Focus policy
            size_policy: Optional size policy (defaults to Expanding, Expanding)
        """
        # Set column count and headers
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        
        # Configure header
        header = table.horizontalHeader()
        if stretch_last:
            header.setStretchLastSection(True)
        
        # Set column widths
        if column_widths:
            for col, width in column_widths.items():
                if col < len(columns):
                    header.resizeSection(col, width)
        
        # Set resize modes
        if resize_modes:
            for col, mode in resize_modes.items():
                if col < len(columns):
                    header.setSectionResizeMode(col, mode)
        
        # Set selection behavior
        table.setSelectionBehavior(selection_behavior)
        table.setSelectionMode(selection_mode)
        
        # Set alternating row colors
        table.setAlternatingRowColors(alternating_rows)
        
        # Set edit triggers
        table.setEditTriggers(edit_triggers)
        
        # Set focus policy
        table.setFocusPolicy(focus_policy)
        
        # Set size policy
        if size_policy is None:
            size_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        table.setSizePolicy(size_policy)
    
    @staticmethod
    def resize_columns_to_content(
        table: QTableWidget,
        column_widths: Optional[Dict[int, int]] = None
    ) -> None:
        """
        Resize columns to content and optionally set minimum widths.
        
        Args:
            table: The QTableWidget to resize
            column_widths: Optional dict mapping column index to minimum width
        """
        table.resizeColumnsToContents()
        
        if column_widths:
            header = table.horizontalHeader()
            for col, width in column_widths.items():
                if col < table.columnCount():
                    current_width = header.sectionSize(col)
                    if current_width < width:
                        header.resizeSection(col, width)
    
    @staticmethod
    def distribute_columns_proportionally(table: QTableWidget, deferred: bool = True) -> None:
        """
        Distribute column widths proportionally based on max content length,
        ensuring the table takes up 100% of available width.
        
        This function:
        1. Calculates the maximum content width for each column (including header)
        2. Distributes column widths proportionally based on those max widths
        3. Ensures the table fills 100% of available width
        
        Args:
            table: The QTableWidget to configure
            deferred: If True, use QTimer to defer execution until viewport has valid width
        """
        if table.columnCount() == 0:
            return
        
        def _do_distribute() -> None:
            """Internal function to perform the distribution."""
            if table.columnCount() == 0:
                return
            
            header = table.horizontalHeader()
            font_metrics = QFontMetrics(table.font())
            
            # Calculate max content width for each column
            max_widths = []
            for col in range(table.columnCount()):
                max_width = 0
                
                # Check header text width
                header_text = header.model().headerData(col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
                if header_text:
                    header_width = font_metrics.horizontalAdvance(str(header_text)) + 40  # Add padding
                    max_width = max(max_width, header_width)
                
                # Check all cell content widths in this column
                for row in range(table.rowCount()):
                    item = table.item(row, col)
                    if item:
                        text = item.text()
                        if text:
                            text_width = font_metrics.horizontalAdvance(text) + 20  # Add padding
                            max_width = max(max_width, text_width)
                
                # Ensure minimum width
                max_width = max(max_width, 50)
                max_widths.append(max_width)
            
            # Calculate total width needed
            total_content_width = sum(max_widths)
            
            # Get viewport width
            viewport_width = table.viewport().width()
            if viewport_width <= 0:
                # Try to get width from parent
                parent = table.parent()
                if parent:
                    viewport_width = parent.width() - 100  # Estimate with margins
                if viewport_width <= 0:
                    # Use content-based calculation as fallback
                    viewport_width = max(total_content_width, 800)
            
            # Distribute widths proportionally
            if total_content_width > 0:
                # Calculate proportional widths
                proportions = [w / total_content_width for w in max_widths]
                
                # Set all columns to Interactive mode (allows manual resizing while maintaining proportions)
                for col in range(table.columnCount()):
                    header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
                
                # Distribute available width proportionally
                for col in range(table.columnCount()):
                    proportional_width = int(viewport_width * proportions[col])
                    header.resizeSection(col, proportional_width)
            else:
                # Fallback: equal distribution
                equal_width = max(50, viewport_width // table.columnCount())
                for col in range(table.columnCount()):
                    header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
                    header.resizeSection(col, equal_width)
            
            # Ensure table takes up 100% width
            table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            
            # Set stretch last section to false to maintain proportional widths
            header.setStretchLastSection(False)
        
        if deferred:
            # Use QTimer to defer execution until viewport has valid width
            QTimer.singleShot(0, _do_distribute)
        else:
            _do_distribute()

