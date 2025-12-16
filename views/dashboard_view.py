"""Dashboard view GUI."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal
from views.base_view import BaseTabbedView


class DashboardView(BaseTabbedView):
    """Dashboard/home page GUI."""
    
    # Additional signals beyond base class (none needed, all in base)
    
    def __init__(self):
        """Initialize the dashboard view."""
        super().__init__(title="Dashboard", current_view="dashboard")
        self.current_username: str = ""
        self._create_widgets()
        self._setup_keyboard_navigation()
    
    def _create_widgets(self):
        """Create and layout UI widgets."""
        # Hide the base title label since we'll use a welcome label instead
        self.title_label.hide()
        
        # Get content layout to add widgets directly (no tabs needed)
        content_layout = self.get_content_layout()
        
        # Welcome label (replaces the title)
        self.welcome_label = QLabel("Welcome!")
        self.welcome_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        content_layout.addWidget(self.welcome_label)
        
        # User info
        self.user_info_label = QLabel("")
        self.user_info_label.setStyleSheet("font-size: 10px;")
        content_layout.addWidget(self.user_info_label)
        
        content_layout.addSpacing(20)
        
        # Separator
        content_separator = QFrame()
        content_separator.setFrameShape(QFrame.Shape.HLine)
        content_separator.setFrameShadow(QFrame.Shadow.Sunken)
        content_layout.addWidget(content_separator)
        
        content_layout.addSpacing(20)
        
        # Dashboard content
        info_label = QLabel("You have successfully logged in.")
        info_label.setStyleSheet("font-size: 12px;")
        content_layout.addWidget(info_label)
        
        # Placeholder for future dashboard content
        placeholder_label = QLabel("Dashboard content goes here...")
        placeholder_label.setStyleSheet("font-size: 10px; color: gray;")
        content_layout.addWidget(placeholder_label)
        
        content_layout.addStretch()
    
    def _setup_keyboard_navigation(self):
        """Set up keyboard navigation."""
        # Navigation panel handles its own keyboard navigation
        pass
    
    def set_username(self, username: str):
        """Set the current username and update display."""
        self.current_username = username
        self.welcome_label.setText(f"Welcome, {username}!")
        self.user_info_label.setText(f"Logged in as: {username}")
