"""Clear database and create a single test user - no data seeding."""
import os
import sys
import sqlite3
from pathlib import Path
from typing import Tuple, Optional, List, Dict

# Add parent directory to path to import models
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.user import User
from models.supplier import Supplier
from models.customer import Customer
from models.product import Product
from models.product_type import ProductType
from models.invoice import Invoice
from models.invoice_item import InvoiceItem
from models.payment import Payment
from models.payment_allocation import PaymentAllocation
from models.nominal_account import NominalAccount
from models.journal_entry import JournalEntry
from models.sales_invoice import SalesInvoice
from models.sales_invoice_item import SalesInvoiceItem
from models.customer_payment import CustomerPayment
from models.customer_payment_allocation import CustomerPaymentAllocation
from models.service import Service
from models.tyre import Tyre
from models.vehicle import Vehicle
from models.api_key import ApiKey


def backup_tyres(db_path: str) -> List[Dict]:
    """
    Backup all tyres from the database before clearing.
    
    Args:
        db_path: Path to the database file
        
    Returns:
        List of tyre dictionaries
    """
    if not os.path.exists(db_path):
        return []
    
    try:
        with sqlite3.connect(db_path, timeout=10.0) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Check if tyres table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='tyres'
            """)
            if not cursor.fetchone():
                return []
            
            # Get all tyres
            cursor.execute("SELECT * FROM tyres")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        print(f"Warning: Could not backup tyres: {str(e)}")
        return []


def restore_tyres(db_path: str, tyres_backup: List[Dict]) -> int:
    """
    Restore tyres to the database after clearing.
    
    Args:
        db_path: Path to the database file
        tyres_backup: List of tyre dictionaries to restore
        
    Returns:
        Number of tyres restored
    """
    if not tyres_backup:
        return 0
    
    try:
        with sqlite3.connect(db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            
            # Insert each tyre (excluding the id column so new IDs are auto-generated)
            restored_count = 0
            for tyre in tyres_backup:
                try:
                    cursor.execute("""
                        INSERT INTO tyres (
                            description, width, profile, diameter, speed_rating, load_index,
                            pattern, oe_fitment, ean, manufacturer_code, brand, model,
                            product_type, vehicle_type, rolling_resistance, wet_grip,
                            noise_class, noise_performance, vehicle_class,
                            created_date, updated_date, tyre_url, brand_url, run_flat
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        tyre.get('description', ''),
                        tyre.get('width', ''),
                        tyre.get('profile', ''),
                        tyre.get('diameter', ''),
                        tyre.get('speed_rating', ''),
                        tyre.get('load_index', ''),
                        tyre.get('pattern', ''),
                        tyre.get('oe_fitment', ''),
                        tyre.get('ean', ''),
                        tyre.get('manufacturer_code', ''),
                        tyre.get('brand', ''),
                        tyre.get('model', ''),
                        tyre.get('product_type', ''),
                        tyre.get('vehicle_type', ''),
                        tyre.get('rolling_resistance', ''),
                        tyre.get('wet_grip', ''),
                        tyre.get('noise_class', ''),
                        tyre.get('noise_performance', ''),
                        tyre.get('vehicle_class', ''),
                        tyre.get('created_date', ''),
                        tyre.get('updated_date', ''),
                        tyre.get('tyre_url', ''),
                        tyre.get('brand_url', ''),
                        tyre.get('run_flat', '')
                    ))
                    restored_count += 1
                except Exception as e:
                    print(f"Warning: Could not restore tyre: {str(e)}")
            
            conn.commit()
            return restored_count
    except Exception as e:
        print(f"Warning: Could not restore tyres: {str(e)}")
        return 0


def clear_database(db_path: str = "data/app.db") -> dict:
    """
    Completely clear the database by deleting it and recreating all tables.
    
    Args:
        db_path: Path to the database file
        
    Returns:
        Dictionary of initialized model instances
    """
    # Delete database file if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Deleted existing database: {db_path}")
    
    # Ensure directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        print(f"Created database directory: {db_dir}")
    
    # Initialize all models (this will create the tables)
    print("Initializing database tables...")
    models = {
        'user': User(db_path),
        'supplier': Supplier(db_path),
        'customer': Customer(db_path),
        'product': Product(db_path),
        'product_type': ProductType(db_path),
        'invoice': Invoice(db_path),
        'invoice_item': InvoiceItem(db_path),
        'payment': Payment(db_path),
        'payment_allocation': PaymentAllocation(db_path),
        'nominal_account': NominalAccount(db_path),
        'journal_entry': JournalEntry(db_path),
        'sales_invoice': SalesInvoice(db_path),
        'sales_invoice_item': SalesInvoiceItem(db_path),
        'customer_payment': CustomerPayment(db_path),
        'customer_payment_allocation': CustomerPaymentAllocation(db_path),
        'service': Service(db_path),
        'tyre': Tyre(db_path),
        'vehicle': Vehicle(db_path),
        'api_key': ApiKey(db_path),
    }
    
    print("Database tables initialized successfully!")
    return models


def create_default_chart_of_accounts(nominal_account_model: NominalAccount, user_id: int) -> int:
    """
    Create default chart of accounts for a UK small business.
    
    Args:
        nominal_account_model: NominalAccount model instance
        user_id: User ID to create accounts for
        
    Returns:
        Number of accounts created successfully
    """
    # Define accounts with: code, name, category, subtype
    accounts = [
        # Assets (1000-1999)
        (1100, "Sales Ledger", "Asset", "Sales Ledger"),
        (1102, "Undeposited Funds", "Asset", "Cash Account"),
        (1200, "Stock Asset", "Asset", "Stock Asset"),
        (1201, "Stock Asset (Back Order)", "Asset", "Stock Asset"),
        (1300, "Bank Account", "Asset", "Bank Account"),
        
        # Liabilities (2000-2999)
        (2100, "Purchase Ledger", "Liability", "Purchase Ledger"),
        (2101, "Input VAT", "Liability", "Current Liability"),
        (2102, "Output VAT", "Liability", "Current Liability"),
        (2103, "VAT Ledger", "Liability", "VAT Ledger"),
        (2104, "Other creditors", "Liability", "Current Liability"),
        (2105, "NI & PAYE Liability", "Liability", "Current Liability"),
        (2200, "Directors Loan Account", "Liability", "Current Liability"),
        
        # Equity (3000-3999)
        (3000, "Opening Balances", "Equity", "Equity"),
        (3100, "Retained Earnings", "Equity", "Equity"),
        
        # Income (4000-4999)
        (4000, "Sales (Products)", "Income", "Turnover"),
        (4100, "Sales (Services)", "Income", "Turnover"),
        (4200, "Stock Adjustment (Gain)", "Income", "Other Income"),
        (4300, "Purchase Cost Differences", "Income", "Other Income"),
        
        # Expenses (5000-5999)
        (5000, "Cost of Sales", "Expense", "Cost of Sales"),
        (5100, "Stock Adjustment (Loss)", "Expense", "Expenses"),
        (5200, "Salary", "Expense", "Expenses"),
        (5300, "Employer NI", "Expense", "Expenses"),
        (5400, "Employee Payroll", "Expense", "Expenses"),
        (5500, "Back Orders", "Expense", "Expenses"),
        
        # Additional standard UK small business accounts
        # Assets
        (1400, "Petty Cash", "Asset", "Cash Account"),
        (1500, "Prepayments", "Asset", "Prepayments"),
        (1600, "Fixed Assets", "Asset", "Fixed Asset"),
        
        # Liabilities
        (2300, "Long Term Loans", "Liability", "Long-Term Liability"),
        (2400, "Accruals", "Liability", "Current Liability"),
        
        # Income
        (4400, "Discounts Received", "Income", "Other Income"),
        (4500, "Interest Received", "Income", "Other Operating Income"),
        
        # Expenses
        (5600, "Rent", "Expense", "Expenses"),
        (5700, "Utilities", "Expense", "Expenses"),
        (5800, "Insurance", "Expense", "Expenses"),
        (5900, "Professional Fees", "Expense", "Expenses"),
        (5950, "Travel & Subsistence", "Expense", "Expenses"),
        (5960, "Office Expenses", "Expense", "Expenses"),
        (5970, "Depreciation", "Expense", "Depreciation"),
        (5980, "Discounts Allowed", "Expense", "Expenses"),
        (5990, "Bad Debts", "Expense", "Expenses"),
    ]
    
    created_count = 0
    failed_count = 0
    
    for code, name, category, subtype in accounts:
        # Determine is_bank_account based on category and subtype
        is_bank = (category == "Asset" and subtype == "Bank Account")
        
        success, message, account_id = nominal_account_model.create(
            account_code=code,
            account_name=name,
            account_type=category,
            account_subtype=subtype,
            opening_balance=0.0,
            is_bank_account=is_bank,
            user_id=user_id
        )
        
        if success:
            created_count += 1
        else:
            failed_count += 1
            print(f"  Warning: Failed to create account '{name}': {message}")
    
    return created_count


def create_test_user(user_model: User, username: str = "test", password: str = "test") -> Tuple[bool, str, Optional[int]]:
    """
    Create a single test user.
    
    Args:
        user_model: User model instance
        username: Username for the test user (default: "test")
        password: Password for the test user (default: "test")
        
    Returns:
        Tuple of (success: bool, message: str, user_id: int | None)
    """
    success, message = user_model.create_user(username, password)
    if success:
        _, _, user_id = user_model.authenticate(username, password)
        return True, message, user_id
    return False, message, None


def main():
    """Main function to clear the database and create a test user."""
    print("=" * 60)
    print("Database Clear Script")
    print("=" * 60)
    
    db_path = "data/app.db"
    
    # Confirm before proceeding
    response = input(f"\nThis will DELETE the database at '{db_path}' and recreate it.\n"
                     "Only a single test user will be created (username: test, password: test).\n"
                     "No other data will be seeded.\n\n"
                     "Are you sure you want to continue? (yes/no): ")
    
    if response.lower() not in ['yes', 'y']:
        print("Operation cancelled.")
        return
    
    try:
        # Backup tyres before clearing
        print("\nBacking up tyres...")
        tyres_backup = backup_tyres(db_path)
        tyre_count = len(tyres_backup)
        if tyre_count > 0:
            print(f"  ✓ Backed up {tyre_count} tyres")
        else:
            print("  No tyres to backup")
        
        # Clear database and initialize tables
        models = clear_database(db_path)
        
        # Restore tyres after clearing
        if tyre_count > 0:
            print("\nRestoring tyres...")
            restored_count = restore_tyres(db_path, tyres_backup)
            if restored_count > 0:
                print(f"  ✓ Restored {restored_count} tyres")
            else:
                print("  ✗ Failed to restore tyres")
        
        # Create test user
        print("\nCreating test user...")
        success, message, user_id = create_test_user(models['user'])
        
        if success:
            print(f"  ✓ {message}")
            print(f"  Username: test")
            print(f"  Password: test")
            print(f"  User ID: {user_id}")
        else:
            print(f"  ✗ Failed to create test user: {message}")
            sys.exit(1)
        
        # Create default chart of accounts
        print("\nCreating default chart of accounts...")
        account_count = create_default_chart_of_accounts(models['nominal_account'], user_id)
        print(f"  ✓ Created {account_count} accounts")
        
        print("\n" + "=" * 60)
        print("✓ Database cleared and test user created successfully!")
        if tyre_count > 0:
            print(f"✓ {tyre_count} tyres preserved")
        print("=" * 60)
        print("\nYou can now test the application with:")
        print("  Username: test")
        print("  Password: test")
        
    except Exception as e:
        print(f"\n✗ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

