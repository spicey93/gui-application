"""Configuration view GUI."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFormLayout, QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from views.base_view import BaseTabbedView


class ConfigurationView(BaseTabbedView):
    """Configuration view GUI."""
    
    # Signals for API key operations
    api_key_save_requested = Signal(str, str)  # service_name, api_key
    api_key_load_requested = Signal()
    
    def __init__(self):
        """Initialize the configuration view."""
        super().__init__(title="Configuration", current_view="configuration")
        self._create_widgets()
        self._setup_keyboard_navigation()
    
    def _create_widgets(self) -> None:
        """Create and layout UI widgets."""
        # Create tabs
        self.create_tabs()
        
        # Add APIs tab
        apis_tab = self._create_apis_tab()
        self.add_tab(apis_tab, "APIs (Alt+1)", "Alt+1")
    
    def _create_apis_tab(self) -> QWidget:
        """Create the APIs configuration tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # UK Vehicle Data API section
        uk_vehicle_group = QGroupBox("UK Vehicle Data")
        uk_vehicle_layout = QFormLayout(uk_vehicle_group)
        uk_vehicle_layout.setSpacing(10)
        
        self.uk_vehicle_api_key_input = QLineEdit()
        self.uk_vehicle_api_key_input.setPlaceholderText("Enter your UK Vehicle Data API key")
        self.uk_vehicle_api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.uk_vehicle_api_key_input.setMinimumWidth(400)
        
        # Show/hide toggle button
        api_key_row = QHBoxLayout()
        api_key_row.addWidget(self.uk_vehicle_api_key_input)
        
        self.toggle_visibility_btn = QPushButton("Show")
        self.toggle_visibility_btn.setFixedWidth(60)
        self.toggle_visibility_btn.clicked.connect(self._toggle_api_key_visibility)
        api_key_row.addWidget(self.toggle_visibility_btn)
        
        uk_vehicle_layout.addRow("API Key:", api_key_row)
        
        # Info label
        info_label = QLabel(
            '<a href="https://ukvehicledata.co.uk/">Get an API key from UK Vehicle Data</a>'
        )
        info_label.setOpenExternalLinks(True)
        info_label.setStyleSheet("color: gray; font-size: 11px;")
        uk_vehicle_layout.addRow("", info_label)
        
        layout.addWidget(uk_vehicle_group)
        
        # Save button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_apis_btn = QPushButton("Save API Keys (Ctrl+S)")
        self.save_apis_btn.setMinimumWidth(150)
        self.save_apis_btn.clicked.connect(self._on_save_api_keys)
        button_layout.addWidget(self.save_apis_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        return tab
    
    def _toggle_api_key_visibility(self) -> None:
        """Toggle visibility of the API key input."""
        if self.uk_vehicle_api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.uk_vehicle_api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_visibility_btn.setText("Hide")
        else:
            self.uk_vehicle_api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_visibility_btn.setText("Show")
    
    def _on_save_api_keys(self) -> None:
        """Handle save API keys button click."""
        api_key = self.uk_vehicle_api_key_input.text().strip()
        self.api_key_save_requested.emit("uk_vehicle_data", api_key)
    
    def set_uk_vehicle_api_key(self, api_key: str) -> None:
        """Set the UK Vehicle Data API key in the input field."""
        self.uk_vehicle_api_key_input.setText(api_key or "")
    
    def show_message(self, title: str, message: str, is_error: bool = False) -> None:
        """Show a message dialog."""
        if is_error:
            QMessageBox.warning(self, title, message)
        else:
            QMessageBox.information(self, title, message)
    
    def _setup_keyboard_navigation(self) -> None:
        """Set up keyboard navigation."""
        from PySide6.QtGui import QShortcut, QKeySequence
        
        # Ctrl+S to save
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self._on_save_api_keys)
