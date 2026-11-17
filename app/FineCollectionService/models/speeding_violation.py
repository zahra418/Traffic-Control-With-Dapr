from datetime import datetime
from pydantic import BaseModel

class SpeedingViolation(BaseModel):
    vehicleId: str
    roadId: str
    violationInKmh: int
    timestamp: datetime