"""Supplier add/edit dialogs."""
from PySide6.QtCore import Signal
from views.widgets import DialogBuilder, FormFieldBuilder, show_error_message, show_confirmation_dialog
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


class SupplierDialogs:
    """Helper class for supplier dialogs."""
    
    def __init__(self, parent: "QWidget", create_signal: Signal, update_signal: Signal, delete_signal: Signal):
        """
        Initialize supplier dialogs helper.
        
        Args:
            parent: Parent widget
            create_signal: Signal to emit when creating a supplier
            update_signal: Signal to emit when updating a supplier
            delete_signal: Signal to emit when deleting a supplier
        """
        self.parent = parent
        self.create_signal = create_signal
        self.update_signal = update_signal
        self.delete_signal = delete_signal
    
    def show_add_dialog(self):
        """Show dialog for adding a new supplier."""
        dialog = DialogBuilder.create_dialog(self.parent, "Add Supplier", 500, 300)
        layout = DialogBuilder.create_layout(dialog)
        
        # Title
        DialogBuilder.add_title(layout, "Add New Supplier")
        
        # Account Number
        account_layout, account_entry = FormFieldBuilder.create_line_edit_field("Account Number:")
        layout.addLayout(account_layout)
        
        # Name
        name_layout, name_entry = FormFieldBuilder.create_line_edit_field("Name:")
        layout.addLayout(name_layout)
        
        # Status label
        status_label = DialogBuilder.add_status_label(layout)
        
        layout.addStretch()
        
        # Button layout
        def handle_save():
            acc_num = account_entry.text().strip()
            supplier_name = name_entry.text().strip()
            
            if not acc_num or not supplier_name:
                status_label.setText("Please fill in both fields")
                return
            
            self.create_signal.emit(acc_num, supplier_name)
            dialog.accept()
        
        button_layout = DialogBuilder.create_button_layout(
            save_callback=handle_save,
            save_text="Save (Ctrl+Enter)",
            dialog=dialog
        )
        layout.addLayout(button_layout)
        
        # Set focus to account entry
        account_entry.setFocus()
        
        # Show dialog
        dialog.exec()
    
    def show_edit_dialog(self, supplier_id: int, account_number: str, name: str):
        """Show dialog for editing a supplier."""
        dialog = DialogBuilder.create_dialog(self.parent, "Edit Supplier", 500, 300)
        layout = DialogBuilder.create_layout(dialog)
        
        # Title
        DialogBuilder.add_title(layout, "Edit Supplier")
        
        # Account Number
        account_layout, account_entry = FormFieldBuilder.create_line_edit_field(
            "Account Number:", account_number
        )
        layout.addLayout(account_layout)
        
        # Name
        name_layout, name_entry = FormFieldBuilder.create_line_edit_field("Name:", name)
        layout.addLayout(name_layout)
        
        # Status label
        status_label = DialogBuilder.add_status_label(layout)
        
        layout.addStretch()
        
        # Button layout
        def handle_save():
            acc_num = account_entry.text().strip()
            supplier_name = name_entry.text().strip()
            
            if not acc_num or not supplier_name:
                status_label.setText("Please fill in both fields")
                return
            
            self.update_signal.emit(supplier_id, acc_num, supplier_name)
            dialog.accept()
        
        def handle_delete():
            if show_confirmation_dialog(dialog, "Confirm Delete", f"Are you sure you want to delete supplier '{name_entry.text()}'?"):
                self.delete_signal.emit(supplier_id)
                dialog.accept()
        
        button_layout = DialogBuilder.create_button_layout(
            save_callback=handle_save,
            save_text="Save (Ctrl+Enter)",
            delete_callback=handle_delete,
            delete_text="Delete (Ctrl+Shift+D)",
            dialog=dialog
        )
        layout.addLayout(button_layout)
        
        # Set focus to account entry
        account_entry.setFocus()
        account_entry.selectAll()
        
        # Show dialog
        dialog.exec()

