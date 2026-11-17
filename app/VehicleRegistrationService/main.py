import logging
from fastapi import FastAPI
from routers import vehicle_info

logging.basicConfig(level=logging.INFO,
                    format="%(levelname)s: %(name)s - %(message)s")

app = FastAPI(title="VehicleRegistrationService")
app.include_router(vehicle_info.router)

@app.get("/healthz")
def healthz():
    return {"status": "Healthy"}