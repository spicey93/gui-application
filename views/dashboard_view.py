"""Dashboard view GUI."""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal
from views.navigation_panel import NavigationPanel


class DashboardView(QWidget):
    """Dashboard/home page GUI."""
    
    # Signals
    logout_requested = Signal()
    suppliers_requested = Signal()
    products_requested = Signal()
    inventory_requested = Signal()
    configuration_requested = Signal()
    
    def __init__(self):
        """Initialize the dashboard view."""
        super().__init__()
        self.current_username: str = ""
        self._create_widgets()
        self._setup_keyboard_navigation()
    
    def _create_widgets(self):
        """Create and layout UI widgets."""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Navigation panel (left sidebar)
        self.nav_panel = NavigationPanel(current_view="dashboard")
        self.nav_panel.dashboard_requested.connect(self._handle_dashboard)
        self.nav_panel.suppliers_requested.connect(self._handle_suppliers)
        self.nav_panel.products_requested.connect(self._handle_products)
        self.nav_panel.inventory_requested.connect(self._handle_inventory)
        self.nav_panel.configuration_requested.connect(self._handle_configuration)
        self.nav_panel.logout_requested.connect(self._handle_logout)
        
        # Add navigation panel to main layout
        main_layout.addWidget(self.nav_panel)
        
        # Content area (right side)
        content_frame = QWidget()
        content_layout = QVBoxLayout(content_frame)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(40, 40, 40, 40)
        
        # Welcome label
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
        
        # Add content area to main layout
        main_layout.addWidget(content_frame, stretch=1)
    
    def _setup_keyboard_navigation(self):
        """Set up keyboard navigation."""
        # Navigation panel handles its own keyboard navigation
        pass
    
    def _handle_dashboard(self):
        """Handle dashboard button click."""
        # Dashboard is already shown, but this allows for future navigation logic
        pass
    
    def _handle_suppliers(self):
        """Handle suppliers button click."""
        self.suppliers_requested.emit()
    
    def _handle_products(self):
        """Handle products button click."""
        self.products_requested.emit()
    
    def _handle_inventory(self):
        """Handle inventory button click."""
        self.inventory_requested.emit()
    
    def _handle_configuration(self):
        """Handle configuration button click."""
        self.configuration_requested.emit()
    
    def _handle_logout(self):
        """Handle logout button click."""
        self.logout_requested.emit()
    
    def set_username(self, username: str):
        """Set the current username and update display."""
        self.current_username = username
        self.welcome_label.setText(f"Welcome, {username}!")
        self.user_info_label.setText(f"Logged in as: {username}")
