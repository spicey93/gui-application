"""Configuration view GUI."""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal
from views.navigation_panel import NavigationPanel


class ConfigurationView(QWidget):
    """Configuration view GUI."""
    
    # Signals
    dashboard_requested = Signal()
    suppliers_requested = Signal()
    products_requested = Signal()
    logout_requested = Signal()
    
    def __init__(self):
        """Initialize the configuration view."""
        super().__init__()
        self._create_widgets()
        self._setup_keyboard_navigation()
    
    def _create_widgets(self):
        """Create and layout UI widgets."""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Navigation panel (left sidebar)
        self.nav_panel = NavigationPanel(current_view="configuration")
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
        
        # Blank page for now
        placeholder_label = QLabel("Configuration")
        placeholder_label.setStyleSheet("font-size: 24px; font-weight: bold; color: gray;")
        content_layout.addWidget(placeholder_label)
        
        info_label = QLabel("Configuration options will be available here in the future.")
        info_label.setStyleSheet("font-size: 12px; color: gray;")
        content_layout.addWidget(info_label)
        
        content_layout.addStretch()
        
        # Add content area to main layout
        main_layout.addWidget(content_frame, stretch=1)
    
    def _setup_keyboard_navigation(self):
        """Set up keyboard navigation."""
        # Navigation panel handles its own keyboard navigation
        pass
    
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
        # Already on configuration page
        pass
    
    def _handle_logout(self):
        """Handle logout button click."""
        self.logout_requested.emit()

