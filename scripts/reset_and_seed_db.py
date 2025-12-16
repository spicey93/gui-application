"""Script to reset and seed the database with test data."""
import os
import sys
import sqlite3
import hashlib
from pathlib import Path

# Add parent directory to path to import models
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.user import User
from models.supplier import Supplier
from models.product import Product
from models.product_type import ProductType
from models.invoice import Invoice
from models.invoice_item import InvoiceItem
from models.payment import Payment
from models.payment_allocation import PaymentAllocation


def _hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


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
    product_model = Product(db_path)
    product_type_model = ProductType(db_path)
    invoice_model = Invoice(db_path)
    invoice_item_model = InvoiceItem(db_path)
    payment_model = Payment(db_path)
    payment_allocation_model = PaymentAllocation(db_path)
    
    print("Database reset complete!")
    return user_model, supplier_model, product_model, product_type_model, invoice_model, invoice_item_model, payment_model, payment_allocation_model


def seed_database(user_model: User, supplier_model: Supplier, 
                 product_model: Product, product_type_model: ProductType,
                 invoice_model: Invoice, invoice_item_model: InvoiceItem,
                 payment_model: Payment, payment_allocation_model: PaymentAllocation):
    """Seed the database with test data."""
    print("\nSeeding database with test data...")
    
    # Create test users
    print("Creating test users...")
    users = [
        ("admin", "admin123", "Admin User"),
        ("testuser", "test123", "Test User"),
        ("demo", "demo123", "Demo User")
    ]
    
    created_users = []
    for username, password, description in users:
        success, message = user_model.create_user(username, password)
        if success:
            print(f"  ✓ Created user: {username} ({description})")
            # Get user ID for later use
            user_id = user_model.authenticate(username, password)[2]
            created_users.append((username, user_id))
        else:
            print(f"  ✗ Failed to create user {username}: {message}")
    
    if not created_users:
        print("  ⚠ No users created. Cannot continue seeding.")
        return
    
    # Create product types for each user
    print("\nCreating product types...")
    product_types_data = [
        "Electronics",
        "Clothing",
        "Food & Beverages",
        "Books",
        "Tools",
        "Furniture"
    ]
    
    for username, user_id in created_users:
        print(f"  Creating types for user: {username}")
        for type_name in product_types_data:
            success, message = product_type_model.create(type_name, user_id)
            if success:
                print(f"    ✓ Created type: {type_name}")
            else:
                print(f"    ✗ Failed to create type {type_name}: {message}")
    
    # Create suppliers for each user
    print("\nCreating suppliers...")
    suppliers_data = [
        ("SUP001", "Acme Corporation"),
        ("SUP002", "Global Supplies Ltd"),
        ("SUP003", "Tech Distributors Inc"),
        ("SUP004", "Best Buy Wholesale"),
        ("SUP005", "Quality Goods Co")
    ]
    
    for username, user_id in created_users:
        print(f"  Creating suppliers for user: {username}")
        for account_number, name in suppliers_data:
            success, message = supplier_model.create(account_number, name, user_id)
            if success:
                print(f"    ✓ Created supplier: {name} ({account_number})")
            else:
                print(f"    ✗ Failed to create supplier {name}: {message}")
    
    # Create products for each user
    print("\nCreating products...")
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
    
    for username, user_id in created_users:
        print(f"  Creating products for user: {username}")
        for stock_number, description, type_name in products_data:
            success, message = product_model.create(stock_number, description, type_name, user_id)
            if success:
                print(f"    ✓ Created product: {stock_number} - {description}")
            else:
                print(f"    ✗ Failed to create product {stock_number}: {message}")
    
    # Create invoices and payments for first user
    print("\nCreating invoices and payments...")
    if created_users:
        username, user_id = created_users[0]
        print(f"  Creating invoices and payments for user: {username}")
        
        # Get suppliers for this user
        suppliers = supplier_model.get_all(user_id)
        if suppliers:
            supplier = suppliers[0]  # Use first supplier
            supplier_internal_id = supplier.get('internal_id', supplier['id'])
            
            # Get products for this user
            products = product_model.get_all(user_id)
            
            # Create invoices
            invoices_data = [
                ("INV-2024-001", "2024-01-15", 20.0),
                ("INV-2024-002", "2024-02-10", 20.0),
                ("INV-2024-003", "2024-03-05", 20.0),
            ]
            
            created_invoices = []
            for inv_num, inv_date, vat_rate in invoices_data:
                success, message, invoice_id = invoice_model.create(
                    supplier_internal_id, inv_num, inv_date, vat_rate, user_id
                )
                if success:
                    print(f"    ✓ Created invoice: {inv_num}")
                    created_invoices.append((invoice_id, inv_num))
                    
                    # Add items to invoice
                    if products:
                        # Add 2-3 items per invoice
                        items_to_add = min(3, len(products))
                        for i in range(items_to_add):
                            product = products[i]
                            qty = (i + 1) * 2.0
                            unit_price = (i + 1) * 10.0
                            
                            success, message, _ = invoice_item_model.create(
                                invoice_id,
                                product.get('internal_id'),
                                product['stock_number'],
                                product['description'],
                                qty,
                                unit_price
                            )
                            if success:
                                print(f"      ✓ Added item: {product['stock_number']}")
                    
                    # Recalculate totals
                    invoice_model.calculate_totals(invoice_id, user_id)
                else:
                    print(f"    ✗ Failed to create invoice {inv_num}: {message}")
            
            # Create payments
            if created_invoices:
                payments_data = [
                    ("2024-01-20", 500.0, "CHQ-001", "Payment for invoice INV-2024-001"),
                    ("2024-02-15", 300.0, "CHQ-002", "Partial payment"),
                ]
                
                created_payments = []
                for pay_date, amount, ref, notes in payments_data:
                    success, message, payment_id = payment_model.create(
                        supplier_internal_id, pay_date, amount, ref, notes, user_id
                    )
                    if success:
                        print(f"    ✓ Created payment: {ref} - £{amount:.2f}")
                        created_payments.append((payment_id, amount))
                    else:
                        print(f"    ✗ Failed to create payment {ref}: {message}")
                
                # Allocate payments to invoices
                if created_payments and created_invoices:
                    # Allocate first payment to first invoice
                    payment_id, payment_amount = created_payments[0]
                    invoice_id, _ = created_invoices[0]
                    
                    # Get invoice outstanding balance
                    outstanding = invoice_model.get_outstanding_balance(invoice_id, user_id)
                    allocate_amount = min(payment_amount, outstanding)
                    
                    if allocate_amount > 0:
                        success, message, _ = payment_allocation_model.create(
                            payment_id, invoice_id, allocate_amount
                        )
                        if success:
                            print(f"    ✓ Allocated £{allocate_amount:.2f} from payment to invoice {created_invoices[0][1]}")
                        else:
                            print(f"    ✗ Failed to allocate payment: {message}")
                    
                    # Allocate second payment to second invoice (if exists)
                    if len(created_payments) > 1 and len(created_invoices) > 1:
                        payment_id, payment_amount = created_payments[1]
                        invoice_id, _ = created_invoices[1]
                        
                        outstanding = invoice_model.get_outstanding_balance(invoice_id, user_id)
                        allocate_amount = min(payment_amount, outstanding)
                        
                        if allocate_amount > 0:
                            success, message, _ = payment_allocation_model.create(
                                payment_id, invoice_id, allocate_amount
                            )
                            if success:
                                print(f"    ✓ Allocated £{allocate_amount:.2f} from payment to invoice {created_invoices[1][1]}")
    
    print("\n✓ Database seeding complete!")
    print("\nTest accounts created:")
    for username, _ in created_users:
        print(f"  - Username: {username}, Password: {username}123")


def main():
    """Main function to reset and seed the database."""
    print("=" * 60)
    print("Database Reset and Seed Script")
    print("=" * 60)
    
    db_path = "data/app.db"
    
    # Confirm before proceeding
    response = input(f"\nThis will DELETE the database at '{db_path}' and recreate it with test data.\n"
                     "Are you sure you want to continue? (yes/no): ")
    
    if response.lower() not in ['yes', 'y']:
        print("Operation cancelled.")
        return
    
    try:
        # Reset database
        user_model, supplier_model, product_model, product_type_model, invoice_model, invoice_item_model, payment_model, payment_allocation_model = reset_database(db_path)
        
        # Seed database
        seed_database(user_model, supplier_model, product_model, product_type_model,
                     invoice_model, invoice_item_model, payment_model, payment_allocation_model)
        
        print("\n" + "=" * 60)
        print("✓ Database reset and seeding completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

