import httpx

from models.speeding_violation import SpeedingViolation


class ViolationPublisher:
    """Plain HTTP stand-in for daprClient.PublishEventAsync (pub/sub, Challenge 4)."""

    def __init__(self, http_client: httpx.Client):
        self._http_client = http_client

    def publish(self, violation: SpeedingViolation) -> None:
        response = self._http_client.post(
            "/collectfine", json=violation.model_dump(mode="json"))
        response.raise_for_status()