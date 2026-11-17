import logging
from fastapi import APIRouter, Depends, Request, Body
import httpx

from domain_services.fine_calculator import FineCalculator
from helpers.email_utils import EmailUtils
from models.speeding_violation import SpeedingViolation
from proxies.vehicle_registration_proxy import VehicleRegistrationProxy

logger = logging.getLogger(__name__)
router = APIRouter()

def get_license_key(request: Request) -> str:
    # Fetched from the Dapr secret store on first use, then cached on the app.
    # (The sidecar may not be ready at app startup, so we don't fetch it earlier.)
    if not hasattr(request.app.state, "license_key"):
        response = request.app.state.dapr_client.get(
            "/secrets/trafficcontrol-secrets/finecalculator-licensekey")
        response.raise_for_status()
        request.app.state.license_key = response.json()["finecalculator-licensekey"]
    return request.app.state.license_key


_calculator = FineCalculator()

def get_calculator() -> FineCalculator:
    return _calculator


def get_proxy(request: Request) -> VehicleRegistrationProxy:
    return request.app.state.proxy

def get_speeding_violation(payload: dict = Body(...)) -> SpeedingViolation:
    # Pub/sub delivers a CloudEvent; a direct call (test.http) sends the plain JSON
    if "specversion" in payload and "data" in payload:
        payload = payload["data"]
    return SpeedingViolation(**payload)

def get_dapr_client(request: Request) -> httpx.Client:
    return request.app.state.dapr_client

@router.post("/collectfine")
def collect_fine(speeding_violation: SpeedingViolation = Depends(get_speeding_violation),
                 calculator: FineCalculator = Depends(get_calculator),
                 proxy: VehicleRegistrationProxy = Depends(get_proxy),
                 dapr_client: httpx.Client = Depends(get_dapr_client),
                 license_key: str = Depends(get_license_key)):
    fine = calculator.calculate_fine(license_key, speeding_violation.violationInKmh)

    # get owner info
    vehicle_info = proxy.get_vehicle_info(speeding_violation.vehicleId)

    # log fine
    fine_string = "tbd by the prosecutor" if fine == 0 else f"{fine} AED"
    ts = speeding_violation.timestamp
    logger.info(
        f"Sent speeding ticket to {vehicle_info.ownerName}. "
        f"Road: {speeding_violation.roadId}, Licensenumber: {speeding_violation.vehicleId}, "
        f"Vehicle: {vehicle_info.brand} {vehicle_info.model}, "
        f"Violation: {speeding_violation.violationInKmh} Km/h, Fine: {fine_string}, "
        f"On: {ts.strftime('%d-%m-%Y')} at {ts.strftime('%I:%M:%S')}."
    )

    # send fine by email
    body = EmailUtils.create_email_body(speeding_violation, vehicle_info, fine_string)

    metadata = {
        "emailFrom": "noreply@cfca.gov",
        "emailTo": vehicle_info.ownerEmail,
        "subject": f"Speeding violation on the {speeding_violation.roadId}",
    }

    # send fine by email (Dapr output binding "sendmail")
    response = dapr_client.post("/bindings/sendmail", json={
        "operation": "create",
        "data": body,
        "metadata": metadata,
    })
    response.raise_for_status()
    return {}