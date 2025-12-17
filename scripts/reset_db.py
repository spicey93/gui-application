"""Comprehensive database reset script - removes everything and creates two users with full data."""
import os
import sys
from pathlib import Path
from datetime import date, timedelta

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


def reset_database(db_path: str = "data/app.db"):
    """Completely reset the database by deleting it and recreating tables."""
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
    user_model = User(db_path)
    supplier_model = Supplier(db_path)
    customer_model = Customer(db_path)
    product_model = Product(db_path)
    product_type_model = ProductType(db_path)
    invoice_model = Invoice(db_path)
    invoice_item_model = InvoiceItem(db_path)
    payment_model = Payment(db_path)
    payment_allocation_model = PaymentAllocation(db_path)
    nominal_account_model = NominalAccount(db_path)
    journal_entry_model = JournalEntry(db_path)
    
    print("Database reset complete!")
    return {
        'user': user_model,
        'supplier': supplier_model,
        'customer': customer_model,
        'product': product_model,
        'product_type': product_type_model,
        'invoice': invoice_model,
        'invoice_item': invoice_item_model,
        'payment': payment_model,
        'payment_allocation': payment_allocation_model,
        'nominal_account': nominal_account_model,
        'journal_entry': journal_entry_model
    }


def seed_default_accounts(nominal_account_model: NominalAccount, user_id: int):
    """Seed default UK nominal accounts for a user."""
    default_accounts = [
        # Assets (1000-1999)
        (1000, "Bank Account - Current", "Asset", 0.0, True),
        (1001, "Bank Account - Savings", "Asset", 0.0, True),
        (1002, "Petty Cash", "Asset", 0.0, False),
        (1100, "Accounts Receivable", "Asset", 0.0, False),
        (1200, "Stock/Inventory", "Asset", 0.0, False),
        (1300, "Fixed Assets - Equipment", "Asset", 0.0, False),
        (1301, "Fixed Assets - Vehicles", "Asset", 0.0, False),
        (1302, "Fixed Assets - Furniture", "Asset", 0.0, False),
        (1400, "Prepayments", "Asset", 0.0, False),
        
        # Liabilities (2000-2999)
        (2000, "Accounts Payable", "Liability", 0.0, False),
        (2100, "VAT Payable", "Liability", 0.0, False),
        (2200, "PAYE Payable", "Liability", 0.0, False),
        (2201, "NI Payable", "Liability", 0.0, False),
        (2300, "Loans - Short Term", "Liability", 0.0, False),
        (2400, "Loans - Long Term", "Liability", 0.0, False),
        (2500, "Credit Cards", "Liability", 0.0, False),
        (2600, "Accruals", "Liability", 0.0, False),
        
        # Equity (3000-3999)
        (3000, "Capital", "Equity", 0.0, False),
        (3100, "Retained Earnings", "Equity", 0.0, False),
        (3200, "Current Year Profit", "Equity", 0.0, False),
        (3300, "Drawings", "Equity", 0.0, False),
        
        # Income (4000-4999)
        (4000, "Sales", "Income", 0.0, False),
        (4001, "Sales - Services", "Income", 0.0, False),
        (4100, "Other Income", "Income", 0.0, False),
        (4101, "Interest Income", "Income", 0.0, False),
        (4200, "Discounts Received", "Income", 0.0, False),
        
        # Expenses (5000-5999)
        (5000, "Cost of Sales", "Expense", 0.0, False),
        (5001, "Purchases", "Expense", 0.0, False),
        (5100, "Rent", "Expense", 0.0, False),
        (5101, "Rates", "Expense", 0.0, False),
        (5102, "Utilities - Electricity", "Expense", 0.0, False),
        (5103, "Utilities - Gas", "Expense", 0.0, False),
        (5104, "Utilities - Water", "Expense", 0.0, False),
        (5105, "Telephone", "Expense", 0.0, False),
        (5106, "Internet", "Expense", 0.0, False),
        (5200, "Wages & Salaries", "Expense", 0.0, False),
        (5201, "Employer NI", "Expense", 0.0, False),
        (5202, "Pension Contributions", "Expense", 0.0, False),
        (5300, "Insurance", "Expense", 0.0, False),
        (5301, "Professional Fees", "Expense", 0.0, False),
        (5302, "Accountancy Fees", "Expense", 0.0, False),
        (5303, "Legal Fees", "Expense", 0.0, False),
        (5400, "Travel Expenses", "Expense", 0.0, False),
        (5401, "Motor Expenses", "Expense", 0.0, False),
        (5402, "Subsistence", "Expense", 0.0, False),
        (5500, "Office Expenses", "Expense", 0.0, False),
        (5501, "Stationery", "Expense", 0.0, False),
        (5502, "Postage", "Expense", 0.0, False),
        (5503, "Printing", "Expense", 0.0, False),
        (5600, "Marketing & Advertising", "Expense", 0.0, False),
        (5601, "Website Costs", "Expense", 0.0, False),
        (5700, "Depreciation", "Expense", 0.0, False),
        (5800, "Bad Debts", "Expense", 0.0, False),
        (5900, "Bank Charges", "Expense", 0.0, False),
        (5901, "Interest Paid", "Expense", 0.0, False),
        (5999, "Other Expenses", "Expense", 0.0, False),
    ]
    
    success_count = 0
    for account_code, account_name, account_type, opening_balance, is_bank_account in default_accounts:
        success, message, account_id = nominal_account_model.create(
            account_code, account_name, account_type, opening_balance, 
            is_bank_account, user_id
        )
        if success:
            success_count += 1
        else:
            print(f"    ✗ Failed to create account {account_code}: {message}")
    
    return success_count


def seed_user_data(models: dict, username: str, password: str, user_id: int):
    """Seed all data for a single user."""
    print(f"\n  Seeding data for user: {username}")
    
    # Product Types
    print("    Creating product types...")
    product_types = ["Electronics", "Clothing", "Food & Beverages", "Books", "Tools", "Furniture"]
    for type_name in product_types:
        models['product_type'].create(type_name, user_id)
    
    # Suppliers
    print("    Creating suppliers...")
    suppliers_data = [
        ("SUP001", "Acme Corporation"),
        ("SUP002", "Global Supplies Ltd"),
        ("SUP003", "Tech Distributors Inc"),
        ("SUP004", "Best Buy Wholesale"),
        ("SUP005", "Quality Goods Co")
    ]
    created_suppliers = []
    for account_number, name in suppliers_data:
        success, message = models['supplier'].create(account_number, name, user_id)
        if success:
            suppliers = models['supplier'].get_all(user_id)
            supplier = next((s for s in suppliers if s['account_number'] == account_number), None)
            if supplier:
                created_suppliers.append(supplier)
    
    # Customers
    print("    Creating customers...")
    customers_data = [
        ("John Smith", "07700 900001", "10", "High Street", "London", "Greater London", "SW1A 1AA"),
        ("Jane Doe", "07700 900002", "25", "Oak Avenue", "Manchester", "Greater Manchester", "M1 2AB"),
        ("Bob Wilson", "07700 900003", "The Willows", "Church Lane", "Birmingham", "West Midlands", "B1 1AA"),
        ("Sarah Brown", "07700 900004", "42", "Station Road", "Leeds", "West Yorkshire", "LS1 1AB"),
        ("Mike Johnson", "07700 900005", "Flat 3", "Park View", "Bristol", "Avon", "BS1 1AA"),
    ]
    for name, phone, house, street, city, county, postcode in customers_data:
        models['customer'].create(name, phone, house, street, city, county, postcode, user_id)
    
    # Products
    print("    Creating products...")
    products_data = [
        ("STK001", "High-quality laptop computer", "Electronics"),
        ("STK002", "Cotton t-shirt, various sizes", "Clothing"),
        ("STK003", "Organic coffee beans, 1kg", "Food & Beverages"),
        ("STK004", "Programming guide book", "Books"),
        ("STK005", "Hammer set, 3 pieces", "Tools"),
        ("STK006", "Office desk chair", "Furniture"),
        ("STK007", "Wireless mouse", "Electronics"),
        ("STK008", "Jeans, blue denim", "Clothing")
    ]
    created_products = []
    for stock_number, description, type_name in products_data:
        success, message = models['product'].create(stock_number, description, type_name, user_id)
        if success:
            products = models['product'].get_all(user_id)
            product = next((p for p in products if p['stock_number'] == stock_number), None)
            if product:
                created_products.append(product)
    
    # Default Nominal Accounts
    print("    Creating default nominal accounts...")
    account_count = seed_default_accounts(models['nominal_account'], user_id)
    print(f"      ✓ Created {account_count} accounts")
    
    # Get accounts for journal entries
    accounts = models['nominal_account'].get_all(user_id)
    bank_account = next((a for a in accounts if a['account_code'] == 1000), None)
    sales_account = next((a for a in accounts if a['account_code'] == 4000), None)
    purchases_account = next((a for a in accounts if a['account_code'] == 5001), None)
    
    # Invoices
    print("    Creating invoices...")
    if created_suppliers and created_products:
        supplier = created_suppliers[0]
        supplier_internal_id = supplier.get('internal_id', supplier['id'])
        
        invoices_data = [
            ("INV-2024-001", "2024-01-15", 20.0),
            ("INV-2024-002", "2024-02-10", 20.0),
            ("INV-2024-003", "2024-03-05", 20.0),
        ]
        
        created_invoices = []
        for inv_num, inv_date, vat_rate in invoices_data:
            success, message, invoice_id = models['invoice'].create(
                supplier_internal_id, inv_num, inv_date, vat_rate, user_id
            )
            if success:
                created_invoices.append((invoice_id, inv_num))
                
                # Add items to invoice
                items_to_add = min(3, len(created_products))
                for i in range(items_to_add):
                    product = created_products[i]
                    qty = (i + 1) * 2.0
                    unit_price = (i + 1) * 10.0
                    
                    models['invoice_item'].create(
                        invoice_id,
                        product.get('internal_id'),
                        product['stock_number'],
                        product['description'],
                        qty,
                        unit_price
                    )
                
                # Recalculate totals
                models['invoice'].calculate_totals(invoice_id, user_id)
        
        # Payments
        print("    Creating payments...")
        if created_invoices:
            payments_data = [
                ("2024-01-20", 500.0, "CHQ-001", "Cheque", "Payment for invoice INV-2024-001"),
                ("2024-02-15", 300.0, "CHQ-002", "Cheque", "Partial payment"),
            ]
            
            created_payments = []
            for pay_date, amount, ref, payment_method, notes in payments_data:
                reference = f"{ref} - {notes}" if notes else ref
                success, message, payment_id = models['payment'].create(
                    supplier_internal_id, pay_date, amount, reference, payment_method, user_id
                )
                if success:
                    created_payments.append((payment_id, amount))
            
            # Allocate payments to invoices
            print("    Allocating payments to invoices...")
            if created_payments and created_invoices:
                # Allocate first payment to first invoice
                payment_id, payment_amount = created_payments[0]
                invoice_id, _ = created_invoices[0]
                outstanding = models['invoice'].get_outstanding_balance(invoice_id, user_id)
                allocate_amount = min(payment_amount, outstanding)
                
                if allocate_amount > 0:
                    models['payment_allocation'].create(payment_id, invoice_id, allocate_amount)
                
                # Allocate second payment to second invoice (if exists)
                if len(created_payments) > 1 and len(created_invoices) > 1:
                    payment_id, payment_amount = created_payments[1]
                    invoice_id, _ = created_invoices[1]
                    outstanding = models['invoice'].get_outstanding_balance(invoice_id, user_id)
                    allocate_amount = min(payment_amount, outstanding)
                    
                    if allocate_amount > 0:
                        models['payment_allocation'].create(payment_id, invoice_id, allocate_amount)
        
        # Journal Entries (sample transactions)
        print("    Creating journal entries...")
        if bank_account and sales_account and purchases_account:
            # Sample: Sales transaction
            models['journal_entry'].create(
                date.today() - timedelta(days=30),
                "Sales transaction",
                bank_account['id'],
                sales_account['id'],
                1000.0,
                "SALE-001",
                user_id
            )
            
            # Sample: Purchase transaction
            models['journal_entry'].create(
                date.today() - timedelta(days=20),
                "Purchase of goods",
                purchases_account['id'],
                bank_account['id'],
                500.0,
                "PUR-001",
                user_id
            )
            
            # Sample: Transfer between accounts
            savings_account = next((a for a in accounts if a['account_code'] == 1001), None)
            if savings_account:
                models['journal_entry'].create(
                    date.today() - timedelta(days=10),
                    "Transfer to savings",
                    savings_account['id'],
                    bank_account['id'],
                    200.0,
                    "TRF-001",
                    user_id
                )


def main():
    """Main function to reset and seed the database."""
    print("=" * 60)
    print("Database Reset Script")
    print("=" * 60)
    
    db_path = "data/app.db"
    
    # Confirm before proceeding
    response = input(f"\nThis will DELETE the database at '{db_path}' and recreate it with two users and full data.\n"
                     "Are you sure you want to continue? (yes/no): ")
    
    if response.lower() not in ['yes', 'y']:
        print("Operation cancelled.")
        return
    
    try:
        # Reset database
        models = reset_database(db_path)
        
        # Create two users
        print("\nCreating users...")
        users_data = [
            ("user1", "password1", "User 1"),
            ("user2", "password2", "User 2")
        ]
        
        created_users = []
        for username, password, description in users_data:
            success, message = models['user'].create_user(username, password)
            if success:
                print(f"  ✓ Created user: {username} ({description})")
                user_id = models['user'].authenticate(username, password)[2]
                created_users.append((username, password, user_id))
            else:
                print(f"  ✗ Failed to create user {username}: {message}")
        
        if not created_users:
            print("  ⚠ No users created. Cannot continue seeding.")
            return
        
        # Seed data for each user
        print("\nSeeding data for users...")
        for username, password, user_id in created_users:
            seed_user_data(models, username, password, user_id)
        
        print("\n" + "=" * 60)
        print("✓ Database reset and seeding completed successfully!")
        print("=" * 60)
        print("\nCreated users:")
        for username, password, _ in created_users:
            print(f"  - Username: {username}, Password: {password}")
        
    except Exception as e:
        print(f"\n✗ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

