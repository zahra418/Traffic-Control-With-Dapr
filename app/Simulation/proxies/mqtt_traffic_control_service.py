import paho.mqtt.client as mqtt

from events.vehicle_registered import VehicleRegistered


class MqttTrafficControlService:
    def __init__(self, camera_number: int):
        # each camera needs its own client id, or the broker drops the older connection
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                                   client_id=f"simulation-cam-{camera_number}")
        self._client.connect("localhost", 1883, keepalive=60)
        self._client.loop_start()

    def send_vehicle_entry(self, vehicle_registered: VehicleRegistered) -> None:
        self._publish("trafficcontrol/entrycam", vehicle_registered)

    def send_vehicle_exit(self, vehicle_registered: VehicleRegistered) -> None:
        self._publish("trafficcontrol/exitcam", vehicle_registered)

    def _publish(self, topic: str, vehicle_registered: VehicleRegistered) -> None:
        info = self._client.publish(topic, vehicle_registered.model_dump_json(), qos=1)
        info.wait_for_publish()