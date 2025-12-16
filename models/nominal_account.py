"""Nominal account model for chart of accounts."""
import sqlite3
from typing import Optional, Tuple, List, Dict
import os
from datetime import datetime


class NominalAccount:
    """Nominal account model with database operations."""
    
    # Account type constants
    ACCOUNT_TYPE_ASSET = "Asset"
    ACCOUNT_TYPE_LIABILITY = "Liability"
    ACCOUNT_TYPE_EQUITY = "Equity"
    ACCOUNT_TYPE_INCOME = "Income"
    ACCOUNT_TYPE_EXPENSE = "Expense"
    
    # UK Account code ranges
    CODE_RANGE_ASSET = (1000, 1999)
    CODE_RANGE_LIABILITY = (2000, 2999)
    CODE_RANGE_EQUITY = (3000, 3999)
    CODE_RANGE_INCOME = (4000, 4999)
    CODE_RANGE_EXPENSE = (5000, 5999)
    
    def __init__(self, db_path: str = "data/app.db"):
        """Initialize nominal account model with database path."""
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_database(self):
        """Initialize the database with nominal_accounts table."""
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='nominal_accounts'
            """)
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Create new table
                cursor.execute("""
                    CREATE TABLE nominal_accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        account_code INTEGER NOT NULL,
                        account_name TEXT NOT NULL,
                        account_type TEXT NOT NULL,
                        opening_balance REAL DEFAULT 0.0,
                        is_bank_account INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        UNIQUE(user_id, account_code)
                    )
                """)
            else:
                # Table exists - check for missing columns and add them
                cursor.execute("PRAGMA table_info(nominal_accounts)")
                column_info = cursor.fetchall()
                column_names = [row[1] for row in column_info]
                
                if 'is_bank_account' not in column_names:
                    cursor.execute("ALTER TABLE nominal_accounts ADD COLUMN is_bank_account INTEGER DEFAULT 0")
                
                if 'updated_at' not in column_names:
                    cursor.execute("ALTER TABLE nominal_accounts ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            
            # Clean up orphaned accounts
            cursor.execute("""
                DELETE FROM nominal_accounts 
                WHERE user_id NOT IN (SELECT id FROM users)
                AND user_id IS NOT NULL
            """)
            
            conn.commit()
    
    def _validate_account_code(self, account_code: int, account_type: str, user_id: int, exclude_id: Optional[int] = None) -> Tuple[bool, str]:
        """
        Validate account code is in correct range for account type.
        
        Args:
            account_code: Account code to validate
            account_type: Account type
            user_id: User ID
            exclude_id: Account ID to exclude from uniqueness check (for updates)
        
        Returns:
            Tuple of (is_valid: bool, message: str)
        """
        # Check code range based on account type
        if account_type == self.ACCOUNT_TYPE_ASSET:
            if not (self.CODE_RANGE_ASSET[0] <= account_code <= self.CODE_RANGE_ASSET[1]):
                return False, f"Asset accounts must use codes {self.CODE_RANGE_ASSET[0]}-{self.CODE_RANGE_ASSET[1]}"
        elif account_type == self.ACCOUNT_TYPE_LIABILITY:
            if not (self.CODE_RANGE_LIABILITY[0] <= account_code <= self.CODE_RANGE_LIABILITY[1]):
                return False, f"Liability accounts must use codes {self.CODE_RANGE_LIABILITY[0]}-{self.CODE_RANGE_LIABILITY[1]}"
        elif account_type == self.ACCOUNT_TYPE_EQUITY:
            if not (self.CODE_RANGE_EQUITY[0] <= account_code <= self.CODE_RANGE_EQUITY[1]):
                return False, f"Equity accounts must use codes {self.CODE_RANGE_EQUITY[0]}-{self.CODE_RANGE_EQUITY[1]}"
        elif account_type == self.ACCOUNT_TYPE_INCOME:
            if not (self.CODE_RANGE_INCOME[0] <= account_code <= self.CODE_RANGE_INCOME[1]):
                return False, f"Income accounts must use codes {self.CODE_RANGE_INCOME[0]}-{self.CODE_RANGE_INCOME[1]}"
        elif account_type == self.ACCOUNT_TYPE_EXPENSE:
            if not (self.CODE_RANGE_EXPENSE[0] <= account_code <= self.CODE_RANGE_EXPENSE[1]):
                return False, f"Expense accounts must use codes {self.CODE_RANGE_EXPENSE[0]}-{self.CODE_RANGE_EXPENSE[1]}"
        else:
            return False, f"Invalid account type: {account_type}"
        
        # Check uniqueness
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                if exclude_id:
                    cursor.execute("""
                        SELECT id FROM nominal_accounts 
                        WHERE user_id = ? AND account_code = ? AND id != ?
                    """, (user_id, account_code, exclude_id))
                else:
                    cursor.execute("""
                        SELECT id FROM nominal_accounts 
                        WHERE user_id = ? AND account_code = ?
                    """, (user_id, account_code))
                if cursor.fetchone():
                    return False, "Account code already exists for this user"
        except Exception:
            return False, "Error checking account code uniqueness"
        
        return True, ""
    
    def create(self, account_code: int, account_name: str, account_type: str, 
               opening_balance: float = 0.0, is_bank_account: bool = False, 
               user_id: int = None) -> Tuple[bool, str, Optional[int]]:
        """
        Create a new nominal account.
        
        Args:
            account_code: UK standard account code
            account_name: Account name
            account_type: Account type (Asset, Liability, Equity, Income, Expense)
            opening_balance: Opening balance
            is_bank_account: Whether this is a bank account (for future reconciliation)
            user_id: ID of the user creating the account
        
        Returns:
            Tuple of (success: bool, message: str, account_id: Optional[int])
        """
        if not account_name or not account_name.strip():
            return False, "Account name is required", None
        
        if not user_id:
            return False, "User ID is required", None
        
        account_name = account_name.strip()
        
        # Validate account code
        is_valid, message = self._validate_account_code(account_code, account_type, user_id)
        if not is_valid:
            return False, message, None
        
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO nominal_accounts 
                    (user_id, account_code, account_name, account_type, opening_balance, is_bank_account)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, account_code, account_name, account_type, opening_balance, 1 if is_bank_account else 0))
                conn.commit()
                account_id = cursor.lastrowid
            return True, f"Account created successfully", account_id
        except sqlite3.IntegrityError as e:
            if "account_code" in str(e).lower():
                return False, "Account code already exists for this user", None
            return False, f"Error creating account: {str(e)}", None
        except Exception as e:
            return False, f"Error creating account: {str(e)}", None
    
    def get_all(self, user_id: int) -> List[Dict[str, any]]:
        """
        Get all nominal accounts for a specific user.
        
        Args:
            user_id: ID of the user
        
        Returns:
            List of account dictionaries with calculated current balance
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        id,
                        account_code,
                        account_name,
                        account_type,
                        opening_balance,
                        is_bank_account,
                        created_at,
                        updated_at
                    FROM nominal_accounts 
                    WHERE user_id = ? 
                    ORDER BY account_code
                """, (user_id,))
                rows = cursor.fetchall()
                accounts = [dict(row) for row in rows]
                
                # Calculate current balance for each account
                for account in accounts:
                    account['current_balance'] = self._calculate_balance(account['id'], account['opening_balance'])
                
                return accounts
        except Exception as e:
            return []
    
    def get_by_id(self, account_id: int, user_id: int) -> Optional[Dict[str, any]]:
        """
        Get a nominal account by ID for a specific user.
        
        Args:
            account_id: Account ID
            user_id: ID of the user
        
        Returns:
            Account dictionary with calculated current balance or None if not found
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        id,
                        account_code,
                        account_name,
                        account_type,
                        opening_balance,
                        is_bank_account,
                        created_at,
                        updated_at
                    FROM nominal_accounts 
                    WHERE id = ? AND user_id = ?
                """, (account_id, user_id))
                row = cursor.fetchone()
                if row:
                    account = dict(row)
                    account['current_balance'] = self._calculate_balance(account['id'], account['opening_balance'])
                    return account
                return None
        except Exception:
            return None
    
    def update(self, account_id: int, account_code: int, account_name: str, 
               account_type: str, opening_balance: float = 0.0, 
               is_bank_account: bool = False, user_id: int = None) -> Tuple[bool, str]:
        """
        Update a nominal account.
        
        Args:
            account_id: Account ID
            account_code: New account code
            account_name: New account name
            account_type: New account type
            opening_balance: New opening balance
            is_bank_account: Whether this is a bank account
            user_id: ID of the user
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not account_name or not account_name.strip():
            return False, "Account name is required"
        
        if not user_id:
            return False, "User ID is required"
        
        account_name = account_name.strip()
        
        # Validate account code
        is_valid, message = self._validate_account_code(account_code, account_type, user_id, exclude_id=account_id)
        if not is_valid:
            return False, message
        
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Check if account exists and belongs to user
                cursor.execute("""
                    SELECT id FROM nominal_accounts 
                    WHERE id = ? AND user_id = ?
                """, (account_id, user_id))
                if not cursor.fetchone():
                    return False, "Account not found"
                
                cursor.execute("""
                    UPDATE nominal_accounts 
                    SET account_code = ?, account_name = ?, account_type = ?, 
                        opening_balance = ?, is_bank_account = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ?
                """, (account_code, account_name, account_type, opening_balance, 1 if is_bank_account else 0, account_id, user_id))
                
                conn.commit()
            return True, "Account updated successfully"
        except sqlite3.IntegrityError as e:
            if "account_code" in str(e).lower():
                return False, "Account code already exists for this user"
            return False, f"Error updating account: {str(e)}"
        except Exception as e:
            return False, f"Error updating account: {str(e)}"
    
    def delete(self, account_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Delete a nominal account.
        
        Args:
            account_id: Account ID
            user_id: ID of the user
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Check if account has journal entries
                cursor.execute("""
                    SELECT COUNT(*) FROM journal_entries 
                    WHERE (debit_account_id = ? OR credit_account_id = ?) AND user_id = ?
                """, (account_id, account_id, user_id))
                entry_count = cursor.fetchone()[0]
                
                if entry_count > 0:
                    return False, "Cannot delete account with existing journal entries"
                
                # Check if account exists and belongs to user
                cursor.execute("""
                    SELECT id FROM nominal_accounts 
                    WHERE id = ? AND user_id = ?
                """, (account_id, user_id))
                if not cursor.fetchone():
                    return False, "Account not found"
                
                cursor.execute("""
                    DELETE FROM nominal_accounts 
                    WHERE id = ? AND user_id = ?
                """, (account_id, user_id))
                
                conn.commit()
            return True, "Account deleted successfully"
        except Exception as e:
            return False, f"Error deleting account: {str(e)}"
    
    def _calculate_balance(self, account_id: int, opening_balance: float) -> float:
        """
        Calculate current balance for an account from journal entries.
        
        Args:
            account_id: Account ID
            opening_balance: Opening balance
        
        Returns:
            Current balance
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Get total debits (increases for assets/expenses, decreases for liabilities/equity/income)
                cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0.0)
                    FROM journal_entries
                    WHERE debit_account_id = ?
                """, (account_id,))
                total_debits = cursor.fetchone()[0] or 0.0
                
                # Get total credits (decreases for assets/expenses, increases for liabilities/equity/income)
                cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0.0)
                    FROM journal_entries
                    WHERE credit_account_id = ?
                """, (account_id,))
                total_credits = cursor.fetchone()[0] or 0.0
                
                # Get account type to determine balance calculation
                cursor.execute("""
                    SELECT account_type FROM nominal_accounts WHERE id = ?
                """, (account_id,))
                result = cursor.fetchone()
                if not result:
                    return opening_balance
                
                account_type = result[0]
                
                # Calculate balance based on account type
                # Assets and Expenses: Opening + Debits - Credits
                # Liabilities, Equity, Income: Opening + Credits - Debits
                if account_type in [self.ACCOUNT_TYPE_ASSET, self.ACCOUNT_TYPE_EXPENSE]:
                    balance = opening_balance + total_debits - total_credits
                else:
                    balance = opening_balance + total_credits - total_debits
                
                return balance
        except Exception:
            return opening_balance
    
    def get_balance(self, account_id: int, user_id: int) -> float:
        """
        Get current balance for an account.
        
        Args:
            account_id: Account ID
            user_id: ID of the user
        
        Returns:
            Current balance
        """
        account = self.get_by_id(account_id, user_id)
        if account:
            return account.get('current_balance', 0.0)
        return 0.0

