"""Keyboard shortcuts help dialog."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt
from utils.styles import apply_theme


class ShortcutsDialog(QDialog):
    """Dialog showing keyboard shortcuts."""
    
    def __init__(self, parent=None):
        """Initialize the shortcuts dialog."""
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        self.resize(500, 400)
        apply_theme(self)
        self._create_widgets()
    
    def _create_widgets(self):
        """Create and layout UI widgets."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("Keyboard Shortcuts")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Shortcuts content
        shortcuts_text = """
        <b>Navigation Shortcuts:</b><br><br>
        
        <b>F1</b> - Navigate to Dashboard<br>
        <b>F2</b> - Navigate to Suppliers<br>
        <b>F3</b> - Navigate to Customers<br>
        <b>F4</b> - Navigate to Products<br>
        <b>F5</b> - Navigate to Inventory<br>
        <b>F6</b> - Navigate to Book Keeper<br>
        <b>F7</b> - Navigate to Configuration<br>
        <b>Ctrl+Q</b> - Exit application<br><br>
        
        <b>Standard Navigation:</b><br><br>
        
        <b>Tab</b> - Move to next element<br>
        <b>Shift+Tab</b> - Move to previous element<br>
        <b>Arrow Keys</b> - Navigate within lists/tables<br>
        <b>Enter</b> - Activate button or confirm action<br>
        <b>Escape</b> - Cancel dialog or close window<br><br>
        
        <b>Context Actions (Ctrl+N):</b><br><br>
        
        <b>Ctrl+N</b> - Add new item (supplier/customer/product/account)<br><br>
        
        <b>Forms:</b><br><br>
        
        <b>Ctrl+Enter</b> - Submit form<br>
        <b>Enter</b> - Submit form (when button is focused)<br>
        <b>Escape</b> - Cancel form
        """
        
        shortcuts_label = QLabel(shortcuts_text)
        shortcuts_label.setStyleSheet("font-size: 11px;")
        shortcuts_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(shortcuts_label)
        
        layout.addStretch()
        
        # Close button
        button_layout = QVBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.setMinimumWidth(100)
        close_button.setMinimumHeight(30)
        close_button.setDefault(True)
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addLayout(button_layout)

