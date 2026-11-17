import httpx

from models.vehicle_info import VehicleInfo


class VehicleRegistrationProxy:
    def __init__(self, http_client: httpx.Client):
        self._http_client = http_client

    def get_vehicle_info(self, license_number: str) -> VehicleInfo:
        response = self._http_client.get(f"/vehicleinfo/{license_number}")
        response.raise_for_status()
        return VehicleInfo(**response.json())