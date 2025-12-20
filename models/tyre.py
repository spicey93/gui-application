"""Tyre model for tyre catalogue management."""
import sqlite3
from typing import Optional, Tuple, List, Dict
import os


class Tyre:
    """Tyre model with database operations."""
    
    def __init__(self, db_path: str = "data/app.db"):
        """Initialize tyre model with database path."""
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_database(self):
        """Initialize the database with tyres table."""
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='tyres'
            """)
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Create new table with all columns
                cursor.execute("""
                    CREATE TABLE tyres (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        description TEXT,
                        width TEXT,
                        profile TEXT,
                        diameter TEXT,
                        speed_rating TEXT,
                        load_index TEXT,
                        pattern TEXT,
                        oe_fitment TEXT,
                        ean TEXT,
                        manufacturer_code TEXT,
                        brand TEXT,
                        model TEXT,
                        product_type TEXT,
                        vehicle_type TEXT,
                        rolling_resistance TEXT,
                        wet_grip TEXT,
                        noise_class TEXT,
                        noise_performance TEXT,
                        vehicle_class TEXT,
                        created_date TEXT,
                        updated_date TEXT,
                        tyre_url TEXT,
                        brand_url TEXT,
                        run_flat TEXT
                    )
                """)
                
                # Create indexes on commonly searched columns
                cursor.execute("""
                    CREATE INDEX idx_tyres_brand ON tyres(brand)
                """)
                cursor.execute("""
                    CREATE INDEX idx_tyres_pattern ON tyres(pattern)
                """)
                cursor.execute("""
                    CREATE INDEX idx_tyres_vehicle_type ON tyres(vehicle_type)
                """)
                cursor.execute("""
                    CREATE INDEX idx_tyres_product_type ON tyres(product_type)
                """)
            
            conn.commit()
    
    def import_from_csv_row(self, row_data: Dict[str, str]) -> Tuple[bool, str]:
        """
        Import a single tyre record from CSV row data.
        
        Args:
            row_data: Dictionary with CSV column names as keys
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO tyres (
                        description, width, profile, diameter, speed_rating, load_index,
                        pattern, oe_fitment, ean, manufacturer_code, brand, model,
                        product_type, vehicle_type, rolling_resistance, wet_grip,
                        noise_class, noise_performance, vehicle_class,
                        created_date, updated_date, tyre_url, brand_url, run_flat
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row_data.get('Description', ''),
                    row_data.get('Width', ''),
                    row_data.get('Profile', ''),
                    row_data.get('Diameter', ''),
                    row_data.get('Speed Rating', ''),
                    row_data.get('Load Index', ''),
                    row_data.get('Pattern', ''),
                    row_data.get('OE Fitment', ''),
                    row_data.get('EAN', ''),
                    row_data.get('Manufacturer Code', ''),
                    row_data.get('Brand', ''),
                    row_data.get('Model', ''),
                    row_data.get('Product Type', ''),
                    row_data.get('Vehicle Type', ''),
                    row_data.get('Rolling Resistance', ''),
                    row_data.get('Wet Grip', ''),
                    row_data.get('Noise Class', ''),
                    row_data.get('Noise Performance', ''),
                    row_data.get('Vehicle Class', ''),
                    row_data.get('Created Date', ''),
                    row_data.get('Updated Date', ''),
                    row_data.get('Tyre URL', ''),
                    row_data.get('Brand URL', ''),
                    row_data.get('Run Flat', '')
                ))
                
                conn.commit()
            return True, "Tyre imported successfully"
        except Exception as e:
            return False, f"Error importing tyre: {str(e)}"
    
    def clear_all(self) -> Tuple[bool, str]:
        """
        Clear all tyre records from the database.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tyres")
                conn.commit()
            return True, "All tyres cleared successfully"
        except Exception as e:
            return False, f"Error clearing tyres: {str(e)}"
    
    def get_count(self) -> int:
        """
        Get the total count of tyres in the database.
        
        Returns:
            Number of tyres
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM tyres")
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception:
            return 0
    
    def search(
        self,
        pattern: Optional[str] = None,
        brand: Optional[str] = None,
        oe_fitment: Optional[str] = None,
        run_flat: Optional[bool] = None,
        width: Optional[str] = None,
        profile: Optional[str] = None,
        diameter: Optional[str] = None,
        vehicle_type: Optional[str] = None,
        product_type: Optional[str] = None,
        ean: Optional[str] = None,
        speed_rating: Optional[str] = None,
        load_index: Optional[str] = None,
        rolling_resistance: Optional[str] = None,
        wet_grip: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, any]]:
        """
        Search tyres with various filters.
        
        Args:
            pattern: Pattern text (partial match)
            brand: Brand (exact match)
            oe_fitment: OE Fitment (exact match)
            run_flat: Run Flat (True = "Yes", False = no filter)
            width: Width text (partial match)
            profile: Profile text (partial match)
            diameter: Diameter text (partial match)
            vehicle_type: Vehicle Type (exact match)
            product_type: Product Type (exact match)
            ean: EAN text (partial match)
            speed_rating: Speed Rating (exact match)
            load_index: Load Index (exact match)
            rolling_resistance: Rolling Resistance (exact match)
            wet_grip: Wet Grip (exact match)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of tyre dictionaries
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Build WHERE clause
                conditions = []
                params = []
                
                if pattern:
                    conditions.append("pattern LIKE ?")
                    params.append(f"%{pattern}%")
                
                if brand:
                    conditions.append("brand = ?")
                    params.append(brand)
                
                if oe_fitment:
                    conditions.append("oe_fitment = ?")
                    params.append(oe_fitment)
                
                if run_flat is True:
                    conditions.append("run_flat = ?")
                    params.append("Yes")
                
                if width:
                    conditions.append("width LIKE ?")
                    params.append(f"%{width}%")
                
                if profile:
                    conditions.append("profile LIKE ?")
                    params.append(f"%{profile}%")
                
                if diameter:
                    conditions.append("diameter LIKE ?")
                    params.append(f"%{diameter}%")
                
                if vehicle_type:
                    conditions.append("vehicle_type = ?")
                    params.append(vehicle_type)
                
                if product_type:
                    conditions.append("product_type = ?")
                    params.append(product_type)
                
                if ean:
                    conditions.append("ean LIKE ?")
                    params.append(f"%{ean}%")
                
                if speed_rating:
                    conditions.append("speed_rating = ?")
                    params.append(speed_rating)
                
                if load_index:
                    conditions.append("load_index = ?")
                    params.append(load_index)
                
                if rolling_resistance:
                    conditions.append("rolling_resistance = ?")
                    params.append(rolling_resistance)
                
                if wet_grip:
                    conditions.append("wet_grip = ?")
                    params.append(wet_grip)
                
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                
                # Build query
                query = f"""
                    SELECT * FROM tyres
                    WHERE {where_clause}
                    ORDER BY brand, pattern
                """
                
                if limit:
                    query += f" LIMIT {limit} OFFSET {offset}"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            return []
    
    def get_unique_brands(self) -> List[str]:
        """Get unique brand values."""
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT brand FROM tyres
                    WHERE brand IS NOT NULL AND brand != ''
                    ORDER BY brand
                """)
                rows = cursor.fetchall()
                return [row[0] for row in rows if row[0]]
        except Exception:
            return []
    
    def get_unique_oe_fitments(self) -> List[str]:
        """Get unique OE Fitment values."""
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT oe_fitment FROM tyres
                    WHERE oe_fitment IS NOT NULL AND oe_fitment != ''
                    ORDER BY oe_fitment
                """)
                rows = cursor.fetchall()
                return [row[0] for row in rows if row[0]]
        except Exception:
            return []
    
    def get_unique_vehicle_types(self) -> List[str]:
        """Get unique Vehicle Type values."""
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT vehicle_type FROM tyres
                    WHERE vehicle_type IS NOT NULL AND vehicle_type != ''
                    ORDER BY vehicle_type
                """)
                rows = cursor.fetchall()
                return [row[0] for row in rows if row[0]]
        except Exception:
            return []
    
    def get_unique_product_types(self) -> List[str]:
        """Get unique Product Type values."""
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT product_type FROM tyres
                    WHERE product_type IS NOT NULL AND product_type != ''
                    ORDER BY product_type
                """)
                rows = cursor.fetchall()
                return [row[0] for row in rows if row[0]]
        except Exception:
            return []
    
    def get_unique_speed_ratings(self) -> List[str]:
        """Get unique Speed Rating values."""
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT speed_rating FROM tyres
                    WHERE speed_rating IS NOT NULL AND speed_rating != ''
                    ORDER BY speed_rating
                """)
                rows = cursor.fetchall()
                return [row[0] for row in rows if row[0]]
        except Exception:
            return []
    
    def get_unique_load_indices(self) -> List[str]:
        """Get unique Load Index values."""
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT load_index FROM tyres
                    WHERE load_index IS NOT NULL AND load_index != ''
                    ORDER BY CAST(load_index AS INTEGER)
                """)
                rows = cursor.fetchall()
                return [row[0] for row in rows if row[0]]
        except Exception:
            return []
    
    def get_unique_rolling_resistances(self) -> List[str]:
        """Get unique Rolling Resistance values."""
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT rolling_resistance FROM tyres
                    WHERE rolling_resistance IS NOT NULL AND rolling_resistance != ''
                    ORDER BY rolling_resistance
                """)
                rows = cursor.fetchall()
                return [row[0] for row in rows if row[0]]
        except Exception:
            return []
    
    def get_unique_wet_grips(self) -> List[str]:
        """Get unique Wet Grip values."""
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT wet_grip FROM tyres
                    WHERE wet_grip IS NOT NULL AND wet_grip != ''
                    ORDER BY wet_grip
                """)
                rows = cursor.fetchall()
                return [row[0] for row in rows if row[0]]
        except Exception:
            return []
    
    def get_unique_models_by_brand(self, brand: str) -> List[str]:
        """Get unique model values for a specific brand."""
        try:
            if not brand or not brand.strip():
                return []
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT model FROM tyres
                    WHERE brand = ? AND model IS NOT NULL AND model != ''
                    ORDER BY model
                """, (brand.strip(),))
                rows = cursor.fetchall()
                return [row[0] for row in rows if row[0]]
        except Exception:
            return []
    
    def check_matching_record(
        self, width: str, profile: str, diameter: str, speed_rating: str,
        load_index: str, brand: str, model: str
    ) -> bool:
        """
        Check if a matching record exists in the catalogue.
        
        Args:
            width: Tyre width
            profile: Tyre profile
            diameter: Tyre diameter
            speed_rating: Speed rating
            load_index: Load index
            brand: Brand name
            model: Model name
        
        Returns:
            True if a matching record exists, False otherwise
        """
        try:
            # All fields must be provided and non-empty for a match
            if not all([width, profile, diameter, speed_rating, load_index, brand, model]):
                return False
            
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM tyres
                    WHERE width = ? AND profile = ? AND diameter = ?
                    AND speed_rating = ? AND load_index = ?
                    AND brand = ? AND model = ?
                """, (
                    width.strip(),
                    profile.strip(),
                    diameter.strip(),
                    speed_rating.strip(),
                    load_index.strip(),
                    brand.strip(),
                    model.strip()
                ))
                result = cursor.fetchone()
                return (result[0] > 0) if result else False
        except Exception:
            return False
    
    def get_urls_by_brand_model(self, brand: str, model: str = None) -> Tuple[str, str]:
        """
        Get tyre URL and brand URL by brand and optionally model.
        
        Search priority:
        1. If model provided: search for brand + model match, return both URLs
        2. If no model match: search for brand only, return brand URL (tyre URL empty)
        3. If no brand match: return both as empty
        
        Args:
            brand: Brand name
            model: Model name (optional)
        
        Returns:
            Tuple of (tyre_url, brand_url)
        """
        try:
            if not brand or not brand.strip():
                return ("", "")
            
            brand = brand.strip()
            model = model.strip() if model else None
            
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # First try: brand + model match
                if model:
                    cursor.execute("""
                        SELECT tyre_url, brand_url FROM tyres
                        WHERE brand = ? AND model = ?
                        LIMIT 1
                    """, (brand, model))
                    row = cursor.fetchone()
                    if row:
                        return (row['tyre_url'] or "", row['brand_url'] or "")
                
                # Second try: brand only match
                cursor.execute("""
                    SELECT brand_url FROM tyres
                    WHERE brand = ?
                    LIMIT 1
                """, (brand,))
                row = cursor.fetchone()
                if row:
                    return ("", row['brand_url'] or "")
                
                # No match found
                return ("", "")
        except Exception:
            return ("", "")

