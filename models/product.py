"""Product model for product management."""
import sqlite3
from typing import Optional, Tuple, List, Dict
import os


class Product:
    """Product model with database operations."""
    
    def __init__(self, db_path: str = "data/app.db"):
        """Initialize product model with database path."""
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_database(self):
        """Initialize the database with products table."""
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='products'
            """)
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Create new table with proper constraints (including tyre columns)
                cursor.execute("""
                    CREATE TABLE products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        user_product_id INTEGER NOT NULL,
                        stock_number TEXT NOT NULL,
                        description TEXT,
                        type TEXT,
                        stock_quantity REAL NOT NULL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_tyre INTEGER NOT NULL DEFAULT 0,
                        tyre_brand TEXT,
                        tyre_model TEXT,
                        tyre_pattern TEXT,
                        tyre_width TEXT,
                        tyre_profile TEXT,
                        tyre_diameter TEXT,
                        tyre_speed_rating TEXT,
                        tyre_load_index TEXT,
                        tyre_oe_fitment TEXT,
                        tyre_ean TEXT,
                        tyre_manufacturer_code TEXT,
                        tyre_vehicle_type TEXT,
                        tyre_product_type TEXT,
                        tyre_rolling_resistance TEXT,
                        tyre_wet_grip TEXT,
                        tyre_run_flat TEXT,
                        tyre_url TEXT,
                        tyre_brand_url TEXT,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        UNIQUE(user_id, user_product_id)
                    )
                """)
                column_names = []  # Empty list for new table
            else:
                # Table exists - check schema and migrate if needed
                cursor.execute("PRAGMA table_info(products)")
                column_info = cursor.fetchall()
                columns = {row[1]: row for row in column_info}
                column_names = list(columns.keys())
                
                # Check if we need to migrate from old schema (name/price) to new schema (stock_number/type)
                # Migration needed if: name exists AND (stock_number doesn't exist OR name has NOT NULL constraint)
                has_name = 'name' in column_names
                has_stock_number = 'stock_number' in column_names
                name_not_null = False
                
                if has_name:
                    name_col_info = columns['name']
                    name_not_null = name_col_info[3] == 1  # Column 3 is "notnull" flag
                
                needs_migration = has_name and (not has_stock_number or name_not_null)
                
                if needs_migration:
                    # Save existing data - handle both old and new schemas
                    try:
                        cursor.execute("""
                            SELECT id, user_id, user_product_id, name, description, price, created_at 
                            FROM products
                        """)
                    except sqlite3.OperationalError:
                        # Try without price column
                        try:
                            cursor.execute("""
                                SELECT id, user_id, user_product_id, name, description, created_at 
                                FROM products
                            """)
                        except sqlite3.OperationalError:
                            # Try minimal columns
                            cursor.execute("SELECT id, name FROM products")
                    
                    old_data = cursor.fetchall()
                    
                    # Drop old table
                    cursor.execute("DROP TABLE products")
                    
                    # Create new table with correct schema
                    cursor.execute("""
                        CREATE TABLE products (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            user_product_id INTEGER NOT NULL,
                            stock_number TEXT NOT NULL,
                            description TEXT,
                            type TEXT,
                            stock_quantity REAL NOT NULL DEFAULT 0.0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                            UNIQUE(user_id, user_product_id)
                        )
                    """)
                    
                    # Migrate data: name -> stock_number, price -> type (as string representation)
                    for row in old_data:
                        try:
                            if len(row) >= 7:
                                # Full old schema
                                old_id, old_user_id, old_user_product_id, old_name, old_description, old_price, old_created_at = row[:7]
                                new_type = str(old_price) if old_price is not None else ""
                            elif len(row) >= 6:
                                # Without price
                                old_id, old_user_id, old_user_product_id, old_name, old_description, old_created_at = row[:6]
                                new_type = ""
                            else:
                                # Minimal
                                old_id = row[0]
                                old_name = row[1] if len(row) > 1 else ""
                                old_user_id = 1  # Default
                                old_user_product_id = old_id  # Use ID as product ID
                                old_description = ""
                                old_created_at = None
                                new_type = ""
                            
                            # Ensure we have valid user_id and user_product_id
                            if old_user_id is None:
                                old_user_id = 1
                            if old_user_product_id is None:
                                old_user_product_id = old_id
                            
                            cursor.execute("""
                                INSERT INTO products (id, user_id, user_product_id, stock_number, description, type, stock_quantity, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, 0.0, ?)
                            """, (old_id, old_user_id, old_user_product_id, old_name or "", old_description or "", new_type, old_created_at))
                        except Exception:
                            # Skip rows that can't be migrated
                            continue
                else:
                    # Standard migration for missing columns
                    if 'user_id' not in column_names:
                        cursor.execute("ALTER TABLE products ADD COLUMN user_id INTEGER")
                        cursor.execute("DELETE FROM products WHERE user_id IS NULL")
                    
                    if 'user_product_id' not in column_names:
                        cursor.execute("ALTER TABLE products ADD COLUMN user_product_id INTEGER")
                        cursor.execute("""
                            UPDATE products 
                            SET user_product_id = (
                                SELECT COUNT(*) + 1
                                FROM products p2
                                WHERE p2.user_id = products.user_id 
                                AND p2.id < products.id
                            )
                            WHERE user_product_id IS NULL
                        """)
                        cursor.execute("UPDATE products SET user_product_id = 1 WHERE user_product_id IS NULL")
                        
                        try:
                            cursor.execute("""
                                CREATE UNIQUE INDEX IF NOT EXISTS idx_product_user_product_id 
                                ON products(user_id, user_product_id)
                            """)
                        except sqlite3.OperationalError:
                            pass
                    
                    if 'stock_number' not in column_names:
                        # If name column exists, migrate data first
                        if 'name' in column_names:
                            cursor.execute("ALTER TABLE products ADD COLUMN stock_number TEXT")
                            cursor.execute("UPDATE products SET stock_number = COALESCE(name, '') WHERE stock_number IS NULL")
                            cursor.execute("ALTER TABLE products ADD COLUMN stock_number_temp TEXT NOT NULL DEFAULT ''")
                            cursor.execute("UPDATE products SET stock_number_temp = stock_number")
                            cursor.execute("ALTER TABLE products DROP COLUMN stock_number")
                            cursor.execute("ALTER TABLE products RENAME COLUMN stock_number_temp TO stock_number")
                        else:
                            cursor.execute("ALTER TABLE products ADD COLUMN stock_number TEXT NOT NULL DEFAULT ''")
                    
                    if 'type' not in column_names:
                        cursor.execute("ALTER TABLE products ADD COLUMN type TEXT")
                    
                    if 'stock_quantity' not in column_names:
                        cursor.execute("ALTER TABLE products ADD COLUMN stock_quantity REAL NOT NULL DEFAULT 0.0")
                    
                    # Remove old name column if it exists and stock_number exists
                    if 'name' in column_names and 'stock_number' in column_names:
                        try:
                            # SQLite doesn't support DROP COLUMN directly, so we need to recreate
                            cursor.execute("PRAGMA table_info(products)")
                            all_columns = cursor.fetchall()
                            
                            # Get all data
                            cursor.execute("SELECT * FROM products")
                            all_data = cursor.fetchall()
                            
                            # Get column names (excluding 'name')
                            keep_columns = [col[1] for col in all_columns if col[1] != 'name']
                            
                            # Recreate table without name column
                            cursor.execute("DROP TABLE products")
                            cursor.execute("""
                                CREATE TABLE products (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    user_id INTEGER NOT NULL,
                                    user_product_id INTEGER NOT NULL,
                                    stock_number TEXT NOT NULL,
                                    description TEXT,
                                    type TEXT,
                                    stock_quantity REAL NOT NULL DEFAULT 0.0,
                                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                                    UNIQUE(user_id, user_product_id)
                                )
                            """)
                            
                            # Re-insert data (skipping name column)
                            for row in all_data:
                                # Map old columns to new (skip name column)
                                col_map = {col[1]: idx for idx, col in enumerate(all_columns)}
                                new_row = []
                                for col_name in ['id', 'user_id', 'user_product_id', 'stock_number', 'description', 'type', 'created_at']:
                                    if col_name in col_map:
                                        new_row.append(row[col_map[col_name]])
                                    elif col_name == 'stock_number' and 'name' in col_map:
                                        # Use name as stock_number if stock_number doesn't exist
                                        new_row.append(row[col_map['name']] if row[col_map['name']] else '')
                                    else:
                                        new_row.append(None)
                                
                                if len(new_row) >= 7:
                                    cursor.execute("""
                                        INSERT INTO products (id, user_id, user_product_id, stock_number, description, type, stock_quantity, created_at)
                                        VALUES (?, ?, ?, ?, ?, ?, 0.0, ?)
                                    """, tuple(new_row[:7]))
                        except Exception:
                            # If migration fails, at least ensure stock_number exists
                            pass
            
            # Add tyre-specific columns if they don't exist (only for existing tables)
            if table_exists:
                # Refresh column_names after potential migrations
                cursor.execute("PRAGMA table_info(products)")
                column_info = cursor.fetchall()
                column_names = [row[1] for row in column_info]
                
                tyre_columns = [
                    ('is_tyre', 'INTEGER NOT NULL DEFAULT 0'),
                    ('tyre_brand', 'TEXT'),
                    ('tyre_model', 'TEXT'),
                    ('tyre_pattern', 'TEXT'),
                    ('tyre_width', 'TEXT'),
                    ('tyre_profile', 'TEXT'),
                    ('tyre_diameter', 'TEXT'),
                    ('tyre_speed_rating', 'TEXT'),
                    ('tyre_load_index', 'TEXT'),
                    ('tyre_oe_fitment', 'TEXT'),
                    ('tyre_ean', 'TEXT'),
                    ('tyre_manufacturer_code', 'TEXT'),
                    ('tyre_vehicle_type', 'TEXT'),
                    ('tyre_product_type', 'TEXT'),
                    ('tyre_rolling_resistance', 'TEXT'),
                    ('tyre_wet_grip', 'TEXT'),
                    ('tyre_run_flat', 'TEXT'),
                    ('tyre_url', 'TEXT'),
                    ('tyre_brand_url', 'TEXT')
                ]
                
                for col_name, col_def in tyre_columns:
                    if col_name not in column_names:
                        try:
                            cursor.execute(f"ALTER TABLE products ADD COLUMN {col_name} {col_def}")
                        except sqlite3.OperationalError:
                            # Column might already exist or there's a constraint issue
                            pass
            
            # Clean up orphaned products
            try:
                cursor.execute("""
                    DELETE FROM products 
                    WHERE user_id NOT IN (SELECT id FROM users)
                    AND user_id IS NOT NULL
                """)
            except Exception:
                pass
            
            conn.commit()
    
    def create(
        self, 
        stock_number: str, 
        description: str, 
        type: str, 
        user_id: int,
        is_tyre: bool = False,
        tyre_brand: Optional[str] = None,
        tyre_model: Optional[str] = None,
        tyre_pattern: Optional[str] = None,
        tyre_width: Optional[str] = None,
        tyre_profile: Optional[str] = None,
        tyre_diameter: Optional[str] = None,
        tyre_speed_rating: Optional[str] = None,
        tyre_load_index: Optional[str] = None,
        tyre_oe_fitment: Optional[str] = None,
        tyre_ean: Optional[str] = None,
        tyre_manufacturer_code: Optional[str] = None,
        tyre_vehicle_type: Optional[str] = None,
        tyre_product_type: Optional[str] = None,
        tyre_rolling_resistance: Optional[str] = None,
        tyre_wet_grip: Optional[str] = None,
        tyre_run_flat: Optional[str] = None,
        tyre_url: Optional[str] = None,
        tyre_brand_url: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Create a new product.
        
        Args:
            stock_number: Product stock number
            description: Product description (optional)
            type: Product type (optional)
            user_id: ID of the user creating the product
            is_tyre: Whether this is a tyre product
            tyre_*: Tyre-specific fields (optional)
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not stock_number:
            return False, "Stock number is required"
        
        if not user_id:
            return False, "User ID is required"
        
        stock_number = stock_number.strip()
        description = description.strip() if description else ""
        type = type.strip() if type else ""
        
        try:
            # Check schema first and migrate if needed
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(products)")
                columns = [row[1] for row in cursor.fetchall()]
                needs_migration = 'name' in columns and 'stock_number' not in columns
                conn.commit()
            
            if needs_migration:
                self._init_database()
            
            # Now perform the insert
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Calculate the next user_product_id for this user
                cursor.execute("""
                    SELECT COALESCE(MAX(user_product_id), 0) + 1 
                    FROM products 
                    WHERE user_id = ?
                """, (user_id,))
                next_user_product_id = cursor.fetchone()[0]
                
                # Prepare tyre fields (tyre_run_flat is already a string or None)
                
                cursor.execute("""
                    INSERT INTO products (
                        stock_number, description, type, user_id, user_product_id, stock_quantity,
                        is_tyre, tyre_brand, tyre_model, tyre_pattern, tyre_width, tyre_profile,
                        tyre_diameter, tyre_speed_rating, tyre_load_index, tyre_oe_fitment,
                        tyre_ean, tyre_manufacturer_code, tyre_vehicle_type, tyre_product_type,
                        tyre_rolling_resistance, tyre_wet_grip, tyre_run_flat, tyre_url, tyre_brand_url
                    ) VALUES (?, ?, ?, ?, ?, 0.0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    stock_number, description, type, user_id, next_user_product_id,
                    1 if is_tyre else 0,
                    tyre_brand, tyre_model, tyre_pattern, tyre_width, tyre_profile,
                    tyre_diameter, tyre_speed_rating, tyre_load_index, tyre_oe_fitment,
                    tyre_ean, tyre_manufacturer_code, tyre_vehicle_type, tyre_product_type,
                    tyre_rolling_resistance, tyre_wet_grip, tyre_run_flat, tyre_url, tyre_brand_url
                ))
                conn.commit()
                product_id = cursor.lastrowid
            return True, f"Product created successfully (ID: {next_user_product_id})"
        except sqlite3.OperationalError as e:
            if "name" in str(e) and "NOT NULL" in str(e):
                # Schema issue - try to fix it
                try:
                    self._init_database()
                    # Retry the operation
                    with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT COALESCE(MAX(user_product_id), 0) + 1 
                            FROM products 
                            WHERE user_id = ?
                        """, (user_id,))
                        next_user_product_id = cursor.fetchone()[0]
                        cursor.execute("""
                            INSERT INTO products (
                                stock_number, description, type, user_id, user_product_id, stock_quantity,
                                is_tyre, tyre_brand, tyre_model, tyre_pattern, tyre_width, tyre_profile,
                                tyre_diameter, tyre_speed_rating, tyre_load_index, tyre_oe_fitment,
                                tyre_ean, tyre_manufacturer_code, tyre_vehicle_type, tyre_product_type,
                                tyre_rolling_resistance, tyre_wet_grip, tyre_run_flat, tyre_url, tyre_brand_url
                            ) VALUES (?, ?, ?, ?, ?, 0.0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            stock_number, description, type, user_id, next_user_product_id,
                            1 if is_tyre else 0,
                            tyre_brand, tyre_model, tyre_pattern, tyre_width, tyre_profile,
                            tyre_diameter, tyre_speed_rating, tyre_load_index, tyre_oe_fitment,
                            tyre_ean, tyre_manufacturer_code, tyre_vehicle_type, tyre_product_type,
                            tyre_rolling_resistance, tyre_wet_grip, tyre_run_flat, tyre_url, tyre_brand_url
                        ))
                        conn.commit()
                    return True, f"Product created successfully (ID: {next_user_product_id})"
                except Exception as retry_e:
                    return False, f"Error creating product after migration: {str(retry_e)}"
            return False, f"Database error: {str(e)}"
        except Exception as e:
            return False, f"Error creating product: {str(e)}"
    
    def get_all(self, user_id: int) -> List[Dict[str, any]]:
        """
        Get all products for a specific user.
        
        Args:
            user_id: ID of the user
        
        Returns:
            List of product dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    id as internal_id,
                    COALESCE(user_product_id, id) as id,
                    stock_number, 
                    description,
                    type,
                    COALESCE(stock_quantity, 0.0) as stock_quantity,
                    created_at,
                    is_tyre,
                    tyre_brand, tyre_model, tyre_pattern, tyre_width, tyre_profile,
                    tyre_diameter, tyre_speed_rating, tyre_load_index, tyre_oe_fitment,
                    tyre_ean, tyre_manufacturer_code, tyre_vehicle_type, tyre_product_type,
                    tyre_rolling_resistance, tyre_wet_grip, tyre_run_flat, tyre_url, tyre_brand_url
                FROM products 
                WHERE user_id = ? 
                ORDER BY user_product_id
            """, (user_id,))
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            return []
    
    def get_by_id(self, product_id: int, user_id: int) -> Optional[Dict[str, any]]:
        """
        Get a product by user_product_id for a specific user.
        
        Args:
            product_id: User product ID (user_product_id)
            user_id: ID of the user
        
        Returns:
            Product dictionary or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    id as internal_id,
                    COALESCE(user_product_id, id) as id,
                    stock_number, 
                    description,
                    type,
                    COALESCE(stock_quantity, 0.0) as stock_quantity,
                    created_at,
                    is_tyre,
                    tyre_brand, tyre_model, tyre_pattern, tyre_width, tyre_profile,
                    tyre_diameter, tyre_speed_rating, tyre_load_index, tyre_oe_fitment,
                    tyre_ean, tyre_manufacturer_code, tyre_vehicle_type, tyre_product_type,
                    tyre_rolling_resistance, tyre_wet_grip, tyre_run_flat, tyre_url, tyre_brand_url
                FROM products 
                WHERE user_product_id = ? AND user_id = ?
            """, (product_id, user_id))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception:
            return None
    
    def update(
        self, 
        product_id: int, 
        stock_number: str, 
        description: str, 
        type: str, 
        user_id: int,
        is_tyre: Optional[bool] = None,
        tyre_brand: Optional[str] = None,
        tyre_model: Optional[str] = None,
        tyre_pattern: Optional[str] = None,
        tyre_width: Optional[str] = None,
        tyre_profile: Optional[str] = None,
        tyre_diameter: Optional[str] = None,
        tyre_speed_rating: Optional[str] = None,
        tyre_load_index: Optional[str] = None,
        tyre_oe_fitment: Optional[str] = None,
        tyre_ean: Optional[str] = None,
        tyre_manufacturer_code: Optional[str] = None,
        tyre_vehicle_type: Optional[str] = None,
        tyre_product_type: Optional[str] = None,
        tyre_rolling_resistance: Optional[str] = None,
        tyre_wet_grip: Optional[str] = None,
        tyre_run_flat: Optional[str] = None,
        tyre_url: Optional[str] = None,
        tyre_brand_url: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Update a product by user_product_id.
        
        Args:
            product_id: User product ID (user_product_id)
            stock_number: New stock number
            description: New description
            type: New type
            user_id: ID of the user
            is_tyre: Whether this is a tyre product (optional, None means don't change)
            tyre_*: Tyre-specific fields (optional, None means don't change)
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not stock_number:
            return False, "Stock number is required"
        
        stock_number = stock_number.strip()
        description = description.strip() if description else ""
        type = type.strip() if type else ""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get the internal ID for this product
            cursor.execute(
                "SELECT id FROM products WHERE user_product_id = ? AND user_id = ?",
                (product_id, user_id)
            )
            internal_id_result = cursor.fetchone()
            
            if not internal_id_result:
                conn.close()
                return False, "Product not found"
            
            # Build update query dynamically based on provided fields
            update_fields = ["stock_number = ?", "description = ?", "type = ?"]
            update_values = [stock_number, description, type]
            
            if is_tyre is not None:
                update_fields.append("is_tyre = ?")
                update_values.append(1 if is_tyre else 0)
            
            tyre_fields = {
                'tyre_brand': tyre_brand,
                'tyre_model': tyre_model,
                'tyre_pattern': tyre_pattern,
                'tyre_width': tyre_width,
                'tyre_profile': tyre_profile,
                'tyre_diameter': tyre_diameter,
                'tyre_speed_rating': tyre_speed_rating,
                'tyre_load_index': tyre_load_index,
                'tyre_oe_fitment': tyre_oe_fitment,
                'tyre_ean': tyre_ean,
                'tyre_manufacturer_code': tyre_manufacturer_code,
                'tyre_vehicle_type': tyre_vehicle_type,
                'tyre_product_type': tyre_product_type,
                'tyre_rolling_resistance': tyre_rolling_resistance,
                'tyre_wet_grip': tyre_wet_grip,
                'tyre_run_flat': tyre_run_flat,
                'tyre_url': tyre_url,
                'tyre_brand_url': tyre_brand_url
            }
            
            for field_name, field_value in tyre_fields.items():
                if field_value is not None:
                    update_fields.append(f"{field_name} = ?")
                    update_values.append(field_value)
            
            update_values.extend([product_id, user_id])
            
            query = f"""
                UPDATE products 
                SET {', '.join(update_fields)}
                WHERE user_product_id = ? AND user_id = ?
            """
            
            cursor.execute(query, update_values)
            
            if cursor.rowcount == 0:
                conn.close()
                return False, "Product not found"
            
            conn.commit()
            conn.close()
            return True, "Product updated successfully"
        except Exception as e:
            return False, f"Error updating product: {str(e)}"
    
    def delete(self, product_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Delete a product by user_product_id.
        
        Args:
            product_id: User product ID (user_product_id)
            user_id: ID of the user
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM products WHERE user_product_id = ? AND user_id = ?", 
                (product_id, user_id)
            )
            
            if cursor.rowcount == 0:
                conn.close()
                return False, "Product not found"
            
            # Recalculate user_product_id for remaining products
            cursor.execute("""
                SELECT id FROM products 
                WHERE user_id = ? 
                ORDER BY id
            """, (user_id,))
            remaining_ids = [row[0] for row in cursor.fetchall()]
            
            for index, internal_id in enumerate(remaining_ids, start=1):
                cursor.execute("""
                    UPDATE products 
                    SET user_product_id = ? 
                    WHERE id = ? AND user_id = ?
                """, (index, internal_id, user_id))
            
            conn.commit()
            conn.close()
            return True, "Product deleted successfully"
        except Exception as e:
            return False, f"Error deleting product: {str(e)}"
    
    def update_stock(self, internal_product_id: int, quantity_delta: float) -> Tuple[bool, str]:
        """
        Update product stock quantity by adding or subtracting.
        
        Args:
            internal_product_id: Internal database product ID (not user_product_id)
            quantity_delta: Quantity to add (positive) or subtract (negative)
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Check if product exists
                cursor.execute("SELECT id, stock_quantity FROM products WHERE id = ?", (internal_product_id,))
                result = cursor.fetchone()
                
                if not result:
                    return False, "Product not found"
                
                current_stock = result[1] or 0.0
                new_stock = current_stock + quantity_delta
                
                # Update stock
                cursor.execute("""
                    UPDATE products 
                    SET stock_quantity = ? 
                    WHERE id = ?
                """, (new_stock, internal_product_id))
                
                conn.commit()
            return True, "Stock updated successfully"
        except Exception as e:
            return False, f"Error updating stock: {str(e)}"
    
    def get_by_internal_id(self, internal_product_id: int) -> Optional[Dict[str, any]]:
        """
        Get a product by internal database ID.
        
        Args:
            internal_product_id: Internal database product ID
        
        Returns:
            Product dictionary or None if not found
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        id as internal_id,
                        COALESCE(user_product_id, id) as id,
                        stock_number, 
                        description,
                        type,
                        COALESCE(stock_quantity, 0.0) as stock_quantity,
                        created_at,
                        is_tyre,
                        tyre_brand, tyre_model, tyre_pattern, tyre_width, tyre_profile,
                        tyre_diameter, tyre_speed_rating, tyre_load_index, tyre_oe_fitment,
                        tyre_ean, tyre_manufacturer_code, tyre_vehicle_type, tyre_product_type,
                        tyre_rolling_resistance, tyre_wet_grip, tyre_run_flat, tyre_url, tyre_brand_url
                    FROM products 
                    WHERE id = ?
                """, (internal_product_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception:
            return None
    
    def get_tyre_products(self, user_id: int) -> List[Dict[str, any]]:
        """
        Get all tyre products for a specific user.
        
        Args:
            user_id: ID of the user
        
        Returns:
            List of tyre product dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    id as internal_id,
                    COALESCE(user_product_id, id) as id,
                    stock_number, 
                    description,
                    type,
                    COALESCE(stock_quantity, 0.0) as stock_quantity,
                    created_at,
                    is_tyre,
                    tyre_brand, tyre_model, tyre_pattern, tyre_width, tyre_profile,
                    tyre_diameter, tyre_speed_rating, tyre_load_index, tyre_oe_fitment,
                    tyre_ean, tyre_manufacturer_code, tyre_vehicle_type, tyre_product_type,
                    tyre_rolling_resistance, tyre_wet_grip, tyre_run_flat, tyre_url, tyre_brand_url
                FROM products 
                WHERE user_id = ? AND is_tyre = 1
                ORDER BY user_product_id
            """, (user_id,))
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            return []
    
    def get_unique_tyre_brands(self, user_id: int) -> List[str]:
        """
        Get unique tyre brands from user's tyre products.
        
        Args:
            user_id: ID of the user
        
        Returns:
            List of unique brand names
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT tyre_brand FROM products
                WHERE user_id = ? AND is_tyre = 1
                AND tyre_brand IS NOT NULL AND tyre_brand != ''
                ORDER BY tyre_brand
            """, (user_id,))
            rows = cursor.fetchall()
            conn.close()
            return [row[0] for row in rows if row[0]]
        except Exception:
            return []
    
    def get_tyre_models_by_brand(self, user_id: int, brand: str) -> List[str]:
        """
        Get unique tyre models for a specific brand from user's tyre products.
        
        Args:
            user_id: ID of the user
            brand: Brand name to filter by
        
        Returns:
            List of unique model names
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT tyre_model FROM products
                WHERE user_id = ? AND is_tyre = 1 AND tyre_brand = ?
                AND tyre_model IS NOT NULL AND tyre_model != ''
                ORDER BY tyre_model
            """, (user_id, brand))
            rows = cursor.fetchall()
            conn.close()
            return [row[0] for row in rows if row[0]]
        except Exception:
            return []
    
    def create_from_tyre_catalogue(self, tyre_data: Dict[str, any], user_id: int) -> Tuple[bool, str, Optional[int]]:
        """
        Create a product from a tyre catalogue entry.
        
        Args:
            tyre_data: Dictionary with tyre data from catalogue
            user_id: ID of the user creating the product
        
        Returns:
            Tuple of (success: bool, message: str, internal_product_id: Optional[int])
        """
        # Use EAN as stock_number if available, otherwise use description
        stock_number = tyre_data.get('ean', '') or tyre_data.get('description', '')[:50] or 'TYRE'
        description = tyre_data.get('description', '')
        
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                # Calculate the next user_product_id for this user
                cursor.execute("""
                    SELECT COALESCE(MAX(user_product_id), 0) + 1 
                    FROM products 
                    WHERE user_id = ?
                """, (user_id,))
                next_user_product_id = cursor.fetchone()[0]
                
                cursor.execute("""
                    INSERT INTO products (
                        stock_number, description, type, user_id, user_product_id, stock_quantity,
                        is_tyre, tyre_brand, tyre_model, tyre_pattern, tyre_width, tyre_profile,
                        tyre_diameter, tyre_speed_rating, tyre_load_index, tyre_oe_fitment,
                        tyre_ean, tyre_manufacturer_code, tyre_vehicle_type, tyre_product_type,
                        tyre_rolling_resistance, tyre_wet_grip, tyre_run_flat, tyre_url, tyre_brand_url
                    ) VALUES (?, ?, ?, ?, ?, 0.0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    stock_number, description, tyre_data.get('product_type', ''), user_id, next_user_product_id,
                    1,  # is_tyre = True
                    tyre_data.get('brand', ''),
                    tyre_data.get('model', ''),
                    tyre_data.get('pattern', ''),
                    tyre_data.get('width', ''),
                    tyre_data.get('profile', ''),
                    tyre_data.get('diameter', ''),
                    tyre_data.get('speed_rating', ''),
                    tyre_data.get('load_index', ''),
                    tyre_data.get('oe_fitment', ''),
                    tyre_data.get('ean', ''),
                    tyre_data.get('manufacturer_code', ''),
                    tyre_data.get('vehicle_type', ''),
                    tyre_data.get('product_type', ''),
                    tyre_data.get('rolling_resistance', ''),
                    tyre_data.get('wet_grip', ''),
                    tyre_data.get('run_flat', ''),
                    tyre_data.get('tyre_url', ''),
                    tyre_data.get('brand_url', '')
                ))
                conn.commit()
                internal_product_id = cursor.lastrowid
                return True, f"Product created successfully (ID: {next_user_product_id})", internal_product_id
        except Exception as e:
            return False, f"Error creating product from catalogue: {str(e)}", None

