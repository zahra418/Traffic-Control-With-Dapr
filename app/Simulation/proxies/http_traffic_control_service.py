import httpx

from events.vehicle_registered import VehicleRegistered


class HttpTrafficControlService:
    def __init__(self, http_client: httpx.Client):
        self._http_client = http_client

    def send_vehicle_entry(self, vehicle_registered: VehicleRegistered) -> None:
        self._http_client.post("http://localhost:6000/entrycam",
                               json=vehicle_registered.model_dump(mode="json"))

    def send_vehicle_exit(self, vehicle_registered: VehicleRegistered) -> None:
        self._http_client.post("http://localhost:6000/exitcam",
                               json=vehicle_registered.model_dump(mode="json"))