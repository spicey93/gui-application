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
    services_requested = Signal()
    sales_requested = Signal()
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
        self.vehicles_view.services_requested.connect(self.handle_services)
        self.vehicles_view.sales_requested.connect(self.handle_sales)
        self.vehicles_view.configuration_requested.connect(self.handle_configuration)
        self.vehicles_view.logout_requested.connect(self.handle_logout)
        
        # Connect view action signals
        self.vehicles_view.vehicle_lookup_requested.connect(self.handle_vehicle_lookup)
        self.vehicles_view.vehicle_api_lookup_requested.connect(self.handle_api_lookup)
        self.vehicles_view.vehicle_selected.connect(self.handle_vehicle_selected)
        self.vehicles_view.vehicle_delete_requested.connect(self.handle_vehicle_delete)
    
    def set_user_id(self, user_id: int) -> None:
        """Set the current user ID."""
        self.user_id = user_id
        self.refresh_vehicles()
    
    def refresh_vehicles(self) -> None:
        """Clear the vehicles list and focus VRM input."""
        if self.user_id is None:
            return
        # Clear the table - don't show any vehicles until a search is performed
        self.vehicles_view.populate_vehicles([])
        self.vehicles_view.focus_vrm_input()
    
    def handle_vehicle_lookup(self, vrm: str) -> None:
        """Handle vehicle search request - search database for partial VRM matches."""
        if self.user_id is None:
            self.vehicles_view.show_message("Error", "Not logged in", is_error=True)
            return
        
        # Validate that query is not empty
        vrm = vrm.strip() if vrm else ""
        if not vrm:
            self.vehicles_view.show_message("Warning", "Please enter a VRM to search", is_error=False)
            return
        
        # Search for vehicles with partial VRM match
        vehicles = self.vehicle_model.search_vehicles_by_vrm(self.user_id, vrm)
        
        if not vehicles:
            self.vehicles_view.show_message(
                "No Results", 
                f"No vehicles found matching '{vrm}' in your database.",
                is_error=False
            )
            # Clear the table
            self.vehicles_view.populate_vehicles([])
            return
        
        # Populate table with search results
        self.vehicles_view.populate_vehicles(vehicles)
    
    def handle_api_lookup(self, vrm: str) -> None:
        """Handle external API lookup request for a VRM."""
        if self.user_id is None:
            self.vehicles_view.show_message("Error", "Not logged in", is_error=True)
            return
        
        # Check if vehicle already exists in database
        existing = self.vehicle_model.get_vehicle_by_vrm(self.user_id, vrm)
        if existing:
            reply = self.vehicles_view.confirm_api_lookup(
                vrm, 
                "Vehicle already exists in database. Update from API?"
            )
            if not reply:
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
            # Get customer and sales history for this vehicle
            customer = self.vehicle_model.get_customer_for_vehicle(self.user_id, vehicle_id)
            sales_history = self.vehicle_model.get_sales_history_for_vehicle(self.user_id, vehicle_id)
            self.vehicles_view.show_vehicle_details(vehicle, customer, sales_history)
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
    
    def handle_services(self) -> None:
        """Handle services navigation."""
        self.services_requested.emit()
    
    def handle_sales(self) -> None:
        """Handle sales navigation."""
        self.sales_requested.emit()
    
    def handle_configuration(self) -> None:
        """Handle configuration navigation."""
        self.configuration_requested.emit()
    
    def handle_logout(self) -> None:
        """Handle logout."""
        self.logout_requested.emit()

