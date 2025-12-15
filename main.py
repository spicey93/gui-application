"""Main entry point for the GUI application."""
import tkinter as tk
from typing import Optional
from models.user import User
from models.supplier import Supplier
from views.login_view import LoginView
from views.dashboard_view import DashboardView
from views.suppliers_view import SuppliersView
from controllers.login_controller import LoginController
from controllers.dashboard_controller import DashboardController
from controllers.suppliers_controller import SuppliersController


class Application:
    """Main application class to manage views and navigation."""
    
    def __init__(self):
        """Initialize the application."""
        # Create root window
        self.root = tk.Tk()
        self.root.title("Login")
        self.root.geometry("350x200")
        self.root.resizable(False, False)
        
        # Configure root grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Center the window
        self._center_window()
        
        # Initialize models
        self.user_model = User()
        self.supplier_model = Supplier()
        
        # Current user ID (None until login)
        self.current_user_id: Optional[int] = None
        
        # Initialize views
        self.login_view = LoginView(self.root)
        self.dashboard_view = DashboardView(self.root)
        self.suppliers_view = SuppliersView(self.root)
        
        # Show login view initially
        self.login_view.show()
        
        # Initialize controllers (suppliers controller will be recreated on login)
        self.login_controller = LoginController(self.user_model, self.login_view)
        self.dashboard_controller = DashboardController(self.dashboard_view)
        self.suppliers_controller = None
        
        # Set up navigation callbacks
        self.login_controller.set_login_success_callback(self.on_login_success)
        self.dashboard_controller.set_logout_callback(self.on_logout)
        self.dashboard_controller.set_suppliers_callback(self.on_suppliers)
    
    def _center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def on_login_success(self, username: str, user_id: int):
        """Handle successful login."""
        # Store current user ID
        self.current_user_id = user_id
        
        # Initialize or update suppliers controller with user_id
        if self.suppliers_controller is None:
            self.suppliers_controller = SuppliersController(self.suppliers_view, self.supplier_model, user_id)
            self.suppliers_controller.set_dashboard_callback(self.on_back_to_dashboard)
            self.suppliers_controller.set_logout_callback(self.on_logout)
        else:
            self.suppliers_controller.set_user_id(user_id)
        
        # Update window for dashboard
        self.root.title("Dashboard")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        self._center_window()
        
        # Switch views
        self.login_view.hide()
        self.dashboard_view.set_username(username)
        self.dashboard_view.show()
    
    def on_suppliers(self):
        """Handle navigation to suppliers."""
        # Refresh suppliers for current user
        if self.suppliers_controller:
            self.suppliers_controller.refresh_suppliers()
        # Hide dashboard and show suppliers
        self.dashboard_view.hide()
        self.suppliers_view.show()
    
    def on_back_to_dashboard(self):
        """Handle navigation back to dashboard."""
        # Hide suppliers and show dashboard
        self.suppliers_view.hide()
        self.dashboard_view.show()
    
    def on_logout(self):
        """Handle logout."""
        # Update window for login
        self.root.title("Login")
        self.root.geometry("350x200")
        self.root.resizable(False, False)
        self._center_window()
        
        # Switch views - hide all and show login
        self.dashboard_view.hide()
        self.suppliers_view.hide()
        self.login_view.show()
    
    def run(self):
        """Run the application."""
        self.root.mainloop()


def main():
    """Initialize and run the application."""
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
