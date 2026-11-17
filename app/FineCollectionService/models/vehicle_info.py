from pydantic import BaseModel

class VehicleInfo(BaseModel):
    vehicleId: str
    brand: str
    model: str
    ownerName: str
    ownerEmail: str