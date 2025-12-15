"""Script to delete all suppliers from the database."""
import sys
import os

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.supplier import Supplier


def main():
    """Delete all suppliers interactively."""
    supplier_model = Supplier()
    
    print("Delete all suppliers")
    print("-" * 30)
    
    # Confirm deletion
    confirm = input("Are you sure you want to delete ALL suppliers? (yes/no): ").strip().lower()
    
    if confirm != "yes":
        print("\n✗ Deletion cancelled")
        return
    
    try:
        import sqlite3
        conn = sqlite3.connect(supplier_model.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM suppliers")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("\n✓ No suppliers to delete")
            conn.close()
            return
        
        cursor.execute("DELETE FROM suppliers")
        conn.commit()
        conn.close()
        
        print(f"\n✓ Deleted {count} supplier(s)")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")


if __name__ == "__main__":
    main()

