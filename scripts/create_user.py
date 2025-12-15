"""Script to create a user in the database."""
import sys
import os

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user import User


def main():
    """Create a user interactively."""
    user_model = User()
    
    print("Create a new user")
    print("-" * 30)
    
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    
    success, message = user_model.create_user(username, password)
    
    if success:
        print(f"\n✓ {message}")
    else:
        print(f"\n✗ {message}")


if __name__ == "__main__":
    main()

