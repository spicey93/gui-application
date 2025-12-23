"""Vehicle model for storing vehicle data from API lookups."""
import sqlite3
import json
from typing import Optional, List, Dict, Tuple, Any
from datetime import datetime
import os


class Vehicle:
    """Vehicle model with database operations."""
    
    def __init__(self, db_path: str = "data/app.db"):
        """Initialize vehicle model with database path."""
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    @staticmethod
    def normalize_vrm(vrm: str) -> str:
        """Normalize VRM to uppercase with no spaces."""
        return vrm.upper().replace(" ", "").strip()
    
    def _ensure_db_directory(self) -> None:
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_database(self) -> None:
        """Initialize the database with vehicles table."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vehicles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    vrm TEXT NOT NULL,
                    make TEXT,
                    model TEXT,
                    build_year TEXT,
                    tyre_data JSON,
                    raw_response JSON,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(user_id, vrm),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            conn.commit()
    
    def save_vehicle(
        self, 
        user_id: int, 
        vrm: str, 
        make: str,
        model: str,
        build_year: str,
        tyre_data: Optional[Dict] = None,
        raw_response: Optional[Dict] = None
    ) -> Tuple[bool, str, Optional[int]]:
        """
        Save or update a vehicle from API response.
        
        Returns:
            Tuple of (success, message, vehicle_id)
        """
        if not vrm:
            return False, "VRM is required", None
        
        vrm = self.normalize_vrm(vrm)
        now = datetime.now().isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO vehicles (user_id, vrm, make, model, build_year, 
                                         tyre_data, raw_response, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id, vrm) DO UPDATE SET
                        make = excluded.make,
                        model = excluded.model,
                        build_year = excluded.build_year,
                        tyre_data = excluded.tyre_data,
                        raw_response = excluded.raw_response,
                        updated_at = excluded.updated_at
                """, (
                    user_id, vrm, make, model, build_year,
                    json.dumps(tyre_data) if tyre_data else None,
                    json.dumps(raw_response) if raw_response else None,
                    now, now
                ))
                conn.commit()
                
                # Get the vehicle ID
                cursor.execute(
                    "SELECT id FROM vehicles WHERE user_id = ? AND vrm = ?",
                    (user_id, vrm)
                )
                result = cursor.fetchone()
                vehicle_id = result[0] if result else None
                
            return True, "Vehicle saved successfully", vehicle_id
        except Exception as e:
            return False, f"Failed to save vehicle: {str(e)}", None
    
    def get_vehicle_by_vrm(self, user_id: int, vrm: str) -> Optional[Dict[str, Any]]:
        """Get a vehicle by VRM."""
        vrm = self.normalize_vrm(vrm)
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM vehicles WHERE user_id = ? AND vrm = ?",
                    (user_id, vrm)
                )
                row = cursor.fetchone()
                if row:
                    return self._row_to_dict(row)
                return None
        except Exception:
            return None
    
    def get_vehicle_by_id(self, user_id: int, vehicle_id: int) -> Optional[Dict[str, Any]]:
        """Get a vehicle by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM vehicles WHERE user_id = ? AND id = ?",
                    (user_id, vehicle_id)
                )
                row = cursor.fetchone()
                if row:
                    return self._row_to_dict(row)
                return None
        except Exception:
            return None
    
    def get_all_vehicles(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all vehicles for a user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM vehicles WHERE user_id = ? ORDER BY updated_at DESC",
                    (user_id,)
                )
                return [self._row_to_dict(row) for row in cursor.fetchall()]
        except Exception:
            return []
    
    def search_vehicles_by_vrm(self, user_id: int, vrm_query: str) -> List[Dict[str, Any]]:
        """
        Search for vehicles by partial VRM match.
        
        Args:
            user_id: The user ID to filter by
            vrm_query: Partial VRM to search for (e.g., "LD" matches "LD07LTF", "HE69LDE")
        
        Returns:
            List of matching vehicles (empty list if query is empty)
        """
        if not vrm_query or not vrm_query.strip():
            return []
        
        vrm_query = self.normalize_vrm(vrm_query)
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM vehicles WHERE user_id = ? AND vrm LIKE ? ORDER BY vrm ASC",
                    (user_id, f"%{vrm_query}%")
                )
                return [self._row_to_dict(row) for row in cursor.fetchall()]
        except Exception:
            return []
    
    def delete_vehicle(self, user_id: int, vehicle_id: int) -> Tuple[bool, str]:
        """Delete a vehicle."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM vehicles WHERE id = ? AND user_id = ?",
                    (vehicle_id, user_id)
                )
                conn.commit()
                if cursor.rowcount > 0:
                    return True, "Vehicle deleted successfully"
                return False, "Vehicle not found"
        except Exception as e:
            return False, f"Failed to delete vehicle: {str(e)}"
    
    def get_customer_for_vehicle(self, user_id: int, vehicle_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the customer associated with a vehicle (from most recent sales invoice).
        
        Args:
            user_id: The user ID
            vehicle_id: The vehicle ID
        
        Returns:
            Customer dictionary or None if no customer found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT c.id as internal_id, c.user_customer_id as id,
                           c.name, c.phone, c.house_name_no, c.street_address,
                           c.city, c.county, c.postcode, c.created_at
                    FROM sales_invoices si
                    JOIN customers c ON si.customer_id = c.id
                    WHERE si.vehicle_id = ? AND si.user_id = ?
                    ORDER BY si.document_date DESC, si.created_at DESC
                    LIMIT 1
                """, (vehicle_id, user_id))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception:
            return None
    
    def get_sales_history_for_vehicle(self, user_id: int, vehicle_id: int) -> List[Dict[str, Any]]:
        """
        Get sales history for a vehicle.
        
        Args:
            user_id: The user ID
            vehicle_id: The vehicle ID
        
        Returns:
            List of sales invoice dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, customer_id, vehicle_id, document_number, document_date,
                           document_type, notes, subtotal, vat_amount, total, status,
                           created_at, updated_at
                    FROM sales_invoices
                    WHERE vehicle_id = ? AND user_id = ?
                    ORDER BY document_date DESC, document_number DESC
                """, (vehicle_id, user_id))
                return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a database row to a dictionary."""
        data = dict(row)
        # Parse JSON fields
        if data.get('tyre_data'):
            data['tyre_data'] = json.loads(data['tyre_data'])
        if data.get('raw_response'):
            data['raw_response'] = json.loads(data['raw_response'])
        return data

