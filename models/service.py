"""Service model for service management."""
import sqlite3
from typing import Optional, Tuple, List, Dict
import os


class Service:
    """Service model with database operations."""
    
    def __init__(self, db_path: str = "data/app.db"):
        """Initialize service model with database path."""
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_database(self):
        """Initialize the database with services table."""
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='services'
            """)
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Create new table with proper constraints
                cursor.execute("""
                    CREATE TABLE services (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        user_service_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        code TEXT NOT NULL,
                        group_name TEXT,
                        description TEXT,
                        estimated_cost REAL DEFAULT 0.0,
                        vat_code TEXT NOT NULL DEFAULT 'S',
                        income_account_id INTEGER,
                        retail_price REAL DEFAULT 0.0,
                        trade_price REAL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        FOREIGN KEY (income_account_id) REFERENCES nominal_accounts(id),
                        UNIQUE(user_id, user_service_id),
                        UNIQUE(user_id, code)
                    )
                """)
            else:
                # Table exists - check for missing columns and add them
                cursor.execute("PRAGMA table_info(services)")
                column_info = cursor.fetchall()
                column_names = [row[1] for row in column_info]
                
                if 'user_id' not in column_names:
                    cursor.execute("ALTER TABLE services ADD COLUMN user_id INTEGER")
                    cursor.execute("DELETE FROM services WHERE user_id IS NULL")
                
                if 'user_service_id' not in column_names:
                    cursor.execute("ALTER TABLE services ADD COLUMN user_service_id INTEGER")
                    cursor.execute("""
                        UPDATE services 
                        SET user_service_id = (
                            SELECT COUNT(*) + 1
                            FROM services s2
                            WHERE s2.user_id = services.user_id 
                            AND s2.id < services.id
                        )
                        WHERE user_service_id IS NULL
                    """)
                    cursor.execute("UPDATE services SET user_service_id = 1 WHERE user_service_id IS NULL")
                    
                    try:
                        cursor.execute("""
                            CREATE UNIQUE INDEX IF NOT EXISTS idx_service_user_service_id 
                            ON services(user_id, user_service_id)
                        """)
                    except sqlite3.OperationalError:
                        pass
                
                if 'group_name' not in column_names:
                    cursor.execute("ALTER TABLE services ADD COLUMN group_name TEXT")
                
                if 'description' not in column_names:
                    cursor.execute("ALTER TABLE services ADD COLUMN description TEXT")
                
                if 'estimated_cost' not in column_names:
                    cursor.execute("ALTER TABLE services ADD COLUMN estimated_cost REAL DEFAULT 0.0")
                
                if 'vat_code' not in column_names:
                    cursor.execute("ALTER TABLE services ADD COLUMN vat_code TEXT NOT NULL DEFAULT 'S'")
                
                if 'income_account_id' not in column_names:
                    cursor.execute("ALTER TABLE services ADD COLUMN income_account_id INTEGER")
                    try:
                        cursor.execute("""
                            CREATE INDEX IF NOT EXISTS idx_service_income_account 
                            ON services(income_account_id)
                        """)
                    except sqlite3.OperationalError:
                        pass
                
                if 'retail_price' not in column_names:
                    cursor.execute("ALTER TABLE services ADD COLUMN retail_price REAL DEFAULT 0.0")
                
                if 'trade_price' not in column_names:
                    cursor.execute("ALTER TABLE services ADD COLUMN trade_price REAL DEFAULT 0.0")
                
                # Ensure UNIQUE constraint exists for code
                try:
                    cursor.execute("""
                        CREATE UNIQUE INDEX IF NOT EXISTS idx_service_user_code 
                        ON services(user_id, code)
                    """)
                except sqlite3.OperationalError:
                    pass
            
            # Clean up orphaned services
            cursor.execute("""
                DELETE FROM services 
                WHERE user_id NOT IN (SELECT id FROM users)
                AND user_id IS NOT NULL
            """)
            
            conn.commit()
    
    def create(
        self,
        name: str,
        code: str,
        user_id: int,
        group_name: Optional[str] = None,
        description: Optional[str] = None,
        estimated_cost: float = 0.0,
        vat_code: str = 'S',
        income_account_id: Optional[int] = None,
        retail_price: float = 0.0,
        trade_price: float = 0.0
    ) -> Tuple[bool, str]:
        """
        Create a new service.
        
        Args:
            name: Service name
            code: Unique service code (unique per user)
            user_id: ID of the user creating the service
            group_name: Service group (optional)
            description: Service description (optional)
            estimated_cost: Estimated cost (default 0.0)
            vat_code: VAT code (default 'S')
            income_account_id: Income account ID (optional)
            retail_price: Retail price (default 0.0)
            trade_price: Trade price (default 0.0)
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not name or not code:
            return False, "Name and code are required"
        
        if not user_id:
            return False, "User ID is required"
        
        name = name.strip()
        code = code.strip()
        group_name = group_name.strip() if group_name else None
        description = description.strip() if description else None
        
        if not name:
            return False, "Name cannot be empty"
        
        if not code:
            return False, "Code cannot be empty"
        
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Calculate the next user_service_id for this user
                cursor.execute("""
                    SELECT COALESCE(MAX(user_service_id), 0) + 1 
                    FROM services 
                    WHERE user_id = ?
                """, (user_id,))
                next_user_service_id = cursor.fetchone()[0]
                
                cursor.execute("""
                    INSERT INTO services (
                        name, code, user_id, user_service_id, group_name, description,
                        estimated_cost, vat_code, income_account_id, retail_price, trade_price
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    name, code, user_id, next_user_service_id, group_name, description,
                    estimated_cost, vat_code, income_account_id, retail_price, trade_price
                ))
                conn.commit()
                return True, f"Service created successfully (ID: {next_user_service_id})"
        except sqlite3.IntegrityError as e:
            if "code" in str(e).lower():
                return False, "Code already exists for this user"
            else:
                return False, f"Error creating service: {str(e)}"
        except Exception as e:
            return False, f"Error creating service: {str(e)}"
    
    def get_all(self, user_id: int) -> List[Dict[str, any]]:
        """
        Get all services for a specific user.
        
        Args:
            user_id: ID of the user
        
        Returns:
            List of service dictionaries (using user_service_id as id for display)
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        id as internal_id,
                        COALESCE(user_service_id, id) as id,
                        name,
                        code,
                        group_name,
                        description,
                        estimated_cost,
                        vat_code,
                        income_account_id,
                        retail_price,
                        trade_price,
                        created_at
                    FROM services 
                    WHERE user_id = ? 
                    ORDER BY user_service_id
                """, (user_id,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            return []
    
    def get_by_id(self, service_id: int, user_id: int) -> Optional[Dict[str, any]]:
        """
        Get a service by user_service_id for a specific user.
        
        Args:
            service_id: User service ID (user_service_id)
            user_id: ID of the user
        
        Returns:
            Service dictionary or None if not found
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        id as internal_id,
                        COALESCE(user_service_id, id) as id,
                        name,
                        code,
                        group_name,
                        description,
                        estimated_cost,
                        vat_code,
                        income_account_id,
                        retail_price,
                        trade_price,
                        created_at
                    FROM services 
                    WHERE user_service_id = ? AND user_id = ?
                """, (service_id, user_id))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception:
            return None
    
    def update(
        self,
        service_id: int,
        name: str,
        code: str,
        user_id: int,
        group_name: Optional[str] = None,
        description: Optional[str] = None,
        estimated_cost: float = 0.0,
        vat_code: str = 'S',
        income_account_id: Optional[int] = None,
        retail_price: float = 0.0,
        trade_price: float = 0.0
    ) -> Tuple[bool, str]:
        """
        Update a service by user_service_id.
        
        Args:
            service_id: User service ID (user_service_id)
            name: New service name
            code: New service code
            user_id: ID of the user
            group_name: Service group (optional)
            description: Service description (optional)
            estimated_cost: Estimated cost
            vat_code: VAT code
            income_account_id: Income account ID (optional)
            retail_price: Retail price
            trade_price: Trade price
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not name or not code:
            return False, "Name and code are required"
        
        name = name.strip()
        code = code.strip()
        group_name = group_name.strip() if group_name else None
        description = description.strip() if description else None
        
        if not name:
            return False, "Name cannot be empty"
        
        if not code:
            return False, "Code cannot be empty"
        
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Get the internal ID for this service
                cursor.execute(
                    "SELECT id FROM services WHERE user_service_id = ? AND user_id = ?",
                    (service_id, user_id)
                )
                internal_id_result = cursor.fetchone()
                
                if not internal_id_result:
                    return False, "Service not found"
                
                internal_id = internal_id_result[0]
                
                # Check if code already exists for another service of the same user
                cursor.execute(
                    "SELECT id FROM services WHERE code = ? AND id != ? AND user_id = ?",
                    (code, internal_id, user_id)
                )
                if cursor.fetchone():
                    return False, "Code already exists"
                
                cursor.execute("""
                    UPDATE services 
                    SET name = ?, code = ?, group_name = ?, description = ?,
                        estimated_cost = ?, vat_code = ?, income_account_id = ?,
                        retail_price = ?, trade_price = ?
                    WHERE user_service_id = ? AND user_id = ?
                """, (
                    name, code, group_name, description, estimated_cost, vat_code,
                    income_account_id, retail_price, trade_price, service_id, user_id
                ))
                
                if cursor.rowcount == 0:
                    return False, "Service not found"
                
                conn.commit()
                return True, "Service updated successfully"
        except Exception as e:
            return False, f"Error updating service: {str(e)}"
    
    def delete(self, service_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Delete a service by user_service_id.
        
        Args:
            service_id: User service ID (user_service_id)
            user_id: ID of the user
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM services WHERE user_service_id = ? AND user_id = ?", 
                    (service_id, user_id)
                )
                
                if cursor.rowcount == 0:
                    return False, "Service not found"
                
                # Recalculate user_service_id for remaining services to maintain sequential IDs
                cursor.execute("""
                    SELECT id FROM services 
                    WHERE user_id = ? 
                    ORDER BY id
                """, (user_id,))
                remaining_ids = [row[0] for row in cursor.fetchall()]
                
                # Update each service with sequential user_service_id
                for index, internal_id in enumerate(remaining_ids, start=1):
                    cursor.execute("""
                        UPDATE services 
                        SET user_service_id = ? 
                        WHERE id = ? AND user_id = ?
                    """, (index, internal_id, user_id))
                
                conn.commit()
                return True, "Service deleted successfully"
        except Exception as e:
            return False, f"Error deleting service: {str(e)}"
    
    def exists(self, code: str, user_id: int) -> bool:
        """Check if a service with the code exists for a user."""
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM services WHERE code = ? AND user_id = ?",
                    (code, user_id)
                )
                result = cursor.fetchone()
                return result is not None
        except Exception:
            return False


