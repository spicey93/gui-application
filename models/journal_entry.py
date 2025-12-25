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
                        transaction_type TEXT,
                        journal_number TEXT,
                        stakeholder TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        FOREIGN KEY (debit_account_id) REFERENCES nominal_accounts(id),
                        FOREIGN KEY (credit_account_id) REFERENCES nominal_accounts(id)
                    )
                """)
            else:
                # Check for missing columns and add them
                cursor.execute("PRAGMA table_info(journal_entries)")
                column_info = cursor.fetchall()
                column_names = [row[1] for row in column_info]
                
                if 'transaction_type' not in column_names:
                    cursor.execute("ALTER TABLE journal_entries ADD COLUMN transaction_type TEXT")
                
                if 'journal_number' not in column_names:
                    cursor.execute("ALTER TABLE journal_entries ADD COLUMN journal_number TEXT")
                
                if 'stakeholder' not in column_names:
                    cursor.execute("ALTER TABLE journal_entries ADD COLUMN stakeholder TEXT")
            
            conn.commit()
    
    def _generate_journal_number(self, user_id: int, transaction_type: str) -> str:
        """
        Generate a unique journal number for Journal Entry or Transfer types.
        
        Args:
            user_id: User ID
            transaction_type: Transaction type (Journal Entry or Transfer)
        
        Returns:
            Journal number string (e.g., "JNL-0001" or "TFR-0001")
        """
        prefix = "JNL" if transaction_type == "Journal Entry" else "TFR"
        
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                # Get the highest journal number for this prefix
                cursor.execute("""
                    SELECT journal_number FROM journal_entries 
                    WHERE user_id = ? AND journal_number LIKE ? 
                    ORDER BY journal_number DESC LIMIT 1
                """, (user_id, f"{prefix}-%"))
                
                result = cursor.fetchone()
                if result:
                    last_number = result[0]
                    # Extract number and increment
                    try:
                        num_part = int(last_number.split('-')[1])
                        new_num = num_part + 1
                    except (IndexError, ValueError):
                        new_num = 1
                else:
                    new_num = 1
                
                return f"{prefix}-{new_num:04d}"
        except Exception:
            return f"{prefix}-0001"
    
    def create(self, entry_date: date, description: str, debit_account_id: int, 
               credit_account_id: int, amount: float, reference: Optional[str] = None, 
               user_id: int = None, transaction_type: Optional[str] = None,
               journal_number: Optional[str] = None, stakeholder: Optional[str] = None) -> Tuple[bool, str, Optional[int]]:
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
            transaction_type: Transaction type (Journal Entry, Sales Invoice, etc.)
            journal_number: Optional journal number (auto-generated for Journal Entry/Transfer if None)
            stakeholder: Optional stakeholder name (customer, supplier, etc.)
        
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
                
                # Auto-generate journal number for Journal Entry and Transfer types
                if transaction_type in ["Journal Entry", "Transfer"] and not journal_number:
                    journal_number = self._generate_journal_number(user_id, transaction_type)
                
                # Create journal entry
                cursor.execute("""
                    INSERT INTO journal_entries 
                    (user_id, entry_date, description, debit_account_id, credit_account_id, amount, reference,
                     transaction_type, journal_number, stakeholder)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, entry_date.isoformat(), description, debit_account_id, credit_account_id, amount, reference,
                      transaction_type, journal_number, stakeholder))
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
                            je.transaction_type,
                            je.journal_number,
                            je.stakeholder,
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
                            je.transaction_type,
                            je.journal_number,
                            je.stakeholder,
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
                        je.transaction_type,
                        je.journal_number,
                        je.stakeholder,
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


