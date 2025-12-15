"""Script to delete a user from the database."""
import sys
import os

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user import User


def main():
    """Delete a user interactively."""
    user_model = User()
    
    print("Delete a user")
    print("-" * 30)
    
    username = input("Username to delete: ").strip()
    
    if not username:
        print("\n✗ Username is required")
        return
    
    # Confirm deletion
    confirm = input(f"Are you sure you want to delete user '{username}'? (yes/no): ").strip().lower()
    
    if confirm != "yes":
        print("\n✗ Deletion cancelled")
        return
    
    success, message = user_model.delete_user(username)
    
    if success:
        print(f"\n✓ {message}")
    else:
        print(f"\n✗ {message}")


if __name__ == "__main__":
    main()
