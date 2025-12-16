"""Reusable navigation panel widget."""
from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QShortcut, QKeySequence


class NavigationPanel(QFrame):
    """Reusable navigation panel for all views."""
    
    # Signals
    dashboard_requested = Signal()
    suppliers_requested = Signal()
    products_requested = Signal()
    inventory_requested = Signal()
    bookkeeper_requested = Signal()
    configuration_requested = Signal()
    logout_requested = Signal()
    
    def __init__(self, current_view: str = "dashboard"):
        """
        Initialize the navigation panel.
        
        Args:
            current_view: The current view name to highlight (dashboard, suppliers, products, configuration)
        """
        super().__init__()
        self.current_view = current_view
        self._create_widgets()
        self._setup_keyboard_navigation()
    
    def _create_widgets(self):
        """Create and layout UI widgets."""
        self.setObjectName("navPanel")
        self.setFixedWidth(240)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        
        nav_layout = QVBoxLayout(self)
        nav_layout.setSpacing(10)
        nav_layout.setContentsMargins(15, 15, 15, 15)
        
        # Navigation title
        nav_title = QLabel("Navigation")
        nav_title.setObjectName("navTitle")
        nav_layout.addWidget(nav_title)
        
        nav_layout.addSpacing(10)
        
        # Dashboard menu item
        self.dashboard_button = QPushButton("Dashboard (F1)")
        self.dashboard_button.setObjectName("navButton")
        self.dashboard_button.setMinimumHeight(30)
        self.dashboard_button.clicked.connect(self._handle_dashboard)
        nav_layout.addWidget(self.dashboard_button)
        
        # Suppliers menu item
        self.suppliers_button = QPushButton("Suppliers (F2)")
        self.suppliers_button.setObjectName("navButton")
        self.suppliers_button.setMinimumHeight(30)
        self.suppliers_button.clicked.connect(self._handle_suppliers)
        nav_layout.addWidget(self.suppliers_button)
        
        # Products menu item
        self.products_button = QPushButton("Products (F3)")
        self.products_button.setObjectName("navButton")
        self.products_button.setMinimumHeight(30)
        self.products_button.clicked.connect(self._handle_products)
        nav_layout.addWidget(self.products_button)
        
        # Inventory menu item
        self.inventory_button = QPushButton("Inventory (F4)")
        self.inventory_button.setObjectName("navButton")
        self.inventory_button.setMinimumHeight(30)
        self.inventory_button.clicked.connect(self._handle_inventory)
        nav_layout.addWidget(self.inventory_button)
        
        # Book Keeper menu item
        self.bookkeeper_button = QPushButton("Book Keeper (F5)")
        self.bookkeeper_button.setObjectName("navButton")
        self.bookkeeper_button.setMinimumHeight(30)
        self.bookkeeper_button.clicked.connect(self._handle_bookkeeper)
        nav_layout.addWidget(self.bookkeeper_button)
        
        # Configuration menu item
        self.config_button = QPushButton("Configuration (F6)")
        self.config_button.setObjectName("navButton")
        self.config_button.setMinimumHeight(30)
        self.config_button.clicked.connect(self._handle_configuration)
        nav_layout.addWidget(self.config_button)
        
        nav_layout.addSpacing(15)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        nav_layout.addWidget(separator)
        
        nav_layout.addSpacing(15)
        
        # Logout menu item
        self.logout_button = QPushButton("Logout (F7)")
        self.logout_button.setObjectName("navButton")
        self.logout_button.setMinimumHeight(30)
        self.logout_button.clicked.connect(self._handle_logout)
        nav_layout.addWidget(self.logout_button)
        
        nav_layout.addStretch()
        
        # Update highlighting based on current view
        self._update_highlighting()
    
    def _setup_keyboard_navigation(self):
        """Set up keyboard navigation."""
        # Tab order: Dashboard -> Suppliers -> Products -> Inventory -> Book Keeper -> Configuration -> Logout
        self.setTabOrder(self.dashboard_button, self.suppliers_button)
        self.setTabOrder(self.suppliers_button, self.products_button)
        self.setTabOrder(self.products_button, self.inventory_button)
        self.setTabOrder(self.inventory_button, self.bookkeeper_button)
        self.setTabOrder(self.bookkeeper_button, self.config_button)
        self.setTabOrder(self.config_button, self.logout_button)
        
        # Arrow keys for navigation panel
        self.dashboard_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.suppliers_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.products_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.inventory_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.bookkeeper_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.config_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.logout_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Note: F key shortcuts are handled by the main window (main.py)
        # to ensure they work globally regardless of focus
    
    def _handle_dashboard(self):
        """Handle dashboard button click."""
        if self.current_view != "dashboard":
            self.dashboard_requested.emit()
    
    def _handle_suppliers(self):
        """Handle suppliers button click."""
        if self.current_view != "suppliers":
            self.suppliers_requested.emit()
    
    def _handle_products(self):
        """Handle products button click."""
        if self.current_view != "products":
            self.products_requested.emit()
    
    def _handle_inventory(self):
        """Handle inventory button click."""
        if self.current_view != "inventory":
            self.inventory_requested.emit()
    
    def _handle_bookkeeper(self):
        """Handle bookkeeper button click."""
        if self.current_view != "bookkeeper":
            self.bookkeeper_requested.emit()
    
    def _handle_configuration(self):
        """Handle configuration button click."""
        if self.current_view != "configuration":
            self.configuration_requested.emit()
    
    def _handle_logout(self):
        """Handle logout button click."""
        self.logout_requested.emit()
    
    def set_current_view(self, view_name: str):
        """
        Update the current view indicator.
        
        Args:
            view_name: The current view name (dashboard, suppliers, products, inventory, configuration)
        """
        self.current_view = view_name
        self._update_highlighting()
    
    def _update_highlighting(self):
        """Update button highlighting based on current view."""
        # Reset all buttons
        buttons = {
            "dashboard": self.dashboard_button,
            "suppliers": self.suppliers_button,
            "products": self.products_button,
            "inventory": self.inventory_button,
            "bookkeeper": self.bookkeeper_button,
            "configuration": self.config_button
        }
        
        for view_name, button in buttons.items():
            if view_name == self.current_view:
                button.setProperty("active", "true")
            else:
                button.setProperty("active", "false")
            # Force style update by unpolishing and repolishing
            style = button.style()
            if style:
                style.unpolish(button)
                style.polish(button)
                button.update()

