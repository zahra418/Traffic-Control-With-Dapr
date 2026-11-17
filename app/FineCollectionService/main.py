import logging
import os
import httpx
from fastapi import FastAPI

from routers import collection
from proxies.vehicle_registration_proxy import VehicleRegistrationProxy

logging.basicConfig(level=logging.INFO,
                    format="%(levelname)s: %(name)s - %(message)s")

app = FastAPI(title="FineCollectionService")

# `dapr run` sets DAPR_HTTP_PORT for the app (3601 here, 3500 on Kubernetes)
dapr_http_port = os.getenv("DAPR_HTTP_PORT", "3500")


# Service invocation: go through our own sidecar to the app-id
# "vehicle-registration-service" (counterpart of DaprClient.CreateInvokeHttpClient)
app.state.http_client = httpx.Client(
    base_url=os.getenv("VEHICLE_REGISTRATION_URL", # optional override for running without Dap
                       f"http://localhost:{dapr_http_port}/v1.0/invoke/vehicle-registration-service/method"),
    timeout=5.0,
)

app.state.dapr_client = httpx.Client(
    base_url=f"http://localhost:{dapr_http_port}/v1.0",
    timeout=5.0,
)

app.state.proxy = VehicleRegistrationProxy(app.state.http_client)

app.include_router(collection.router)


@app.get("/healthz")
def healthz():
    return {"status": "Healthy"}

@app.get("/dapr/subscribe")
def subscribe():
    return [{"pubsubname": "pubsub", "topic": "collectfine", "route": "/collectfine"}]