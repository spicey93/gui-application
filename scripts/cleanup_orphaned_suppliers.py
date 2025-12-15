"""Script to clean up orphaned suppliers (suppliers with non-existent user_id)."""
import sys
import os

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.supplier import Supplier


def main():
    """Clean up orphaned suppliers."""
    supplier_model = Supplier()
    
    print("Cleaning up orphaned suppliers...")
    print("-" * 40)
    
    deleted_count = supplier_model.cleanup_orphaned_suppliers()
    
    if deleted_count > 0:
        print(f"\n✓ Cleaned up {deleted_count} orphaned supplier(s)")
    else:
        print("\n✓ No orphaned suppliers found")


if __name__ == "__main__":
    main()

