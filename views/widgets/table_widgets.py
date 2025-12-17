"""Reusable table widget classes."""
from PySide6.QtWidgets import QTableWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from typing import Callable, Optional


class EnterKeyTableWidget(QTableWidget):
    """
    Custom table widget with Enter key support.
    
    Handles Enter/Return key presses and calls a callback function.
    Supports both row-based callbacks (passes row index) and simple callbacks.
    """
    
    def __init__(self, enter_callback: Optional[Callable] = None, pass_row: bool = False):
        """
        Initialize the table widget.
        
        Args:
            enter_callback: Callback function to call when Enter is pressed.
                           If pass_row is True, callback should accept row index.
                           If pass_row is False, callback takes no arguments.
            pass_row: If True, passes the selected row index to callback.
                     If False, calls callback with no arguments.
        """
        super().__init__()
        self.enter_callback = enter_callback
        self.pass_row = pass_row
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.selectedItems() and self.enter_callback:
                if self.pass_row:
                    row = self.selectedItems()[0].row()
                    self.enter_callback(row)
                else:
                    self.enter_callback()
                event.accept()
                return
        super().keyPressEvent(event)
