# GUI Login Application

A simple Python GUI application with login functionality, built using tkinter and SQLite.

## Features

- Clean, simple login interface
- Dashboard/home page after successful login
- User authentication with password hashing
- SQLite database for local storage
- MVC (Model-View-Controller) architecture
- Unit tests for core functionality

## Requirements

- Python 3.6 or higher
- tkinter (usually included with Python)

## Installation

1. Clone or download this repository
2. No external dependencies required - uses only Python standard library

## Usage

Run the application:

```bash
python main.py
```

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
│   └── user.py     # User model with database operations
├── views/           # GUI views
│   ├── __init__.py
│   ├── login_view.py  # Login window
│   └── dashboard_view.py  # Dashboard/home page
├── controllers/     # Business logic
│   ├── __init__.py
│   ├── login_controller.py  # Login controller
│   └── dashboard_controller.py  # Dashboard controller
├── tests/           # Unit tests
│   ├── __init__.py
│   └── test_user.py
├── data/            # Database storage (created automatically)
│   └── app.db
├── main.py          # Application entry point
├── requirements.txt
└── README.md
```

## Usage Flow

1. **Login**: Enter your username and password to log in
2. **Dashboard**: After successful login, you'll be taken to the dashboard
3. **Logout**: Click the logout button to return to the login screen

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
