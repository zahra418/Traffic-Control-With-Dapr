import logging
from fastapi import APIRouter, Depends
from models.VehicleInfo import VehicleInfo
from repositories.VehicleInfoRepository import VehicleInfoRepository

logger = logging.getLogger(__name__)
router = APIRouter()

def get_repo() -> VehicleInfoRepository:
    return VehicleInfoRepository()

@router.get("/vehicleinfo/{license_number}", response_model=VehicleInfo)
def get_vehicle_info(license_number: str,
                     repo: VehicleInfoRepository = Depends(get_repo)):
    logger.info(f"Retrieving vehicle-info for licensenumber {license_number}")
    return repo.get(license_number)