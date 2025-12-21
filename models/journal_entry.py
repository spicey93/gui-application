"""Journal entry model for double-entry bookkeeping."""
import sqlite3
from typing import Optional, Tuple, List, Dict
import os
from datetime import date, datetime


class JournalEntry:
    """Journal entry model with database operations."""
    
    def __init__(self, db_path: str = "data/app.db"):
        """Initialize journal entry model with database path."""
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_database(self):
        """Initialize the database with journal_entries table."""
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='journal_entries'
            """)
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Create new table
                cursor.execute("""
                    CREATE TABLE journal_entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        entry_date DATE NOT NULL,
                        description TEXT NOT NULL,
                        debit_account_id INTEGER NOT NULL,
                        credit_account_id INTEGER NOT NULL,
                        amount REAL NOT NULL,
                        reference TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        FOREIGN KEY (debit_account_id) REFERENCES nominal_accounts(id),
                        FOREIGN KEY (credit_account_id) REFERENCES nominal_accounts(id)
                    )
                """)
            
            conn.commit()
    
    def create(self, entry_date: date, description: str, debit_account_id: int, 
               credit_account_id: int, amount: float, reference: Optional[str] = None, 
               user_id: int = None) -> Tuple[bool, str, Optional[int]]:
        """
        Create a new journal entry (double-entry bookkeeping).
        
        Args:
            entry_date: Entry date
            description: Entry description
            debit_account_id: Debit account ID
            credit_account_id: Credit account ID
            amount: Transaction amount (must be positive)
            reference: Optional reference number
            user_id: ID of the user creating the entry
        
        Returns:
            Tuple of (success: bool, message: str, entry_id: Optional[int])
        """
        if not description or not description.strip():
            return False, "Description is required", None
        
        if not user_id:
            return False, "User ID is required", None
        
        if amount <= 0:
            return False, "Amount must be greater than zero", None
        
        if debit_account_id == credit_account_id:
            return False, "Debit and credit accounts cannot be the same", None
        
        description = description.strip()
        reference = reference.strip() if reference else None
        
        # Validate accounts exist and belong to user
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Check debit account
                cursor.execute("""
                    SELECT id FROM nominal_accounts 
                    WHERE id = ? AND user_id = ?
                """, (debit_account_id, user_id))
                if not cursor.fetchone():
                    return False, "Debit account not found or does not belong to user", None
                
                # Check credit account
                cursor.execute("""
                    SELECT id FROM nominal_accounts 
                    WHERE id = ? AND user_id = ?
                """, (credit_account_id, user_id))
                if not cursor.fetchone():
                    return False, "Credit account not found or does not belong to user", None
                
                # Create journal entry
                cursor.execute("""
                    INSERT INTO journal_entries 
                    (user_id, entry_date, description, debit_account_id, credit_account_id, amount, reference)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (user_id, entry_date.isoformat(), description, debit_account_id, credit_account_id, amount, reference))
                conn.commit()
                entry_id = cursor.lastrowid
            return True, "Journal entry created successfully", entry_id
        except Exception as e:
            return False, f"Error creating journal entry: {str(e)}", None
    
    def get_all(self, user_id: int, account_id: Optional[int] = None) -> List[Dict[str, any]]:
        """
        Get all journal entries for a user, optionally filtered by account.
        
        Args:
            user_id: ID of the user
            account_id: Optional account ID to filter entries (entries where account is debit or credit)
        
        Returns:
            List of journal entry dictionaries
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if account_id:
                    cursor.execute("""
                        SELECT 
                            je.id,
                            je.entry_date,
                            je.description,
                            je.debit_account_id,
                            je.credit_account_id,
                            je.amount,
                            je.reference,
                            je.created_at,
                            da.account_code as debit_account_code,
                            da.account_name as debit_account_name,
                            ca.account_code as credit_account_code,
                            ca.account_name as credit_account_name
                        FROM journal_entries je
                        LEFT JOIN nominal_accounts da ON je.debit_account_id = da.id
                        LEFT JOIN nominal_accounts ca ON je.credit_account_id = ca.id
                        WHERE je.user_id = ? 
                        AND (je.debit_account_id = ? OR je.credit_account_id = ?)
                        ORDER BY je.entry_date DESC, je.created_at DESC
                    """, (user_id, account_id, account_id))
                else:
                    cursor.execute("""
                        SELECT 
                            je.id,
                            je.entry_date,
                            je.description,
                            je.debit_account_id,
                            je.credit_account_id,
                            je.amount,
                            je.reference,
                            je.created_at,
                            da.account_code as debit_account_code,
                            da.account_name as debit_account_name,
                            ca.account_code as credit_account_code,
                            ca.account_name as credit_account_name
                        FROM journal_entries je
                        LEFT JOIN nominal_accounts da ON je.debit_account_id = da.id
                        LEFT JOIN nominal_accounts ca ON je.credit_account_id = ca.id
                        WHERE je.user_id = ? 
                        ORDER BY je.entry_date DESC, je.created_at DESC
                    """, (user_id,))
                
                rows = cursor.fetchall()
                entries = []
                for row in rows:
                    entry = dict(row)
                    # Convert date string to date object
                    if entry['entry_date']:
                        entry['entry_date'] = datetime.strptime(entry['entry_date'], '%Y-%m-%d').date()
                    entries.append(entry)
                
                return entries
        except Exception as e:
            return []
    
    def get_by_id(self, entry_id: int, user_id: int) -> Optional[Dict[str, any]]:
        """
        Get a journal entry by ID for a specific user.
        
        Args:
            entry_id: Entry ID
            user_id: ID of the user
        
        Returns:
            Journal entry dictionary or None if not found
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        je.id,
                        je.entry_date,
                        je.description,
                        je.debit_account_id,
                        je.credit_account_id,
                        je.amount,
                        je.reference,
                        je.created_at,
                        da.account_code as debit_account_code,
                        da.account_name as debit_account_name,
                        ca.account_code as credit_account_code,
                        ca.account_name as credit_account_name
                    FROM journal_entries je
                    LEFT JOIN nominal_accounts da ON je.debit_account_id = da.id
                    LEFT JOIN nominal_accounts ca ON je.credit_account_id = ca.id
                    WHERE je.id = ? AND je.user_id = ?
                """, (entry_id, user_id))
                row = cursor.fetchone()
                if row:
                    entry = dict(row)
                    # Convert date string to date object
                    if entry['entry_date']:
                        entry['entry_date'] = datetime.strptime(entry['entry_date'], '%Y-%m-%d').date()
                    return entry
                return None
        except Exception:
            return None
    
    def delete(self, entry_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Delete a journal entry.
        
        Args:
            entry_id: Entry ID
            user_id: ID of the user
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Check if entry exists and belongs to user
                cursor.execute("""
                    SELECT id FROM journal_entries 
                    WHERE id = ? AND user_id = ?
                """, (entry_id, user_id))
                if not cursor.fetchone():
                    return False, "Journal entry not found"
                
                cursor.execute("""
                    DELETE FROM journal_entries 
                    WHERE id = ? AND user_id = ?
                """, (entry_id, user_id))
                
                conn.commit()
            return True, "Journal entry deleted successfully"
        except Exception as e:
            return False, f"Error deleting journal entry: {str(e)}"
    
    def get_account_entries(self, account_id: int, user_id: int) -> List[Dict[str, any]]:
        """
        Get all journal entries for a specific account.
        
        Args:
            account_id: Account ID
            user_id: ID of the user
        
        Returns:
            List of journal entry dictionaries with debit/credit indicators
        """
        entries = self.get_all(user_id, account_id)
        
        # Add debit/credit indicator for each entry
        for entry in entries:
            if entry['debit_account_id'] == account_id:
                entry['is_debit'] = True
                entry['is_credit'] = False
            else:
                entry['is_debit'] = False
                entry['is_credit'] = True
        
        return entries


