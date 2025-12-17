"""Table configuration helper utilities."""
from PySide6.QtWidgets import QTableWidget, QHeaderView, QSizePolicy
from PySide6.QtCore import Qt
from typing import List, Dict, Optional, Union


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
