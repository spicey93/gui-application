"""Vehicles controller."""
import requests
from typing import TYPE_CHECKING, Optional
from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from views.vehicles_view import VehiclesView
    from models.vehicle import Vehicle
    from models.api_key import ApiKey


class VehiclesController(QObject):
    """Controller for vehicles functionality."""
    
    # Navigation signals
    dashboard_requested = Signal()
    suppliers_requested = Signal()
    customers_requested = Signal()
    products_requested = Signal()
    inventory_requested = Signal()
    bookkeeper_requested = Signal()
    configuration_requested = Signal()
    logout_requested = Signal()
    
    UK_VEHICLE_DATA_URL = "https://legacy.api.vehicledataglobal.com/api/datapackage/TyreData"
    
    def __init__(
        self, 
        vehicles_view: "VehiclesView", 
        vehicle_model: "Vehicle",
        api_key_model: "ApiKey",
        user_id: Optional[int] = None
    ):
        """Initialize the vehicles controller."""
        super().__init__()
        self.vehicles_view = vehicles_view
        self.vehicle_model = vehicle_model
        self.api_key_model = api_key_model
        self.user_id = user_id
        
        # Connect view navigation signals
        self.vehicles_view.dashboard_requested.connect(self.dashboard_requested.emit)
        self.vehicles_view.suppliers_requested.connect(self.suppliers_requested.emit)
        self.vehicles_view.customers_requested.connect(self.customers_requested.emit)
        self.vehicles_view.products_requested.connect(self.products_requested.emit)
        self.vehicles_view.inventory_requested.connect(self.inventory_requested.emit)
        self.vehicles_view.bookkeeper_requested.connect(self.bookkeeper_requested.emit)
        self.vehicles_view.configuration_requested.connect(
            self.configuration_requested.emit
        )
        self.vehicles_view.logout_requested.connect(self.logout_requested.emit)
        
        # Connect view action signals
        self.vehicles_view.vehicle_lookup_requested.connect(self.handle_vehicle_lookup)
        self.vehicles_view.vehicle_selected.connect(self.handle_vehicle_selected)
        self.vehicles_view.vehicle_delete_requested.connect(self.handle_vehicle_delete)
    
    def set_user_id(self, user_id: int) -> None:
        """Set the current user ID."""
        self.user_id = user_id
        self.refresh_vehicles()
    
    def refresh_vehicles(self) -> None:
        """Refresh the vehicles list."""
        if self.user_id is None:
            return
        vehicles = self.vehicle_model.get_all_vehicles(self.user_id)
        self.vehicles_view.populate_vehicles(vehicles)
    
    def handle_vehicle_lookup(self, vrm: str) -> None:
        """Handle vehicle lookup request - check database first."""
        if self.user_id is None:
            self.vehicles_view.show_message("Error", "Not logged in", is_error=True)
            return
        
        # Check if vehicle exists in database first
        existing = self.vehicle_model.get_vehicle_by_vrm(self.user_id, vrm)
        if existing:
            # Vehicle found - show details
            self.vehicles_view.show_vehicle_details(existing)
            self.vehicles_view.clear_vrm_input()
            return
        
        # Vehicle not in database - ask user if they want to do API lookup
        if not self.vehicles_view.confirm_api_lookup(vrm):
            return
        
        # Get API key
        api_key = self.api_key_model.get_api_key(self.user_id, "uk_vehicle_data")
        if not api_key:
            self.vehicles_view.show_message(
                "Error", 
                "No UK Vehicle Data API key configured. Please add one in Configuration.",
                is_error=True
            )
            return
        
        # Make API request
        try:
            params = {"v": 2, "api_nullitems": 1, "key_vrm": vrm, "auth_apikey": api_key}
            response = requests.get(self.UK_VEHICLE_DATA_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Check response status
            status = data.get("Response", {}).get("StatusCode", "")
            if status != "Success":
                message = data.get("Response", {}).get("StatusMessage", "Lookup failed")
                self.vehicles_view.show_message("Lookup Failed", message, is_error=True)
                return
            
            # Extract vehicle details
            vehicle_details = data.get("Response", {}).get("DataItems", {}).get(
                "VehicleDetails", {}
            )
            tyre_details = data.get("Response", {}).get("DataItems", {}).get(
                "TyreDetails", {}
            )
            
            # Save vehicle
            success, message, vehicle_id = self.vehicle_model.save_vehicle(
                user_id=self.user_id,
                vrm=vrm,
                make=vehicle_details.get("Make", ""),
                model=vehicle_details.get("Model", ""),
                build_year=vehicle_details.get("BuildYear", ""),
                tyre_data=tyre_details,
                raw_response=data
            )
            
            if success:
                self.vehicles_view.show_message("Success", f"Vehicle {vrm} saved")
                self.vehicles_view.clear_vrm_input()
                self.refresh_vehicles()
            else:
                self.vehicles_view.show_message("Error", message, is_error=True)
                
        except requests.RequestException as e:
            self.vehicles_view.show_message(
                "Error", f"API request failed: {str(e)}", is_error=True
            )
    
    def handle_vehicle_selected(self, vehicle_id: int) -> None:
        """Handle vehicle selection to show details."""
        if self.user_id is None:
            return
        
        vehicle = self.vehicle_model.get_vehicle_by_id(self.user_id, vehicle_id)
        if vehicle:
            self.vehicles_view.show_vehicle_details(vehicle)
        else:
            self.vehicles_view.show_message("Error", "Vehicle not found", is_error=True)
    
    def handle_vehicle_delete(self, vehicle_id: int) -> None:
        """Handle vehicle delete request."""
        if self.user_id is None:
            return
        
        success, message = self.vehicle_model.delete_vehicle(self.user_id, vehicle_id)
        if success:
            self.refresh_vehicles()
        else:
            self.vehicles_view.show_message("Error", message, is_error=True)
