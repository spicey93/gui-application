"""Login controller."""
from typing import TYPE_CHECKING, Optional, Callable

if TYPE_CHECKING:
    from models.user import User
    from views.login_view import LoginView


class LoginController:
    """Controller for login functionality."""
    
    def __init__(self, user_model: "User", login_view: "LoginView"):
        """Initialize the login controller."""
        self.user_model = user_model
        self.login_view = login_view
        self.login_view.set_login_callback(self.handle_login)
        self.on_login_success: Optional[Callable[[str], None]] = None
    
    def handle_login(self, username: str, password: str):
        """Handle login attempt."""
        self.login_view.disable_login()
        
        success, message, user_id = self.user_model.authenticate(username, password)
        
        if success:
            self.login_view.show_success(message)
            # Navigate to dashboard
            if self.on_login_success:
                self.on_login_success(username, user_id)
        else:
            self.login_view.show_error(message)
            self.login_view.clear_fields()
        
        self.login_view.enable_login()
    
    def set_login_success_callback(self, callback: Callable[[str, int], None]):
        """Set callback for successful login."""
        self.on_login_success = callback

