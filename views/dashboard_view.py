"""Dashboard view GUI."""
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class DashboardView:
    """Dashboard/home page GUI."""
    
    def __init__(self, root: tk.Tk):
        """Initialize the dashboard view."""
        self.root = root
        
        # Callbacks
        self.logout_callback: Optional[Callable[[], None]] = None
        self.suppliers_callback: Optional[Callable[[], None]] = None
        
        # Current username
        self.current_username: Optional[str] = None
        
        # Create container frame (initially hidden)
        self.frame = ttk.Frame(self.root)
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.frame.grid_remove()
        
        # Create UI
        self._create_widgets()
    
    def _create_widgets(self):
        """Create and layout UI widgets."""
        # Configure grid weights
        self.frame.columnconfigure(0, weight=0)  # Navigation panel (fixed width)
        self.frame.columnconfigure(1, weight=1)  # Content area (expands)
        self.frame.rowconfigure(0, weight=1)
        
        # Navigation panel (left sidebar)
        nav_panel = ttk.Frame(self.frame, padding="10")
        nav_panel.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 2))
        nav_panel.configure(relief="raised", borderwidth=1)
        
        # Navigation title
        nav_title = ttk.Label(
            nav_panel,
            text="Navigation",
            font=("Arial", 12, "bold")
        )
        nav_title.grid(row=0, column=0, pady=(0, 20), sticky=tk.W)
        
        # Dashboard menu item
        self.dashboard_button = ttk.Button(
            nav_panel,
            text="Dashboard",
            command=self._handle_dashboard,
            width=18
        )
        self.dashboard_button.grid(row=1, column=0, pady=5, sticky=(tk.W, tk.E))
        
        # Suppliers menu item
        self.suppliers_button = ttk.Button(
            nav_panel,
            text="Suppliers",
            command=self._handle_suppliers,
            width=18
        )
        self.suppliers_button.grid(row=2, column=0, pady=5, sticky=(tk.W, tk.E))
        
        # Separator
        nav_separator = ttk.Separator(nav_panel, orient="horizontal")
        nav_separator.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=15)
        
        # Logout menu item
        self.logout_button = ttk.Button(
            nav_panel,
            text="Logout",
            command=self._handle_logout,
            width=18
        )
        self.logout_button.grid(row=4, column=0, pady=5, sticky=(tk.W, tk.E))
        
        # Configure navigation panel column
        nav_panel.columnconfigure(0, weight=1)
        
        # Content area (right side)
        content_frame = ttk.Frame(self.frame, padding="30")
        content_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        # Content container
        content_container = ttk.Frame(content_frame)
        content_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        content_container.columnconfigure(0, weight=1)
        
        # Welcome label
        self.welcome_label = ttk.Label(
            content_container,
            text="Welcome!",
            font=("Arial", 24, "bold")
        )
        self.welcome_label.grid(row=0, column=0, pady=(0, 20), sticky=tk.W)
        
        # User info
        self.user_info_label = ttk.Label(
            content_container,
            text="",
            font=("Arial", 10)
        )
        self.user_info_label.grid(row=1, column=0, pady=(0, 30), sticky=tk.W)
        
        # Separator
        separator = ttk.Separator(content_container, orient="horizontal")
        separator.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=20)
        
        # Dashboard content
        info_label = ttk.Label(
            content_container,
            text="You have successfully logged in.",
            font=("Arial", 12)
        )
        info_label.grid(row=3, column=0, pady=20, sticky=tk.W)
        
        # Placeholder for future dashboard content
        placeholder_label = ttk.Label(
            content_container,
            text="Dashboard content goes here...",
            font=("Arial", 10),
            foreground="gray"
        )
        placeholder_label.grid(row=4, column=0, pady=10, sticky=tk.W)
    
    def _handle_dashboard(self):
        """Handle dashboard button click."""
        # Dashboard is already shown, but this allows for future navigation logic
        pass
    
    def _handle_suppliers(self):
        """Handle suppliers button click."""
        if self.suppliers_callback:
            self.suppliers_callback()
    
    def _handle_logout(self):
        """Handle logout button click."""
        if self.logout_callback:
            self.logout_callback()
    
    def set_logout_callback(self, callback: Callable[[], None]):
        """Set the callback function for logout."""
        self.logout_callback = callback
    
    def set_suppliers_callback(self, callback: Callable[[], None]):
        """Set the callback function for suppliers navigation."""
        self.suppliers_callback = callback
    
    def set_username(self, username: str):
        """Set the current username and update display."""
        self.current_username = username
        self.welcome_label.config(text=f"Welcome, {username}!")
        self.user_info_label.config(text=f"Logged in as: {username}")
    
    def show(self):
        """Show the dashboard view."""
        self.frame.grid()
    
    def hide(self):
        """Hide the dashboard view."""
        self.frame.grid_remove()

