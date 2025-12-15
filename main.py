"""Main entry point for the GUI application."""
import sys
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence

from models.user import User
from models.supplier import Supplier
from views.login_view import LoginView
from views.dashboard_view import DashboardView
from views.suppliers_view import SuppliersView
from views.shortcuts_dialog import ShortcutsDialog
from controllers.login_controller import LoginController
from controllers.dashboard_controller import DashboardController
from controllers.suppliers_controller import SuppliersController


class Application(QMainWindow):
    """Main application class to manage views and navigation."""
    
    def __init__(self):
        """Initialize the application."""
        super().__init__()
        
        # Set window properties
        self.setWindowTitle("Login")
        self.setGeometry(100, 100, 400, 250)
        self.setMinimumSize(400, 250)
        
        # Load Windows XP theme
        self._load_xp_theme()
        
        # Initialize models
        self.user_model = User()
        self.supplier_model = Supplier()
        
        # Current user ID (None until login)
        self.current_user_id: Optional[int] = None
        
        # Create stacked widget for views
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Initialize views
        self.login_view = LoginView()
        self.dashboard_view = DashboardView()
        self.suppliers_view = SuppliersView()
        
        # Add views to stacked widget
        self.login_index = self.stacked_widget.addWidget(self.login_view)
        self.dashboard_index = self.stacked_widget.addWidget(self.dashboard_view)
        self.suppliers_index = self.stacked_widget.addWidget(self.suppliers_view)
        
        # Show login view initially
        self.stacked_widget.setCurrentIndex(self.login_index)
        
        # Initialize controllers
        self.login_controller = LoginController(self.user_model, self.login_view)
        self.dashboard_controller = DashboardController(self.dashboard_view)
        self.suppliers_controller = None
        
        # Set up navigation callbacks
        self.login_controller.login_success.connect(self.on_login_success)
        self.dashboard_controller.logout_requested.connect(self.on_logout)
        self.dashboard_controller.suppliers_requested.connect(self.on_suppliers)
        
        # Center the window
        self._center_window()
        
        # Set up global keyboard shortcuts
        self._setup_shortcuts()
    
    def _load_xp_theme(self):
        """Load Windows XP theme stylesheet."""
        stylesheet_path = Path(__file__).parent / "styles" / "xp_theme.qss"
        if stylesheet_path.exists():
            with open(stylesheet_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
    
    def _center_window(self):
        """Center the window on the screen."""
        frame_geometry = self.frameGeometry()
        screen = QApplication.primaryScreen().availableGeometry().center()
        frame_geometry.moveCenter(screen)
        self.move(frame_geometry.topLeft())
    
    def _setup_shortcuts(self):
        """Set up global keyboard shortcuts."""
        # Ctrl+D: Dashboard
        self.shortcut_dashboard = QShortcut(QKeySequence("Ctrl+D"), self)
        self.shortcut_dashboard.activated.connect(self._navigate_to_dashboard)
        
        # Ctrl+S: Suppliers
        self.shortcut_suppliers = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_suppliers.activated.connect(self._navigate_to_suppliers)
        
        # Ctrl+L: Logout
        self.shortcut_logout = QShortcut(QKeySequence("Ctrl+L"), self)
        self.shortcut_logout.activated.connect(self._handle_logout_shortcut)
        
        # Ctrl+N: Add Supplier (only when in suppliers view)
        self.shortcut_add_supplier = QShortcut(QKeySequence("Ctrl+N"), self)
        self.shortcut_add_supplier.activated.connect(self._handle_add_supplier_shortcut)
        
        # F5: Refresh (only when in suppliers view)
        self.shortcut_refresh = QShortcut(QKeySequence("F5"), self)
        self.shortcut_refresh.activated.connect(self._handle_refresh_shortcut)
        
        # F1: Show keyboard shortcuts help
        self.shortcut_help = QShortcut(QKeySequence("F1"), self)
        self.shortcut_help.activated.connect(self._show_shortcuts_help)
    
    def _navigate_to_dashboard(self):
        """Navigate to dashboard if logged in."""
        if self.current_user_id is not None:
            self.stacked_widget.setCurrentIndex(self.dashboard_index)
            self.setWindowTitle("Dashboard")
            self.setMinimumSize(800, 600)
            self._center_window()
    
    def _navigate_to_suppliers(self):
        """Navigate to suppliers if logged in."""
        if self.current_user_id is not None:
            if self.suppliers_controller:
                self.suppliers_controller.refresh_suppliers()
            self.stacked_widget.setCurrentIndex(self.suppliers_index)
            self.setWindowTitle("Suppliers")
            self.setMinimumSize(800, 600)
            self._center_window()
    
    def _handle_logout_shortcut(self):
        """Handle logout keyboard shortcut."""
        if self.current_user_id is not None:
            self.on_logout()
    
    def _handle_add_supplier_shortcut(self):
        """Handle add supplier keyboard shortcut."""
        if (self.current_user_id is not None and 
            self.stacked_widget.currentIndex() == self.suppliers_index):
            self.suppliers_view.add_supplier()
    
    def _handle_refresh_shortcut(self):
        """Handle refresh keyboard shortcut."""
        if (self.current_user_id is not None and 
            self.stacked_widget.currentIndex() == self.suppliers_index):
            if self.suppliers_controller:
                self.suppliers_controller.refresh_suppliers()
    
    def _show_shortcuts_help(self):
        """Show keyboard shortcuts help dialog."""
        if self.current_user_id is not None:
            dialog = ShortcutsDialog(self)
            dialog.exec()
    
    def on_login_success(self, username: str, user_id: int):
        """Handle successful login."""
        # Store current user ID
        self.current_user_id = user_id
        
        # Initialize or update suppliers controller with user_id
        if self.suppliers_controller is None:
            self.suppliers_controller = SuppliersController(
                self.suppliers_view, 
                self.supplier_model, 
                user_id
            )
            self.suppliers_controller.dashboard_requested.connect(self.on_back_to_dashboard)
            self.suppliers_controller.logout_requested.connect(self.on_logout)
        else:
            self.suppliers_controller.set_user_id(user_id)
        
        # Update window for dashboard
        self.setWindowTitle("Dashboard")
        self.setMinimumSize(800, 600)
        self.resize(1200, 800)
        self._center_window()
        
        # Switch views
        self.stacked_widget.setCurrentIndex(self.dashboard_index)
        self.dashboard_view.set_username(username)
    
    def on_suppliers(self):
        """Handle navigation to suppliers."""
        # Refresh suppliers for current user
        if self.suppliers_controller:
            self.suppliers_controller.refresh_suppliers()
        # Switch to suppliers view
        self.stacked_widget.setCurrentIndex(self.suppliers_index)
        self.setWindowTitle("Suppliers")
        self.setMinimumSize(800, 600)
        self._center_window()
    
    def on_back_to_dashboard(self):
        """Handle navigation back to dashboard."""
        # Switch to dashboard view
        self.stacked_widget.setCurrentIndex(self.dashboard_index)
        self.setWindowTitle("Dashboard")
        self.setMinimumSize(800, 600)
        self._center_window()
    
    def on_logout(self):
        """Handle logout."""
        # Update window for login
        self.setWindowTitle("Login")
        self.setMinimumSize(400, 250)
        self.resize(400, 250)
        self._center_window()
        
        # Switch views - show login
        self.stacked_widget.setCurrentIndex(self.login_index)
        self.current_user_id = None
        self.login_view.clear_fields()


def main():
    """Initialize and run the application."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("GUI Application")
    app.setOrganizationName("GUI App")
    
    # Create and show main window
    window = Application()
    window.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
