import threading
from typing import Dict, Optional
import httpx

from models.vehicle_state import VehicleState


class InMemoryVehicleStateRepository:
    def __init__(self):
        self._state: Dict[str, VehicleState] = {}
        self._lock = threading.Lock()  # stands in for ConcurrentDictionary

    def get_vehicle_state(self, license_number: str) -> Optional[VehicleState]:
        with self._lock:
            return self._state.get(license_number)

    def save_vehicle_state(self, vehicle_state: VehicleState) -> None:
        with self._lock:
            self._state[vehicle_state.licenseNumber] = vehicle_state
            

class DaprVehicleStateRepository:
    """Saves and reads vehicle state through the Dapr state API (store: statestore)."""

    def __init__(self, http_client: httpx.Client):
        # base_url is http://localhost:<dapr http port>/v1.0/state/statestore
        self._http_client = http_client

    def get_vehicle_state(self, license_number: str) -> Optional[VehicleState]:
        response = self._http_client.get(f"/{license_number}")
        if response.status_code == 204:      # Dapr answers 204 when the key doesn't exist
            return None
        response.raise_for_status()
        return VehicleState(**response.json())

    def save_vehicle_state(self, vehicle_state: VehicleState) -> None:
        response = self._http_client.post("", json=[{
            "key": vehicle_state.licenseNumber,
            "value": vehicle_state.model_dump(mode="json"),
        }])
        response.raise_for_status()