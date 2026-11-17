# Traffic Control with Dapr (Python)

A Python port of the WhatTheHack "Traffic Control with Dapr" sample. Cameras on a road section record cars entering and leaving. The average speed is calculated, and speeding cars get a fine by email.

All three services use Dapr building blocks: service invocation, state management, pub/sub, an MQTT input binding, an SMTP output binding and a secret store. The system runs locally in three ways: with `dapr run`, with Docker Compose, or on a local Kubernetes cluster (kind). No cloud account is needed.

## Services

| Service | Port | Job |
|---|---|---|
| VehicleRegistrationService | 6002 | `GET /vehicleinfo/{licenseNumber}` returns a random vehicle and owner |
| FineCollectionService | 6001 | `POST /collectfine` calculates the fine and builds the email |
| TrafficControlService | 6000 | `POST /entrycam` and `POST /exitcam` track cars and detect speeding |
| Simulation | none | Console program: generates random cars on 3 lanes and publishes their entry and exit over MQTT |
| VisualSimulation | 5000 | Browser animation of cars on a 5-lane road. Publishes the same MQTT messages as the Simulation |

Each service also has `GET /healthz`.

## Flow

    Simulation or VisualSimulation
        |  MQTT (Mosquitto)
        v
    TrafficControlService --(pub/sub, RabbitMQ)--> FineCollectionService --(service invocation)--> VehicleRegistrationService
      entry/exit, speed                              fine + email                                    owner lookup
                                                         |  SMTP binding
                                                         v
                                                      MailDev

## Project layout

    app/
      VehicleRegistrationService/
      FineCollectionService/
      TrafficControlService/
      Simulation/                console car generator (MQTT)
      VisualSimulation/          browser animation (wwwroot = static front end)
    dapr/
      components/                Dapr components for `dapr run` (localhost hosts)
      components-docker/         the same components for Docker Compose
      mosquitto/                 Mosquitto config (MQTT and WebSocket listeners)
    k8s/                         Kubernetes manifests (kind)
    docker-compose.yml
    requirements.txt

Every service has its own `main.py` and its own `requirements.txt`.

## Setup

Python 3.8 or newer (3.11 or 3.12 recommended).

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt

## Run (with Dapr)

The services need their Dapr sidecars. Start them with `dapr run`, not plain `uvicorn`.

Prerequisites: Docker running, `dapr init` done once, then start the infrastructure containers:

- Redis (state store), started by `dapr init` on port 6379
- RabbitMQ: `docker run -d --name dtc-rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management`
- MailDev: `docker run -d --name dtc-maildev -p 4000:1080 -p 4025:1025 maildev/maildev`
- Mosquitto: `docker run -d --name dtc-mosquitto -p 1883:1883 -p 9001:9001 -v ${PWD}/dapr/mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf eclipse-mosquitto`

Port 9001 is the WebSocket port that the VisualSimulation needs. `dapr/mosquitto/mosquitto.conf` must contain both listeners:

    listener 1883
    listener 9001
    protocol websockets
    allow_anonymous true

Copy `dapr/components/secrets.example.json` to `dapr/components/secrets.json` first.

Then open four terminals, activate the venv in each, and start the services from their own folders. The `app-id` must match the `scopes` in the component files exactly.

    cd app\VehicleRegistrationService
    dapr run --app-id vehicle-registration-service --app-port 6002 --dapr-http-port 3602 --dapr-grpc-port 60002 --resources-path ..\..\dapr\components -- uvicorn main:app --port 6002

    cd app\FineCollectionService
    dapr run --app-id fine-collection-service --app-port 6001 --dapr-http-port 3601 --dapr-grpc-port 60001 --resources-path ..\..\dapr\components -- uvicorn main:app --port 6001

    cd app\TrafficControlService
    dapr run --app-id traffic-control-service --app-port 6000 --dapr-http-port 3600 --dapr-grpc-port 60000 --resources-path ..\..\dapr\components -- uvicorn main:app --port 6000

    cd app\Simulation
    python main.py

Instead of the console Simulation you can use the VisualSimulation (see below). Stop any of them with Ctrl+C. Dapr reads component files only at startup, so restart the `dapr run` command after changing a component.

## Run with Docker Compose

One command starts the infrastructure (Redis, RabbitMQ, Mosquitto, MailDev), the three services, and a Dapr sidecar next to each service. No `dapr init` or `dapr run` is needed for this.

    docker compose up --build

Each service has a `Dockerfile` in its own folder. The sidecars load their components from `dapr/components-docker/`, which uses container names (`redis`, `rabbitmq`, `mosquitto`, `maildev`) instead of `localhost`. The secret store reads `dapr/components/secrets.json`, mounted into the FineCollection sidecar. Mosquitto publishes ports 1883 (MQTT) and 9001 (WebSocket).

Stop any `dapr run` terminals and the `dtc-*` containers first, because they use the same ports.

Then run the Simulation from `app\Simulation` with `python main.py`, or the VisualSimulation (see below). Neither is containerised yet. Read the fine emails at http://localhost:4000. RabbitMQ management is at http://localhost:15672.

    docker compose down

## Run on Kubernetes (local, kind)

Needs Docker, [kind](https://kind.sigs.k8s.io), `kubectl` and the Dapr CLI. The cluster uses Kubernetes v1.34, because newer versions refuse to run on hosts with cgroup v1.

    kind create cluster --name traffic-control --image kindest/node:v1.34.0
    dapr init -k --wait

Build the images and load them into the cluster (kind cannot see local Docker images):

    docker build -t vehicle-registration-service:local app\VehicleRegistrationService
    docker build -t fine-collection-service:local app\FineCollectionService
    docker build -t traffic-control-service:local app\TrafficControlService
    kind load docker-image vehicle-registration-service:local fine-collection-service:local traffic-control-service:local --name traffic-control

Create the license key secret from the git-ignored `secrets.json` (the value never goes into a file in the repo):

    kubectl apply -f k8s/namespace.yaml
    $key = (Get-Content dapr\components\secrets.json -Raw | ConvertFrom-Json).'finecalculator-licensekey'
    kubectl create secret generic finecalculator-licensekey --from-literal=finecalculator-licensekey=$key -n traffic-control

Deploy everything:

    kubectl apply -f k8s/infrastructure.yaml
    kubectl apply -f k8s/rbac.yaml
    kubectl apply -n traffic-control -f k8s/components/
    kubectl apply -f k8s/services.yaml
    kubectl get pods -n traffic-control

Each service pod should show `2/2` (the app and its Dapr sidecar). In `k8s/infrastructure.yaml`, the Mosquitto ConfigMap has both listeners and the Mosquitto Service exposes ports 1883 and 9001. To try it, forward the MQTT broker and MailDev to your machine, then run the Simulation:

    kubectl port-forward -n traffic-control svc/mosquitto 1883:1883
    kubectl port-forward -n traffic-control svc/maildev 4000:1080
    cd app\Simulation
    python main.py

Read the emails at http://localhost:4000. In the cluster the secret store is the built-in Kubernetes one (`k8s/components/secretstore.yaml`) instead of the local file.

## Visual simulation (browser)

`app\VisualSimulation` shows the traffic as an animation: cars drive along a 5-lane road, and each car publishes its entry and exit to MQTT, like the console Simulation does. The front end is a static web page (a Phaser game, car images and a Paho MQTT client) taken from the original sample and served by a small FastAPI app (`main.py`). All the logic runs in the browser. The browser connects to Mosquitto over WebSocket at `ws://127.0.0.1:9001`, so that port must be reachable from your machine:

- `dapr run` mode: the Mosquitto `docker run` command above already publishes 9001.
- Docker Compose: `docker-compose.yml` already publishes 9001.
- Kubernetes: run `kubectl port-forward -n traffic-control svc/mosquitto 9001:9001`.

Start the rest of the system first (any of the three ways above), then:

    cd app\VisualSimulation
    uvicorn main:app --port 5000

Open http://localhost:5000. Do not run the console Simulation at the same time.

Notes:

- The speed on screen is not the speed TrafficControlService computes. The road on screen is about 200 m long, while the service assumes a 10 km section and 1 second = 1 minute, so the computed speed is about 0.83 times the speed on screen. Only the fast "speed demon" cars (roughly 126 km/h and above on screen) get a fine.
- If no cars appear, open the browser console (F12). `Socket error` means port 9001 is not reachable. An error about a module script and `text/plain` means the `mimetypes` line in `main.py` is missing.

## Run without Dapr (optional)

Plain `uvicorn` still works for quick checks, but it only covers the original HTTP flow. State, pub/sub, MQTT, email and the secret store all need the sidecar, so `/collectfine` fails without it.

    cd app\VehicleRegistrationService
    uvicorn main:app --port 6002 --reload

## Test by hand

Five seconds over a 10 km section is 120 km/h, which is 15 km/h over the limit with the correction applied.

    Invoke-RestMethod -Method Post -Uri http://localhost:6000/entrycam -ContentType "application/json" -Body '{"lane":1,"licenseNumber":"AB-123-C","timestamp":"2026-10-13T10:00:00"}'
    Invoke-RestMethod -Method Post -Uri http://localhost:6000/exitcam -ContentType "application/json" -Body '{"lane":2,"licenseNumber":"AB-123-C","timestamp":"2026-10-13T10:00:05"}'

Expected: `Speeding violation detected (15 KMh)` in TrafficControlService, and `Fine: 130 AED` in FineCollectionService.

Interactive docs: `http://localhost:6001/docs` and `http://localhost:6002/docs`.

Note: browsers block port 6000 (`ERR_UNSAFE_PORT`), so `/docs` for TrafficControlService does not open in a browser. The service itself works fine from PowerShell, scripts, and Dapr.

## Notes

- The fine email is sent through the Dapr SMTP output binding (`sendmail`) to MailDev. Open http://localhost:4000 to read it.
- The license key for the fine calculator comes from the Dapr secret store (`trafficcontrol-secrets`, local file). Copy `dapr/components/secrets.example.json` to `dapr/components/secrets.json` and fill it in. `secrets.json` is git-ignored.
- The VisualSimulation front end (Phaser game, car images, Paho client) comes from the original sample, `EdwinVW/dapr-traffic-control`, folder `src/VisualSimulation`. Check that repository's license and credits before redistributing it.
- Never commit keys or connection strings.

## Status

- [x] VehicleRegistrationService (plain)
- [x] FineCollectionService (plain)
- [x] TrafficControlService (plain)
- [x] Simulation (HTTP)
- [x] Dapr service invocation
- [x] Dapr state management (Redis)
- [x] Dapr pub/sub (RabbitMQ)
- [x] Dapr input binding (MQTT, Mosquitto)
- [x] Dapr output binding (SMTP, MailDev)
- [x] Dapr secret store (local file)
- [x] Dockerfiles and Docker Compose
- [x] Kubernetes (local cluster, kind)
- [x] VisualSimulation (browser animation)