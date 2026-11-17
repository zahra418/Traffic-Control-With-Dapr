# Traffic Control with Dapr (Python)

A small microservices system that catches speeding cars. Two cameras on a road section report every car that enters and leaves. The system calculates the average speed, and speeding cars get a fine by email.

It uses [Dapr](https://dapr.io) for service calls, state, messaging, email and secrets, and runs fully on your own machine in three ways: with `dapr run`, with Docker Compose, or on a local Kubernetes cluster. No cloud account is needed.

## Services

| Service | Port | Job |
|---|---|---|
| VehicleRegistrationService | 6002 | Returns the owner of a vehicle (random data) |
| FineCollectionService | 6001 | Calculates the fine and emails it |
| TrafficControlService | 6000 | Receives camera messages, tracks cars, detects speeding |
| Simulation | none | Console program that plays the cameras with random cars |
| VisualSimulation | 5000 | Browser animation that plays the cameras |

Each service also has `GET /healthz`.

## Flow

    Simulation or VisualSimulation
        |  MQTT (Mosquitto)
        v
    TrafficControlService --(pub/sub, RabbitMQ)--> FineCollectionService --(service invocation)--> VehicleRegistrationService
      speed check                                    fine + email                                    owner lookup
                                                         |  SMTP
                                                         v
                                                      MailDev (read the emails)

## Project layout

    app/                      the services, Simulation and VisualSimulation
    dapr/components/          Dapr config for `dapr run`
    dapr/components-docker/   the same config for Docker Compose
    dapr/mosquitto/           Mosquitto config
    k8s/                      Kubernetes files and deploy.ps1
    docker-compose.yml

## Setup

You need Python 3.8+ (3.11 or 3.12 recommended), Docker Desktop and the [Dapr CLI](https://docs.dapr.io/getting-started/install-dapr-cli/).

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt

Create your secrets file (it is git-ignored) and put a license key in it:

    copy dapr\components\secrets.example.json dapr\components\secrets.json

## Run (with Dapr)

Run `dapr init` once. It starts Redis for you. Then start the other tools:

    docker run -d --name dtc-rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
    docker run -d --name dtc-maildev -p 4000:1080 -p 4025:1025 maildev/maildev
    docker run -d --name dtc-mosquitto -p 1883:1883 -p 9001:9001 -v ${PWD}/dapr/mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf eclipse-mosquitto

Open three terminals, activate the venv in each, and start one service per terminal:

    cd app\VehicleRegistrationService
    dapr run --app-id vehicle-registration-service --app-port 6002 --dapr-http-port 3602 --dapr-grpc-port 60002 --resources-path ..\..\dapr\components -- uvicorn main:app --port 6002

    cd app\FineCollectionService
    dapr run --app-id fine-collection-service --app-port 6001 --dapr-http-port 3601 --dapr-grpc-port 60001 --resources-path ..\..\dapr\components -- uvicorn main:app --port 6001

    cd app\TrafficControlService
    dapr run --app-id traffic-control-service --app-port 6000 --dapr-http-port 3600 --dapr-grpc-port 60000 --resources-path ..\..\dapr\components -- uvicorn main:app --port 6000

Then start a simulation (see below). Read the fine emails at http://localhost:4000. Stop a service with Ctrl+C.

## Run with Docker Compose

One command starts everything: the tools, the three services and a Dapr sidecar for each.

    docker compose up --build

Then start a simulation (see below). Emails: http://localhost:4000. RabbitMQ dashboard: http://localhost:15672.

Stop any `dapr run` terminals and `dtc-*` containers first, because they use the same ports. To stop the system:

    docker compose down

## Run on Kubernetes (local, kind)

Needs Docker, [kind](https://kind.sigs.k8s.io), `kubectl` and the Dapr CLI. One script creates the cluster, installs Dapr, builds and loads the images, and deploys everything:

    .\k8s\deploy.ps1

When it finishes, each service pod shows `2/2`. Open two more terminals to reach the cluster from your machine:

    kubectl port-forward -n traffic-control svc/mosquitto 1883:1883
    kubectl port-forward -n traffic-control svc/maildev 4000:1080

Then start a simulation (see below) and read the emails at http://localhost:4000. For the VisualSimulation, also forward port 9001 the same way (`svc/mosquitto 9001:9001`).

## Simulation

The console Simulation sends random cars on 3 lanes. Start the system first (any way above), then:

    cd app\Simulation
    python main.py

## Visual simulation (browser)

The same idea as the Simulation, but you watch cars drive on a 5-lane road. Start the system first, then:

    cd app\VisualSimulation
    uvicorn main:app --port 5000

Open http://localhost:5000. Do not run the console Simulation at the same time.

- The screen speed is not the speed the system computes (the road on screen is short, while the system assumes 10 km with 1 second = 1 minute). Only the fastest cars, roughly 126 km/h and above on screen, get a fine.
- If no cars appear, open the browser console (F12). `Socket error` means port 9001 is not reachable.

## Run without Dapr (optional)

Plain `uvicorn` works for quick checks of a single service. Anything that needs Dapr (state, messaging, email, secrets) fails without the sidecar.

    cd app\VehicleRegistrationService
    uvicorn main:app --port 6002 --reload

## Test by hand

Five seconds over the 10 km section is 120 km/h, which is 15 km/h over the limit after the 5 km/h correction.

    Invoke-RestMethod -Method Post -Uri http://localhost:6000/entrycam -ContentType "application/json" -Body '{"lane":1,"licenseNumber":"AB-123-C","timestamp":"2026-10-13T10:00:00"}'
    Invoke-RestMethod -Method Post -Uri http://localhost:6000/exitcam -ContentType "application/json" -Body '{"lane":2,"licenseNumber":"AB-123-C","timestamp":"2026-10-13T10:00:05"}'

Expected: `Speeding violation detected (15 KMh)` in TrafficControlService and `Fine: 130 AED` in FineCollectionService, plus an email in MailDev.

API docs: http://localhost:6001/docs and http://localhost:6002/docs. Browsers block port 6000, so TrafficControlService has no browser docs. Use PowerShell as above.

## Notes

- Dapr reads its config files only at startup. After changing a file in `dapr/components`, restart that service.
- Never commit `secrets.json` or any real key.
- The VisualSimulation front end (Phaser game, images, Paho client) comes from `EdwinVW/dapr-traffic-control`, folder `src/VisualSimulation`. Check its license before redistributing.