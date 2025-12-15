"""Login view GUI."""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional


class LoginView:
    """Login window GUI."""
    
    def __init__(self, root: tk.Tk):
        """Initialize the login view."""
        self.root = root
        
        # Login callback
        self.login_callback: Optional[Callable[[str, str], None]] = None
        
        # Create container frame
        self.frame = ttk.Frame(self.root)
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create UI
        self._create_widgets()
    
    def _create_widgets(self):
        """Create and layout UI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.frame, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Username
        ttk.Label(main_frame, text="Username:").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        self.username_entry = ttk.Entry(main_frame, width=25)
        self.username_entry.grid(row=0, column=1, pady=5, padx=(10, 0))
        self.username_entry.focus()
        
        # Password
        ttk.Label(main_frame, text="Password:").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        self.password_entry = ttk.Entry(main_frame, width=25, show="*")
        self.password_entry.grid(row=1, column=1, pady=5, padx=(10, 0))
        
        # Bind Enter key to login
        self.password_entry.bind("<Return>", lambda e: self._handle_login())
        
        # Login button
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        self.login_button = ttk.Button(
            button_frame,
            text="Login",
            command=self._handle_login,
            width=15
        )
        self.login_button.pack()
        
        # Status label
        self.status_label = ttk.Label(
            main_frame,
            text="",
            foreground="red"
        )
        self.status_label.grid(row=3, column=0, columnspan=2, pady=5)
    
    def _handle_login(self):
        """Handle login button click."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            self.show_error("Please enter both username and password")
            return
        
        if self.login_callback:
            self.login_callback(username, password)
    
    def set_login_callback(self, callback: Callable[[str, str], None]):
        """Set the callback function for login attempts."""
        self.login_callback = callback
    
    def show_error(self, message: str):
        """Display an error message."""
        self.status_label.config(text=message, foreground="red")
        self.root.after(3000, lambda: self.status_label.config(text=""))
    
    def show_success(self, message: str):
        """Display a success message."""
        self.status_label.config(text=message, foreground="green")
    
    def clear_fields(self):
        """Clear the input fields."""
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self.username_entry.focus()
    
    def disable_login(self):
        """Disable the login button."""
        self.login_button.config(state="disabled")
    
    def enable_login(self):
        """Enable the login button."""
        self.login_button.config(state="normal")
    
    def show_success_dialog(self, message: str):
        """Show a success dialog."""
        messagebox.showinfo("Success", message)
    
    def show_error_dialog(self, message: str):
        """Show an error dialog."""
        messagebox.showerror("Error", message)
    
    def show(self):
        """Show the login view."""
        self.frame.grid()
        self.clear_fields()
    
    def hide(self):
        """Hide the login view."""
        self.frame.grid_remove()

