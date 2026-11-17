import logging
import os

import httpx
from fastapi import FastAPI

from domain_services.speeding_violation_calculator import DefaultSpeedingViolationCalculator
from publishers.violation_publisher import ViolationPublisher
from repositories.vehicle_state_repository import DaprVehicleStateRepository
# from repositories.vehicle_state_repository import InMemoryVehicleStateRepository
from routers import traffic

logging.basicConfig(level=logging.INFO,
                    format="%(levelname)s: %(name)s - %(message)s")

app = FastAPI(title="TrafficControlService")

dapr_http_port = os.getenv("DAPR_HTTP_PORT", "3500")

# Singletons, like the AddSingleton calls in Startup.cs
app.state.calculator = DefaultSpeedingViolationCalculator("A12", 10, 100, 5)

# app.state.vehicle_state_repository = InMemoryVehicleStateRepository()
app.state.vehicle_state_repository = DaprVehicleStateRepository(
    httpx.Client(
        base_url=f"http://localhost:{dapr_http_port}/v1.0/state/statestore",
        timeout=5.0,
    )
)


app.state.http_client = httpx.Client(
    base_url=f"http://localhost:{dapr_http_port}/v1.0/publish/pubsub",
    timeout=5.0,
)
app.state.publisher = ViolationPublisher(app.state.http_client)

app.include_router(traffic.router)


@app.get("/healthz")
def healthz():
    return {"status": "Healthy"}