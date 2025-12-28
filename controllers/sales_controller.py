"""Sales controller."""
from typing import TYPE_CHECKING, Optional, List, Dict
from PySide6.QtCore import QObject, Signal
from datetime import datetime
from utils.transaction_logger import TransactionLogger
from utils.account_finder import (
    find_trade_debtors_account,
    find_sales_account,
    find_bank_account,
    find_undeposited_funds_account,
    find_vat_output_account,
    find_cost_of_sales_account,
    find_stock_asset_account
)

if TYPE_CHECKING:
    from views.sales_view import SalesView
    from models.sales_invoice import SalesInvoice
    from models.sales_invoice_item import SalesInvoiceItem
    from models.customer_payment import CustomerPayment
    from models.customer_payment_allocation import CustomerPaymentAllocation
    from models.customer import Customer
    from models.product import Product
    from models.service import Service
    from models.vehicle import Vehicle


class SalesController(QObject):
    """Controller for sales functionality."""
    
    # Navigation signals
    dashboard_requested = Signal()
    suppliers_requested = Signal()
    customers_requested = Signal()
    products_requested = Signal()
    inventory_requested = Signal()
    bookkeeper_requested = Signal()
    vehicles_requested = Signal()
    services_requested = Signal()
    configuration_requested = Signal()
    logout_requested = Signal()
    
    # Sales document signals
    document_created = Signal()
    document_updated = Signal()
    document_deleted = Signal()
    item_added = Signal()
    item_updated = Signal()
    item_deleted = Signal()
    payment_created = Signal()
    allocation_created = Signal()
    
    def __init__(self, sales_view: "SalesView", 
                 sales_invoice_model: "SalesInvoice",
                 sales_invoice_item_model: "SalesInvoiceItem",
                 customer_payment_model: "CustomerPayment",
                 customer_payment_allocation_model: "CustomerPaymentAllocation",
                 customer_model: "Customer",
                 product_model: "Product",
                 service_model: "Service",
                 vehicle_model: "Vehicle",
                 user_id: int):
        """Initialize the sales controller."""
        super().__init__()
        self.sales_view = sales_view
        self.sales_invoice_model = sales_invoice_model
        self.sales_invoice_item_model = sales_invoice_item_model
        self.customer_payment_model = customer_payment_model
        self.customer_payment_allocation_model = customer_payment_allocation_model
        self.customer_model = customer_model
        self.product_model = product_model
        self.service_model = service_model
        self.vehicle_model = vehicle_model
        self.user_id = user_id
        self.transaction_logger = TransactionLogger(sales_invoice_model.db_path)
        
        # Connect view signals to controller handlers
        self.sales_view.dashboard_requested.connect(self.handle_dashboard)
        self.sales_view.suppliers_requested.connect(self.handle_suppliers)
        self.sales_view.customers_requested.connect(self.handle_customers)
        self.sales_view.products_requested.connect(self.handle_products)
        self.sales_view.inventory_requested.connect(self.handle_inventory)
        self.sales_view.bookkeeper_requested.connect(self.handle_bookkeeper)
        self.sales_view.vehicles_requested.connect(self.handle_vehicles)
        self.sales_view.services_requested.connect(self.handle_services)
        self.sales_view.configuration_requested.connect(self.handle_configuration)
        self.sales_view.logout_requested.connect(self.handle_logout)
        
        # Sales document signals
        self.sales_view.create_document_requested.connect(self.handle_create_document)
        self.sales_view.update_document_requested.connect(self.handle_update_document)
        self.sales_view.delete_document_requested.connect(self.handle_delete_document)
        self.sales_view.change_document_type_requested.connect(self.handle_change_document_type)
        self.sales_view.refresh_documents_requested.connect(self.refresh_documents)
        
        # Item signals
        self.sales_view.add_item_requested.connect(self.handle_add_item)
        self.sales_view.update_item_requested.connect(self.handle_update_item)
        self.sales_view.delete_item_requested.connect(self.handle_delete_item)
        self.sales_view.document_selected.connect(self.handle_document_selected)
        
        # Payment signals
        self.sales_view.create_payment_requested.connect(self.handle_create_payment)
        self.sales_view.allocate_payment_requested.connect(self.handle_allocate_payment)
        self.sales_view.delete_payment_requested.connect(self.handle_delete_payment)
        self.sales_view.delete_allocation_requested.connect(self.handle_delete_allocation)
        
        # Customer creation signal
        self.sales_view.create_customer_requested.connect(self.handle_create_customer)
        
        # Load initial data
        self.refresh_documents()
        self.refresh_customers()
        self.refresh_products()
        self.refresh_services()
    
    def set_user_id(self, user_id: int):
        """Update the user ID and refresh data."""
        self.user_id = user_id
        self.refresh_documents()
        self.refresh_customers()
        self.refresh_products()
        self.refresh_services()
    
    def get_document_number_preview(self, document_type: str) -> str:
        """Get preview of next document number for a document type."""
        return self.sales_invoice_model.generate_document_number(document_type, self.user_id)
    
    def handle_create_document(self, wizard_data: Dict):
        """Handle create sales document from wizard."""
        customer_id = wizard_data.get('customer_id')  # This is internal_id from wizard
        document_date = wizard_data.get('document_date')
        document_type = wizard_data.get('document_type', 'order')
        notes = wizard_data.get('notes', '')
        status = wizard_data.get('status', 'draft')
        vehicle_id = wizard_data.get('vehicle_id')
        items = wizard_data.get('items', [])
        
        # customer_id from wizard is already internal_id (can be None)
        internal_customer_id = customer_id
        
        # Create document (document number will be auto-generated)
        success, message, sales_invoice_id = self.sales_invoice_model.create(
            internal_customer_id, document_date, document_type, notes, self.user_id,
            vehicle_id=vehicle_id
        )
        
        if not success:
            self.sales_view.show_error_dialog(message)
            return
        
        # Update status if provided
        if status and status != 'draft':
            document = self.sales_invoice_model.get_by_id(sales_invoice_id, self.user_id)
            if document:
                self.sales_invoice_model.update(
                    sales_invoice_id, 
                    document['document_number'],
                    document_date, document_type, notes, status, self.user_id, vehicle_id
                )
        
        # Add items
        if items:
            for item in items:
                product_id = item.get('product_id')
                service_id = item.get('service_id')
                stock_number = item.get('stock_number', '')
                description = item.get('description', '')
                quantity = item.get('quantity', 1.0)
                unit_price = item.get('unit_price', 0.0)
                vat_code = item.get('vat_code', 'S')
                
                # Get internal IDs
                internal_product_id = None
                if product_id:
                    product_data = self.product_model.get_by_id(product_id, self.user_id)
                    if product_data:
                        internal_product_id = product_data['internal_id']
                
                internal_service_id = None
                if service_id:
                    service_data = self.service_model.get_by_id(service_id, self.user_id)
                    if service_data:
                        internal_service_id = service_data['internal_id']
                
                self.sales_invoice_item_model.create(
                    sales_invoice_id, internal_product_id, internal_service_id,
                    stock_number, description, quantity, unit_price, vat_code
                )
        
        self.sales_view.show_success_dialog(message)
        self.document_created.emit()
        self.refresh_documents()
    
    def handle_update_document(self, sales_invoice_id: int, document_number: str,
                              document_date: str, document_type: str, notes: str, status: str,
                              vehicle_id: Optional[int] = None):
        """Handle update sales document."""
        success, message = self.sales_invoice_model.update(
            sales_invoice_id, document_number, document_date, document_type, notes, status, self.user_id,
            vehicle_id=vehicle_id
        )
        
        if success:
            # Recalculate totals
            self.sales_invoice_model.calculate_totals(sales_invoice_id, self.user_id)
            self.sales_view.show_success_dialog(message)
            self.document_updated.emit()
            self.refresh_documents()
        else:
            self.sales_view.show_error_dialog(message)
    
    def handle_delete_document(self, sales_invoice_id: int):
        """Handle delete sales document."""
        success, message = self.sales_invoice_model.delete(sales_invoice_id, self.user_id)
        
        if success:
            self.sales_view.show_success_dialog(message)
            self.document_deleted.emit()
            self.refresh_documents()
        else:
            self.sales_view.show_error_dialog(message)
    
    def handle_change_document_type(self, sales_invoice_id: int, new_type: str):
        """Handle change document type."""
        # Get current document
        document = self.sales_invoice_model.get_by_id(sales_invoice_id, self.user_id)
        if not document:
            self.sales_view.show_error_dialog("Document not found")
            return
        
        # Update document type
        success, message = self.sales_invoice_model.update(
            sales_invoice_id, document['document_number'], document['document_date'],
            new_type, document.get('notes', ''), document['status'], self.user_id
        )
        
        if success:
            self.sales_view.show_success_dialog(message)
            self.document_updated.emit()
            self.refresh_documents()
        else:
            self.sales_view.show_error_dialog(message)
    
    def handle_add_item(self, sales_invoice_id: int, product_id: Optional[int],
                       service_id: Optional[int], stock_number: str, description: str,
                       quantity: float, unit_price: float, vat_code: str):
        """Handle add item to sales document."""
        # Get internal product/service IDs if provided
        internal_product_id = None
        if product_id:
            product_data = self.product_model.get_by_id(product_id, self.user_id)
            if product_data:
                internal_product_id = product_data['internal_id']
        
        internal_service_id = None
        if service_id:
            service_data = self.service_model.get_by_id(service_id, self.user_id)
            if service_data:
                internal_service_id = service_data['internal_id']
        
        success, message, item_id = self.sales_invoice_item_model.create(
            sales_invoice_id, internal_product_id, internal_service_id,
            stock_number, description, quantity, unit_price, vat_code
        )
        
        if success:
            # Log transaction to journal entries
            self._log_sales_invoice_item_transaction(
                sales_invoice_id, internal_product_id, internal_service_id,
                description, quantity, unit_price, vat_code, item_id
            )
            self.sales_view.show_success_dialog(message)
            self.item_added.emit()
            self.refresh_documents()
            # Refresh items for the current document
            if self.sales_view.selected_document_id:
                self.handle_document_selected(self.sales_view.selected_document_id)
        else:
            self.sales_view.show_error_dialog(message)
    
    def handle_update_item(self, item_id: int, quantity: float, unit_price: float):
        """Handle update item."""
        # Get old item data before update for reversal
        import sqlite3
        old_item_data = None
        try:
            with sqlite3.connect(self.sales_invoice_model.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT sales_invoice_id, product_id, service_id, description, quantity, unit_price, vat_code
                    FROM sales_invoice_items WHERE id = ?
                """, (item_id,))
                result = cursor.fetchone()
                if result:
                    old_item_data = {
                        'sales_invoice_id': result[0],
                        'product_id': result[1],
                        'service_id': result[2],
                        'description': result[3],
                        'quantity': result[4],
                        'unit_price': result[5],
                        'vat_code': result[6] or 'S'
                    }
        except Exception:
            pass
        
        success, message = self.sales_invoice_item_model.update(item_id, quantity, unit_price)
        
        if success:
            if old_item_data:
                # Reverse old journal entries
                self._reverse_sales_invoice_item_entries(
                    old_item_data['sales_invoice_id'], old_item_data['product_id'],
                    old_item_data['service_id'], old_item_data['description'],
                    old_item_data['quantity'], old_item_data['unit_price'],
                    old_item_data['vat_code']
                )
                
                # Create new journal entries with updated amounts
                self._log_sales_invoice_item_transaction(
                    old_item_data['sales_invoice_id'], old_item_data['product_id'],
                    old_item_data['service_id'], old_item_data['description'],
                    quantity, unit_price, old_item_data['vat_code'], item_id
                )
            
            self.sales_view.show_success_dialog(message)
            self.item_updated.emit()
            self.refresh_documents()
            # Refresh items for the current document
            if self.sales_view.selected_document_id:
                self.handle_document_selected(self.sales_view.selected_document_id)
        else:
            self.sales_view.show_error_dialog(message)
    
    def handle_delete_item(self, item_id: int):
        """Handle delete item."""
        # Get item data before deletion for reversal
        import sqlite3
        item_data = None
        try:
            with sqlite3.connect(self.sales_invoice_model.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT sales_invoice_id, product_id, service_id, description, quantity, unit_price, vat_code
                    FROM sales_invoice_items WHERE id = ?
                """, (item_id,))
                result = cursor.fetchone()
                if result:
                    item_data = {
                        'sales_invoice_id': result[0],
                        'product_id': result[1],
                        'service_id': result[2],
                        'description': result[3],
                        'quantity': result[4],
                        'unit_price': result[5],
                        'vat_code': result[6] or 'S'
                    }
        except Exception:
            pass
        
        success, message = self.sales_invoice_item_model.delete(item_id)
        
        if success:
            if item_data:
                # Reverse journal entries
                self._reverse_sales_invoice_item_entries(
                    item_data['sales_invoice_id'], item_data['product_id'],
                    item_data['service_id'], item_data['description'],
                    item_data['quantity'], item_data['unit_price'],
                    item_data['vat_code']
                )
            
            self.sales_view.show_success_dialog(message)
            self.item_deleted.emit()
            self.refresh_documents()
            # Refresh items for the current document
            if self.sales_view.selected_document_id:
                self.handle_document_selected(self.sales_view.selected_document_id)
        else:
            self.sales_view.show_error_dialog(message)
    
    def _reverse_sales_invoice_item_entries(self, sales_invoice_id: int, product_id: Optional[int],
                                           service_id: Optional[int], description: str,
                                           quantity: float, unit_price: float, vat_code: str):
        """
        Reverse journal entries for a sales invoice item.
        
        Args:
            sales_invoice_id: Sales invoice ID
            product_id: Product ID
            service_id: Service ID
            description: Item description
            quantity: Quantity
            unit_price: Unit price
            vat_code: VAT code
        """
        try:
            # Get sales invoice details
            invoice = self.sales_invoice_model.get_by_id(sales_invoice_id, self.user_id)
            if not invoice:
                return
            
            invoice_number = invoice.get('document_number', '')
            invoice_date_str = invoice.get('document_date')
            
            # Parse invoice date
            try:
                if isinstance(invoice_date_str, str):
                    invoice_date = datetime.strptime(invoice_date_str, '%Y-%m-%d').date()
                else:
                    invoice_date = invoice_date_str
            except (ValueError, AttributeError):
                invoice_date = datetime.now().date()
            
            # Find entries to reverse by reference and description
            entries_to_reverse = self.transaction_logger.find_entries_by_reference_and_description(
                self.user_id, invoice_number, description
            )
            
            # Also find VAT entries if applicable
            if vat_code == 'S':
                vat_entries = self.transaction_logger.find_entries_by_reference_and_description(
                    self.user_id, invoice_number, f"VAT Output: {description}"
                )
                entries_to_reverse.extend(vat_entries)
            
            # Also find Cost of Sales entries if product
            if product_id is not None:
                cos_entries = self.transaction_logger.find_entries_by_reference_and_description(
                    self.user_id, invoice_number, f"Cost of Sales: {description}"
                )
                entries_to_reverse.extend(cos_entries)
            
            # Reverse all found entries
            for entry in entries_to_reverse:
                self.transaction_logger.reverse_journal_entry(
                    entry['id'], self.user_id, invoice_date, f"REV-{invoice_number}"
                )
        except Exception:
            # Don't fail if reversal fails
            pass
    
    def handle_create_payment(self, customer_id: int, payment_date: str, amount: float,
                             reference: str, payment_method: str):
        """Handle create customer payment."""
        # Get internal customer ID
        customer_data = self.customer_model.get_by_id(customer_id, self.user_id)
        if not customer_data:
            self.sales_view.show_error_dialog("Customer not found")
            return
        
        internal_customer_id = customer_data['internal_id']
        
        success, message, payment_id = self.customer_payment_model.create(
            internal_customer_id, payment_date, amount, reference, payment_method, self.user_id
        )
        
        if success:
            # Log transaction to journal entries
            self._log_customer_payment_transaction(
                internal_customer_id, payment_date, reference, payment_method, amount
            )
            self.sales_view.show_success_dialog(message)
            self.payment_created.emit()
        else:
            self.sales_view.show_error_dialog(message)
    
    def handle_allocate_payment(self, payment_id: int, sales_invoice_id: int, amount: float):
        """Handle allocate payment to sales invoice."""
        success, message, allocation_id = self.customer_payment_allocation_model.create(
            payment_id, sales_invoice_id, amount
        )
        
        if success:
            # Update sales invoice status if fully paid
            self.sales_invoice_model.update_status_if_paid(sales_invoice_id, self.user_id)
            self.sales_view.show_success_dialog(message)
            self.allocation_created.emit()
            self.refresh_documents()
        else:
            self.sales_view.show_error_dialog(message)
    
    def handle_delete_payment(self, payment_id: int):
        """Handle delete payment."""
        success, message = self.customer_payment_model.delete(payment_id, self.user_id)
        
        if success:
            self.sales_view.show_success_dialog(message)
            self.payment_created.emit()
        else:
            self.sales_view.show_error_dialog(message)
    
    def handle_delete_allocation(self, allocation_id: int):
        """Handle delete payment allocation."""
        success, message, sales_invoice_id = self.customer_payment_allocation_model.delete(allocation_id)
        
        if success:
            # Update sales invoice status if it was fully paid and now isn't
            if sales_invoice_id:
                self.sales_invoice_model.update_status_if_paid(sales_invoice_id, self.user_id)
            self.sales_view.show_success_dialog(message)
            self.allocation_created.emit()
            self.refresh_documents()
        else:
            self.sales_view.show_error_dialog(message)
    
    def handle_document_selected(self, sales_invoice_id: int):
        """Handle document selection - load items and details."""
        document = self.sales_invoice_model.get_by_id(sales_invoice_id, self.user_id)
        if document:
            items = self.sales_invoice_item_model.get_by_sales_invoice(sales_invoice_id)
            self.sales_view.load_items(items, document)
    
    def handle_create_customer(self, name: str, phone: str, house_name_no: str,
                               street_address: str, city: str, county: str, postcode: str):
        """Handle create customer from sales view."""
        success, message = self.customer_model.create(
            name, phone, house_name_no, street_address, city, county, postcode, self.user_id
        )
        
        if success:
            self.sales_view.show_success_dialog(message)
            self.refresh_customers()
        else:
            self.sales_view.show_error_dialog(message)
    
    def get_sales_documents(self, customer_id: Optional[int] = None,
                           document_type: Optional[str] = None) -> List[Dict]:
        """Get sales documents, optionally filtered by customer or type."""
        return self.sales_invoice_model.get_all(self.user_id, customer_id, document_type)
    
    def get_sales_document(self, sales_invoice_id: int) -> Optional[Dict]:
        """Get a sales document by ID."""
        return self.sales_invoice_model.get_by_id(sales_invoice_id, self.user_id)
    
    def get_items(self, sales_invoice_id: int) -> List[Dict]:
        """Get all items for a sales document."""
        return self.sales_invoice_item_model.get_by_sales_invoice(sales_invoice_id)
    
    def get_outstanding_sales_invoices(self, customer_id: int) -> List[Dict]:
        """Get sales invoices with outstanding balances for a customer."""
        # Get internal customer ID
        customer_data = self.customer_model.get_by_id(customer_id, self.user_id)
        if not customer_data:
            return []
        
        internal_customer_id = customer_data['internal_id']
        invoices = self.sales_invoice_model.get_all(self.user_id, internal_customer_id)
        
        # Add outstanding balance to each invoice
        for invoice in invoices:
            invoice_id = invoice['id']
            invoice['outstanding_balance'] = self.sales_invoice_model.get_outstanding_balance(
                invoice_id, self.user_id
            )
        
        # Filter to only invoices with outstanding balance > 0
        return [inv for inv in invoices if inv['outstanding_balance'] > 0.01]
    
    def refresh_documents(self):
        """Refresh the sales documents list."""
        documents = self.sales_invoice_model.get_all(self.user_id)
        self.sales_view.load_documents(documents)
    
    def refresh_customers(self):
        """Refresh the customers list."""
        customers = self.customer_model.get_all(self.user_id)
        self.sales_view.load_customers(customers)
    
    def refresh_products(self):
        """Refresh the products list."""
        products = self.product_model.get_all(self.user_id)
        self.sales_view.load_products(products)
    
    def refresh_services(self):
        """Refresh the services list."""
        services = self.service_model.get_all(self.user_id)
        self.sales_view.load_services(services)
    
    def handle_dashboard(self):
        """Handle dashboard navigation."""
        self.dashboard_requested.emit()
    
    def handle_suppliers(self):
        """Handle suppliers navigation."""
        self.suppliers_requested.emit()
    
    def handle_customers(self):
        """Handle customers navigation."""
        self.customers_requested.emit()
    
    def handle_products(self):
        """Handle products navigation."""
        self.products_requested.emit()
    
    def handle_inventory(self):
        """Handle inventory navigation."""
        self.inventory_requested.emit()
    
    def handle_bookkeeper(self):
        """Handle bookkeeper navigation."""
        self.bookkeeper_requested.emit()
    
    def handle_vehicles(self):
        """Handle vehicles navigation."""
        self.vehicles_requested.emit()
    
    def handle_services(self):
        """Handle services navigation."""
        self.services_requested.emit()
    
    def handle_configuration(self):
        """Handle configuration navigation."""
        self.configuration_requested.emit()
    
    def handle_logout(self):
        """Handle logout."""
        self.logout_requested.emit()
    
    def _log_sales_invoice_item_transaction(self, sales_invoice_id: int, product_id: Optional[int],
                                           service_id: Optional[int], description: str,
                                           quantity: float, unit_price: float, vat_code: str = 'S',
                                           item_id: Optional[int] = None):
        """
        Log sales invoice item transaction to journal entries.
        
        Args:
            sales_invoice_id: Sales invoice ID
            product_id: Product ID (if product item)
            service_id: Service ID (if service item)
            description: Item description
            quantity: Quantity
            unit_price: Unit price
            vat_code: VAT code (S, E, or Z)
            item_id: Sales invoice item ID (optional, for getting VAT code if not provided)
        """
        try:
            # Get sales invoice details
            invoice = self.sales_invoice_model.get_by_id(sales_invoice_id, self.user_id)
            if not invoice:
                return
            
            invoice_date_str = invoice.get('document_date')
            invoice_number = invoice.get('document_number', '')
            customer_id = invoice.get('customer_id')
            
            # Parse invoice date
            try:
                if isinstance(invoice_date_str, str):
                    invoice_date = datetime.strptime(invoice_date_str, '%Y-%m-%d').date()
                else:
                    invoice_date = invoice_date_str
            except (ValueError, AttributeError):
                invoice_date = datetime.now().date()
            
            # Get customer name
            import sqlite3
            customer_name = 'Unknown Customer'
            try:
                with sqlite3.connect(self.sales_invoice_model.db_path, timeout=10.0) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM customers WHERE id = ? AND user_id = ?", (customer_id, self.user_id))
                    row = cursor.fetchone()
                    if row:
                        customer_name = row[0]
            except Exception:
                pass
            
            # Get VAT code from item if not provided and item_id is available
            if not vat_code and item_id:
                try:
                    import sqlite3
                    with sqlite3.connect(self.sales_invoice_model.db_path, timeout=10.0) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT vat_code FROM sales_invoice_items WHERE id = ?", (item_id,))
                        result = cursor.fetchone()
                        if result:
                            vat_code = result[0] or 'S'
                except Exception:
                    vat_code = 'S'
            
            vat_code = (vat_code or 'S').strip().upper()
            
            # Calculate amount (excluding VAT - we log the net amount)
            amount = quantity * unit_price
            
            # Get nominal accounts
            from models.nominal_account import NominalAccount
            nominal_account_model = NominalAccount(self.sales_invoice_model.db_path)
            
            # Find Trade Debtors account (Asset - Current Asset)
            debtor_account_id = find_trade_debtors_account(self.user_id, self.sales_invoice_model.db_path)
            if not debtor_account_id:
                # Account not found, skip logging (but don't fail the item creation)
                return
            
            # Find Sales account (Income - Turnover)
            sales_account_id = find_sales_account(self.user_id, self.sales_invoice_model.db_path)
            if not sales_account_id:
                # Account not found, skip logging (but don't fail the item creation)
                return
            
            # Log the net sales transaction
            self.transaction_logger.log_sales_invoice_item(
                user_id=self.user_id,
                invoice_date=invoice_date,
                invoice_number=invoice_number,
                customer_name=customer_name,
                sales_account_id=sales_account_id,
                debtor_account_id=debtor_account_id,
                amount=amount,
                description=description
            )
            
            # Log VAT Output if VAT code is 'S' (Standard rate 20%)
            if vat_code == 'S':
                vat_amount = amount * 0.20  # 20% VAT
                vat_output_account_id = find_vat_output_account(self.user_id, self.sales_invoice_model.db_path)
                if vat_output_account_id:
                    self.transaction_logger.log_vat_output(
                        user_id=self.user_id,
                        invoice_date=invoice_date,
                        invoice_number=invoice_number,
                        customer_name=customer_name,
                        debtor_account_id=debtor_account_id,
                        vat_output_account_id=vat_output_account_id,
                        vat_amount=vat_amount,
                        description=description
                    )
            
            # Log Cost of Sales if product is sold
            if product_id is not None:
                # Get product cost price (we'll use unit_price from invoice as cost for now)
                # In a real system, products should have a cost_price field
                # For now, we'll need to get it from the product or use a default
                cost_of_sales_account_id = find_cost_of_sales_account(self.user_id, self.sales_invoice_model.db_path)
                stock_account_id = find_stock_asset_account(self.user_id, self.sales_invoice_model.db_path)
                
                if cost_of_sales_account_id and stock_account_id:
                    # Try to get cost price from product
                    try:
                        product_data = self.product_model.get_by_id(product_id, self.user_id)
                        # For now, we'll use unit_price as cost (this should be improved to use actual cost_price)
                        # If products have a cost_price field, use that instead
                        cost_price = unit_price  # TODO: Get actual cost_price from product
                        cost_amount = quantity * cost_price
                    except Exception:
                        # If we can't get product data, skip Cost of Sales logging
                        cost_amount = 0.0
                    
                    if cost_amount > 0:
                        self.transaction_logger.log_cost_of_sales(
                            user_id=self.user_id,
                            invoice_date=invoice_date,
                            invoice_number=invoice_number,
                            customer_name=customer_name,
                            cost_of_sales_account_id=cost_of_sales_account_id,
                            stock_account_id=stock_account_id,
                            cost_amount=cost_amount,
                            description=description
                        )
        except Exception as e:
            # Don't fail the item creation if logging fails
            # Log error but continue
            pass
    
    def _log_customer_payment_transaction(self, customer_id: int, payment_date: str,
                                          payment_reference: str, payment_method: str, amount: float):
        """
        Log customer payment transaction to journal entries.
        
        Args:
            customer_id: Internal customer ID
            payment_date: Payment date (YYYY-MM-DD)
            payment_reference: Payment reference
            payment_method: Payment method (Cash, Card, Cheque, BACS)
            amount: Payment amount
        """
        try:
            # Parse payment date
            try:
                if isinstance(payment_date, str):
                    payment_date_obj = datetime.strptime(payment_date, '%Y-%m-%d').date()
                else:
                    payment_date_obj = payment_date
            except (ValueError, AttributeError):
                payment_date_obj = datetime.now().date()
            
            # Get customer name
            import sqlite3
            customer_name = 'Unknown Customer'
            try:
                with sqlite3.connect(self.sales_invoice_model.db_path, timeout=10.0) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM customers WHERE id = ? AND user_id = ?", (customer_id, self.user_id))
                    row = cursor.fetchone()
                    if row:
                        customer_name = row[0]
            except Exception:
                pass
            
            # Find Trade Debtors account
            debtor_account_id = find_trade_debtors_account(self.user_id, self.sales_invoice_model.db_path)
            if not debtor_account_id:
                return
            
            # Determine debit account based on payment method
            # BACS goes directly to Bank, others go to Undeposited Funds
            if payment_method == 'BACS':
                debit_account_id = find_bank_account(self.user_id, self.sales_invoice_model.db_path)
            else:
                # Cash, Card, Cheque go to Undeposited Funds
                debit_account_id = find_undeposited_funds_account(self.user_id, self.sales_invoice_model.db_path)
            
            if not debit_account_id:
                # Account not found, skip logging
                return
            
            # Log the transaction
            self.transaction_logger.log_customer_payment(
                user_id=self.user_id,
                payment_date=payment_date_obj,
                payment_reference=payment_reference or '',
                customer_name=customer_name,
                debit_account_id=debit_account_id,
                debtor_account_id=debtor_account_id,
                amount=amount
            )
        except Exception as e:
            # Don't fail the payment creation if logging fails
            pass

