"""Dialog builder utilities for creating consistent dialogs."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence
from typing import Optional, Callable
from utils.styles import apply_theme


class DialogBuilder:
    """Helper class for building consistent dialogs."""
    
    # Standard sizes
    DEFAULT_WIDTH = 500
    DEFAULT_HEIGHT = 400
    LARGE_WIDTH = 600
    LARGE_HEIGHT = 500
    
    # Standard button sizes
    BUTTON_MIN_WIDTH = 140
    BUTTON_MIN_HEIGHT = 30
    BUTTON_MIN_WIDTH_LARGE = 200
    
    @staticmethod
    def create_dialog(
        parent: Optional[QWidget],
        title: str,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        modal: bool = True
    ) -> QDialog:
        """
        Create and configure a basic dialog.
        
        Args:
            parent: Parent widget
            title: Window title
            width: Dialog width
            height: Dialog height
            modal: Whether dialog is modal
        
        Returns:
            Configured QDialog instance
        """
        dialog = QDialog(parent)
        dialog.setWindowTitle(title)
        dialog.setModal(modal)
        dialog.setMinimumSize(width, height)
        dialog.resize(width, height)
        apply_theme(dialog)
        
        # Add Escape key shortcut for cancel
        esc_shortcut = QShortcut(QKeySequence("Escape"), dialog)
        esc_shortcut.activated.connect(dialog.reject)
        
        return dialog
    
    @staticmethod
    def create_layout(
        dialog: QDialog,
        spacing: int = 20,
        margins: tuple[int, int, int, int] = (30, 30, 30, 30)
    ) -> QVBoxLayout:
        """
        Create and set a vertical layout for the dialog.
        
        Args:
            dialog: The dialog widget
            spacing: Layout spacing
            margins: Layout margins (left, top, right, bottom)
        
        Returns:
            QVBoxLayout instance
        """
        layout = QVBoxLayout(dialog)
        layout.setSpacing(spacing)
        layout.setContentsMargins(*margins)
        return layout
    
    @staticmethod
    def add_title(
        layout: QVBoxLayout,
        title_text: str,
        font_size: str = "16px"
    ) -> QLabel:
        """
        Add a title label to the layout.
        
        Args:
            layout: The layout to add to
            title_text: Title text
            font_size: Font size for title
        
        Returns:
            QLabel instance
        """
        title_label = QLabel(title_text)
        title_label.setStyleSheet(f"font-size: {font_size}; font-weight: bold;")
        layout.addWidget(title_label)
        return title_label
    
    @staticmethod
    def create_button_layout(
        save_callback: Optional[Callable] = None,
        save_text: str = "Save (Ctrl+Enter)",
        save_shortcut: str = "Ctrl+Return",
        delete_callback: Optional[Callable] = None,
        delete_text: str = "Delete (Ctrl+Shift+D)",
        delete_shortcut: str = "Ctrl+Shift+D",
        cancel_callback: Optional[Callable] = None,
        cancel_text: str = "Cancel (Esc)",
        dialog: Optional[QDialog] = None
    ) -> QHBoxLayout:
        """
        Create a button layout with Save, Delete (optional), and Cancel buttons.
        
        Args:
            save_callback: Callback for save button
            save_text: Text for save button
            save_shortcut: Keyboard shortcut for save
            delete_callback: Optional callback for delete button
            delete_text: Text for delete button
            delete_shortcut: Keyboard shortcut for delete
            cancel_callback: Callback for cancel (defaults to dialog.reject)
            cancel_text: Text for cancel button
            dialog: Dialog instance for shortcuts (required if using shortcuts)
        
        Returns:
            QHBoxLayout with buttons
        """
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Save button
        if save_callback:
            save_btn = QPushButton(save_text)
            save_btn.setMinimumWidth(DialogBuilder.BUTTON_MIN_WIDTH_LARGE if "Changes" in save_text else DialogBuilder.BUTTON_MIN_WIDTH)
            save_btn.setMinimumHeight(DialogBuilder.BUTTON_MIN_HEIGHT)
            save_btn.setDefault(True)
            save_btn.clicked.connect(save_callback)
            
            # Add shortcut if dialog provided
            if dialog and save_shortcut:
                save_shortcut_obj = QShortcut(QKeySequence(save_shortcut), dialog)
                save_shortcut_obj.activated.connect(save_callback)
            
            button_layout.addWidget(save_btn)
        
        # Delete button
        if delete_callback:
            delete_btn = QPushButton(delete_text)
            delete_btn.setMinimumWidth(DialogBuilder.BUTTON_MIN_WIDTH_LARGE + 20)
            delete_btn.setMinimumHeight(DialogBuilder.BUTTON_MIN_HEIGHT)
            delete_btn.clicked.connect(delete_callback)
            
            # Add shortcut if dialog provided
            if dialog and delete_shortcut:
                delete_shortcut_obj = QShortcut(QKeySequence(delete_shortcut), dialog)
                delete_shortcut_obj.activated.connect(delete_callback)
            
            button_layout.addWidget(delete_btn)
        
        # Cancel button
        cancel_btn = QPushButton(cancel_text)
        cancel_btn.setMinimumWidth(DialogBuilder.BUTTON_MIN_WIDTH)
        cancel_btn.setMinimumHeight(DialogBuilder.BUTTON_MIN_HEIGHT)
        
        if cancel_callback:
            cancel_btn.clicked.connect(cancel_callback)
        elif dialog:
            cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addWidget(cancel_btn)
        
        return button_layout
    
    @staticmethod
    def add_status_label(layout: QVBoxLayout) -> QLabel:
        """
        Add a status label for error messages.
        
        Args:
            layout: The layout to add to
        
        Returns:
            QLabel instance for status messages
        """
        status_label = QLabel("")
        status_label.setStyleSheet("color: red; font-size: 9px;")
        layout.addWidget(status_label)
        return status_label

