# GUI Login Application

A desktop application with login functionality, built using PySide6 (Qt) with Windows XP styling and comprehensive keyboard navigation support.

## Features

- Classic Windows XP desktop application styling
- Clean, simple login interface
- Dashboard/home page after successful login
- User authentication with password hashing
- Supplier management system
- SQLite database for local storage
- MVC (Model-View-Controller) architecture
- Full keyboard navigation support
- Unit tests for core functionality

## Requirements

- Python 3.8 or higher
- PySide6 (Qt for Python)

## Installation

1. Clone or download this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:

```bash
python main.py
```

## Keyboard Navigation

The application supports full keyboard-only navigation:

### Standard Navigation
- **Tab/Shift+Tab**: Navigate between interactive elements
- **Arrow Keys**: Navigate within lists/tables, move between menu items
- **Enter**: Activate focused button or confirm action
- **Escape**: Cancel dialogs, close windows

### Custom Keyboard Shortcuts
- **F1**: Navigate to Dashboard
- **F2**: Navigate to Suppliers
- **F3**: Navigate to Products
- **F4**: Navigate to Inventory
- **F5**: Navigate to Book Keeper
- **F6**: Navigate to Configuration
- **F7**: Logout
- **Ctrl+N**: Add new supplier (when in Suppliers view)
- **Ctrl+Enter**: Submit forms (login, create supplier, etc.)

## Testing

Run the test suite:

```bash
python -m pytest tests/
```

Or using unittest:

```bash
python -m unittest discover tests
```

## Project Structure

```
gui-app/
├── models/          # Data models
│   ├── __init__.py
│   ├── user.py     # User model with database operations
│   └── supplier.py # Supplier model with database operations
├── views/           # GUI views (PySide6/Qt widgets)
│   ├── __init__.py
│   ├── login_view.py  # Login window
│   ├── dashboard_view.py  # Dashboard/home page
│   └── suppliers_view.py  # Suppliers management
├── controllers/     # Business logic
│   ├── __init__.py
│   ├── login_controller.py  # Login controller
│   ├── dashboard_controller.py  # Dashboard controller
│   └── suppliers_controller.py  # Suppliers controller
├── styles/          # Styling
│   └── xp_theme.qss # Windows XP theme stylesheet
├── tests/           # Unit tests
│   ├── __init__.py
│   ├── test_user.py
│   └── test_supplier.py
├── data/            # Database storage (created automatically)
│   └── app.db
├── scripts/         # Utility scripts
│   ├── create_user.py
│   ├── delete_user.py
│   └── ...
├── main.py          # Application entry point
├── requirements.txt
└── README.md
```

## Usage Flow

1. **Login**: Enter your username and password to log in
2. **Dashboard**: After successful login, you'll be taken to the dashboard
3. **Suppliers**: Navigate to suppliers to manage your supplier list
4. **Logout**: Click the logout button or press F7 to return to the login screen

## Default Users

The application starts with no users. You can create users using the provided script:

```bash
python3 scripts/create_user.py
```

## Notes

- Passwords are hashed using SHA-256 before storage
- Database is stored in `data/app.db`
- Username must be at least 3 characters
- Password must be at least 4 characters
- The application uses Windows XP styling for a classic desktop feel
- All functionality is accessible via keyboard only

## Technology Stack

- **GUI Framework**: PySide6 (Qt for Python)
- **Database**: SQLite3
- **Architecture**: MVC (Model-View-Controller)
- **Styling**: Qt Style Sheets (QSS) with Windows XP theme
