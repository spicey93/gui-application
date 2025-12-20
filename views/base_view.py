"""Base view class for consistent layout across the application."""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QPushButton, QTabWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QShortcut, QKeySequence
from typing import List, Optional, Dict
from views.navigation_panel import NavigationPanel


class BaseTabbedView(QWidget):
    """
    Base class for views with consistent layout: navigation panel, title, action buttons, and tabs.
    
    Provides a standard layout pattern:
    - Navigation panel on the left
    - Content area on the right with:
      - Title and action buttons at the top
      - Tabs widget underneath (optional)
      - Content in tabs or directly in content area
    """
    
    # Standard navigation signals
    dashboard_requested = Signal()
    suppliers_requested = Signal()
    customers_requested = Signal()
    products_requested = Signal()
    inventory_requested = Signal()
    bookkeeper_requested = Signal()
    vehicles_requested = Signal()
    services_requested = Signal()
    configuration_requested = Signal()
    logout_requested = Signal()
    
    def __init__(self, title: str, current_view: str):
        """
        Initialize the base tabbed view.
        
        Args:
            title: The title to display at the top
            current_view: The current view name for navigation highlighting
        """
        super().__init__()
        self._title = title
        self._current_view = current_view
        self._action_buttons: List[QPushButton] = []
        self._tab_shortcuts: Dict[int, QShortcut] = {}
        self._create_base_layout()
    
    def _create_base_layout(self):
        """Create the base layout structure."""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Navigation panel (left sidebar)
        self.nav_panel = NavigationPanel(current_view=self._current_view)
        self.nav_panel.dashboard_requested.connect(self._handle_dashboard)
        self.nav_panel.suppliers_requested.connect(self._handle_suppliers)
        self.nav_panel.customers_requested.connect(self._handle_customers)
        self.nav_panel.products_requested.connect(self._handle_products)
        self.nav_panel.inventory_requested.connect(self._handle_inventory)
        self.nav_panel.bookkeeper_requested.connect(self._handle_bookkeeper)
        self.nav_panel.vehicles_requested.connect(self._handle_vehicles)
        self.nav_panel.services_requested.connect(self._handle_services)
        self.nav_panel.configuration_requested.connect(self._handle_configuration)
        self.nav_panel.logout_requested.connect(self._handle_logout)
        
        # Add navigation panel to main layout
        main_layout.addWidget(self.nav_panel)
        
        # Content area (right side)
        self.content_frame = QWidget()
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setSpacing(20)
        self.content_layout.setContentsMargins(40, 40, 40, 40)
        
        # Title and action buttons at the top
        self.title_layout = QHBoxLayout()
        self.title_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_label = QLabel(self._title)
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.title_layout.addWidget(self.title_label)
        
        self.title_layout.addStretch()
        
        # Tabs widget (optional, created when first tab is added)
        self.tab_widget: Optional[QTabWidget] = None
        
        # Add title layout to content layout
        self.content_layout.addLayout(self.title_layout)
        
        # Add content area to main layout
        main_layout.addWidget(self.content_frame, stretch=1)
    
    def add_action_button(self, text: str, callback, shortcut: Optional[str] = None) -> QPushButton:
        """
        Add an action button to the title bar.
        
        Args:
            text: Button text (should include shortcut in parentheses if shortcut is provided)
            callback: Callback function to call when button is clicked
            shortcut: Optional keyboard shortcut (e.g., "Ctrl+N")
        
        Returns:
            The created QPushButton instance
        """
        button = QPushButton(text)
        button.setMinimumWidth(180)
        button.setMinimumHeight(30)
        button.clicked.connect(callback)
        self.title_layout.addWidget(button)
        self._action_buttons.append(button)
        
        # Add keyboard shortcut if provided
        if shortcut:
            shortcut_obj = QShortcut(QKeySequence(shortcut), self)
            shortcut_obj.activated.connect(callback)
        
        return button
    
    def create_tabs(self) -> QTabWidget:
        """
        Create and return a QTabWidget for tabbed content.
        Should be called before adding content if tabs are needed.
        
        Returns:
            The created QTabWidget instance
        """
        if self.tab_widget is None:
            self.tab_widget = QTabWidget()
            # Align tabs to the left
            self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
            self.tab_widget.setElideMode(Qt.TextElideMode.ElideNone)
            self.tab_widget.setTabBarAutoHide(False)
            
            # Add tabs widget to content layout (after title, before any other content)
            # Insert at position 1 (after title_layout which is at 0)
            self.content_layout.insertWidget(1, self.tab_widget, stretch=1)
        
        return self.tab_widget
    
    def add_tab(self, widget: QWidget, title: str, shortcut: Optional[str] = None) -> int:
        """
        Add a tab to the tab widget.
        
        Args:
            widget: The widget to add as tab content
            title: Tab title (should include shortcut in parentheses if shortcut is provided)
            shortcut: Optional keyboard shortcut (e.g., "Ctrl+1")
        
        Returns:
            The index of the added tab
        """
        if self.tab_widget is None:
            self.create_tabs()
        
        tab_index = self.tab_widget.addTab(widget, title)
        
        # Add keyboard shortcut if provided
        if shortcut:
            shortcut_obj = QShortcut(QKeySequence(shortcut), self)
            shortcut_obj.activated.connect(lambda idx=tab_index: self.tab_widget.setCurrentIndex(idx))
            self._tab_shortcuts[tab_index] = shortcut_obj
        
        return tab_index
    
    def get_content_layout(self) -> QVBoxLayout:
        """
        Get the main content layout for adding widgets directly (when not using tabs).
        
        Returns:
            The QVBoxLayout for the content area
        """
        return self.content_layout
    
    def get_tab_widget(self) -> Optional[QTabWidget]:
        """
        Get the tab widget if it has been created.
        
        Returns:
            The QTabWidget or None if tabs haven't been created
        """
        return self.tab_widget
    
    def _handle_dashboard(self):
        """Handle dashboard button click."""
        self.dashboard_requested.emit()
    
    def _handle_suppliers(self):
        """Handle suppliers button click."""
        self.suppliers_requested.emit()
    
    def _handle_customers(self):
        """Handle customers button click."""
        self.customers_requested.emit()
    
    def _handle_products(self):
        """Handle products button click."""
        self.products_requested.emit()
    
    def _handle_inventory(self):
        """Handle inventory button click."""
        self.inventory_requested.emit()
    
    def _handle_bookkeeper(self):
        """Handle bookkeeper button click."""
        self.bookkeeper_requested.emit()
    
    def _handle_vehicles(self):
        """Handle vehicles button click."""
        self.vehicles_requested.emit()
    
    def _handle_services(self):
        """Handle services button click."""
        self.services_requested.emit()
    
    def _handle_configuration(self):
        """Handle configuration button click."""
        self.configuration_requested.emit()
    
    def _handle_logout(self):
        """Handle logout button click."""
        self.logout_requested.emit()

