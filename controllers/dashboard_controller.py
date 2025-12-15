"""Dashboard controller."""
from typing import TYPE_CHECKING, Optional, Callable

if TYPE_CHECKING:
    from views.dashboard_view import DashboardView


class DashboardController:
    """Controller for dashboard functionality."""
    
    def __init__(self, dashboard_view: "DashboardView"):
        """Initialize the dashboard controller."""
        self.dashboard_view = dashboard_view
        self.dashboard_view.set_logout_callback(self.handle_logout)
        self.dashboard_view.set_suppliers_callback(self.handle_suppliers)
        self.on_logout: Optional[Callable[[], None]] = None
        self.on_suppliers: Optional[Callable[[], None]] = None
    
    def handle_logout(self):
        """Handle logout."""
        if self.on_logout:
            self.on_logout()
    
    def handle_suppliers(self):
        """Handle suppliers navigation."""
        if self.on_suppliers:
            self.on_suppliers()
    
    def set_logout_callback(self, callback: Callable[[], None]):
        """Set callback for logout."""
        self.on_logout = callback
    
    def set_suppliers_callback(self, callback: Callable[[], None]):
        """Set callback for suppliers navigation."""
        self.on_suppliers = callback

