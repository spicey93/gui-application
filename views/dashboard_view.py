"""Dashboard view GUI."""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from views.shortcuts_dialog import ShortcutsDialog


class DashboardView(QWidget):
    """Dashboard/home page GUI."""
    
    # Signals
    logout_requested = Signal()
    suppliers_requested = Signal()
    
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
        nav_panel = QFrame()
        nav_panel.setObjectName("navPanel")
        nav_panel.setFixedWidth(180)
        nav_panel.setFrameShape(QFrame.Shape.StyledPanel)
        nav_panel.setFrameShadow(QFrame.Shadow.Raised)
        
        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setSpacing(10)
        nav_layout.setContentsMargins(15, 15, 15, 15)
        
        # Navigation title
        nav_title = QLabel("Navigation")
        nav_title.setStyleSheet("font-weight: bold; font-size: 12px;")
        nav_layout.addWidget(nav_title)
        
        nav_layout.addSpacing(10)
        
        # Dashboard menu item
        self.dashboard_button = QPushButton("Dashboard")
        self.dashboard_button.setMinimumHeight(30)
        self.dashboard_button.clicked.connect(self._handle_dashboard)
        nav_layout.addWidget(self.dashboard_button)
        
        # Suppliers menu item
        self.suppliers_button = QPushButton("Suppliers")
        self.suppliers_button.setMinimumHeight(30)
        self.suppliers_button.clicked.connect(self._handle_suppliers)
        nav_layout.addWidget(self.suppliers_button)
        
        nav_layout.addSpacing(15)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        nav_layout.addWidget(separator)
        
        nav_layout.addSpacing(15)
        
        # Logout menu item
        self.logout_button = QPushButton("Logout")
        self.logout_button.setMinimumHeight(30)
        self.logout_button.clicked.connect(self._handle_logout)
        nav_layout.addWidget(self.logout_button)
        
        nav_layout.addSpacing(15)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        nav_layout.addWidget(separator2)
        
        nav_layout.addSpacing(15)
        
        # Help/Shortcuts button
        self.help_button = QPushButton("Keyboard Shortcuts")
        self.help_button.setMinimumHeight(30)
        self.help_button.clicked.connect(self._handle_help)
        nav_layout.addWidget(self.help_button)
        
        nav_layout.addStretch()
        
        # Add navigation panel to main layout
        main_layout.addWidget(nav_panel)
        
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
        # Tab order: Dashboard -> Suppliers -> Logout -> Help
        self.setTabOrder(self.dashboard_button, self.suppliers_button)
        self.setTabOrder(self.suppliers_button, self.logout_button)
        self.setTabOrder(self.logout_button, self.help_button)
        
        # Arrow keys for navigation panel
        self.dashboard_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.suppliers_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.logout_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.help_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def _handle_dashboard(self):
        """Handle dashboard button click."""
        # Dashboard is already shown, but this allows for future navigation logic
        pass
    
    def _handle_suppliers(self):
        """Handle suppliers button click."""
        self.suppliers_requested.emit()
    
    def _handle_logout(self):
        """Handle logout button click."""
        self.logout_requested.emit()
    
    def _handle_help(self):
        """Handle help button click."""
        dialog = ShortcutsDialog(self)
        dialog.exec()
    
    def set_username(self, username: str):
        """Set the current username and update display."""
        self.current_username = username
        self.welcome_label.setText(f"Welcome, {username}!")
        self.user_info_label.setText(f"Logged in as: {username}")
