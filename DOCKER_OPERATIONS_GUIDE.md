# AutoForge Docker Operations & Troubleshooting Guide

This guide details command-line procedures for building, running, and debugging the AutoForge Smart Manufacturing Data Intelligence platform in a containerized environment.

---

## 1. Core Operations Commands

All commands should be executed from the root of the repository.

### Build the Platform
Compiles/downloads all required Docker images:
```bash
docker compose build
```

### Start the Platform
Launches all services (`backend`, `simulator`, `frontend`) in the background (detached mode):
```bash
docker compose up -d
```

### View Logs
Displays consolidated logs from all services with log prefixes:
```bash
docker compose logs -f
```

### Service-Specific Logs
To monitor logs for a single service:
* **Backend API**:
  ```bash
  docker compose logs -f backend
  ```
* **Factory Simulator**:
  ```bash
  docker compose logs -f simulator
  ```
* **React Dashboard Frontend**:
  ```bash
  docker compose logs -f frontend
  ```

### Restart a Service
Restarts a container without rebuilding it (e.g. backend):
```bash
docker compose restart backend
```

### Rebuild a Specific Service
Forces a rebuild of a single service and starts it up (useful when changing package requirements):
```bash
docker compose up --build -d backend
```

### Stop the Platform
Stops and removes the container stack (preserves persistent volumes):
```bash
docker compose down
```

### Full Clean Tear-Down
Stops containers, removes networks, and deletes all anonymous volumes:
```bash
docker compose down -v
```

---

## 2. Troubleshooting & Common Issues

### Issue A: Port Conflicts (`8000` or `5173` already in use)
* **Symptom**: Container build/start fails with `bind: address already in use` or similar.
* **Diagnosis**: Another process on your host machine is already running on port 8000 (FastAPI) or 5173 (Vite).
* **Fix**:
  1. Find and kill the process using the port on Windows:
     - **Port 8000 (FastAPI)**:
       ```powershell
       Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess -Force
       ```
     - **Port 5173 (Vite)**:
       ```powershell
       Stop-Process -Id (Get-NetTCPConnection -LocalPort 5173).OwningProcess -Force
       ```
  2. Alternatively, edit the host port mappings in `docker-compose.yml` (e.g. change `"8000:8000"` to `"8080:8000"`).

### Issue B: AWS Credential Failures
* **Symptom**: Simulator or Backend container logs show `botocore.exceptions.NoCredentialsError: Unable to locate credentials` or Kinesis/Athena client connection timeouts.
* **Diagnosis**: Docker cannot locate the `.aws` credentials directory or configuration files.
* **Fix**:
  1. Ensure the `.aws` folder exists under your home directory on the host (`C:\Users\<username>\.aws`).
  2. Verify that `credentials` and `config` files are present inside the folder and have valid keys.
  3. Ensure your CLI session has credentials loaded (e.g. run `aws sts get-caller-identity` on the host to verify your session is valid).
  4. If you use custom env variables, explicitly set them in the shell before running `docker compose up`.

### Issue C: Container Startup Failures (`ModuleNotFoundError` or `Exit Code 1`)
* **Symptom**: Service stops immediately upon launch.
* **Diagnosis**: Python module missing or a configuration value was not injected.
* **Fix**:
  1. Inspect the stopped container logs:
     ```bash
     docker compose logs <service_name>
     ```
  2. If a dependency is missing, rebuild with no-cache:
     ```bash
     docker compose build --no-cache
     ```
  3. Ensure your local `.env` is fully populated with all keys in `.env.example`.

### Issue D: Health Check Failures (`unhealthy` container status)
* **Symptom**: `docker compose ps` shows a service is `unhealthy`.
* **Diagnosis**: 
  - Backend: API `/health` endpoint is not responding.
  - Simulator: Heartbeat file `logs/simulator.heartbeat` has not updated in the last 15 seconds.
  - Frontend: Vite dashboard is not serving index HTML.
* **Fix**:
  1. View logs to see if the process has hung:
     ```bash
     docker compose logs <service_name>
     ```
  2. For the simulator, check if `logs/simulator.heartbeat` is being generated and verify write permissions to the `logs` folder.
  3. Verify container resources (CPU/RAM). In Docker Desktop settings, verify that WSL 2 is allocated adequate memory (at least 2GB is recommended).
