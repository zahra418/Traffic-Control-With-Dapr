import logging

from fastapi import APIRouter, Depends, Request, Response

from domain_services.speeding_violation_calculator import DefaultSpeedingViolationCalculator
from events.vehicle_registered import VehicleRegistered
from models.speeding_violation import SpeedingViolation
from models.vehicle_state import VehicleState
from publishers.violation_publisher import ViolationPublisher
from repositories.vehicle_state_repository import DaprVehicleStateRepository

logger = logging.getLogger(__name__)
router = APIRouter()


def get_repo(request: Request) -> DaprVehicleStateRepository:
    return request.app.state.vehicle_state_repository


def get_calculator(request: Request) -> DefaultSpeedingViolationCalculator:
    return request.app.state.calculator


def get_publisher(request: Request) -> ViolationPublisher:
    return request.app.state.publisher


@router.post("/entrycam")
def vehicle_entry(msg: VehicleRegistered,
                  repo: DaprVehicleStateRepository = Depends(get_repo)):
    try:
        # log entry
        logger.info(f"ENTRY detected in lane {msg.lane} at {msg.timestamp.strftime('%I:%M:%S')} "
                    f"of vehicle with license-number {msg.licenseNumber}.")

        # store vehicle state
        repo.save_vehicle_state(VehicleState(
            licenseNumber=msg.licenseNumber,
            entryTimestamp=msg.timestamp,
        ))
        return Response(status_code=200)
    except Exception:
        logger.exception("Error handling entry")
        return Response(status_code=500)


@router.post("/exitcam")
def vehicle_exit(msg: VehicleRegistered,
                 repo: DaprVehicleStateRepository = Depends(get_repo),
                 calculator: DefaultSpeedingViolationCalculator = Depends(get_calculator),
                 publisher: ViolationPublisher = Depends(get_publisher)):
    try:
        # get vehicle state
        vehicle_state = repo.get_vehicle_state(msg.licenseNumber)
        if vehicle_state is None:
            return Response(status_code=404)

        # log exit
        logger.info(f"EXIT detected in lane {msg.lane} at {msg.timestamp.strftime('%I:%M:%S')} "
                    f"of vehicle with license-number {msg.licenseNumber}.")

        # update state
        vehicle_state.exitTimestamp = msg.timestamp
        repo.save_vehicle_state(vehicle_state)

        # handle possible speeding violation
        violation = calculator.determine_speeding_violation_in_kmh(
            vehicle_state.entryTimestamp, vehicle_state.exitTimestamp)
        if violation > 0:
            logger.info(f"Speeding violation detected ({violation} KMh) of vehicle"
                        f"with license-number {vehicle_state.licenseNumber}.")

            speeding_violation = SpeedingViolation(
                vehicleId=msg.licenseNumber,
                roadId=calculator.get_road_id(),
                violationInKmh=violation,
                timestamp=msg.timestamp,
            )

            # publish speedingviolation
            publisher.publish(speeding_violation)

        return Response(status_code=200)
    except Exception:
        logger.exception("Error handling exit")
        return Response(status_code=500)