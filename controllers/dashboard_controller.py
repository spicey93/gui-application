"""Dashboard controller."""
from typing import TYPE_CHECKING
from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from views.dashboard_view import DashboardView


class DashboardController(QObject):
    """Controller for dashboard functionality."""
    
    # Signals
    logout_requested = Signal()
    suppliers_requested = Signal()
    
    def __init__(self, dashboard_view: "DashboardView"):
        """Initialize the dashboard controller."""
        super().__init__()
        self.dashboard_view = dashboard_view
        
        # Connect view signals to controller
        self.dashboard_view.logout_requested.connect(self.handle_logout)
        self.dashboard_view.suppliers_requested.connect(self.handle_suppliers)
    
    def handle_logout(self):
        """Handle logout."""
        self.logout_requested.emit()
    
    def handle_suppliers(self):
        """Handle suppliers navigation."""
        self.suppliers_requested.emit()
