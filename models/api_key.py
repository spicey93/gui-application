"""API key model for storing external service credentials."""
import sqlite3
from typing import Optional, List, Dict, Tuple
import os


class ApiKey:
    """API key model with database operations."""
    
    def __init__(self, db_path: str = "data/app.db"):
        """Initialize API key model with database path."""
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self) -> None:
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_database(self) -> None:
        """Initialize the database with api_keys table."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    service_name TEXT NOT NULL,
                    api_key TEXT NOT NULL,
                    UNIQUE(user_id, service_name),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            conn.commit()
    
    def save_api_key(self, user_id: int, service_name: str, api_key: str) -> Tuple[bool, str]:
        """
        Save or update an API key for a service.
        
        Args:
            user_id: The user ID
            service_name: Name of the service (e.g., 'uk_vehicle_data')
            api_key: The API key value
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not api_key:
            return False, "API key cannot be empty"
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO api_keys (user_id, service_name, api_key)
                    VALUES (?, ?, ?)
                    ON CONFLICT(user_id, service_name) DO UPDATE SET api_key = excluded.api_key
                """, (user_id, service_name, api_key))
                conn.commit()
            return True, "API key saved successfully"
        except Exception as e:
            return False, f"Failed to save API key: {str(e)}"
    
    def get_api_key(self, user_id: int, service_name: str) -> Optional[str]:
        """
        Get an API key for a service.
        
        Args:
            user_id: The user ID
            service_name: Name of the service
        
        Returns:
            The API key or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT api_key FROM api_keys WHERE user_id = ? AND service_name = ?",
                    (user_id, service_name)
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception:
            return None
    
    def get_all_api_keys(self, user_id: int) -> Dict[str, str]:
        """
        Get all API keys for a user.
        
        Args:
            user_id: The user ID
        
        Returns:
            Dictionary of service_name -> api_key
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT service_name, api_key FROM api_keys WHERE user_id = ?",
                    (user_id,)
                )
                return {row[0]: row[1] for row in cursor.fetchall()}
        except Exception:
            return {}
    
    def delete_api_key(self, user_id: int, service_name: str) -> Tuple[bool, str]:
        """
        Delete an API key.
        
        Args:
            user_id: The user ID
            service_name: Name of the service
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM api_keys WHERE user_id = ? AND service_name = ?",
                    (user_id, service_name)
                )
                conn.commit()
                if cursor.rowcount > 0:
                    return True, "API key deleted successfully"
                return False, "API key not found"
        except Exception as e:
            return False, f"Failed to delete API key: {str(e)}"

