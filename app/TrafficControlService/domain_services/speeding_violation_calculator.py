from datetime import datetime


class DefaultSpeedingViolationCalculator:
    def __init__(self, road_id: str, section_length_in_km: int,
                 max_allowed_speed_in_kmh: int, legal_correction_in_kmh: int):
        self._road_id = road_id
        self._section_length_in_km = section_length_in_km
        self._max_allowed_speed_in_kmh = max_allowed_speed_in_kmh
        self._legal_correction_in_kmh = legal_correction_in_kmh

    def determine_speeding_violation_in_kmh(self, entry_timestamp: datetime,
                                            exit_timestamp: datetime) -> int:
        elapsed_minutes = (exit_timestamp - entry_timestamp).total_seconds()  # 1 sec == 1 min in simulation
        avg_speed_in_kmh = round((self._section_length_in_km / elapsed_minutes) * 60)
        return int(avg_speed_in_kmh - self._max_allowed_speed_in_kmh - self._legal_correction_in_kmh)

    def get_road_id(self) -> str:
        return self._road_id