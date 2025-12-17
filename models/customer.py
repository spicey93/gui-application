"""Customer model for customer management."""
import sqlite3
from typing import Optional, Tuple, List, Dict
import os


class Customer:
    """Customer model with database operations."""
    
    def __init__(self, db_path: str = "data/app.db"):
        """Initialize customer model with database path."""
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self) -> None:
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_database(self) -> None:
        """Initialize the database with customers table."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    user_customer_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    phone TEXT,
                    house_name_no TEXT,
                    street_address TEXT,
                    city TEXT,
                    county TEXT,
                    postcode TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE(user_id, user_customer_id)
                )
            """)
            conn.commit()
    
    def create(self, name: str, phone: str, house_name_no: str, street_address: str,
               city: str, county: str, postcode: str, user_id: int) -> Tuple[bool, str]:
        """
        Create a new customer.
        
        Args:
            name: Customer name
            phone: Customer phone number
            house_name_no: House name or number
            street_address: Street address
            city: City
            county: County
            postcode: Postcode
            user_id: ID of the user creating the customer
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not name or not name.strip():
            return False, "Name is required"
        
        if not user_id:
            return False, "User ID is required"
        
        name = name.strip()
        phone = phone.strip() if phone else ""
        house_name_no = house_name_no.strip() if house_name_no else ""
        street_address = street_address.strip() if street_address else ""
        city = city.strip() if city else ""
        county = county.strip() if county else ""
        postcode = postcode.strip() if postcode else ""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Calculate the next user_customer_id for this user
                cursor.execute("""
                    SELECT COALESCE(MAX(user_customer_id), 0) + 1 
                    FROM customers 
                    WHERE user_id = ?
                """, (user_id,))
                next_user_customer_id = cursor.fetchone()[0]
                
                cursor.execute(
                    """INSERT INTO customers 
                       (name, phone, house_name_no, street_address, city, county, postcode, user_id, user_customer_id) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (name, phone, house_name_no, street_address, city, county, postcode, user_id, next_user_customer_id)
                )
                conn.commit()
                return True, f"Customer created successfully (ID: {next_user_customer_id})"
        except Exception as e:
            return False, f"Error creating customer: {str(e)}"
    
    def get_all(self, user_id: int) -> List[Dict[str, any]]:
        """
        Get all customers for a specific user.
        
        Args:
            user_id: ID of the user
        
        Returns:
            List of customer dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        id as internal_id,
                        user_customer_id as id,
                        name, 
                        phone,
                        house_name_no,
                        street_address,
                        city,
                        county,
                        postcode,
                        created_at 
                    FROM customers 
                    WHERE user_id = ? 
                    ORDER BY user_customer_id
                """, (user_id,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception:
            return []
    
    def get_by_id(self, customer_id: int, user_id: int) -> Optional[Dict[str, any]]:
        """
        Get a customer by user_customer_id for a specific user.
        
        Args:
            customer_id: User customer ID (user_customer_id)
            user_id: ID of the user
        
        Returns:
            Customer dictionary or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        id as internal_id,
                        user_customer_id as id,
                        name, 
                        phone,
                        house_name_no,
                        street_address,
                        city,
                        county,
                        postcode,
                        created_at 
                    FROM customers 
                    WHERE user_customer_id = ? AND user_id = ?
                """, (customer_id, user_id))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception:
            return None
    
    def update(self, customer_id: int, name: str, phone: str, house_name_no: str,
               street_address: str, city: str, county: str, postcode: str,
               user_id: int) -> Tuple[bool, str]:
        """
        Update a customer by user_customer_id.
        
        Args:
            customer_id: User customer ID (user_customer_id)
            name: New name
            phone: New phone
            house_name_no: House name or number
            street_address: Street address
            city: City
            county: County
            postcode: Postcode
            user_id: ID of the user
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not name or not name.strip():
            return False, "Name is required"
        
        name = name.strip()
        phone = phone.strip() if phone else ""
        house_name_no = house_name_no.strip() if house_name_no else ""
        street_address = street_address.strip() if street_address else ""
        city = city.strip() if city else ""
        county = county.strip() if county else ""
        postcode = postcode.strip() if postcode else ""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """UPDATE customers 
                       SET name = ?, phone = ?, house_name_no = ?, street_address = ?,
                           city = ?, county = ?, postcode = ?
                       WHERE user_customer_id = ? AND user_id = ?""",
                    (name, phone, house_name_no, street_address, city, county, postcode,
                     customer_id, user_id)
                )
                
                if cursor.rowcount == 0:
                    return False, "Customer not found"
                
                conn.commit()
                return True, "Customer updated successfully"
        except Exception as e:
            return False, f"Error updating customer: {str(e)}"
    
    def delete(self, customer_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Delete a customer by user_customer_id.
        
        Args:
            customer_id: User customer ID (user_customer_id)
            user_id: ID of the user
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM customers WHERE user_customer_id = ? AND user_id = ?", 
                    (customer_id, user_id)
                )
                
                if cursor.rowcount == 0:
                    return False, "Customer not found"
                
                # Recalculate user_customer_id for remaining customers
                cursor.execute("""
                    SELECT id FROM customers 
                    WHERE user_id = ? 
                    ORDER BY id
                """, (user_id,))
                remaining_ids = [row[0] for row in cursor.fetchall()]
                
                for index, internal_id in enumerate(remaining_ids, start=1):
                    cursor.execute("""
                        UPDATE customers 
                        SET user_customer_id = ? 
                        WHERE id = ? AND user_id = ?
                    """, (index, internal_id, user_id))
                
                conn.commit()
                return True, "Customer deleted successfully"
        except Exception as e:
            return False, f"Error deleting customer: {str(e)}"
