"""Suppliers view GUI."""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional, List, Dict


class SuppliersView:
    """Suppliers management GUI."""
    
    def __init__(self, root: tk.Tk):
        """Initialize the suppliers view."""
        self.root = root
        
        # Callbacks
        self.dashboard_callback: Optional[Callable[[], None]] = None
        self.logout_callback: Optional[Callable[[], None]] = None
        self.create_callback: Optional[Callable[[str, str], None]] = None
        self.update_callback: Optional[Callable[[int, str, str], None]] = None
        self.delete_callback: Optional[Callable[[int], None]] = None
        self.refresh_callback: Optional[Callable[[], None]] = None
        
        # Current editing supplier ID (None when creating new)
        self.editing_supplier_id: Optional[int] = None
        
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
        
        # Navigation panel (left sidebar) - same as dashboard
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
        
        # Content container with scrollable area
        content_container = ttk.Frame(content_frame)
        content_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        content_container.columnconfigure(0, weight=1)
        content_container.rowconfigure(1, weight=1)
        
        # Title and Add Supplier button
        title_frame = ttk.Frame(content_container)
        title_frame.grid(row=0, column=0, pady=(0, 20), sticky=(tk.W, tk.E))
        title_frame.columnconfigure(0, weight=1)
        
        title_label = ttk.Label(
            title_frame,
            text="Suppliers",
            font=("Arial", 24, "bold")
        )
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        self.add_supplier_button = ttk.Button(
            title_frame,
            text="Add Supplier",
            command=self._handle_add_supplier,
            width=15
        )
        self.add_supplier_button.grid(row=0, column=1, sticky=tk.E)
        
        # Suppliers list frame
        list_frame = ttk.LabelFrame(content_container, text="Suppliers List", padding="10")
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Treeview for suppliers list
        columns = ("ID", "Account Number", "Name")
        self.suppliers_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        # Configure columns
        self.suppliers_tree.heading("ID", text="ID")
        self.suppliers_tree.heading("Account Number", text="Account Number")
        self.suppliers_tree.heading("Name", text="Name")
        
        self.suppliers_tree.column("ID", width=50, anchor=tk.CENTER)
        self.suppliers_tree.column("Account Number", width=150, anchor=tk.W)
        self.suppliers_tree.column("Name", width=200, anchor=tk.W)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.suppliers_tree.yview)
        self.suppliers_tree.configure(yscrollcommand=scrollbar.set)
        
        self.suppliers_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Bind double-click event to show supplier details
        self.suppliers_tree.bind("<Double-1>", self._on_double_click)
    
    def _handle_dashboard(self):
        """Handle dashboard button click."""
        if self.dashboard_callback:
            self.dashboard_callback()
    
    def _handle_suppliers(self):
        """Handle suppliers button click."""
        # Already on suppliers page
        pass
    
    def _handle_logout(self):
        """Handle logout button click."""
        if self.logout_callback:
            self.logout_callback()
    
    
    def _on_supplier_select(self, event):
        """Handle supplier selection in treeview."""
        # Selection is now only used for double-click functionality
        pass
    
    def _on_double_click(self, event):
        """Handle double-click on supplier in treeview - opens details window."""
        selection = self.suppliers_tree.selection()
        if not selection:
            return
        
        item = self.suppliers_tree.item(selection[0])
        supplier_id = int(item['values'][0])
        account_number = item['values'][1]
        name = item['values'][2]
        
        self._show_supplier_details(supplier_id, account_number, name)
    
    def _handle_add_supplier(self):
        """Handle Add Supplier button click - opens window for adding new supplier."""
        self._show_supplier_form_window()
    
    def _show_supplier_details(self, supplier_id: int, account_number: str, name: str):
        """Show supplier details in a popup window with tabs."""
        # Create a new top-level window
        details_window = tk.Toplevel(self.root)
        details_window.title("Supplier Details")
        details_window.geometry("600x500")
        details_window.resizable(False, False)
        
        # Center the window
        details_window.update_idletasks()
        x = (details_window.winfo_screenwidth() // 2) - (600 // 2)
        y = (details_window.winfo_screenheight() // 2) - (500 // 2)
        details_window.geometry(f"600x500+{x}+{y}")
        
        # Make window modal
        details_window.transient(self.root)
        details_window.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(details_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="Supplier Information",
            font=("Arial", 20, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Info tab
        info_frame = ttk.Frame(notebook, padding="30")
        notebook.add(info_frame, text="Info")
        info_frame.columnconfigure(1, weight=1)
        
        # Supplier ID (read-only)
        ttk.Label(info_frame, text="ID:", font=("Arial", 12, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=15, padx=(0, 20)
        )
        id_label = ttk.Label(info_frame, text=str(supplier_id), font=("Arial", 12))
        id_label.grid(row=0, column=1, sticky=tk.W, pady=15)
        
        # Account Number (editable)
        ttk.Label(info_frame, text="Account Number:", font=("Arial", 12, "bold")).grid(
            row=1, column=0, sticky=tk.W, pady=15, padx=(0, 20)
        )
        account_entry = ttk.Entry(info_frame, width=30, font=("Arial", 12))
        account_entry.insert(0, account_number)
        account_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=15)
        
        # Name (editable)
        ttk.Label(info_frame, text="Name:", font=("Arial", 12, "bold")).grid(
            row=2, column=0, sticky=tk.W, pady=15, padx=(0, 20)
        )
        name_entry = ttk.Entry(info_frame, width=30, font=("Arial", 12))
        name_entry.insert(0, name)
        name_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=15)
        
        # Actions tab
        actions_frame = ttk.Frame(notebook, padding="30")
        notebook.add(actions_frame, text="Actions")
        
        # Delete button in Actions tab
        delete_btn = ttk.Button(
            actions_frame,
            text="Delete Supplier",
            command=lambda: self._delete_from_details_window(details_window, supplier_id, name),
            width=20
        )
        delete_btn.pack(pady=20)
        
        # Save Changes button at the bottom
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        def handle_save():
            new_account_number = account_entry.get().strip()
            new_name = name_entry.get().strip()
            
            if not new_account_number or not new_name:
                messagebox.showerror("Error", "Please fill in both account number and name")
                return
            
            if self.update_callback:
                self.update_callback(supplier_id, new_account_number, new_name)
            
            details_window.destroy()
        
        save_btn = ttk.Button(
            button_frame,
            text="Save Changes",
            command=handle_save,
            width=20
        )
        save_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = ttk.Button(
            button_frame,
            text="Cancel",
            command=details_window.destroy,
            width=20
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)
    
    def _delete_from_details_window(self, details_window: tk.Toplevel, supplier_id: int, supplier_name: str):
        """Handle delete from details window."""
        # Confirm deletion
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete supplier '{supplier_name}'?"):
            details_window.destroy()
            if self.delete_callback:
                self.delete_callback(supplier_id)
    
    def _show_supplier_form_window(self, supplier_id: Optional[int] = None, account_number: str = "", name: str = ""):
        """Show a window for adding or editing a supplier."""
        is_editing = supplier_id is not None
        
        # Create a new top-level window
        form_window = tk.Toplevel(self.root)
        form_window.title("Edit Supplier" if is_editing else "Add Supplier")
        form_window.geometry("500x300")
        form_window.resizable(False, False)
        
        # Center the window
        form_window.update_idletasks()
        x = (form_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (form_window.winfo_screenheight() // 2) - (300 // 2)
        form_window.geometry(f"500x300+{x}+{y}")
        
        # Make window modal
        form_window.transient(self.root)
        form_window.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(form_window, padding="30")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_text = "Edit Supplier" if is_editing else "Add New Supplier"
        title_label = ttk.Label(
            main_frame,
            text=title_text,
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 30), sticky=tk.W)
        
        # Account Number
        ttk.Label(main_frame, text="Account Number:", font=("Arial", 11)).grid(
            row=1, column=0, sticky=tk.W, pady=10, padx=(0, 15)
        )
        account_entry = ttk.Entry(main_frame, width=30, font=("Arial", 11))
        account_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=10)
        if account_number:
            account_entry.insert(0, account_number)
        
        # Name
        ttk.Label(main_frame, text="Name:", font=("Arial", 11)).grid(
            row=2, column=0, sticky=tk.W, pady=10, padx=(0, 15)
        )
        name_entry = ttk.Entry(main_frame, width=30, font=("Arial", 11))
        name_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=10)
        if name:
            name_entry.insert(0, name)
        
        # Status label
        status_label = ttk.Label(main_frame, text="", font=("Arial", 9))
        status_label.grid(row=3, column=0, columnspan=2, pady=(10, 0))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(20, 0))
        
        def handle_save():
            acc_num = account_entry.get().strip()
            supplier_name = name_entry.get().strip()
            
            if not acc_num or not supplier_name:
                status_label.config(text="Please fill in both fields", foreground="red")
                return
            
            if is_editing:
                if self.update_callback:
                    self.update_callback(supplier_id, acc_num, supplier_name)
            else:
                if self.create_callback:
                    self.create_callback(acc_num, supplier_name)
            
            form_window.destroy()
        
        # Save button
        save_btn = ttk.Button(
            button_frame,
            text="Save",
            command=handle_save,
            width=15
        )
        save_btn.pack(side=tk.LEFT, padx=5)
        
        # Cancel button
        cancel_btn = ttk.Button(
            button_frame,
            text="Cancel",
            command=form_window.destroy,
            width=15
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # Focus on first entry
        account_entry.focus()
        
        # Configure column weights
        main_frame.columnconfigure(1, weight=1)
    
    def set_dashboard_callback(self, callback: Callable[[], None]):
        """Set the callback function for dashboard navigation."""
        self.dashboard_callback = callback
    
    def set_logout_callback(self, callback: Callable[[], None]):
        """Set the callback function for logout."""
        self.logout_callback = callback
    
    def set_create_callback(self, callback: Callable[[str, str], None]):
        """Set the callback function for creating a supplier."""
        self.create_callback = callback
    
    def set_update_callback(self, callback: Callable[[int, str, str], None]):
        """Set the callback function for updating a supplier."""
        self.update_callback = callback
    
    def set_delete_callback(self, callback: Callable[[int], None]):
        """Set the callback function for deleting a supplier."""
        self.delete_callback = callback
    
    def set_refresh_callback(self, callback: Callable[[], None]):
        """Set the callback function for refreshing the suppliers list."""
        self.refresh_callback = callback
    
    def load_suppliers(self, suppliers: List[Dict[str, any]]):
        """Load suppliers into the treeview."""
        # Clear existing items
        for item in self.suppliers_tree.get_children():
            self.suppliers_tree.delete(item)
        
        # Add suppliers
        for supplier in suppliers:
            self.suppliers_tree.insert(
                "",
                tk.END,
                values=(
                    supplier['id'],
                    supplier['account_number'],
                    supplier['name']
                )
            )
    
    def show_success(self, message: str):
        """Display a success message."""
        self.show_success_dialog(message)
    
    def show_error(self, message: str):
        """Display an error message."""
        self.show_error_dialog(message)
    
    def show_success_dialog(self, message: str):
        """Show a success dialog."""
        messagebox.showinfo("Success", message)
    
    def show_error_dialog(self, message: str):
        """Show an error dialog."""
        messagebox.showerror("Error", message)
    
    def show(self):
        """Show the suppliers view."""
        self.frame.grid()
    
    def hide(self):
        """Hide the suppliers view."""
        self.frame.grid_remove()

