# deploy.ps1 - deploys Traffic Control with Dapr to a local kind cluster.
# Run from the repo root:  .\k8s\deploy.ps1   
# Cluster, Dapr and secret steps are skipped if they already exist.

$ErrorActionPreference = "Stop"

$cluster   = "traffic-control"
$namespace = "traffic-control"
$nodeImage = "kindest/node:v1.34.0"
$services  = @("vehicle-registration-service", "fine-collection-service", "traffic-control-service")
$folders   = @("VehicleRegistrationService", "FineCollectionService", "TrafficControlService")

# Always work from the repo root, wherever the script is started from.
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Run($description, [scriptblock]$command) {
    Write-Host ""
    Write-Host "==> $description" -ForegroundColor Cyan
    & $command
    if ($LASTEXITCODE -ne 0) { throw "Step failed: $description" }
}

# 1. Cluster (once)
$clusters = kind get clusters 2>$null
if ($clusters -notcontains $cluster) {
    Run "Creating kind cluster '$cluster'" { kind create cluster --name $cluster --image $nodeImage }
} else {
    Write-Host "Cluster '$cluster' already exists, skipping." -ForegroundColor Yellow
}
kubectl config use-context "kind-$cluster" | Out-Null

# 2. Dapr in the cluster (once)
kubectl get namespace dapr-system 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Run "Installing Dapr in the cluster" { dapr init -k --wait }
} else {
    Write-Host "Dapr already installed, skipping." -ForegroundColor Yellow
}

# 3. Build the images and load them into the cluster
for ($i = 0; $i -lt $services.Count; $i++) {
    $name = $services[$i]
    $dir  = "app\$($folders[$i])"
    Run "Building $name" { docker build -t "${name}:local" $dir }
}
$images = $services | ForEach-Object { "${_}:local" }
Run "Loading images into kind" { kind load docker-image @images --name $cluster }

# 4. Namespace and license key secret (never stored in a repo file)
Run "Applying namespace" { kubectl apply -f k8s/namespace.yaml }

kubectl get secret finecalculator-licensekey -n $namespace 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    $secretsFile = "dapr\components\secrets.json"
    if (-not (Test-Path $secretsFile)) {
        throw "Missing $secretsFile. Copy secrets.example.json to secrets.json and fill it in."
    }
    $key = (Get-Content $secretsFile -Raw | ConvertFrom-Json).'finecalculator-licensekey'
    Run "Creating license key secret" {
        kubectl create secret generic finecalculator-licensekey --from-literal=finecalculator-licensekey=$key -n $namespace
    }
} else {
    Write-Host "Secret already exists, skipping." -ForegroundColor Yellow
}

# 5. Deploy everything, in order
Run "Applying infrastructure" { kubectl apply -f k8s/infrastructure.yaml }
Run "Applying RBAC"           { kubectl apply -f k8s/rbac.yaml }
Run "Applying Dapr components" { kubectl apply -n $namespace -f k8s/components/ }
Run "Applying services"       { kubectl apply -f k8s/services.yaml }

# 6. Restart the services so they pick up freshly loaded images, then wait
foreach ($name in $services) {
    kubectl rollout restart deployment/$name -n $namespace 2>$null | Out-Null
}
Run "Waiting for services to be ready" {
    foreach ($name in $services) {
        kubectl rollout status deployment/$name -n $namespace --timeout=180s
        if ($LASTEXITCODE -ne 0) { exit 1 }
    }
}

Write-Host ""
kubectl get pods -n $namespace
Write-Host ""
Write-Host "Done. Each service pod should show 2/2." -ForegroundColor Green
Write-Host "To try it, open two more terminals:"
Write-Host "  kubectl port-forward -n $namespace svc/mosquitto 1883:1883"
Write-Host "  kubectl port-forward -n $namespace svc/maildev 4000:1080"
Write-Host "Then run the Simulation (cd app\Simulation; python main.py) and read emails at http://localhost:4000"