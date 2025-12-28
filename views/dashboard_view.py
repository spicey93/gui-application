"""Dashboard view GUI."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from views.base_view import BaseTabbedView
from utils.styles import apply_theme


class DashboardView(BaseTabbedView):
    """Dashboard/home page GUI."""
    
    # Additional signals beyond base class
    cash_up_requested = Signal()  # Request to navigate to cash up view
    
    def __init__(self):
        """Initialize the dashboard view."""
        super().__init__(title="Dashboard", current_view="dashboard")
        self.current_username: str = ""
        self._create_widgets()
        self._setup_keyboard_navigation()
    
    def _create_widgets(self):
        """Create and layout UI widgets."""
        # Add Cash Up button at the top using base class method
        # Note: Shortcut is handled globally in main.py, not here to avoid conflicts
        self.cash_up_button = self.add_action_button(
            "Cash Up (Ctrl+U)",
            self._handle_cash_up,
            None
        )
        
        # Create tabs widget
        self.tab_widget = self.create_tabs()
        
        # Tab 1: Overview (placeholder)
        overview_widget = QWidget()
        overview_layout = QVBoxLayout(overview_widget)
        overview_layout.setSpacing(20)
        overview_layout.setContentsMargins(20, 20, 20, 20)
        
        self.welcome_label = QLabel("Welcome!")
        self.welcome_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        overview_layout.addWidget(self.welcome_label)
        
        self.user_info_label = QLabel("")
        self.user_info_label.setStyleSheet("font-size: 12px;")
        overview_layout.addWidget(self.user_info_label)
        
        overview_layout.addSpacing(20)
        
        info_label = QLabel("You have successfully logged in.")
        info_label.setStyleSheet("font-size: 12px;")
        overview_layout.addWidget(info_label)
        
        placeholder_label = QLabel("Dashboard overview content goes here...")
        placeholder_label.setStyleSheet("font-size: 10px; color: gray;")
        overview_layout.addWidget(placeholder_label)
        
        overview_layout.addStretch()
        
        self.add_tab(overview_widget, "Overview (Ctrl+1)", "Ctrl+1")
        
        # Tab 2: Recent Activity (placeholder)
        activity_widget = QWidget()
        activity_layout = QVBoxLayout(activity_widget)
        activity_layout.setSpacing(20)
        activity_layout.setContentsMargins(20, 20, 20, 20)
        
        activity_title = QLabel("Recent Activity")
        activity_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        activity_layout.addWidget(activity_title)
        
        activity_placeholder = QLabel("Recent transactions and activity will appear here...")
        activity_placeholder.setStyleSheet("font-size: 10px; color: gray;")
        activity_layout.addWidget(activity_placeholder)
        
        activity_layout.addStretch()
        
        self.add_tab(activity_widget, "Recent Activity (Ctrl+2)", "Ctrl+2")
        
        # Tab 3: Summary (placeholder)
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)
        summary_layout.setSpacing(20)
        summary_layout.setContentsMargins(20, 20, 20, 20)
        
        summary_title = QLabel("Summary")
        summary_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        summary_layout.addWidget(summary_title)
        
        summary_placeholder = QLabel("Financial summary and statistics will appear here...")
        summary_placeholder.setStyleSheet("font-size: 10px; color: gray;")
        summary_layout.addWidget(summary_placeholder)
        
        summary_layout.addStretch()
        
        self.add_tab(summary_widget, "Summary (Ctrl+3)", "Ctrl+3")
        
        # Set first tab as default
        self.tab_widget.setCurrentIndex(0)
    
    def _setup_keyboard_navigation(self):
        """Set up keyboard navigation."""
        # Navigation panel handles its own keyboard navigation
        pass
    
    def set_username(self, username: str):
        """Set the current username and update display."""
        self.current_username = username
        if hasattr(self, 'welcome_label'):
            self.welcome_label.setText(f"Welcome, {username}!")
        if hasattr(self, 'user_info_label'):
            self.user_info_label.setText(f"Logged in as: {username}")
    
    def _handle_cash_up(self):
        """Handle cash up button click - open cash up dialog."""
        self.cash_up_requested.emit()
    
    def show_success_dialog(self, message: str):
        """Show a success dialog."""
        QMessageBox.information(self, "Success", message)
    
    def show_error_dialog(self, message: str):
        """Show an error dialog."""
        QMessageBox.critical(self, "Error", message)
