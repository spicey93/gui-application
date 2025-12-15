"""Login controller."""
from typing import TYPE_CHECKING
from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from models.user import User
    from views.login_view import LoginView


class LoginController(QObject):
    """Controller for login functionality."""
    
    # Signal emitted on successful login with username and user_id
    login_success = Signal(str, int)
    
    def __init__(self, user_model: "User", login_view: "LoginView"):
        """Initialize the login controller."""
        super().__init__()
        self.user_model = user_model
        self.login_view = login_view
        
        # Connect view signal to controller handler
        self.login_view.login_attempted.connect(self.handle_login)
    
    def handle_login(self, username: str, password: str):
        """Handle login attempt."""
        self.login_view.disable_login()
        
        success, message, user_id = self.user_model.authenticate(username, password)
        
        if success:
            self.login_view.show_success(message)
            # Emit signal for successful login
            self.login_success.emit(username, user_id)
        else:
            self.login_view.show_error(message)
            self.login_view.clear_fields()
        
        self.login_view.enable_login()
