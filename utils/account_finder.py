"""Account finder utility for locating nominal accounts by type."""
from typing import Optional
from models.nominal_account import NominalAccount


def find_trade_debtors_account(user_id: int, db_path: str = "data/app.db") -> Optional[int]:
    """
    Find Trade Debtors account (Asset - Current Asset).
    
    Args:
        user_id: User ID
        db_path: Database path
        
    Returns:
        Account ID or None if not found
    """
    nominal_account_model = NominalAccount(db_path)
    accounts = nominal_account_model.get_all(user_id)
    
    for account in accounts:
        account_type = account.get('account_type', '')
        account_subtype = account.get('account_subtype', '')
        account_name = account.get('account_name', '').lower()
        
        # Look for Current Asset account with "debtor" or "receivable" in name
        if account_type == 'Asset' and account_subtype == 'Current Asset':
            if 'debtor' in account_name or 'receivable' in account_name or 'trade debtor' in account_name:
                return account['id']
    
    # Fallback: return first Current Asset account
    for account in accounts:
        if account.get('account_type') == 'Asset' and account.get('account_subtype') == 'Current Asset':
            return account['id']
    
    return None


def find_trade_creditors_account(user_id: int, db_path: str = "data/app.db") -> Optional[int]:
    """
    Find Trade Creditors account (Liability - Current Liability or Purchase Ledger).
    
    Args:
        user_id: User ID
        db_path: Database path
        
    Returns:
        Account ID or None if not found
    """
    nominal_account_model = NominalAccount(db_path)
    accounts = nominal_account_model.get_all(user_id)
    
    for account in accounts:
        account_type = account.get('account_type', '')
        account_subtype = account.get('account_subtype', '')
        account_name = account.get('account_name', '').lower()
        account_code = account.get('account_code', 0)
        
        # Look for Purchase Ledger account (code 2100) or accounts with "purchase ledger" in name
        if account_type == 'Liability':
            if (account_code == 2100 or 
                'purchase ledger' in account_name or
                (account_subtype == 'Purchase Ledger')):
                return account['id']
        
        # Look for Current Liability account with "creditor" or "payable" in name
        if account_type == 'Liability' and account_subtype == 'Current Liability':
            if 'creditor' in account_name or 'payable' in account_name or 'trade creditor' in account_name:
                return account['id']
    
    # Fallback: return first Current Liability or Purchase Ledger account
    for account in accounts:
        if account.get('account_type') == 'Liability':
            if (account.get('account_subtype') in ['Current Liability', 'Purchase Ledger'] or
                account.get('account_code') == 2100):
                return account['id']
    
    return None


def find_sales_account(user_id: int, db_path: str = "data/app.db") -> Optional[int]:
    """
    Find Sales/Turnover account (Income - Turnover).
    
    Args:
        user_id: User ID
        db_path: Database path
        
    Returns:
        Account ID or None if not found
    """
    nominal_account_model = NominalAccount(db_path)
    accounts = nominal_account_model.get_all(user_id)
    
    for account in accounts:
        account_type = account.get('account_type', '')
        account_subtype = account.get('account_subtype', '')
        account_name = account.get('account_name', '').lower()
        
        # Look for Turnover account
        if account_type == 'Income' and account_subtype == 'Turnover':
            if 'sales' in account_name or 'turnover' in account_name or 'revenue' in account_name:
                return account['id']
    
    # Fallback: return first Turnover account
    for account in accounts:
        if account.get('account_type') == 'Income' and account.get('account_subtype') == 'Turnover':
            return account['id']
    
    return None


def find_bank_account(user_id: int, db_path: str = "data/app.db", payment_method: Optional[str] = None) -> Optional[int]:
    """
    Find Bank account (Asset - Bank Account).
    
    Args:
        user_id: User ID
        db_path: Database path
        payment_method: Optional payment method (for future use)
        
    Returns:
        Account ID or None if not found
    """
    nominal_account_model = NominalAccount(db_path)
    accounts = nominal_account_model.get_all(user_id)
    
    for account in accounts:
        account_type = account.get('account_type', '')
        account_subtype = account.get('account_subtype', '')
        is_bank = account.get('is_bank_account', False)
        
        # Look for Bank Account
        if account_type == 'Asset' and account_subtype == 'Bank Account' and is_bank:
            return account['id']
    
    # Fallback: return first Bank Account
    for account in accounts:
        if account.get('account_type') == 'Asset' and account.get('account_subtype') == 'Bank Account':
            return account['id']
    
    return None


def find_undeposited_funds_account(user_id: int, db_path: str = "data/app.db") -> Optional[int]:
    """
    Find Undeposited Funds account (Asset - Current Asset).
    
    Args:
        user_id: User ID
        db_path: Database path
        
    Returns:
        Account ID or None if not found
    """
    nominal_account_model = NominalAccount(db_path)
    accounts = nominal_account_model.get_all(user_id)
    
    for account in accounts:
        account_type = account.get('account_type', '')
        account_subtype = account.get('account_subtype', '')
        account_name = account.get('account_name', '').lower()
        
        # Look for Undeposited Funds account
        if account_type == 'Asset' and account_subtype == 'Current Asset':
            if 'undeposited' in account_name or 'funds' in account_name:
                return account['id']
    
    # Fallback: return first Current Asset account (if no specific Undeposited Funds found)
    for account in accounts:
        if account.get('account_type') == 'Asset' and account.get('account_subtype') == 'Current Asset':
            return account['id']
    
    return None


def find_stock_asset_account(user_id: int, db_path: str = "data/app.db") -> Optional[int]:
    """
    Find Stock Asset account (Asset - Current Asset or Stock).
    
    Args:
        user_id: User ID
        db_path: Database path
        
    Returns:
        Account ID or None if not found
    """
    nominal_account_model = NominalAccount(db_path)
    accounts = nominal_account_model.get_all(user_id)
    
    for account in accounts:
        account_type = account.get('account_type', '')
        account_subtype = account.get('account_subtype', '')
        account_name = account.get('account_name', '').lower()
        
        # Look for Stock Asset account
        if account_type == 'Asset':
            if 'stock' in account_name or 'inventory' in account_name:
                return account['id']
    
    # Fallback: return first Current Asset account
    for account in accounts:
        if account.get('account_type') == 'Asset' and account.get('account_subtype') == 'Current Asset':
            return account['id']
    
    return None


def find_sales_products_account(user_id: int, db_path: str = "data/app.db") -> Optional[int]:
    """
    Find Sales (Products) account (Income - Turnover).
    
    Args:
        user_id: User ID
        db_path: Database path
        
    Returns:
        Account ID or None if not found
    """
    # This is essentially the same as find_sales_account, but with product-specific naming
    return find_sales_account(user_id, db_path)


def find_cost_of_sales_account(user_id: int, db_path: str = "data/app.db") -> Optional[int]:
    """
    Find Cost of Sales account (Expense - Cost of Sales).
    
    Args:
        user_id: User ID
        db_path: Database path
        
    Returns:
        Account ID or None if not found
    """
    nominal_account_model = NominalAccount(db_path)
    accounts = nominal_account_model.get_all(user_id)
    
    for account in accounts:
        account_type = account.get('account_type', '')
        account_subtype = account.get('account_subtype', '')
        account_name = account.get('account_name', '').lower()
        
        # Look for Cost of Sales account
        if account_type == 'Expense' and account_subtype == 'Cost of Sales':
            if 'cost' in account_name or 'sales' in account_name or 'cogs' in account_name:
                return account['id']
    
    # Fallback: return first Cost of Sales account
    for account in accounts:
        if account.get('account_type') == 'Expense' and account.get('account_subtype') == 'Cost of Sales':
            return account['id']
    
    return None


def find_vat_input_account(user_id: int, db_path: str = "data/app.db") -> Optional[int]:
    """
    Find VAT Input account (Asset - Current Asset).
    
    Args:
        user_id: User ID
        db_path: Database path
        
    Returns:
        Account ID or None if not found
    """
    nominal_account_model = NominalAccount(db_path)
    accounts = nominal_account_model.get_all(user_id)
    
    for account in accounts:
        account_type = account.get('account_type', '')
        account_subtype = account.get('account_subtype', '')
        account_name = account.get('account_name', '').lower()
        
        # Look for VAT Input account
        if account_type == 'Asset' and account_subtype == 'Current Asset':
            if 'vat input' in account_name or 'vat recoverable' in account_name or 'input vat' in account_name:
                return account['id']
    
    # Fallback: return first Current Asset account (if no specific VAT Input found)
    for account in accounts:
        if account.get('account_type') == 'Asset' and account.get('account_subtype') == 'Current Asset':
            return account['id']
    
    return None


def find_vat_output_account(user_id: int, db_path: str = "data/app.db") -> Optional[int]:
    """
    Find VAT Output account (Liability - Current Liability).
    
    Args:
        user_id: User ID
        db_path: Database path
        
    Returns:
        Account ID or None if not found
    """
    nominal_account_model = NominalAccount(db_path)
    accounts = nominal_account_model.get_all(user_id)
    
    for account in accounts:
        account_type = account.get('account_type', '')
        account_subtype = account.get('account_subtype', '')
        account_name = account.get('account_name', '').lower()
        
        # Look for VAT Output account
        if account_type == 'Liability' and account_subtype == 'Current Liability':
            if 'vat output' in account_name or 'vat collected' in account_name or 'output vat' in account_name:
                return account['id']
    
    # Fallback: return first Current Liability account (if no specific VAT Output found)
    for account in accounts:
        if account.get('account_type') == 'Liability' and account.get('account_subtype') == 'Current Liability':
            return account['id']
    
    return None


