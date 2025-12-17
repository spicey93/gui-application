"""Common dialog patterns and utilities."""
from PySide6.QtWidgets import QMessageBox, QWidget
from typing import Optional


def show_confirmation_dialog(
    parent: Optional[QWidget],
    title: str,
    message: str,
    detailed_message: Optional[str] = None
) -> bool:
    """
    Show a confirmation dialog (Yes/No).
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Main message text
        detailed_message: Optional detailed message
    
    Returns:
        True if user clicked Yes, False otherwise
    """
    reply = QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    return reply == QMessageBox.StandardButton.Yes


def show_success_message(
    parent: Optional[QWidget],
    message: str,
    title: str = "Success"
) -> None:
    """
    Show a success message dialog.
    
    Args:
        parent: Parent widget
        message: Success message text
        title: Dialog title (default: "Success")
    """
    QMessageBox.information(parent, title, message)


def show_error_message(
    parent: Optional[QWidget],
    message: str,
    title: str = "Error"
) -> None:
    """
    Show an error message dialog.
    
    Args:
        parent: Parent widget
        message: Error message text
        title: Dialog title (default: "Error")
    """
    QMessageBox.critical(parent, title, message)


def show_warning_message(
    parent: Optional[QWidget],
    message: str,
    title: str = "Warning"
) -> None:
    """
    Show a warning message dialog.
    
    Args:
        parent: Parent widget
        message: Warning message text
        title: Dialog title (default: "Warning")
    """
    QMessageBox.warning(parent, title, message)
