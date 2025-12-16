"""Configuration view GUI."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel
)
from PySide6.QtCore import Qt, Signal
from views.base_view import BaseTabbedView


class ConfigurationView(BaseTabbedView):
    """Configuration view GUI."""
    
    def __init__(self):
        """Initialize the configuration view."""
        super().__init__(title="Configuration", current_view="configuration")
        self._create_widgets()
        self._setup_keyboard_navigation()
    
    def _create_widgets(self):
        """Create and layout UI widgets."""
        # Get content layout to add widgets directly (no tabs needed)
        content_layout = self.get_content_layout()
        
        # Blank page for now
        placeholder_label = QLabel("Configuration")
        placeholder_label.setStyleSheet("font-size: 24px; font-weight: bold; color: gray;")
        content_layout.addWidget(placeholder_label)
        
        info_label = QLabel("Configuration options will be available here in the future.")
        info_label.setStyleSheet("font-size: 12px; color: gray;")
        content_layout.addWidget(info_label)
        
        content_layout.addStretch()
    
    def _setup_keyboard_navigation(self):
        """Set up keyboard navigation."""
        # Navigation panel handles its own keyboard navigation
        pass

