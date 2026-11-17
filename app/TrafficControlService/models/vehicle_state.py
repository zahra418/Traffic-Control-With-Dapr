from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class VehicleState(BaseModel):
    licenseNumber: str
    entryTimestamp: datetime
    exitTimestamp: Optional[datetime] = None  