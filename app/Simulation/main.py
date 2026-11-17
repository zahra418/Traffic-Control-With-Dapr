import threading
import time


from camera_simulation import CameraSimulation
from proxies.mqtt_traffic_control_service import MqttTrafficControlService


def main() -> None:
    lanes = 3

    for i in range(lanes):
        cam_number = i + 1
        traffic_control_service = MqttTrafficControlService(cam_number)
        camera = CameraSimulation(cam_number, traffic_control_service)
        # like Parallel.ForEach(cameras, cam => cam.Start())
        threading.Thread(target=camera.start, daemon=True).start()

    # like Thread.Sleep(Timeout.Infinite)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Simulation stopped.")


if __name__ == "__main__":
    main()