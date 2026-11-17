import random
import threading
import time
from datetime import datetime

from events.vehicle_registered import VehicleRegistered


class CameraSimulation:
    _VALID_LICENSE_NUMBER_CHARS = "DFGHJKLNPRSTXYZ"

    def __init__(self, cam_number: int, traffic_control_service):
        self._cam_number = cam_number
        self._traffic_control_service = traffic_control_service
        self._rnd = random.Random()
        self._min_entry_delay_in_ms = 50
        self._max_entry_delay_in_ms = 5000
        self._min_exit_delay_in_s = 4
        self._max_exit_delay_in_s = 10

    def start(self) -> None:
        print(f"Start camera {self._cam_number} simulation.")

        while True:
            try:
                # simulate entry
                entry_delay = (self._rnd.randrange(self._min_entry_delay_in_ms,
                                                   self._max_entry_delay_in_ms)
                               + self._rnd.random()) / 1000
                time.sleep(entry_delay)

                # like Task.Run: each vehicle gets its own thread
                threading.Thread(target=self._simulate_vehicle, daemon=True).start()
            except Exception as ex:
                print(ex)

    def _simulate_vehicle(self) -> None:
        try:
            # simulate entry
            vehicle_registered = VehicleRegistered(
                lane=self._cam_number,
                licenseNumber=self._generate_random_license_number(),
                timestamp=datetime.now(),
            )
            self._traffic_control_service.send_vehicle_entry(vehicle_registered)
            print(f"Simulated ENTRY of vehicle with license-number "
                  f"{vehicle_registered.licenseNumber} in lane {vehicle_registered.lane}")

            # simulate exit
            exit_delay = (self._rnd.randrange(self._min_exit_delay_in_s,
                                              self._max_exit_delay_in_s)
                          + self._rnd.random())
            time.sleep(exit_delay)
            vehicle_registered.timestamp = datetime.now()
            vehicle_registered.lane = self._rnd.randrange(1, 4)
            self._traffic_control_service.send_vehicle_exit(vehicle_registered)
            print(f"Simulated EXIT of vehicle with license-number "
                  f"{vehicle_registered.licenseNumber} in lane {vehicle_registered.lane}")
        except Exception as ex:
            print(ex)

    # ---- private helper methods ----

    def _generate_random_license_number(self) -> str:
        r = self._rnd
        t = r.randrange(1, 9)
        if t == 1:    # 99-AA-99
            return f"{r.randrange(1, 99):02d}-{self._chars(2)}-{r.randrange(1, 99):02d}"
        if t == 2:    # AA-99-AA
            return f"{self._chars(2)}-{r.randrange(1, 99):02d}-{self._chars(2)}"
        if t == 3:    # AA-AA-99
            return f"{self._chars(2)}-{self._chars(2)}-{r.randrange(1, 99):02d}"
        if t == 4:    # 99-AA-AA
            return f"{r.randrange(1, 99):02d}-{self._chars(2)}-{self._chars(2)}"
        if t == 5:    # 99-AAA-9
            return f"{r.randrange(1, 99):02d}-{self._chars(3)}-{r.randrange(1, 10)}"
        if t == 6:    # 9-AAA-99
            return f"{r.randrange(1, 9)}-{self._chars(3)}-{r.randrange(1, 10):02d}"
        if t == 7:    # AA-999-A
            return f"{self._chars(2)}-{r.randrange(1, 999):03d}-{self._chars(1)}"
        return f"{self._chars(1)}-{r.randrange(1, 999):03d}-{self._chars(2)}"  # A-999-AA

    def _chars(self, count: int) -> str:
        valid = self._VALID_LICENSE_NUMBER_CHARS
        # len - 1 so the last character ("Z") is never picked
        return "".join(valid[self._rnd.randrange(len(valid) - 1)] for _ in range(count))