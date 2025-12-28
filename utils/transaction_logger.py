"""Transaction logger utility for automatic journal entry creation."""
from typing import Optional, List, Dict
from datetime import date
from models.journal_entry import JournalEntry


class TransactionLogger:
    """Utility class for logging transactions as journal entries."""
    
    def __init__(self, db_path: str = "data/app.db"):
        """Initialize the transaction logger."""
        self.journal_entry_model = JournalEntry(db_path)
    
    def log_sales_invoice_item(self, user_id: int, invoice_date: date, invoice_number: str,
                               customer_name: str, sales_account_id: int, 
                               debtor_account_id: int, amount: float, 
                               description: str) -> tuple[bool, str, Optional[int]]:
        """
        Log a sales invoice item transaction.
        
        For sales: Debit Debtors (Customer), Credit Sales (Products)
        
        Args:
            user_id: User ID
            invoice_date: Invoice date
            invoice_number: Invoice number (reference)
            customer_name: Customer name (stakeholder)
            sales_account_id: Sales (Products) account ID
            debtor_account_id: Debtors (Trade Debtors) account ID
            amount: Sale amount (excluding VAT)
            description: Item description
        
        Returns:
            Tuple of (success: bool, message: str, entry_id: Optional[int])
        """
        return self.journal_entry_model.create(
            entry_date=invoice_date,
            description=description,
            debit_account_id=debtor_account_id,
            credit_account_id=sales_account_id,
            amount=amount,
            reference=invoice_number,
            user_id=user_id,
            transaction_type="Sales Invoice",
            stakeholder=customer_name
        )
    
    def log_supplier_invoice_item(self, user_id: int, invoice_date: date, invoice_number: str,
                                  supplier_name: str, expense_account_id: int,
                                  creditor_account_id: int, amount: float,
                                  description: str) -> tuple[bool, str, Optional[int]]:
        """
        Log a supplier invoice item transaction.
        
        For purchases: Debit Expense/Stock, Credit Creditors (Supplier)
        
        Args:
            user_id: User ID
            invoice_date: Invoice date
            invoice_number: Invoice number (reference)
            supplier_name: Supplier name (stakeholder)
            expense_account_id: Expense or Stock account ID
            creditor_account_id: Creditors (Trade Creditors) account ID
            amount: Purchase amount (excluding VAT)
            description: Item description
        
        Returns:
            Tuple of (success: bool, message: str, entry_id: Optional[int])
        """
        return self.journal_entry_model.create(
            entry_date=invoice_date,
            description=description,
            debit_account_id=expense_account_id,
            credit_account_id=creditor_account_id,
            amount=amount,
            reference=invoice_number,
            user_id=user_id,
            transaction_type="Supplier Invoice",
            stakeholder=supplier_name
        )
    
    def log_customer_payment(self, user_id: int, payment_date: date, payment_reference: str,
                            customer_name: str, debit_account_id: int, 
                            debtor_account_id: int, amount: float) -> tuple[bool, str, Optional[int]]:
        """
        Log a customer payment transaction.
        
        For customer payments: Debit Bank/Undeposited Funds, Credit Debtors
        
        Args:
            user_id: User ID
            payment_date: Payment date
            payment_reference: Payment reference
            customer_name: Customer name (stakeholder)
            debit_account_id: Bank or Undeposited Funds account ID
            debtor_account_id: Debtors account ID
            amount: Payment amount
        
        Returns:
            Tuple of (success: bool, message: str, entry_id: Optional[int])
        """
        return self.journal_entry_model.create(
            entry_date=payment_date,
            description=f"Payment from {customer_name}",
            debit_account_id=debit_account_id,
            credit_account_id=debtor_account_id,
            amount=amount,
            reference=payment_reference,
            user_id=user_id,
            transaction_type="Customer Payment",
            stakeholder=customer_name
        )
    
    def log_supplier_payment(self, user_id: int, payment_date: date, payment_reference: str,
                            supplier_name: str, creditor_account_id: int,
                            credit_account_id: int, amount: float) -> tuple[bool, str, Optional[int]]:
        """
        Log a supplier payment transaction.
        
        For supplier payments: Debit Creditors, Credit Bank/Undeposited Funds
        
        Args:
            user_id: User ID
            payment_date: Payment date
            payment_reference: Payment reference
            supplier_name: Supplier name (stakeholder)
            creditor_account_id: Creditors account ID
            credit_account_id: Bank or Undeposited Funds account ID
            amount: Payment amount
        
        Returns:
            Tuple of (success: bool, message: str, entry_id: Optional[int])
        """
        return self.journal_entry_model.create(
            entry_date=payment_date,
            description=f"Payment to {supplier_name}",
            debit_account_id=creditor_account_id,
            credit_account_id=credit_account_id,
            amount=amount,
            reference=payment_reference,
            user_id=user_id,
            transaction_type="Supplier Payment",
            stakeholder=supplier_name
        )
    
    def log_stock_adjustment(self, user_id: int, adjustment_date: date, adjustment_reference: str,
                            stock_account_id: int, adjustment_account_id: int,
                            amount: float, description: str) -> tuple[bool, str, Optional[int]]:
        """
        Log a stock adjustment transaction.
        
        Args:
            user_id: User ID
            adjustment_date: Adjustment date
            adjustment_reference: Adjustment reference
            stock_account_id: Stock account ID
            adjustment_account_id: Adjustment account ID (usually Stock Adjustments or Cost of Sales)
            amount: Adjustment amount
            description: Adjustment description
        
        Returns:
            Tuple of (success: bool, message: str, entry_id: Optional[int])
        """
        return self.journal_entry_model.create(
            entry_date=adjustment_date,
            description=description,
            debit_account_id=stock_account_id if amount > 0 else adjustment_account_id,
            credit_account_id=adjustment_account_id if amount > 0 else stock_account_id,
            amount=abs(amount),
            reference=adjustment_reference,
            user_id=user_id,
            transaction_type="Stock Adjustment",
            stakeholder=None
        )
    
    def log_vat_output(self, user_id: int, invoice_date: date, invoice_number: str,
                      customer_name: str, debtor_account_id: int, vat_output_account_id: int,
                      vat_amount: float, description: str) -> tuple[bool, str, Optional[int]]:
        """
        Log a VAT Output transaction (VAT collected on sales).
        
        For VAT Output: Debit Debtors, Credit VAT Output
        
        Args:
            user_id: User ID
            invoice_date: Invoice date
            invoice_number: Invoice number (reference)
            customer_name: Customer name (stakeholder)
            debtor_account_id: Debtors (Trade Debtors) account ID
            vat_output_account_id: VAT Output account ID
            vat_amount: VAT amount
            description: Item description
        
        Returns:
            Tuple of (success: bool, message: str, entry_id: Optional[int])
        """
        return self.journal_entry_model.create(
            entry_date=invoice_date,
            description=f"VAT Output: {description}",
            debit_account_id=debtor_account_id,
            credit_account_id=vat_output_account_id,
            amount=vat_amount,
            reference=invoice_number,
            user_id=user_id,
            transaction_type="Sales Invoice VAT",
            stakeholder=customer_name
        )
    
    def log_vat_input(self, user_id: int, invoice_date: date, invoice_number: str,
                     supplier_name: str, vat_input_account_id: int, creditor_account_id: int,
                     vat_amount: float, description: str) -> tuple[bool, str, Optional[int]]:
        """
        Log a VAT Input transaction (VAT recoverable on purchases).
        
        For VAT Input: Debit VAT Input, Credit Creditors
        
        Args:
            user_id: User ID
            invoice_date: Invoice date
            invoice_number: Invoice number (reference)
            supplier_name: Supplier name (stakeholder)
            vat_input_account_id: VAT Input account ID
            creditor_account_id: Creditors (Trade Creditors) account ID
            vat_amount: VAT amount
            description: Item description
        
        Returns:
            Tuple of (success: bool, message: str, entry_id: Optional[int])
        """
        return self.journal_entry_model.create(
            entry_date=invoice_date,
            description=f"VAT Input: {description}",
            debit_account_id=vat_input_account_id,
            credit_account_id=creditor_account_id,
            amount=vat_amount,
            reference=invoice_number,
            user_id=user_id,
            transaction_type="Supplier Invoice VAT",
            stakeholder=supplier_name
        )
    
    def log_cost_of_sales(self, user_id: int, invoice_date: date, invoice_number: str,
                         customer_name: str, cost_of_sales_account_id: int, stock_account_id: int,
                         cost_amount: float, description: str) -> tuple[bool, str, Optional[int]]:
        """
        Log a Cost of Sales transaction (when product is sold).
        
        For Cost of Sales: Debit Cost of Sales, Credit Stock
        
        Args:
            user_id: User ID
            invoice_date: Invoice date
            invoice_number: Invoice number (reference)
            customer_name: Customer name (stakeholder)
            cost_of_sales_account_id: Cost of Sales account ID
            stock_account_id: Stock account ID
            cost_amount: Cost amount (cost price × quantity)
            description: Item description
        
        Returns:
            Tuple of (success: bool, message: str, entry_id: Optional[int])
        """
        return self.journal_entry_model.create(
            entry_date=invoice_date,
            description=f"Cost of Sales: {description}",
            debit_account_id=cost_of_sales_account_id,
            credit_account_id=stock_account_id,
            amount=cost_amount,
            reference=invoice_number,
            user_id=user_id,
            transaction_type="Cost of Sales",
            stakeholder=customer_name
        )
    
    def reverse_journal_entry(self, entry_id: int, user_id: int, reversal_date: date,
                             reversal_reference: Optional[str] = None) -> tuple[bool, str, Optional[int]]:
        """
        Reverse a journal entry by creating an opposite entry.
        
        Args:
            entry_id: Journal entry ID to reverse
            user_id: User ID
            reversal_date: Date for the reversal entry
            reversal_reference: Optional reference for reversal
        
        Returns:
            Tuple of (success: bool, message: str, reversal_entry_id: Optional[int])
        """
        try:
            # Get the original entry
            original_entry = self.journal_entry_model.get_by_id(entry_id, user_id)
            if not original_entry:
                return False, "Original journal entry not found", None
            
            # Create reversal entry (swap debit and credit)
            return self.journal_entry_model.create(
                entry_date=reversal_date,
                description=f"Reversal: {original_entry.get('description', '')}",
                debit_account_id=original_entry['credit_account_id'],
                credit_account_id=original_entry['debit_account_id'],
                amount=original_entry['amount'],
                reference=reversal_reference or original_entry.get('reference', ''),
                user_id=user_id,
                transaction_type=f"Reversal: {original_entry.get('transaction_type', 'Journal Entry')}",
                stakeholder=original_entry.get('stakeholder')
            )
        except Exception as e:
            return False, f"Error reversing journal entry: {str(e)}", None
    
    def find_entries_by_reference_and_description(self, user_id: int, reference: str,
                                                  description_pattern: str) -> List[Dict]:
        """
        Find journal entries by reference and description pattern.
        
        Args:
            user_id: User ID
            reference: Reference number (e.g., invoice number)
            description_pattern: Description pattern to match
        
        Returns:
            List of journal entry dictionaries
        """
        try:
            all_entries = self.journal_entry_model.get_all(user_id)
            matching_entries = []
            for entry in all_entries:
                if (entry.get('reference') == reference and 
                    description_pattern in entry.get('description', '')):
                    matching_entries.append(entry)
            return matching_entries
        except Exception:
            return []


