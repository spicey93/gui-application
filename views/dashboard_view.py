"""Dashboard view GUI."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QDateEdit, QMessageBox, QDialog
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QShortcut, QKeySequence
from views.base_view import BaseTabbedView
from utils.styles import apply_theme


class DashboardView(BaseTabbedView):
    """Dashboard/home page GUI."""
    
    # Additional signals beyond base class
    cash_up_requested = Signal(str, str)  # start_date, end_date
    
    def __init__(self):
        """Initialize the dashboard view."""
        super().__init__(title="Dashboard", current_view="dashboard")
        self.current_username: str = ""
        self._create_widgets()
        self._setup_keyboard_navigation()
    
    def _create_widgets(self):
        """Create and layout UI widgets."""
        # Add Cash Up button at the top using base class method
        self.cash_up_button = self.add_action_button(
            "Cash Up",
            self._handle_cash_up,
            None
        )
        
        # Create tabs widget
        self.tab_widget = self.create_tabs()
        
        # Tab 1: Overview (placeholder)
        overview_widget = QWidget()
        overview_layout = QVBoxLayout(overview_widget)
        overview_layout.setSpacing(20)
        overview_layout.setContentsMargins(20, 20, 20, 20)
        
        self.welcome_label = QLabel("Welcome!")
        self.welcome_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        overview_layout.addWidget(self.welcome_label)
        
        self.user_info_label = QLabel("")
        self.user_info_label.setStyleSheet("font-size: 12px;")
        overview_layout.addWidget(self.user_info_label)
        
        overview_layout.addSpacing(20)
        
        info_label = QLabel("You have successfully logged in.")
        info_label.setStyleSheet("font-size: 12px;")
        overview_layout.addWidget(info_label)
        
        placeholder_label = QLabel("Dashboard overview content goes here...")
        placeholder_label.setStyleSheet("font-size: 10px; color: gray;")
        overview_layout.addWidget(placeholder_label)
        
        overview_layout.addStretch()
        
        self.add_tab(overview_widget, "Overview (Ctrl+1)", "Ctrl+1")
        
        # Tab 2: Recent Activity (placeholder)
        activity_widget = QWidget()
        activity_layout = QVBoxLayout(activity_widget)
        activity_layout.setSpacing(20)
        activity_layout.setContentsMargins(20, 20, 20, 20)
        
        activity_title = QLabel("Recent Activity")
        activity_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        activity_layout.addWidget(activity_title)
        
        activity_placeholder = QLabel("Recent transactions and activity will appear here...")
        activity_placeholder.setStyleSheet("font-size: 10px; color: gray;")
        activity_layout.addWidget(activity_placeholder)
        
        activity_layout.addStretch()
        
        self.add_tab(activity_widget, "Recent Activity (Ctrl+2)", "Ctrl+2")
        
        # Tab 3: Summary (placeholder)
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)
        summary_layout.setSpacing(20)
        summary_layout.setContentsMargins(20, 20, 20, 20)
        
        summary_title = QLabel("Summary")
        summary_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        summary_layout.addWidget(summary_title)
        
        summary_placeholder = QLabel("Financial summary and statistics will appear here...")
        summary_placeholder.setStyleSheet("font-size: 10px; color: gray;")
        summary_layout.addWidget(summary_placeholder)
        
        summary_layout.addStretch()
        
        self.add_tab(summary_widget, "Summary (Ctrl+3)", "Ctrl+3")
        
        # Set first tab as default
        self.tab_widget.setCurrentIndex(0)
    
    def _setup_keyboard_navigation(self):
        """Set up keyboard navigation."""
        # Navigation panel handles its own keyboard navigation
        pass
    
    def set_username(self, username: str):
        """Set the current username and update display."""
        self.current_username = username
        if hasattr(self, 'welcome_label'):
            self.welcome_label.setText(f"Welcome, {username}!")
        if hasattr(self, 'user_info_label'):
            self.user_info_label.setText(f"Logged in as: {username}")
    
    def _handle_cash_up(self):
        """Handle cash up button click - open cash up dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Cash Up Card Payments")
        dialog.setModal(True)
        dialog.setMinimumSize(500, 250)
        dialog.resize(500, 250)
        apply_theme(dialog)
        
        # Add Escape key shortcut for cancel
        esc_shortcut = QShortcut(QKeySequence("Escape"), dialog)
        esc_shortcut.activated.connect(dialog.reject)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("Cash Up Card Payments")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        info_label = QLabel("Move card payments from Undeposited Funds to Bank account for a selected date range.")
        info_label.setStyleSheet("font-size: 11px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addSpacing(10)
        
        # Date range selection
        date_range_layout = QHBoxLayout()
        date_range_layout.setSpacing(10)
        
        start_date_label = QLabel("From Date:")
        start_date_label.setMinimumWidth(100)
        start_date_label.setStyleSheet("font-size: 11px;")
        date_range_layout.addWidget(start_date_label)
        
        start_date_edit = QDateEdit()
        start_date_edit.setCalendarPopup(True)
        start_date_edit.setDate(QDate.currentDate().addDays(-1))  # Default to yesterday
        start_date_edit.setStyleSheet("font-size: 11px;")
        date_range_layout.addWidget(start_date_edit, stretch=1)
        
        layout.addLayout(date_range_layout)
        
        end_date_layout = QHBoxLayout()
        end_date_layout.setSpacing(10)
        
        end_date_label = QLabel("To Date:")
        end_date_label.setMinimumWidth(100)
        end_date_label.setStyleSheet("font-size: 11px;")
        end_date_layout.addWidget(end_date_label)
        
        end_date_edit = QDateEdit()
        end_date_edit.setCalendarPopup(True)
        end_date_edit.setDate(QDate.currentDate().addDays(-1))  # Default to yesterday
        end_date_edit.setStyleSheet("font-size: 11px;")
        end_date_layout.addWidget(end_date_edit, stretch=1)
        
        layout.addLayout(end_date_layout)
        
        layout.addStretch()
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        def handle_cash_up():
            start_date = start_date_edit.date().toPython()
            end_date = end_date_edit.date().toPython()
            
            if start_date > end_date:
                QMessageBox.warning(dialog, "Invalid Date Range", "Start date must be before or equal to end date.")
                return
            
            dialog.accept()
            self.cash_up_requested.emit(start_date.isoformat(), end_date.isoformat())
        
        cash_up_btn = QPushButton("Cash Up (Ctrl+Enter)")
        cash_up_btn.setMinimumWidth(150)
        cash_up_btn.setMinimumHeight(30)
        cash_up_btn.setDefault(True)
        cash_up_btn.clicked.connect(handle_cash_up)
        
        # Ctrl+Enter shortcut for cash up
        ctrl_enter_shortcut = QShortcut(QKeySequence("Ctrl+Return"), dialog)
        ctrl_enter_shortcut.activated.connect(handle_cash_up)
        button_layout.addWidget(cash_up_btn)
        
        cancel_btn = QPushButton("Cancel (Esc)")
        cancel_btn.setMinimumWidth(120)
        cancel_btn.setMinimumHeight(30)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Set focus to start date
        start_date_edit.setFocus()
        
        # Show dialog
        dialog.exec()
    
    def show_success_dialog(self, message: str):
        """Show a success dialog."""
        QMessageBox.information(self, "Success", message)
    
    def show_error_dialog(self, message: str):
        """Show an error dialog."""
        QMessageBox.critical(self, "Error", message)
