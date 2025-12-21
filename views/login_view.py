"""Login view GUI."""
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent


class LoginView(QWidget):
    """Login window GUI."""
    
    # Signal emitted when login is attempted
    login_attempted = Signal(str, str)
    
    def __init__(self):
        """Initialize the login view."""
        super().__init__()
        self._create_widgets()
        self._setup_keyboard_navigation()
    
    def _create_widgets(self):
        """Create and layout UI widgets."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Username
        username_label = QLabel("Username:")
        layout.addWidget(username_label)
        
        self.username_entry = QLineEdit()
        self.username_entry.setPlaceholderText("Enter username")
        self.username_entry.setMinimumHeight(25)
        layout.addWidget(self.username_entry)
        
        # Password
        password_label = QLabel("Password:")
        layout.addWidget(password_label)
        
        self.password_entry = QLineEdit()
        self.password_entry.setPlaceholderText("Enter password")
        self.password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_entry.setMinimumHeight(25)
        layout.addWidget(self.password_entry)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: red; font-size: 10px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setMinimumHeight(20)
        layout.addWidget(self.status_label)
        
        # Login button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.login_button = QPushButton("Login (Enter)")
        self.login_button.setMinimumWidth(140)
        self.login_button.setMinimumHeight(30)
        self.login_button.setDefault(True)  # Makes it respond to Enter key
        self.login_button.clicked.connect(self._handle_login)
        button_layout.addWidget(self.login_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        # Autofill in dev mode
        if self._is_dev_mode():
            self.username_entry.setText("user1")
            self.password_entry.setText("password1")
            # Set focus to password entry so user can just press Enter
            self.password_entry.setFocus()
        else:
            # Set focus to username entry
            self.username_entry.setFocus()
    
    def _is_dev_mode(self) -> bool:
        """Check if running in development mode."""
        # First check environment variable
        env_value = os.getenv("DEV_MODE", "")
        if env_value.lower() in ("1", "true", "yes"):
            return True
        
        # Then check .env file
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            if "=" in line:
                                key, value = line.split("=", 1)
                                key = key.strip()
                                value = value.strip().strip('"').strip("'")
                                if key == "DEV_MODE" and value.lower() in ("1", "true", "yes"):
                                    return True
            except Exception:
                pass
        
        return False
    
    def _setup_keyboard_navigation(self):
        """Set up keyboard navigation."""
        # Tab order is automatically handled by Qt based on widget creation order
        # Enter key on both username and password fields triggers login
        self.username_entry.returnPressed.connect(self._handle_login)
        self.password_entry.returnPressed.connect(self._handle_login)
    
    def _handle_login(self):
        """Handle login button click or Enter key."""
        username = self.username_entry.text().strip()
        password = self.password_entry.text()
        
        if not username or not password:
            self.show_error("Please enter both username and password")
            return
        
        self.login_attempted.emit(username, password)
    
    def show_error(self, message: str):
        """Display an error message."""
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: red;")
        # Clear after 3 seconds
        from PySide6.QtCore import QTimer
        QTimer.singleShot(3000, lambda: self.status_label.setText(""))
    
    def show_success(self, message: str):
        """Display a success message."""
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: green;")
    
    def clear_fields(self):
        """Clear the input fields."""
        self.username_entry.clear()
        self.password_entry.clear()
        self.username_entry.setFocus()
        self.status_label.clear()
    
    def disable_login(self):
        """Disable the login button."""
        self.login_button.setEnabled(False)
    
    def enable_login(self):
        """Enable the login button."""
        self.login_button.setEnabled(True)
    
    def show_success_dialog(self, message: str):
        """Show a success dialog."""
        QMessageBox.information(self, "Success", message)
    
    def show_error_dialog(self, message: str):
        """Show an error dialog."""
        QMessageBox.critical(self, "Error", message)
